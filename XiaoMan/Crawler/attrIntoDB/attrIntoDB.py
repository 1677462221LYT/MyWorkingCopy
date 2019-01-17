'''
        2018/10/30 9:52
        python版本：3.70
        通过读取末级目录的属性文件，提取需要的数据，处理为可插入数据库的文本语句
        文件路径：
                要析取的文件路径 D:/LTest/Crawler/attrIntoDB/dataFile/proAttr_ + id .txt
                将存放的文件路径 D:/LTest/Crawler/attrIntoDB/dataFile/attrIntoDB.txt
        注：需要手动将要析取的json文件的utf-8-BOM头去掉

        2018/10/30   11:20
        取出需要的内容形成一条记录并存入指定文件
        对所有属性条目进行去重处理

        2018/10/31   9:53
        功能：1.读取末级类目id文件：idSet.txt
              2.通过id值去找对应的处理过的类目属性json文件：proAttr_id.json
              3.读取该json文件并提取相关信息
              4.相关属性及属性值，写入数据库表中：product_category_attribute
              5.部分属性相关options，写入数据库表中：product_category_list
        注：正式用时需要更改相关路径，末级类目id需要由测试的testIdSet更为idSet
'''
import json
import sys
import importlib
import pymysql

importlib.reload(sys)

attrIntoDBFileName = "D:/LTest/Crawler/attrIntoDB/attrIntoDB.txt"
attrOptionsIntoDBFileName = "D:/LTest/Crawler/attrIntoDB/attrOptionsIntoDB.txt"

idFileName = 'D:/LTest/Crawler/attrIntoDB/testIdSet.txt'
#idFileName = 'D:/LTest/Crawler/attrIntoDB/idSet.txt'
attr_count=0
options_count=0

with open(attrIntoDBFileName,'a',encoding='utf-8') as file:
    file.write("use lytdb;\n"+"UPDATE globaldb3.tmp_seqno SET seq_no=99000001 WHERE seq_name='productc_display_field_id';\n"+"UPDATE globaldb3.tmp_seqno SET seq_no=1 WHERE seq_name='productc_list_id';\n")

with open(idFileName,'r',encoding = "UTF-8") as file:
    for line in file:
        id=line.strip('\n')
        readFilename="D:/LTest/Crawler/attrIntoDB/dataFile/proAttr_" + id + ".json"

        with open(readFilename,'r',encoding = "UTF-8") as file:
            data=json.load(file)
        for i in data.get('data'):
            name=i.get('name')
            attrType=i.get('type')
            isEditable=i.get('is_editable')
            if isEditable is None:
                isEditable='NULL'
            options=i.get('options')
            attr_count+=1
            with open(attrIntoDBFileName,'a',encoding='utf-8') as file:
                if options is None:
                    file.write('insert into product_category_attribute (productc_rid, name, type, is_editable, record_id, productc_list_id, productc_display_field_id) values('+id+',"'+name+'","'+attrType+'",'+str(isEditable)+','+str(attr_count)+','+ 'NULL,globaldb3.get_next_seqno("productc_display_field_id"));\n')
                    continue
                else:
                    file.write('insert into product_category_attribute (productc_rid, name, type, is_editable, record_id, productc_list_id, productc_display_field_id) values('+id+',"'+name+'","'+attrType+'",'+str(isEditable)+','+str(attr_count)+','+ 'globaldb3.get_next_seqno("productc_list_id"),globaldb3.get_next_seqno("productc_display_field_id"));\n')
                    selectCode=len(options)
                for j in i.get('options'):
                    optionsName=j.get('label')
                    with open(attrOptionsIntoDBFileName,'a',encoding='utf-8') as file:
                        options_count+=1
                        file.write('insert into product_category_list (producta_rid, record_id, value) values('+str(attr_count)+','+str(options_count)+',"'+optionsName+'");\n')

db = pymysql.connect("localhost","lyt","lyt123456","lytdb")
cursor = db.cursor()

for line in open(attrIntoDBFileName,encoding = "utf-8"):   
    try:
        cursor.execute(line)
        db.commit()
    except:
        db.rollback


for line in open(attrOptionsIntoDBFileName,encoding = "utf-8"):   
    try:
        cursor.execute(line)
        db.commit()
    except:
        db.rollback
    cursor.connection.commit()
    
db.close()
