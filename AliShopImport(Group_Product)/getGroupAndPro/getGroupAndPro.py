# -*- coding: utf-8 -*-
"""
    2019/1/9    18:03
    完成功能：根据ali店铺的url地址提取产品分组及产品信息，包括并发检测及重复检测
            1.产品分组：上传至新增产品分组API并导入分组中间表
            2.产品：上传至新增产品API并导入产品中间表
            并发：
                情境一：不同tenant对同一url发起导入请求
                        可继续导入，tenant_id与shop_id联合查询，故无冲突
                情境二：同一tenant对同一url发起导入请求
                       建立导入记录表，对当前tenant_id及shop_id联合查询导入记录检查
                            a.查询记录结果以start_time倒序取第一条记录，其finished_time不为空：
                                该tenant对该店铺的前一次导入已结束，可继续导入
                            b.查询记录结果以start_time倒序取第一条记录，其finished_time为空：
                                该tenant对该店铺的前一次导入未结束，不可继续导入
            重复：（分组重复检测与产品重复检测思路一致）
                    根据ali分组/产品id及tenant_id查询分组/产品中间表
                            a.存在： -API  查询其原系统分组/产品ID并将其传至API
                                    -中间表    更新原对应数据记录
                            b.不存在：  -API    上传API并获取其分配的系统分组/产品ID
                                       -中间表     更新原对应数据记录
    入参：shopUrl  店铺URL
            有格式要求：https://taixiangfood.en.alibaba.com，后面可跟'/'
         tenant_id  租户ID
         account_id 账户ID
         language   语言
            选语言将导致整个产品分组及产品信息为同一语言，重复导入则将覆盖，即只支持单一语言
            EN  英文        CN  中文
    @lyt

"""
import urllib.request
from urllib import parse
import os
import re
import requests
import pymysql
import json
import traceback
from bs4 import BeautifulSoup
import time
import configparser
from retrying import retry
import datetime

#外部参数，传参方式还未确定
shopUrl = 'https://taixiangfood.en.alibaba.com'
# shopUrl = 'https://oreva.en.alibaba.com'
tenant_id = str(201)
account_id = str(201)
language = "CN"
ungroupedId = str(11111111111111)

################## 配置变量 || start ###################
#读取配置文件
conf=configparser.ConfigParser()
conf.read('config.ini')
#json相关
groupPacking = conf.get('product','group_packing')
groupFeature = conf.get('product','group_feature')
#API相关
headers = {
    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'content-type':'text/html;charset=UTF-8'
}
jsonAPIHeaders= {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'Content-Type': "application/json"
}
#新增产品分组API
uploadGroupAPIUrl = conf.get('api','api_newgroup_url')
uploadGroupQuerystring = {
    "tenantId":tenant_id,
    "accountId":account_id,
    "dirType": conf.get('api','api_newgroup_dirType')
}
#上传图片API
uploadImgAPIUrl = conf.get('api','api_uploadImg_url')
uploadImgQuerystring = {"tenantId":tenant_id,"accountId":account_id,"objectType":conf.get('api','api_uploadImg_objectType')}
#新增产品API
APIUrl = conf.get('api','api_newproduct_url')
APIquerystring = {"tenantId":tenant_id,"accountId":tenant_id}
#数据库连接相关
link_name = conf.get('database','db_link_name')
user_name = conf.get('database','db_user_name')
pwd = conf.get('database','db_pwd')
db_name = conf.get('database','db_name')
port = conf.getint('database','db_port')
charset = conf.get('database','db_charset')
################## 配置变量 || end ###################

shopSet = './shopSet'
imgSave = './imgSave'
startTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
#sql语句
insertGroup = 'insert into alip_group(alipg_id,group_name,shop_id,group_level,tenant_id,pro_group_id,parent_id)values('
sqlExistEN = "select label_en from alic_attribute where alic_nid=(select new_id from ali_category where id="
sqlExistCN = "select `label_zh-CN` from alic_attribute where alic_nid=(select new_id from ali_category where id="
sqlAttrId = "select new_display_id from alic_attribute where alic_nid=(select new_id from ali_category where id="
sqlRealCateId = "select new_category_id from `ali_category` where id="
sqlRealGroupId = "select pro_group_id from `alip_group` where alipg_id="
sqlProInsert = 'insert into product(record_id,tenant_id,productg_rid,product_code,`name`,product_model,product_images,productc_rid,\
hs_code,pitc_currency,pitc_price,pitc_unit,fob_currency,fob_min_price,fob_max_price,fob_unit,order_min_num,\
order_min_unit,packing_unit,packing_num_per_unit,packing_volume,packing_rough_weight,packing_desrciption,product_description,product_link,product_remarks,\
attachments,tenant_json,record_json,create_time,update_time,delete_flag,organization_rid,follow_category,remarks_for_purchasers,\
inventory_amount,reserved_amount,inventory_unit)\
values(%(recordId)s,%(tenantId)s,%(productgRid)s,%(productCode)s,%(productName)s,%(productModel)s,%(productImages)s,%(productcRid)s,\
%(hsCode)s,NULL,NULL,NULL,%(fobCurrency)s,%(fobMinPrice)s,%(fobMaxPrice)s,%(fobUnit)s,%(orderMinNum)s,\
%(orderMinUnit)s,%(packingUnit)s,%(packingNumPerUnit)s,%(packingVolume)s,%(packingRoughWeight)s,%(packingDesrciption)s,%(productDescription)s,%(productLink)s,NULL,\
NULL,%(tenantJson)s,%(recordJson)s,%(createTime)s,%(updateTime)s,0,NULL,3,NULL,\
0,0,NULL);'
sqlProUpdate = 'update product set record_id=%(recordId)s,productg_rid=%(productgRid)s,product_code=%(productCode)s,\
`name`=%(productName)s,product_model=%(productModel)s,product_images=%(productImages)s,productc_rid=%(productcRid)s,hs_code=%(hsCode)s,\
fob_currency=%(fobCurrency)s,fob_min_price=%(fobMinPrice)s,fob_max_price=%(fobMaxPrice)s,fob_unit=%(fobUnit)s,order_min_num=%(orderMinNum)s,\
order_min_unit=%(orderMinUnit)s,packing_unit=%(packingUnit)s,packing_num_per_unit=%(packingNumPerUnit)s,packing_volume=%(packingVolume)s,\
packing_rough_weight=%(packingRoughWeight)s,packing_desrciption=%(packingDesrciption)s,product_description=%(productDescription)s,\
product_link=%(productLink)s,tenant_json=%(tenantJson)s,record_json=%(recordJson)s,create_time=%(createTime)s,update_time=%(updateTime)s \
where tenant_id='+str(tenant_id)+' and product_code='

#导入前检查函数
@retry(stop_max_attempt_number=3,wait_random_min=1000,wait_random_max=2000)
def checkImportedRecord():
    try:
        response,soup = requestNet_get(shopUrl+'/productlist.html',headers)
        #以下情况一为另一种页面结构，在重构后暂未发现该组织方式的页面，预计为ali改版过程中旧版页面
        #注：由于后期代码重构，以下代码仅供参考
        # ali_name=soup.find_all('span',class_='cp-name')[0].text    #ali店铺名称
        # ali_id=soup.find_all('div',class_='add-fav')[0].get('data-fav-id')    #ali店铺id
        # # 情况一：页面中无json数据，硬解析(旧版本页面)
        # if soup.find('div', class_='app-productGroup'):
        #     proGroup = soup.find('div', class_='app-productGroup').find('div', class_='m-content')
        #     # 提取进行格式处理以甄别分组级别
        #     # 利用对空行计数对不同级分组列表进行分离，大多数为二级，阿里官方最多支持三级
        #     # 由于未找到有三级分组的店铺进行测试，尚不清楚该提取格式对三级分组是否有效
        #     with open(proGroupListTmp, 'a', encoding='utf-8')as f:
        #         f.write(html.unescape(proGroup.text))  # html.unescape()用于对转义字符的处理
        #     vailline = 0  # 空行计数
        #     groupLevelList = []
        #     with open(proGroupListTmp, 'r', encoding='utf-8') as f2:
        #         for line in f2:
        #             # line_name = replaceSpecailSignal(line)  # 对特殊符号进行处理,用于提取阿里的产品分组url
        #             if line.strip() == '':  # 若为空行，则计数后继续下一行
        #                 vailline += 1
        #                 continue
        #             if vailline <= 1:  # 空一行，表示为上一级的子集
        #                 groupLevelList.append(2)
        #                 vailline = 0
        #             elif vailline == 2:  # 空两行，表示为一级分组
        #                 groupLevelList.append(1)
        #                 vailline = 0
        #             else:  # 其它，表示为一级分组
        #                 groupLevelList.append(1)
        #                 vailline = 0
        #     hrefList = re.findall('href="(.+?)</a>', html.unescape(str(proGroup)))  # 提取所有分组id及分组名称
        #     index = 0
        #     for item in hrefList:
        #         tmpCrawl = re.sub(' title=("|\')(.+?)("|\')','',hrefList[index])
        #         # groupId = "".join(re.findall('/productgrouplist-(.+?)/', tmpCrawl))
        #         groupName = "".join(re.findall('>(.+?)$', tmpCrawl))
        #         with open(insertDBPGroup, 'a', encoding='utf-8') as gF:
        #             if groupLevelList[index] == 1:
        #                 num += 1
        #                 groupName = checkGroupName(groupName)
        #                 payload = "{\r\n  \"name\": \"" + groupName + "\",\r\n  \"parentRid\": null\r\n}"
        #                 level1_APIresponse = requests.request("POST", APIUrl, data=payload, headers=APIheaders,
        #                                                       params=querystring)
        #                 level1_groupId = level1_APIresponse.json()['data']
        #                 parentId = level1_groupId
        #                 gF.write(insertGroup + str(num) + ',' + level1_groupId + ',' + groupName + ',' + str(groupLevelList[index]) + ',' + str(shopId) + ',NULL);\n')
        #             if groupLevelList[index] == 2:
        #                 num += 1
        #                 groupName = checkGroupName(groupName)
        #                 payload = "{\r\n  \"name\": \"" + groupName + "\",\r\n  \"parentRid\": null\r\n}"
        #                 level2_APIresponse = requests.request("POST", APIUrl, data=payload, headers=APIheaders,
        #                                                       params=querystring)
        #                 level2_groupId = level2_APIresponse.json()['data']
        #                 gF.write(insertGroup + str(num) + ',' + level2_groupId + ',' + groupName + ',' + str(groupLevelList[index]) + ',' + str(shopId) + ',' + parentId + ');\n')
        #         index += 1
        # 情况二：页面中携带json信息，利用json提取
        global shopId
        shopId = str(json.loads(parse.unquote(soup.find_all('div',attrs={'module-title':'globalData'})[0].get('module-data')))['mds']['moduleData']['data']['companyId'])
        #导入前检查-导入记录表中是否存在该租户导入该店铺的记录（tenant_id、shop_id）
        #           1.存在    则检查finished_time字段是否为空
        #                       a）空     则该租户正在导入该店铺信息，不插入该条导入信息并停止后续导入，程序退出
        #                                   异常处理：若服务器网络断开，将造成程序中断且该用户无法再次导入该店铺数据
        #                                   解决方案：若finished_time字段为空，则提取该次记录的开始时间，若超过24h，则更新该记录并重新爬取数据
        #                       b）不为空       则该租户已导入过该店铺信息，插入该条导入记录并继续后续导入，程序继续
        #           2.不存在   则插入该条导入记录并继续后续导入，程序继续
        sqlIsImported = 'select * from `import_record` where tenant_id="' + tenant_id + '" and shop_id=' + shopId + ';'
        isImported = dbExcuSql(db, sqlIsImported)
        if isImported:
            sqlIsFinished = 'select start_time,finished_time from `import_record` where tenant_id="' + tenant_id + '" and shop_id=' + shopId + ' order by start_time desc;'
            isFinished = dbExcuSql(db, sqlIsFinished)
            if isFinished[1]:
                importExec(shopId,soup,1)
            else:
                if (datetime.datetime.strptime(startTime,'%Y-%m-%d %H:%M:%S')-isFinished[0]).days>=1:
                    print('--------已经正在导入该店铺产品且已超时--------')
                    sql_update_record = "update `import_record` set start_time='"+startTime+"' where tenant_id="+tenant_id+" and shop_id="+shopId+" and isnull(finished_time);"
                    dbExcuSql(db,sql_update_record)
                    importExec(shopId, soup,0)
                else:
                    print('--------已经正在导入该店铺产品--------')
        else:
            importExec(shopId,soup,1)
    except Exception as e:
        traceback.print_exc()
        print('-------店铺页面解析错误----------')
    finally:
        response.close()
#执行抓取函数
def importExec(shopId,soup,insertFlag):
    shopName = re.findall('https://(.+?)\.',shopUrl)[0]
    shopSingleDir = shopSet + '/' + tenant_id + '_' + str(startTime).replace(' ','').replace(':','').replace('-','') + '_' + shopName
    mkdir(shopSingleDir)
    insertDBPGroupFile = shopSingleDir + '/insertDBPGroup.txt'
    importRecordFile = shopSingleDir + '/importRecord.txt'
    try:
        if insertFlag:
            # 导入记录表中插入记录 || 开始
            sqlInsertImportRecord = "insert into import_record(tenant_id,shop_url,shop_id,import_language,start_time,finished_time)values(" \
                                    + tenant_id + ',"' + shopUrl + '",'+ shopId +',"' + language + '","' + startTime + '",NULL);'
            dbExcuSql(db,sqlInsertImportRecord)
            # 导入记录表中插入记录 || 结束
        # 产品分组导入部分 || 开始
        print('--------- 开始导入   ' + shopUrl + ' ----------\n----------START TIME: ' + startTime + '----------------\n')
        writeFile(importRecordFile,'--------- 开始导入   ' + shopUrl + ' ----------\n----------START TIME: ' + startTime + '----------------\n')
        if soup.find('div', class_='module-productGroups'):
            infoJson = json.loads(parse.unquote(soup.find_all('div', attrs={'module-title': 'productGroups'})[0].get('module-data')))
            groups = infoJson['mds']['moduleData']['data']['groups']
            flagUngrouped = 0
            for i in groups:
                firstLevelChildren = i['children']
                if i['id']==0:
                    checkExistGroup(str(i['id']),str(i['name']),str(shopId),str(1),str(ungroupedId),'NULL',insertDBPGroupFile)
                    flagUngrouped = 1
                    continue
                level1_groupId = uploadProGroup(i['name'], 'null')
                checkExistGroup(str(i['id']), str(i['name']), str(shopId), str(1), str(level1_groupId), 'NULL' ,insertDBPGroupFile)
                for j in firstLevelChildren:
                    secondLevelChildren = j['children']
                    level2_groupId = uploadProGroup(j['name'], level1_groupId)
                    checkExistGroup(str(j['id']),str(j['name']),str(shopId),str(2),str(level2_groupId),str(level1_groupId),insertDBPGroupFile)
                    for k in secondLevelChildren:
                        level3_groupId = uploadProGroup(k['name'], level2_groupId)
                        checkExistGroup(str(k['id']), str(k['name']), str(shopId), str(3), str(level3_groupId), str(level2_groupId),insertDBPGroupFile)
            if not flagUngrouped:      #若ali店铺分组中无‘未分组’提取，则默认为其创建一个‘未分组’
                checkExistGroup(str(0), 'Ungrouped', str(shopId), str(1), str(ungroupedId), 'NULL',insertDBPGroupFile)
        insertDB(insertDBPGroupFile, link_name, user_name, pwd, db_name, importRecordFile)
        # 产品分组导入部分 || 结束
        # 产品导入部分
        getProInfo(soup,shopSingleDir,importRecordFile)
        os.removedirs(imgSave)
        print('--------' + str(tenant_id) + '   导入结束----------')
        writeFile(importRecordFile,'--------' + str(tenant_id) + '   本次导入结束----------')
    except Exception as e:
        traceback.print_exc()
        print('导入信息插入失败')
        writeFile(importRecordFile,'--------导入信息插入失败----------')

#########################产品分组部分#########################################
#检查分组是否存在函数
def checkExistGroup(alipg_id,group_name,shop_id,group_level,pro_group_id,parent_id,insertDBPGroupFile):
    sql = 'select * from alip_group where tenant_id=' +tenant_id+ ' and alipg_id=' +alipg_id+ ';'
    sqlExistGroup = dbExcuSql(db,sql)
    if sqlExistGroup:
        with open(insertDBPGroupFile, 'a', encoding='utf-8')as f:
            f.write('update alip_group set group_name="' + group_name \
                    + '",group_level=' + group_level + ',shop_id=' + shop_id + ',parent_id=' + parent_id \
                    + ' where tenant_id=' + tenant_id + ' and alipg_id=' + alipg_id + ';\n')
    else:
        with open(insertDBPGroupFile, 'a', encoding='utf-8')as f:
            f.write(insertGroup+alipg_id+',"'+group_name+'",'+shop_id+','+group_level+','\
                    +tenant_id+','+pro_group_id+','+parent_id+');\n')
#调用新增产品分组API函数
def uploadProGroup(name, parentId):
    payload = "{\r\n  \"name\": \"" + name + "\",\r\n  \"parentRid\": " + parentId + "\r\n}"
    APIresponse = requestNet_post(uploadGroupAPIUrl,str(payload).encode('utf-8'),jsonAPIHeaders,uploadGroupQuerystring)
    groupId = str(APIresponse.json()['data'])
    return groupId
#数据库插入函数
def insertDB(file,link_name, user_name, pwd, db_name, importRecordFile):
    # 连接数据库，执行插入数据库语句文件
    db = pymysql.connect(link_name, user_name, pwd, db_name)
    cursor = db.cursor()
    totalData = 0
    num = 0
    for line in open(file, encoding="utf-8"):
        totalData += 1
        num += 1
        if num == 1000:
            num = 0
            try:
                cursor.execute(line)
            except:
                db.rollback
                print('产品分组插入数据库失败')
                writeFile(importRecordFile, '--------产品分组插入数据库失败----------')
            db.commit()
            db.close()
            db = pymysql.connect(link_name, user_name, pwd, db_name)
            cursor = db.cursor()
            continue
        else:
            try:
                cursor.execute(line)
            except:
                db.rollback
                print('产品分组插入数据库失败')
                writeFile(importRecordFile, '--------产品分组插入数据库失败----------')
    db.commit()
    db.close()

########################产品部分#############################################
#获取产品信息
def getProInfo(soup,shopSingleDir,importRecordFile):
    try:
        productSet = shopSingleDir + '/productSet'
        mkdir(productSet)
        # 获取totalPages的值 || 开始
        if soup.find('span', class_='next-pagination-display'):
            isNewVersion = soup.find('span', class_='next-pagination-display')
            if isNewVersion:
                totalPages = isNewVersion.text.split('/')[1]
        else:
            totalPages = 1
        # 获取totalPages的值 || 结束
        # 针对每一页提取产品信息
        curPage = 1
        testNum = 0
        while curPage <= int(totalPages):
            infoJson = json.loads(
                parse.unquote(soup.find('div', attrs={'module-title': 'productListPc'}).get('module-data')))
            productList = infoJson['mds']['moduleData']['data']['productList']
            for i in productList:
                testNum += 1
                if language=="EN":
                    product_link = shopUrl+i['url']  # 英语
                elif language=="CN":
                    product_link = 'https:'+i['url']   # 中文
                try:
                    product_name, product_code, record_id = dealSinglePro(i, product_link, productSet)
                    print(str(testNum) + ':aliId_' + str(product_code) + ':' + str(record_id) + ':' + product_name)
                    writeFile(importRecordFile, str(testNum) + ':aliId_' + str(product_code) + ':' + str(record_id) + ':' + product_name + '\n')
                except Exception as e:
                    traceback.print_exc()
                    print('----------------单个产品导入失败-----------------')
                    writeFile(importRecordFile,'-------------单个产品导入失败-------------\n'+str(testNum) + ' ' + product_link + '\n')
            curPage += 1
            try:
                response,soup = requestNet_get(shopUrl + '/productlist-' + str(curPage) + '.html',headers)
            except Exception as e:
                traceback.print_exc()
    except Exception as e:
        traceback.print_exc()
        print('----error 1----')
    print('-----------------finished-----------------')
    writeFile(importRecordFile,'-----------------finished-----------------\n')
# 单个产品信息提取函数
def dealSinglePro(i, product_link, productSet):
    try:
        response = requestNet_get(product_link,headers)[0]
        product_code = i['id']
        sql = 'select record_id from product where tenant_id='+str(tenant_id)+' and product_code='+str(product_code)+';'
        pre_record_id = dbExcuSql(db,sql)
        if pre_record_id:
            pre_record_id = pre_record_id[0]
        singleProHTMLFile = productSet + '/' + str(product_code) + '_html.txt'
        writeFile(singleProHTMLFile,tenant_id+'  '+shopUrl+'  https:'+i['url']+'\nstart time: '+startTime+'\n'+response.text+'\n')
        product_images, productc_rid, new_productc_rid = getJsonAttr(response.text)
        #sku属性相关
        # product_model, packing_unit, packing_num_per_unit, packing_volume, packing_rough_weight, packing_desrciption, hs_code, \
        # product_description, tenant_json, record_json = dealNoInjson(response.text, hasSkuInfoFlag, productSku, productc_rid, skuNames)
        product_model, packing_unit, packing_num_per_unit, packing_volume, packing_rough_weight, packing_desrciption, \
        product_description, tenant_json, record_json = dealNoInjson(response.text, productc_rid)
        fob_currency = None
        fob_min_price = None
        fob_max_price = None
        fob_unit = None
        order_min_num = None
        order_min_unit = None
        hs_code = None
        product_name = dealDevil(i['subject'].replace('"', '\\"'))
        productg_rid = str(i['groupId'])
        # 查询数据库产品分组的系统id
        productg_rid = str(dbExcuRealGroupId(db, sqlRealGroupId, productg_rid))
        if 'fobPrice' in i:
            fob_currency = i['currencyType'] + ' ' + i['currencySymbol']
            fob_price = i['fobPrice'].split(i['currencyType'] + ' ' + i['currencySymbol'])[1].split('/')[0]
            if '-' in fob_price:
                fob_min_price = float(fob_price.split('-')[0])
                fob_max_price = float(fob_price.split('-')[1])
            else:
                fob_min_price = float(fob_price)
                fob_max_price = None
            fob_unit = i['fobUnit']
        if 'moq' in i:
            order_min_num = float(i['moq'].split(' ')[0].replace(',', ''))
            order_min_unit = i['moq'].split(' ')[1]
        createTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        updateTime = createTime
        #调用新增产品API
        payload = {
            "recordId": pre_record_id or 'NULL',
            "fobCurrency": fob_currency or 'NULL',
            "fobMaxPrice": fob_max_price or 'NULL',
            "fobMinPrice": fob_min_price or 'NULL',
            "fobUnit": fob_unit or 'NULL',
            "followCategory": 3,
            "inventoryAmount": 0,
            "name": product_name,
            "orderMinNum": order_min_num or 'NULL',
            "orderMinUnit": order_min_unit or 'NULL',
            "packingDesrciption": packing_desrciption or 'NULL',
            "packingNumPerUnit": 'NULL',
            "packingRoughWeight": packing_rough_weight or 'NULL',
            "packingUnit": packing_unit or 'NULL',
            "packingVolume": packing_volume or 'NULL',
            "productDescription": product_description or 'NULL',
            "productImages": str(product_images).replace('[', '').replace(']', '').replace(' ', ''),
            "productLink": product_link,
            "productModel": product_model or 'NULL',
            "productcRid": new_productc_rid,
            "productgRid": int(productg_rid),
            "recordJson": record_json,
            "tenantJson": tenant_json,
            "reservedAmount": 0
        }
        try:
            APIresponse = requestNet_post(APIUrl,str(payload).replace("'NULL'",'NULL').encode('utf-8'),jsonAPIHeaders,APIquerystring)
        except Exception as e:
            traceback.print_exc()
            print('新增产品API调用出错')
        record_id = APIresponse.json()['data']
        #上传至远程数据库中间表
        insertProLoad = {
            # "taskId": task_id,
            "recordId": int(record_id),
            "tenantId": tenant_id,
            "productgRid": int(productg_rid),
            "productCode": product_code,
            "productName": product_name,
            "productModel": product_model,
            "productImages": str(product_images).replace('[', '').replace(']', '').replace(' ', ''),
            "productcRid": new_productc_rid,
            "hsCode": hs_code,
            "fobCurrency": fob_currency,
            "fobMinPrice": fob_min_price,
            "fobMaxPrice": fob_max_price,
            "fobUnit": fob_unit,
            "orderMinNum": order_min_num,
            "orderMinUnit": order_min_unit,
            "packingUnit": packing_unit,
            "packingNumPerUnit": packing_num_per_unit,
            "packingVolume": packing_volume,
            "packingRoughWeight": packing_rough_weight,
            "packingDesrciption": packing_desrciption,
            "productDescription": product_description,
            "productLink": product_link,
            "tenantJson": tenant_json,
            "recordJson": record_json,
            "createTime": createTime,
            "updateTime": updateTime,
        }
        try:
            cursor = db.cursor()
            if pre_record_id:
                cursor.execute(sqlProUpdate+str(product_code)+';',insertProLoad)
            else:
                cursor.execute(sqlProInsert,insertProLoad)
            db.commit()
        except Exception as e:
            traceback.print_exc()
            print('产品中间表导入数据出错')
        return product_name, product_code, record_id
    except Exception as e:
        traceback.print_exc()
        print('------单个产品信息提取出错------')
#  对页面中携带的json信息解析提取
def getJsonAttr(text):
    if re.findall('window\._PAGE_SCHEMA_', text):
        proJsonText = BeautifulSoup(text, "html.parser").findAll('script')
        for js in proJsonText:
            if re.findall('window\._PAGE_SCHEMA_ =', js.text):
                proJson = json.loads(re.findall('window\._PAGE_SCHEMA_ = (.+?)$', js.text)[0])
                childrenAttr_010 = proJson['children'][0]['children'][1]['children'][0]['attributes']
                # ali图片上传API返回id
                imgUrls = proJson['children'][1]['children'][0]['children'][0]['attributes']['productImage']['value'][
                    'urls']
                # 产品图片id
                product_images = getImgId(imgUrls)
                # categoryId产品类目ID
                productc_rid = childrenAttr_010['productCategoryId']['value']
                #查询数据库系统产品类目id
                new_productc_rid = dbExcuRealRecordId(db, sqlRealCateId, productc_rid)
                # sku属性相关
                # sku部分（颜色等）    sku属性提取
                # childrenAttr_110 = proJson['children'][1]['children'][1]['children'][0]['attributes']
                # if childrenAttr_110['productSkuInfo'].get('value') == None:
                #     hasSkuInfoFlag = 0
                #     productSku = ''
                # else:
                #     productSkuInfo = childrenAttr_110['productSkuInfo']['value']
                #     hasSkuInfoFlag = 1
                #     productSku = ''
                #     skuNames = []
                #     for j in productSkuInfo:
                #         skuName = j['name']
                #         skuNames.append(skuName)
                #         skuValues = j['values']
                #         skuItem = ''
                #         skuImgId = ''
                #         for k in skuValues:
                #             skuValuesName = k['name']
                #             skuValuesColor = k['color']
                #             skuValuesType = k['type']
                #             skuValuesImg = k['largeImage']
                #             if skuValuesType == "IMAGE":
                #                 skuImgId = '1'
                #                 # skuImg = urllib.request.urlopen('http:' + k['largeImage'])
                #                 # imgSavePath = imgSave + '/' + skuValuesName
                #                 # with open(imgSavePath, 'wb') as f:
                #                 #     f.write(skuImg.read())
                #                 # file = open(imgSavePath, 'rb')
                #                 # files = {'file': file}
                #                 # skuImgId = int(requests.post(imgUploadUrl, files=files).json()['data']['fileId'])
                #                 # file.close()
                #                 # os.remove(imgSavePath)
                #                 # skuItem += '{"name":"' + skuValuesName + '","color":"' + skuValuesColor + '","type":"' + skuValuesType + '","skuImgId":' + str(
                #                 #     skuImgId) + '},'
                #                 skuItem += str(skuImgId) + ','
                #             elif skuValuesType == "COLOR":
                #                 skuItem += skuValuesColor + ','
                #             elif skuValuesType == "TEXT":
                #                 skuItem += skuValuesName + ','
                #         productSku += '"' + skuName + '":"' + skuItem.strip(',') + '",'
                #     productSku = productSku.strip(',')
    return product_images, productc_rid, new_productc_rid
#  对页面中json信息中不携带的信息做提取
def dealNoInjson(text, productc_rid):
    product_model = None
    packing_unit = None
    packing_volume = None
    packing_rough_weight = None
    packing_desrciption = None
    packing_num_per_unit = None
    port = ''
    # 针对json中没有的信息爬取页面信息做处理
    detailsSoup = BeautifulSoup(text, "html.parser")
    detail_overview = detailsSoup.find('div', class_='details-info').find('div',class_='do-overview')
    detail_module = detail_overview.findAll('div', class_='do-entry')
    tenant_json = '{"'+groupFeature+'":{'
    record_json = '['
    proNum = 0
    recordNum = 0
    for i in detail_module:
        proNum += 1
        title = (i.find('div', class_='do-entry-title') or i.find('h3',class_='do-entry-title')).text
        detailList = i.findAll('dl')
        if title == 'Quick Details' or title == '简介':
            if language == "EN":
                attrList,attrIdList = dbExcu(db, sqlExistEN, productc_rid)
            elif language == "CN":
                attrList,attrIdList = dbExcu(db, sqlExistCN, productc_rid)
            attrSet = []        #基础属性（数据库查询）
            attrIdStr = []      #基础属性ID
            for attr in attrList:
                attrSet.append(attr[0])
            for attrId in attrIdList:
                attrIdStr.append(attrId[0])
            # sku属性相关
            # for skuItem in skuNames:
            #     new = str(attrIdStr[attrSet.index(skuItem)])
            #     productSku = productSku.replace(skuItem,new)
            for j in detailList:
                tenantFlag = 0
                detailTag = j.find('span').text.strip(':')
                detailValue = j.find('div', class_='ellipsis').text
                if detailTag == 'Model Number' or detailTag == '型号':
                    product_model = detailValue
                for item in attrSet:
                    if detailTag == item:  # 租户级自定义
                        tenantFlag = 1
                        tenant_json += '"' + str(attrIdStr[attrSet.index(detailTag)]) + '":"' + dealDevil(detailValue).strip() + '",'
                        break
                    else:
                        continue
                if tenantFlag == 0:     # 记录级自定义
                    recordNum += 1
                    record_json += '{"groupCode": '+groupFeature+',"key":"'+groupFeature+'_'+str(recordNum) +'","label":"'+ dealDevil(detailTag) + '","value":"' + dealDevil(detailValue).strip() + '"},'
                    continue
                else:
                    continue
        if title == 'Packaging & Delivery' or title == '包装与物流':
            for j in detailList:
                detailTag = j.find('dt').text.strip()
                detailValue = j.find('dd').text
                if detailTag == 'Selling Units:':
                    packing_unit = dealDevil(detailValue)
                #暂未找到对应关系字段
                # elif detailTag == 'Packing Num Per Unit':
                #     packing_num_per_unit = dealDevil(detailValue)
                elif detailTag == 'Single package size:':
                    if 'X' in detailValue:
                        nums = detailValue.split('X')
                        packing_volume = int(nums[0]) * int(nums[1]) * int(nums[2].split(' ')[0])*0.000001
                    else:
                        packing_volume = int(detailValue.split(' ')[0])
                elif detailTag == 'Single gross weight:':
                    packing_rough_weight = dealDevil(detailValue.split(' ')[0])
                elif detailTag == 'Packaging Details':
                    packing_desrciption = dealDevil(detailValue)
                    packing_desrciption = packing_desrciption.replace('\r\n', ' ')
                elif detailTag == 'Port':
                    port = ',{"groupCode":'+groupPacking+',"key":"'+groupPacking+'_1","label":"Port","value":"'+dealDevil(detailValue)+'"}'
    # 产品描述
    product_description = ''
    if detailsSoup.find('div', attrs={'data-section-title': 'Product Description'}):
        product_description_module = detailsSoup.find('div', attrs={
            'data-section-title': 'Product Description'}).findAll('p')
        for p in product_description_module:
            product_description += dealDevil(p.text.strip("\n"))
    elif detailsSoup.find('div', class_='rich-text-description'):
        product_description_module = detailsSoup.find('div',class_='rich-text-description').findAll('p')
        for p in product_description_module:
            product_description += dealDevil(p.text)
    product_description = " ".join(product_description.split())
    # sku属性相关
    # if hasSkuInfoFlag:
    #     tenant_json = tenant_json + productSku + '}'
    # else:
    #     tenant_json = tenant_json.strip(',') + '}'
    tenant_json = tenant_json.strip(',') + '}}'
    record_json = record_json.strip(',')+']'+port
    return product_model,packing_unit,packing_num_per_unit,packing_volume,packing_rough_weight,packing_desrciption,\
           product_description, tenant_json, record_json
#  数据库操作函数，通过ali的产品分组id查询系统产品分组id
def dbExcuRealGroupId(db, sql, productg_rid):
    cursor = db.cursor()
    realId = sql + str(productg_rid) + ";"
    cursor.execute(realId)
    productg_rid = cursor.fetchall()
    if productg_rid:
        productg_rid = productg_rid[0][0]
    else:
        productg_rid = ungroupedId   #三级分组归并至默认‘未分组’中
    return productg_rid
#  图片上传函数,上传图片至服务器并获取返回的图片ID
def getImgId(imgUrls):
    imgId = []
    pic_num = 0
    for imgUrl in imgUrls:
        pic_num += 1
        imgName = imgUrl['big'].split('/')[5]
        link_img = urllib.request.urlopen('http:' + imgUrl['big'])
        imgSavePath = imgSave + '/' + str(pic_num) + '-' + imgName
        with open(imgSavePath, 'wb') as f:
            f.write(link_img.read())
        file = open(imgSavePath, 'rb')
        files = {'file': file}
        imgId.append(int(requests.post(uploadImgAPIUrl, files=files).json()['data']['fileId']))
        file.close()
        try:
            os.remove(imgSavePath)
        except Exception as e:
            pass
    return imgId
#  数据库操作函数，通过ali的产品类目id查询系统产品类目id
def dbExcuRealRecordId(db, sql, productc_rid):
    cursor = db.cursor()
    realId = sql + str(productc_rid) + ";"
    cursor.execute(realId)
    productc_rid = cursor.fetchall()[0][0]
    return productc_rid
# 数据库操作函数,数据库查询比对后分解，取出当前产品类目的所有基础属性
def dbExcu(db, sql, productc_rid):
    cursor = db.cursor()
    isExist = sql + str(productc_rid) + ");"
    attrId = sqlAttrId + str(productc_rid) + ");"
    cursor.execute(isExist)
    result = cursor.fetchall()
    cursor.execute(attrId)
    attrIdList = cursor.fetchall()
    return result, attrIdList

def dbExcuSql(db, sql):
    result=()
    try:
        cursor = db.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        db.commit()
    except Exception as e:
        traceback.print_exc()
        db.rollback()
        print('数据库操作失败')
        endImport()
    # finally:
    # db.close()
    return result
def writeFile(file,context):
    with open(file,'a',encoding='utf-8') as f:
        f.write(context)
def requestNet_get(url,headers):
    try:
        response = requests.request("GET", url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
    except:
        while max_try_attept>0:
            try:
                response = requests.request("GET", url, headers=headers)
                soup = BeautifulSoup(response.text, "html.parser")
                max_try_attept = max_try_attept - 1
            except:
                print('get请求出错')
    return response,soup
def requestNet_post(url,data,headers,params):
    try:
        response = requests.request("POST", url, data=data, headers=headers, params=params)
    except:
        while max_try_attept>0:
            try:
                response = requests.request("POST",url,data=data,headers=headers,params=params)
                max_try_attept = max_try_attept - 1
            except:
                print('post请求出错')
    return response
def endImport():
    finishedTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    sql = 'update import_record set finished_time="' + finishedTime + '" where tenant_id=' + tenant_id + ' and shop_id=' + shopId + ' and start_time="' + startTime + '";'
    dbExcuSql(db, sql)
def mkdir(dirPath):
    if not os.path.exists(dirPath):
        os.mkdir(dirPath)
def dealDevil(s):
    if "'" in s:
        s = s.replace("'","\\'")
    return s

if __name__ == '__main__':
    db = pymysql.connect(
        host=link_name,
        port=port,
        user=user_name,
        passwd=pwd,
        db=db_name,
        charset=charset
    )
    mkdir(shopSet)
    mkdir(imgSave)
    if language == 'CN':
        shopUrl = shopUrl + '/zh_CN'
    checkImportedRecord()
    endImport()
    try:
        db.close()
    except:
        pass