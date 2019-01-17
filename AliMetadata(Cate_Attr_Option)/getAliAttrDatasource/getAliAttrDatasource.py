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
attrFilePath = './data/insertDBAliAttr.txt'
datasourceFilePath = './data/inserDBAliDatasource.txt'
subDatasourceFilePath = './data/insertDBAliSubDatasource.txt'

#变量定义部分
num=0
itemNum=0
subNum=0
insertAttr = "insert into alic_attribute (alica_rid,alic_nid,name,ui_type,label,placeholder,required,readonly,async,multiple,max_length,plugin,max_custom_items,locale,expression,max,max_items,has_alias,min_items,only_select,image_config,validator,info,patterns,text,value,list_id,new_list_id) values"
insertDataSource = "insert into alica_datasource (alicad_rid,parent_attr_opt_id,parent_attr_opt_name,disabled,select_readonly,selected,text,text_readonly,value,rgb,list_id,new_list_id) values"
insertSubDatasource = "insert into alica_sub_datasource (alicasd_rid,value,text,alicad_rid) values"

#函数定义部分
# 特殊字段处理
def dealAttr(i):
    placeholder = ('"' + i['placeholder'] + '"') if i.get('placeholder') else 'NULL'
    readonly = ('1' if i['readonly'] else '0') if i.get('readonly') else 'NULL'
    i_async = ('"' + str(i['async']) + '"') if i.get('async') else 'NULL'
    multiple = ('1' if i['multiple'] else '0') if i.get('multiple') else 'NULL'
    max_length = str(i['maxLength']) if i.get('maxLength') else 'NULL'
    max_custom_items = str(i['maxCustomItems']) if i.get('maxCustomItems') else 'NULL'
    locale = ('"' + str(i['locale']) + '"') if i.get('locale') else 'NULL'
    expression = ('"' + str(i['expression']) + '"') if i.get('expression') else 'NULL'
    max = str(i['max']) if i.get('max') else 'NULL'
    max_items = str(i['maxItems']) if i.get('maxItems') else 'NULL'
    has_alias = ('1' if i['hasAlias'] else '0') if i.get('hasAlias') else 'NULL'
    min_items = str(i['minItems']) if i.get('minItems') else 'NULL'
    only_select = ('1' if i['onlySelect'] else '0') if i.get('onlySelect') else 'NULL'
    image_config = ('"' + str(i['imageConfig']) + '"') if i.get('imageConfig') else 'NULL'
    validator = ('"' + str(i['validator']) + '"') if i.get('validator') else 'NULL'
    info = ('"' + str(i['info']) + '"') if i.get('info') else 'NULL'
    patterns = ('"' + str(i['patterns']) + '"') if i.get('patterns') else 'NULL'
    return placeholder, readonly, i_async, multiple, max_length, max_custom_items, locale, expression, max, max_items, has_alias, min_items, only_select, image_config, validator, info, patterns
def dealDataSource(i):
    disabled = ('1' if i['disabled'] else '0') if i.get('disabled') else 'NULL'
    select_readonly = ('1' if i['selectReadonly'] else '0') if i.get('selectReadonly') else 'NULL'
    selected = ('1' if i['selected'] else '0') if i.get('selected') else 'NULL'
    if i.get('text'):
        text = str(i['text'])
        if re.findall('"',text):
            text = "'"+text+"'"
        else:
            text = '"'+text+'"'
    else:
        text='NULL'
    # text = ('"' + str(i['text']) + '"') if i.get('text') else 'NULL'
    text_readonly = ('1' if i['textReadonly'] else '0') if i.get('textReadonly') else 'NULL'
    value = ('"' + str(i['value']) + '"') if i.get('value') else 'NULL'
    rgb = ('"' + str(i['rgb']) + '"') if i.get('rgb') else 'NULL'
    return disabled, select_readonly, selected, text, text_readonly, value, rgb
def getData():
    with open(idSetFile, 'r', encoding='utf-8') as idF:
        for line in idF:
            id = line.strip()
            file = "./aliAttrJsonSet/" + id + "_Json.txt"
            with open(file, 'r', encoding='utf-8') as jf:
                data = json.loads(jf.readline())
                # 新类目ID
                newId = data["models"]["global"]["catId"]
                # 属性表(商品属性+产品规格)
                # 商品属性部分
                datasource = data["models"]["icbuCatProp"]["dataSource"]
                for i in datasource:
                    num += 1
                    placeholder, readonly, i_async, multiple, max_length, max_custom_items, locale, expression, max, max_items, has_alias, min_items, only_select, image_config, validator, info, patterns = dealAttr(
                        i)
                    if not readonly == 'NULL':
                        formValues = data['models']['formValues']['icbuCatProp'][i['name']]
                        text = '"' + str(formValues['text']) + '"'
                        # text = str(formValues['text'])
                        # if re.findall('"',text):
                        #     text = "'"+text+"'"
                        # if re.findall("'",text):
                        #     text = '"'+text+'"'
                        value = '"' + str(formValues['value']) + '"'
                    else:
                        text = 'NULL'
                        value = 'NULL'
                    result = '(' + str(num) + ',' + str(newId) + ',"' + i['name'] + '","' + i['uiType'] + '","' + i[
                        'label'] + '",' + placeholder + ',' + ('1' if i[
                        'required'] else '0') + ',' + readonly + ',' + i_async + ',' + multiple + ',' + max_length + ',"' + \
                             i[
                                 'plugin'] + '",' + max_custom_items + ',' + locale + ',' + expression + ',' + max + ',' + max_items + ',' + has_alias + ',' + min_items + ',' + only_select + ',' + image_config + ',' + validator + ',' + info + ',' + patterns + ',' + str(
                        text) + ',' + str(value) + ',' + str(num) + ',NULL);\n'
                    with open(attrFilePath, 'a', encoding='utf-8') as attrFile:
                        attrFile.write(insertAttr + result)
                    # 选项表(datasource+units)
                    # datasource部分
                    if i.get('dataSource'):  # 若dataSource不为空，即有属性选项，则提取选项名称及选项值
                        for j in i['dataSource']:
                            itemNum += 1
                            parent_attr_opt_id = 1
                            parent_attr_opt_name = 'dataSource'
                            disabled, select_readonly, selected, text, text_readonly, value, rgb = dealDataSource(j)
                            result = '(' + str(itemNum) + ',' + str(
                                parent_attr_opt_id) + ',"' + parent_attr_opt_name + '",' + disabled + ',' + select_readonly + ',' + selected + ',' + text + ',' + text_readonly + ',' + value + ',' + rgb + ',' + str(
                                num) + ',NULL);\n'
                            with open(datasourceFilePath, 'a', encoding='utf-8') as dsFile:
                                dsFile.write(insertDataSource + result)
                            # 子选项表
                            if j.get('children'):
                                for k in j['children']:
                                    subNum += 1
                                    result = '(' + str(subNum) + ',"' + k['value'] + '","' + k['text'] + '",' + str(
                                        itemNum) + ');\n'
                                    with open(subDatasourceFilePath, 'a', encoding='utf-8') as subFile:
                                        subFile.write(insertSubDatasource + result)
                    # units部分
                    if i.get('units'):  # 若dataSource不为空，即有属性选项，则提取选项名称及选项值
                        for j in i['units']:
                            itemNum += 1
                            parent_attr_opt_id = 2
                            parent_attr_opt_name = 'units'
                            text = str(j['text'])
                            if re.findall('"', text):
                                text = "'" + text + "'"
                            else:
                                text = '"' + text + '"'
                            result = '(' + str(itemNum) + ',' + str(
                                parent_attr_opt_id) + ',"' + parent_attr_opt_name + '", NULL, NULL, NULL,' + text + ', NULL,"' + str(
                                j['value']) + '", NULL, ' + str(num) + ',NULL);\n'
                            with open(datasourceFilePath, 'a', encoding='utf-8') as dsFile:
                                dsFile.write(insertDataSource + result)
                # 产品规格部分
                salePropConfig = data["models"]["salePropConfig"]
                for i in salePropConfig:
                    num += 1
                    proStan = data["components"][i["name"]]["props"]
                    placeholder, readonly, i_async, multiple, max_length, max_custom_items, locale, expression, max, max_items, has_alias, min_items, only_select, image_config, validator, info, patterns = dealAttr(
                        proStan)
                    text = str(proStan['text']) if proStan.get('text') else 'NULL'
                    value = str(proStan['value']) if proStan.get('value') else 'NULL'
                    result = '(' + str(num) + ',' + str(newId) + ',"' + proStan['name'] + '","' + proStan[
                        'uiType'] + '","' + proStan['label'] + '",' + placeholder + ',' + ('1' if proStan[
                        'required'] else '0') + ',' + readonly + ',' + i_async + ',' + multiple + ',' + max_length + ',' + (
                                 '"' + str(proStan['plugin'] + '"') if proStan.get(
                                     'plugin') else 'NULL') + ',' + max_custom_items + ',' + locale + ',' + expression + ',' + max + ',' + max_items + ',' + has_alias + ',' + min_items + ',' + only_select + ',' + image_config + ',' + validator + ',' + info + ',' + patterns + ',' + text + ',' + value + ',' + str(
                        num) + ',NULL);\n'
                    with open(attrFilePath, 'a', encoding='utf-8') as attrFile:
                        attrFile.write(insertAttr + result)
                    # 选项表(datasource+units+产品规格)
                    # 产品规格部分
                    if proStan.get('dataSource'):  # 若dataSource不为空，即有属性选项，则提取选项名称及选项值
                        for j in proStan['dataSource']:
                            itemNum += 1
                            parent_attr_opt_id = 1
                            parent_attr_opt_name = 'dataSource'
                            text = str(j['text'])
                            if re.findall('"', text):
                                text = "'" + text + "'"
                            else:
                                text = '"' + text + '"'
                            result = '(' + str(itemNum) + ',' + str(
                                parent_attr_opt_id) + ',"' + parent_attr_opt_name + '", NULL, NULL, NULL,' + text + ', NULL,"' + str(
                                j['value']) + '", NULL, ' + str(num) + ',NULL);\n'
                            with open(datasourceFilePath, 'a', encoding='utf-8') as dsFile:
                                dsFile.write(insertDataSource + result)
    print('----------num:' + str(num) + ' iteamNum:' + str(itemNum) + ' subNum:' + str(subNum) + '---------------')

# #文本格式处理
# with open(datasourceFilePath, 'r', encoding='utf-8') as f:
#     with open(new_datasourceFilePath, 'a', encoding='utf-8') as nf:
#         for line in f:
#             if re.findall(',"(.+?)""', line):
#                 newLine = re.sub('"",','"\',',line)
#                 q=re.findall(',"(.+?)"\'',newLine)
#                 print(q)
#                 #nf.write(newLine)
#                 #print(newLine)
#                 continue

#连接数据库，执行插入数据库语句文件   适用于海量数据情况，每1000条commit一次，不会丢失数据
def execDB(file):
    db = pymysql.connect("localhost", "lyt", "lyt123456", "lytdb")
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

getData()
execDB(attrFilePath)
execDB(datasourceFilePath)
execDB(subDatasourceFilePath)