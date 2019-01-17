'''
    2018/10/25  15:03
    python版本：3.70
    通过python连接数据库
    逐行读取插入文本将数据写入数据库（建表并插入数据）
    对文件读取位置及数据库参数设置有一定要求
'''
import pymysql

readFileName="D:/LTest/Crawler/insertCategoryIntoDataBase.txt"

db = pymysql.connect("localhost","lyt","Pwd123456","lytdb")
cursor = db.cursor()

for line in open(readFileName,encoding = "utf-8"):   
    try:
        cursor.execute(line)
        db.commit()
    except:
        db.rollback
db.close()
