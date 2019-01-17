'''
    2018/11/28  15:53
    功能：获取阿里所有末级产品类目的属性页面Json相关数据并储存
    爬取时需手动更改的内容：cookie值，涉及登录验证，须从浏览器登录账号进入https://post.alibaba.com/product/category.htm页面，手动获取cookie值（注：其中包含多语言信息）
                        1.getAliCatAttrJson.py中cookie参数更改
                        2.getAliCatAttrJson文件夹下curGetUrl.bat中cookie参数更改
    若更换文件夹路径，则相应路径均需更改
    @lyt
'''
import sys
import importlib
import requests
import time
import traceback
import subprocess
import pymysql
import re
import os
importlib.reload(sys)
#携带传递信息部分
cookie = "_bl_uid=avjR2oeC95IsbglwUa3CvXU6zLg7; ali_apache_id=11.179.217.160.1540172152871.110138.6; cna=ehdUFD0kpUMCAdpqddIjxJD7; ali_ab=218.106.117.210.1540172155756.8; t=1f3534590bddc634e04f73213b60dbe8; gangesweb-buckettest=218.106.117.210.1540172156412.0; UM_distinctid=16699946bf4c63-0bcc78584b2cc8-b79193d-1fa400-16699946bf547c; _ga=GA1.2.21064647.1540279409; __utma=226363722.21064647.1540279409.1542959283.1542959283.1; __utmz=226363722.1542959283.1.1.utmcsr=alibaba.com|utmccn=(referral)|utmcmd=referral|utmcct=/product-detail/Mentorvii-shockproof-tpu-smart-phone-case_60804075629.html; history=company%5E%0A232290982; _m_h5_tk=df10a524eaa48679b95f3cb44261faef_1545799906756; _m_h5_tk_enc=48137728562c39a3fe76eae7efc407ad; sc_g_cfg_f=sc_b_locale=de_DE&sc_b_site=GLO; acs_usuc_t=acs_rt=c9deb318cea344ec87f763a45046dc90; cookie2=1511fe9e193a9c708f23bb41c1d74d05; _tb_token_=78eb065e4577e; XSRF-TOKEN=7955f991-d33c-4951-963d-9c9c7f267707; _csrf_token=1545964709556; acs_rt=9a5376a048ed48ad9cd298eddb2bb580; ali_apache_tracktmp=W_signed=Y; _hvn_login=4; csg=489a48eb; xman_us_t=ctoken=1c38isdqmd6hc&l_source=alibaba&x_user=WdPqUuS4hfkfnjFbOCs4+XVvYGDBHkfXxBp97Let5D4=&x_lid=szoreva&sign=y&need_popup=y; xman_us_f=x_locale=zh_CN&x_l=1&last_popup_time=1540521185275&x_user=CN|Louis|Liu|cgs|230417156&no_popup_today=n; intl_locale=zh_CN; intl_common_forever=2O6qIH48vbG888AVJcB8EXoaKPB2YCWVb9C/tMg9mtzjpoU9Vh2mgehriUA4TsyHMF6W96gtTlpFGtwhpzwH4G1pdKqwUtIDB6ShQ5Q7Cvw=; JSESSIONID=DD66DDEC6B7868CF86B5DC8C3FE9B5B8; xman_f=Qa4RDXzlmPiT8YuJdU3rmYrncCkjxxBpE85yEpicDgoElr/RQjvw0sCYfBg3Bztf15X7UR8ekOKXztXa9Bq93W6730hq9wMCfU0uU5O7fZCkbmQnuJTJBVYeAPONuq61qlxkpotjkMzb4BYdkAppSsPY18MA34167j1PHiRRWwFqfJX8+e31FGWtvMpCYdK2yu7alXDVcwisrRVj9mAT/eYoIKnzn/L/Pwy7jjQ0IfBbp2rww/VAyqAJ0D+yqdGzc3DTGu5BmHz+NlbMGblJWWWufh4MzABH5gEH2HjJ8TD5aqX0SrAOh7N6TbzN496yy2Ig0P47Owg85tsOvMy/6G9jdoxoujiki8DxcmMqEM2wSye3h1CS4Yg0jgWwGfFeqIs8Vqjz4u4=; l=aBdM4OJ1ysNhIKC8yManDsNvH707gDfPNZbW1MakeTEhNPfG7RXy1Kno-VwRj_qC5JUy_7-5F; isg=BImJ7VXGMR2D18o50sRDZlUHmLUjfnzL7y9ECyv-A3CvcqmEcyTy2bmgsJ7hKhVA; ali_apache_track=mt=3|ms=|mid=szoreva; xman_t=mD8NhEf7wrHE55Jqz7FHWkEZcp0FxZzV9tD/SVQMq+9B3Sm75z3CXn2ObA5cdSZiJk6CdCl7yCGIpnJsK0QrZ8KK5On9b03yN1vNpvqPC5K/7BzBxqkmd3golKtAg0EOCCFs2fA8aSyhf+UtJDh/OFxz4xyg06B9M1snk3z3v7Bt/+kOyoArgJ+c0wYP28hdjhMYxWecMvCsujo3jEClIHI55pPYAtSItM1KPvLwT4QZwzcq3dz0FJw/c0PpNH98hu3UQBp1tRYl3pfCtOEJPmjOcipaEj27OJ7v+5TLMFTfGs+uzFXAYhh8u165ircL3MesCoxea4+Jkpw2/BnnSu+qRZSS5C4Y0PpacE0rjDECMjEd0AEbPbflZ2YjSO363hjX2gFFcHGHNNiZCsLnwaFq2mE6S6M+9g5tkZOQXHjVBVjGIPthuGKaBPuPJkYKBuxwRtRWPYWDFKJXz8sybbSmGsrDMiSWv09LB90osqihIeizz/47MsmKU4Qnr+V/XiDizQIneidB3UrF8beqw+EFmQ/uI2t7/La9tlYYKRw06WyyioKU4+CZIBNSrULxyfpz4nXdk1C8PmtGfniwo3MZdSRnH9fr2VAUam3CsuY6OnJfeM5sAgdu92msFCbRe6OKSnVc8t02HI9KTyT/8j36SRjPHI/+RvC9JiPi+rfoQpgOkJaaDQ=="
#  数据库连接参数
link_name = "localhost"
user_name = "lyt"
pwd = "lyt123456"
db_name = "lytdb"
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Cookie": cookie,
    "referer": "https://post.alibaba.com/product/category.htm",
    "upgrade-insecure-requests": "1",
    "user-agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
         }
#文件路径定义部分
lastCatIdSet = "./lastCategoryIdSet.txt"
# 这里及bat文件中均要用绝对路径，否则调用bat脚本不成功
### 再次启用程序时可以吧绝对路径换成%~dp0相对路径试一下，之前调用不成功用的是./方式
curlPath = "C:/Users/lyt/Desktop/getAliCatAttrJson/curlGetUrl.bat "
aliAttrJsonSetPath = "./data/aliAttrJsonSet"
urlFilePath = './data/responseSet'
insertNewIdIntoDB = "./data/insertNewIdIntoDB.txt"
failedCatIdSet = "./data/failedCatIdSet.txt"
logFile = "./data/record.txt"
def mkdir(path):
    if not os.path.exists(path):
        os.mkdir(path)
mkdir('./data')
mkdir(aliAttrJsonSetPath)
mkdir(urlFilePath)

# #变量定义部分
# catNum=0
#获取重定向的响应头信息函数
def getcurlrealurl(id):
    path = curlPath + id
    p = subprocess.Popen(path)
    p.wait()
    p.terminate()
# 数据库插入函数    连接数据库，执行插入数据库语句文件
def insertDB(file,link_name, user_name, pwd, db_name):
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
    db.commit()
    db.close()
# 获取产品类目对应的属性信息
def getData():
    # 变量定义部分
    catNum = 0
    with open(insertNewIdIntoDB,'a',encoding='utf-8')as newInit:
        newInit.write('use lytdb;\nupdate lytdb.ali_category set new_id=id;\n')
    with open(lastCatIdSet, 'r', encoding='utf-8') as idSet:
        for line in idSet:
            catNum += 1
            catId = line.strip()
            try:
                # 获取重定向的响应头信息
                getcurlrealurl(catId)
                # 打开对应的响应头.txt文件，读取url
                urlFile = urlFilePath +'/' + catId + ".txt"
                with open(urlFile, 'r', encoding='utf-8') as urlF:
                    responseText = urlF.read()
                    realUrl = str(re.findall(r'Location: (.+?)\n', responseText)[0])
                    realId = str(re.findall(r'catId=(.+?)\n', responseText)[0])
                    aliAttrJsonSet = aliAttrJsonSetPath + '/' + catId + "_Json.txt"
                    # 向数据库new_id列插入新的ID值，数据库插入语句
                    with open(insertNewIdIntoDB, 'a', encoding='utf-8') as dbf_newId:
                        dbf_newId.write('update ali_category set new_id=' + realId + ' where id=' + catId + ';\n')
                if str(re.findall(r'product/(.+?).htm', realUrl)[0]) == 'publish':
                    response = requests.request("GET", realUrl, headers=headers).text
                    page = "".join(re.findall(r"window.Json = (.+?);\n</script>", response))
                    with open(aliAttrJsonSet, 'a', encoding='utf-8') as aliAttrJsonF:
                        aliAttrJsonF.write(page)
                else:
                    break
            except Exception as e:
                traceback.print_exc()
                with open(failedCatIdSet, 'a', encoding='UTF-8') as failedFile:
                    failedFile.write(str(catId) + '\n')
            finally:
                time.sleep(2)
                with open(logFile, 'a', encoding='UTF-8') as log:
                    nowTimes = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))  # 获取当前时间
                    log.write(nowTimes + '\t\tcatId = ' + catId + '\n')
        print('-----------------------finished-----------------------')
        with open(logFile, 'a', encoding='UTF-8') as log:
            log.write('-----------------------finished     Total:' + str(catNum) + '-----------------------')

getData()
insertDB(insertNewIdIntoDB,link_name, user_name, pwd, db_name)