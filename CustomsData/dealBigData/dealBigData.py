'''
    2018/12/11  9:55
    功能：1.对指定文件夹（201706）内所有.rar .zip .tgz压缩包批量解压至压缩包同名文件夹并删除压缩包
         2.将所有文件夹下.mdb或.accdb文件（单个）导入本地mysql指定数据库中，表名以文件夹名命名
    @lyt
    注：数据库中若存在import表则会先删除

    2019/01/10   17:53
    功能：1.增加导入记录功能（bdata_load_mapping、bdata_src_tablename、bdrel_filename_srctable）
         2.增加导入前逻辑处理，导入前检查是否以导入过，是则删除旧表，无论是否导入过都导入新表数据并记录更新时间至记录表
         3.增加统一配置文件
         4.增加bat文件，点击即可直接执行对配置文件中指定文件夹及文件做相关处理
         5.该程序中途意外关闭只需重启重新开始整个导入过程即可
    @lyt
'''

#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import shutil
import traceback
import pymysql
import tarfile
from unrar import rarfile
import zipfile
from retrying import retry
import configparser
import time
import re

#配置变量
conf=configparser.ConfigParser()
conf.read('config.ini')
dealDir = conf.get('file','deal_dir')
table_name = conf.get('file','table_name')
navicat_path = conf.get('file','navicat_path')
navicat_config_file_name = conf.get('file','navicat_config_file_name')

myhost = conf.get('database','myhost')
myport = conf.getint('database','myport')
myuser = conf.get('database','myuser')
mypasswd = conf.get('database','mypasswd')
mydb = conf.get('database','mydb')
mycharset = conf.get('database','mycharset')
db_link_name = conf.get('database','db_link_name')
bdata_load_mapping = conf.get('database','bdata_load_mapping')
bdata_src_tablename  = conf.get('database','bdata_src_tablename')
bdrel_filename_srctable  = conf.get('database','bdrel_filename_srctable')

sql_statement = '将数据从原始数据表（由{src_tablename}变量表示）导入目标数据表（表名固定为bdata_dest_native）的Mysql SQL脚本。'
exist = "select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='"+mydb+"' and table_name='"
path = './'+dealDir
importDir = './'+table_name
importSet = './'+table_name+'/'+table_name+'.accdb'
sysCallsNavicat = 'cd '+navicat_path+' && navicat.exe -import '+navicat_config_file_name+' -t MySQL -c '+db_link_name+' -d '+mydb
pathList = []
fileList = []
rootList = []
tableNameList = []

#函数定义部分
#   解压tgz压缩文件
def un_tgz(filename):
    tar=tarfile.open(filename)
    #判断同名文件夹是否存在，若不存在则创建同名文件夹
    if os.path.isdir(os.path.splitext(filename)[0]):
        pass
    else:
        os.mkdir(os.path.splitext(filename)[0])
        tar.extractall(os.path.splitext(filename)[0])
        tar.close()
#   解压rar压缩包
def un_rar(filename):
    rar=rarfile.RarFile(filename)
    #判断同名文件夹是否存在，若不存在则创建同名文件夹
    if os.path.isdir(os.path.splitext(filename)[0]):
        pass
    else:
        os.mkdir(os.path.splitext(filename)[0])
        rar.extractall(os.path.splitext(filename)[0])
#   解压缩zip压缩包
def un_zip(filename):
    zip_file=zipfile.ZipFile(filename)
    #判断同名文件夹是否存在，若不存在则创建同名文件夹
    if os.path.isdir(os.path.splitext(filename)[0]):
        pass
    else:
        os.mkdir(os.path.splitext(filename)[0])
        for names in zip_file.namelist():
            zip_file.extract(names,os.path.splitext(filename)[0])
            zip_file.close()
#   提取根路径、文件名
def getallFile(path):
    for root,dirs,files in os.walk(path):
        return root,files
#   解压指定路径下文件夹中所有压缩包
def unpack():
    root,files = getallFile(path)
    for i in files:
        pathList = root+'/'+i
        suffix = i.split('.')[1]
        if suffix == 'rar':
            un_rar(pathList)
        elif suffix == 'zip':
            un_zip(pathList)
        elif suffix == 'tgz':
            un_tgz(pathList)
        os.remove(pathList)
#   提取根路径、子文件夹名、文件名列表
def getTableLIst(path):
    for root,dirs,files in os.walk(path):
        tableNameList.append(dirs)
        for i in files:
            fileList.append(files)
            rootList.append(root.replace('\\','/'))
    return fileList,rootList,tableNameList

if __name__ == '__main__':
    unpack()
    if os.path.exists(importDir):
        root,files = getallFile(importDir)
        if files:
            for file in files:
                os.remove(root+'/'+file)
    else:
        os.mkdir(importDir)

    fileList,rootList,tableNameList = getTableLIst(path)
    tableNameList = tableNameList[0]
    fileNum = len(fileList)
    db = pymysql.connect(       # 连接数据库参数
        host=myhost,
        port=myport,
        user=myuser,
        passwd=mypasswd,
        db=mydb,
        charset=mycharset
    )
    cursor = db.cursor()
    for i in range(fileNum):
        tableNameList[i] = tableNameList[i].replace('-','_').lower()
        fP = rootList[i]+'/'+fileList[i][0]
        existImport=exist+table_name+"';"
        cursor.execute(existImport)
        isExistImport = cursor.fetchall()
        if isExistImport:
            cursor.execute("drop table `"+table_name+"`")
        isExist= exist + tableNameList[i] +"';"
        cursor.execute(isExist)       #判断数据库中是否存在该表
        results = cursor.fetchall()
        if results:
            if results[0][0] == tableNameList[i]:
                print('--------------' + str(i+1) + ': ' + tableNameList[i] + '该表已存在  Total: ' + str(fileNum) + '-------------')
                sql_dropTable = "drop table `"+tableNameList[i]+"`;"
                cursor.execute(sql_dropTable)
        #导入开始
        shutil.copy(fP, importSet)
        try:
            os.system(sysCallsNavicat)  # 系统调用navicat存储设置
            try:  # 表改名
                cursor.execute('rename table '+table_name+' to ' + tableNameList[i] + ';')
                try:
                    curTime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    country = re.findall('(.+?)_', tableNameList[i])[0]
                    mapping_name = country + '_' + dealDir

                    # 导入记录表记录 表1
                    sql_checkExist_bdata_load_mapping = "select * from `" + bdata_load_mapping + "` where mapping_name='" + mapping_name + "';"
                    existLoadMapping = cursor.execute(sql_checkExist_bdata_load_mapping)
                    if existLoadMapping:
                        sql_update_load_mapping = "update `" + bdata_load_mapping + "` set sql_statement='" + sql_statement + "',update_time='" + curTime + "';"
                        cursor.execute(sql_update_load_mapping)
                    else:
                        sql_bdata_load_mapping = "insert into `" + bdata_load_mapping + "` (mapping_name,country,version,sql_statement,description,create_time,update_time)values('" \
                                                 + mapping_name + "','" + country + "'," + dealDir + ",'" + sql_statement + "',NULL,'" + curTime + "','" + curTime + "');"
                        cursor.execute(sql_bdata_load_mapping)

                    # 导入记录表记录 表2
                    sqlfeildList = "select column_name from information_schema.columns where table_schema='" + mydb + "' and table_name='" + \
                                   tableNameList[i] + "' order by ordinal_position;"
                    cursor.execute(sqlfeildList)
                    result = cursor.fetchall()
                    feildList = ''
                    for feild in result:
                        feildList = feildList + feild[0] + ','
                    feildList = feildList.strip(',')

                    sql_checkExist_bdata_src_tablename = "select * from `" + bdata_src_tablename + "` where src_tablename='" + tableNameList[i] + "';"
                    existSrcTablename = cursor.execute(sql_checkExist_bdata_src_tablename)
                    if existSrcTablename:
                        sql_update_src_tablename = "update `"+bdata_src_tablename+"` set table_columns='"+feildList+"',update_time='"+curTime+"';"
                        cursor.execute(sql_update_src_tablename)
                    else:
                        sql_bdata_src_tablename = "insert into `" + bdata_src_tablename + "` (src_tablename,mapping_name,description,table_columns,create_time,update_time)values('" + \
                                              tableNameList[i] + "','" + mapping_name + "',NULL,'" + feildList + "','" + curTime + "','" + curTime + "');"
                        cursor.execute(sql_bdata_src_tablename)

                    # 导入记录表3
                    sql_checkExist_bdrel_filename_srctable = "select * from `" + bdrel_filename_srctable + "` where src_tablename='" + \
                                                         tableNameList[i] + "' and filename='"+ rootList[i] +"';"
                    existRelFilenameSrctable = cursor.execute(sql_checkExist_bdrel_filename_srctable)
                    if existRelFilenameSrctable:
                        sql_update_rel_filename_srctable = "update `" + bdrel_filename_srctable + "` set update_time='" + curTime + "';"
                        cursor.execute(sql_update_rel_filename_srctable)
                    else:
                        sql_bdrel_filename_srctable = 'insert into `' + bdrel_filename_srctable + '` (src_tablename,filename,create_time,update_time)values("' + \
                                                  tableNameList[i] + '","' + rootList[i] + '","' + curTime + '","' + curTime + '");'
                        cursor.execute(sql_bdrel_filename_srctable)
                except Exception as e:
                    db.rollback()  # 事务回滚
                    print('导入表记录失败', e)
                else:
                    print('导入表记录成功')
            except Exception as e:
                db.rollback()  # 事务回滚
                print('改表名处理失败', e)
            else:
                print('改表名处理成功')
            finally:
                db.commit()  # 事务提交

        except Exception as e:
            traceback.print_exc()
            print(tableNameList[i] + ' is failed!')
        finally:
            print('--------------' + str(i + 1) + ': ' + tableNameList[i] + ' finished  Total: ' + str(
                fileNum) + '---------------')
    cursor.close()
    db.close()
    if os.path.exists(importSet):
        os.remove(importSet)
    os.removedirs(importDir)
    print('****************本次文件已全部导入完毕*****************')
