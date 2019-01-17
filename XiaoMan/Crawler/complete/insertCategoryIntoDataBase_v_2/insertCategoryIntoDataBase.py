'''
        2018/10/25 13:27
        python版本：3.70
        从json文件中获取对象的属性列表并处理为可插入数据库的文本语句
        文件路径：
                要析取的文件路径 D:/LTest/Crawler/product_category.json
                将存放的文件路径 D:/LTest/Crawler/insertCategoryIntoDataBase.txt
        注：需要手动将要析取的json文件的utf-8-BOM头去掉

        2018/10/25  15:03
        python版本：3.70
        通过python连接数据库
        逐行读取插入文本将数据写入数据库（建表并插入数据）
        对文件读取位置及数据库参数设置有一定要求

        2018/11/08   11:34
        更新:增加表字段插入判断并在文件头部插入相关索引清零语句

        整合：向数据库product_category表插入所有产品类目信息（最后一个字段计数先清零）
        待优化：批量插入数据语句
'''

import json
import sys
import importlib

import pymysql

importlib.reload(sys)

readFilename="D:/LTest/Crawler/complete/insertCategoryIntoDataBase_v_2/product_category.json"
writeFileName = "D:/LTest/Crawler/complete/insertCategoryIntoDataBase_v_2/insertCategoryIntoDataBase.txt"

with open(readFilename,'r',encoding = "UTF-8") as file:
    data=json.load(file)

with open(writeFileName,'a',encoding = 'utf-8') as file:
        file.write("use lytdb;\n"+"UPDATE globaldb3.tmp_seqno SET seq_no=98000001 WHERE seq_name='product_category_id';\n")
        for level1 in data.get('product_category'):
                level1_id=level1.get('id')
                file.write('insert into product_category (id, en_name, name, pinyin, is_node, path_value, parent_id, product_category_id) values(' + level1.get('id')+',"'+ level1.get('en_name') +'","' + level1.get('name') + '","' + level1.get('pinyin') + '",' + str(level1.get('is_node')) + ',"' + level1.get('value') + '", NULL' + ',' + 'globaldb3.get_next_seqno("product_category_id")' + ');\n')
                for level2 in level1.get('nodes'):
                        level2_id=level2.get('id')
                        file.write('insert into product_category (id, en_name, name, pinyin, is_node, path_value, parent_id, product_category_id) values(' + level2.get('id')+',"'+ level2.get('en_name') +'","' + level2.get('name') + '","' + level2.get('pinyin') + '",' + str(level2.get('is_node')) + ',"' + level2.get('value') + '",' + level1_id + ',' + 'globaldb3.get_next_seqno("product_category_id")' +  ');\n')
                        if level2.get('nodes') is None:
                                continue
                        for level3 in level2.get('nodes'):
                                level3_id=level3.get('id')
                                file.write('insert into product_category (id, en_name, name, pinyin, is_node, path_value, parent_id, product_category_id) values(' + level3.get('id')+',"'+ level3.get('en_name') +'","' + level3.get('name') + '","' + level3.get('pinyin') + '",' + str(level3.get('is_node')) + ',"' + level3.get('value') + '",' + level2_id + ',' + 'globaldb3.get_next_seqno("product_category_id")' + ');\n')
                                if level3.get('nodes') is None:
                                        continue
                                for level4 in level3.get('nodes'):
                                        file.write('insert into product_category (id, en_name, name, pinyin, is_node, path_value, parent_id, product_category_id) values(' + level4.get('id')+',"'+ level4.get('en_name') +'","' + level4.get('name') + '","' + level4.get('pinyin') + '",' + str(level4.get('is_node')) + ',"' + level4.get('value') + '",' + level3_id + ',' + 'globaldb3.get_next_seqno("product_category_id")' + ');\n')

db = pymysql.connect("localhost","lyt","lyt123456","lytdb")
cursor = db.cursor()

for line in open(writeFileName,encoding = "utf-8"):   
    try:
        cursor.execute(line)
        db.commit()
    except:
        db.rollback
db.close()

