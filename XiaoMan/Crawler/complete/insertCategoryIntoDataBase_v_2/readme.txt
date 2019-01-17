'''
	2018/10/25  13:28	
	完成功能
'''
product_category.json : 已去除utf-8-BOM头的json数据文件
insertCategoryIntoDataBase.txt : 已提取出的数据，数据库语句形式
insertCategoryIntoDataBase.py : python源代码，其中对文件存放的位置有要求

'''
	2018/10/25  17:04
	更新迭代：由于部分字段中包含'字符，与外包裹字符串字符定义冲突，导致无法用Python进行批量导入
		解决：更新字符串外包裹字符定义(由''更为"")
'''