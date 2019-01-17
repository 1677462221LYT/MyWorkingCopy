# -*- coding: utf-8 -*-
'''
    2018/12/14   13:21
    功能:完成对产品类目目录树的提取，包括路径和树的信息，生成后交由前端
    注：若重新更新同步阿里的产品类目、产品属性及属性选项信息，则需在之后运行本程序并将三个结果文件交由前端
    @lyt
'''
import json
import pymysql
import os
# 连接数据库参数
db = pymysql.connect(
        host='localhost',
        port=3306,
        user='lyt',
        passwd='Pwd123456',
        db='lytdb',
        charset='utf8'
    )
sql = 'select * from `ali_category` where parent_id='
sqlId = 'select new_category_id,path_value from ali_category where id='
proSetEn = './proSetEn.txt'
proSetTmpEn = './proSetTmpEn.txt'
proSetCn = './proSetCn.txt'
proSetTmpCn = './proSetTmpCn.txt'
pathSet = './pathSet.txt'
pathSetTmp = './pathSetTmp.txt'
firstJson = './Ali_firstLevelCategory.json'

# 获取子集类目信息
def dbExcu(db, sql, id):
    cursor = db.cursor()
    children = sql + str(id) + " order by `en_name`;"
    cursor.execute(children)
    result = cursor.fetchall()
    return result
# 从数据库获取产品类型对应的新id及类目层级信息
def dbExecNewId(db,sqlId,id):
    cursor = db.cursor()
    newId = sqlId + str(id) + ";"
    cursor.execute(newId)
    result = cursor.fetchall()
    return result
# 写文件通用函数
def writeFile(file,context):
    with open(file,'a',encoding='utf-8') as f:
        f.write(context)
def generateFile(tmpfile,file,end):
    with open(tmpfile,'r',encoding='utf-8') as f:
        path = str((f.readlines()[0]).strip(',')+end)
        writeFile(file,path)
    return f,path
with open(pathSetTmp,'a',encoding='utf-8') as f2:
    f2.write('{')
    with open(proSetTmpEn, 'a', encoding='utf-8') as f1:
        f1.write('[')
        with open(proSetTmpCn, 'a', encoding='utf-8') as f3:
            f3.write('[')
            with open(firstJson, 'r') as fjF:
                json = json.loads(fjF.readlines()[0])['data']['cateItems']
                s1=''
                s1Cn=''
                for level1 in json:
                    level1Id = level1['catId']
                    level1enName = level1['enName'].strip()
                    level1cnName = level1['cnName']
                    result = dbExecNewId(db,sqlId,level1Id)
                    level1newId = result[0][0]
                    level1pathValue = result[0][1]
                    level1children = dbExcu(db, sql, level1newId)
                    s2=''
                    s2Cn = ''
                    for level2 in level1children:
                        level2Id = level2[0]
                        level2enName = level2[1].strip()
                        level2cnName = level2[2]
                        level2catePath = level2[5]
                        level2newId = level2[8]
                        level2Children = dbExcu(db, sql, level2newId)
                        s3=''
                        s3Cn = ''
                        for level3 in level2Children:
                            level3Id = level3[0]
                            level3enName = level3[1].strip()
                            level3cnName = level3[2]
                            level3catePath = level3[5].replace('/', ',')
                            level3newId = level3[8]
                            level3Children = dbExcu(db, sql, level3newId)
                            s4=''
                            s4Cn = ''
                            for level4 in level3Children:
                                level4Id = level4[0]
                                level4enName = level4[1].strip()
                                level4cnName = level4[2]
                                level4catePath = level4[5]
                                level4newId = level4[8]
                                s4 += '{"id":"' + str(level4newId) + '","name":"' + level4enName + '","children":null},'
                                s4Cn += '{"id":"' + str(level4newId) + '","name":"' + level4cnName + '","children":null},'
                                f2.write('"' + str(level4newId) + '":"' + level4catePath + '",')
                            s3 += '{"id":"' + str(level3newId) + '","name":"' + level3enName + '","children":' +(('['+ s4.strip(',') + ']')if not s4=='' else 'null') +'},'
                            s3Cn += '{"id":"' + str(level3newId) + '","name":"' + level3cnName + '","children":' + (('['+ s4Cn.strip(',') + ']')if not s4Cn=='' else 'null') + '},'
                            f2.write('"' + str(level3newId) + '":"' + level3catePath + '",')
                        s2 += '{"id":"' + str(level2newId) + '","name":"' + level2enName + '","children":' + (('['+ s3.strip(',') + ']')if not s3=='' else 'null') + '},'
                        s2Cn += '{"id":"' + str(level2newId) + '","name":"' + level2cnName + '","children":' + (('['+ s3Cn.strip(',') + ']')if not s3Cn=='' else 'null') + '},'
                        f2.write('"' + str(level2newId) + '":"' + level2catePath + '",')
                    s1 += '{"id":"' + str(level1newId) + '","name":"' + level1enName + '","children":' + (('['+ s2.strip(',') + ']')if not s2=='' else 'null')+ '},'
                    s1Cn += '{"id":"' + str(level1newId) + '","name":"' + level1cnName + '","children":' + (('['+ s2Cn.strip(',') + ']')if not s2Cn=='' else 'null')+ '},'
                    f2.write('"' + str(level1newId) + '":"' + level1pathValue + '",')
                f3.write(s1Cn)
                f1.write(s1)
#结果文件操作
generateFile(pathSetTmp,pathSet,'}')
generateFile(proSetTmpEn,proSetEn,']')
generateFile(proSetTmpCn,proSetCn,']')
os.remove(pathSetTmp)
os.remove(proSetTmpEn)
os.remove(proSetTmpCn)