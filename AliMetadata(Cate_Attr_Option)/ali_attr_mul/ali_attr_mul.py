# -*- coding:utf-8 -*-
import json
import sys
import importlib
import requests
import time
import pymysql
from bs4 import BeautifulSoup
import traceback
from urllib.parse import unquote
import os
import subprocess
import re
importlib.reload(sys)

#文件路径定义部分
idSetFile = './lastCategoryIdSet.txt'
enInsert = './insertSet/insertIntoDBEnMulti.txt'
cnInsert = './insertSet/insertIntoDBCnMulti.txt'

# jsonFilePath = './data_en'
jsonFilePath = './data_cn'
# language = 'en_US'
language = 'zh-CN'
# insertType = enInsert
insertType = cnInsert

def getData():
    total = 0
    num = 0
    insert = 'insert into alica_multilingual (alicam_rid,alica_rid,language_name,label_value) values'
    with open(idSetFile, 'r', encoding='utf-8') as idF:
        for line in idF:
            id = line.strip()
            jsonFile = jsonFilePath + '/aliAttrJsonSet/' + id + '_Json.txt'
            with open(jsonFile, 'r', encoding='utf-8') as jf:
                data = json.loads(jf.readline())
                # 属性表(商品属性+产品规格)
                # 商品属性部分
                datasource = data["models"]["icbuCatProp"]["dataSource"]
                for i in datasource:
                    num += 1
                    total += 1
                    result = insert + '(' + str(total) + ',' + str(num) + ',"' + language + '","' + str(
                        i['label']) + '");\n'
                    with open(insertType, 'a', encoding='utf-8') as attrFile:
                        attrFile.write(result)
                # 产品规格部分
                salePropConfig = data["models"]["salePropConfig"]
                for i in salePropConfig:
                    num += 1
                    total += 1
                    proStan = data["components"][i["name"]]["props"]
                    result = insert + '(' + str(total) + ',' + str(num) + ',"' + language + '","' + str(
                        proStan['label']) + '");\n'
                    with open(insertType, 'a', encoding='utf-8') as attrFile:
                        attrFile.write(result)
getData()

#连接数据库，执行插入数据库语句文件
#db = pymysql.connect("39.108.119.161","lyt","Pwd123456","lytdb")
db = pymysql.connect("localhost","lyt","lyt123456","lytdb")
cursor = db.cursor()
totalData = 0
num=0
for line in open(cnInsert,encoding = "utf-8"):
    totalData+=1
    num+=1
    if num==1000:
        num=0
        try:
            cursor.execute(line)
        except:
            db.rollback
        db.commit()
        db.close()
        db = pymysql.connect("localhost", "lyt", "lyt123456", "lytdb")
        cursor = db.cursor()
        continue
    else:
        try:
            cursor.execute(line)
        except:
            db.rollback
db.commit()
db.close()

