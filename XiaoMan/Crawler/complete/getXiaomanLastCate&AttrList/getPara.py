'''
    2018/10/24  13:12
    通过指定id值向小满对应URL发起get请求
    获取相对应id值下商品类别的商品属性json列表并存入单独json文件
    注：文件命名格式：proAttr + id值

    2018/10/25  17:19
    更新：
    通过读取文件中所有商品类别id值定时向小满发起get请求
    获取对应商品类别下的json属性列表并存入单独文件
    请求时间间隔：60s  【 要不实现一个间隔大一点的随机数（嘻嘻嘻）】
    
    2018/10/25遗留:4级目录id提取

    2018/10/26    9:15
    更新：
    获取所有末级商品分类id
    idSet与请求需要一次完成(是否拆分)
    实现定时读取所有末级商品分类id并向小满发送get请求，获取其对应的属性json列表
    存入指定的文件中【请求时间间隔是否随机化？随机请求时间区间：30-299s】

    2018/10/29     9:21
    更新：去掉属性文件proAttr_id中时间及id标注写入
          增加try...except...finally...模块捕捉异常
          增加recordFile记录.txt文件
          采用随机数作为sleep函数的参数，请求时间间隔随机化

    2018/10/30    11:24
    更新：为了方便下一步操作，单独存放的文件以.json格式存放
    
'''
import requests
import os
import json

import time
import random
import traceback

import sys
import importlib
importlib.reload(sys)

proId=''
readFilename = "D:/LTest/Crawler/complete/getXiaomanLastCate&AttrList/simpleTest.json"
#readFilename = "D:/LTest/Crawler/getXiaomanLastCate&AttrList/product_category.json"

headers = {"Cookie":"gr_user_id=8709560f-2f99-4d68-91c3-b7f0afb91a45; grwng_uid=7fbdf696-0d21-4099-9622-c152d00b095f; fingerprint=cb69e34450ea31f45f244c9605dfed1e; pskey=3a5aa6afb35b975361289cbdd3f0fac127828ab358e7617d5aaa841583951798; account=joe180%40qq.com; clientId=9134; userId=54908287; pskey_exist=1; set_id=670; Hm_lvt_925e072f764b8f193431ee7c9099e6f5=1540295446,1540344103; _t_language=zh-CN; Hm_lpvt_925e072f764b8f193431ee7c9099e6f5=1540347229; gr_session_id_ab214d89d8d4215b=a58ccc53-bd99-46e9-aea5-842864359a19; gr_cs1_a58ccc53-bd99-46e9-aea5-842864359a19=user_id%3A54908287; gr_session_id_ab214d89d8d4215b_a58ccc53-bd99-46e9-aea5-842864359a19=true"}

idFileName = "D:/LTest/Crawler/complete/getXiaomanLastCate&AttrList/idSet.txt"
recordFileName = "D:/LTest/Crawler/complete/getXiaomanLastCate&AttrList/recordFile.txt"

with open(readFilename,'r',encoding = "UTF-8") as file:
    data=json.load(file)

for level1 in data.get('product_category'):
        for level2 in level1.get('nodes'):
                level2_id=level2.get('id')
                if level2.get('nodes') is None:
                        with open(idFileName,'a',encoding = 'utf-8') as file:
                                file.write(level2_id + '\n')
                        continue
                for level3 in level2.get('nodes'):
                        level3_id=level3.get('id')
                        if level3.get('nodes') is None:
                                with open(idFileName,'a',encoding = 'utf-8') as file:
                                        file.write(level3_id + '\n')
                                continue
                        for level4 in level3.get('nodes'):
                                level4_id=level4.get('id')
                                if level4.get('nodes') is None:
                                        with open(idFileName,'a',encoding = 'utf-8') as file:
                                                file.write(level4_id + '\n')

#读取每行id值，定时发送get请求获取json属性列表并存入指定文件
for line in open(idFileName,encoding = "utf-8"):
        proId = line.strip('\n')
        writeFileName = "D:/LTest/Crawler/complete/getXiaomanLastCate&AttrList/dataFile/proAttr_" + proId + ".json"
        url = "https://sales.xiaoman.cn/api/productRead/attrTpl?category_id="+proId
        try:
                get = requests.get(url,headers = headers)
        except:
                with open(recordFileName,'a',encoding = 'utf-8') as file:
                        file.write("id:" + proId+ "  errorTraceBack: " + traceback.print_exc() + "\n")
        finally:
                with open(recordFileName,'a',encoding = 'utf-8') as file:
                        nowTimes = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))    #获取当前时间
                        file.write("id:" + proId + "  nowTimes: " + nowTimes + "\n")
        with open(writeFileName,'a',encoding = 'utf-8') as file:
                file.write(get.text)
                sleepTime = random.randint(0,2)*100+random.randint(3,9)*10+random.randint(0,9)
                time.sleep(sleepTime)

















