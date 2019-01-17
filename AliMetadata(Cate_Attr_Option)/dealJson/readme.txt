#######################
#######  文件说明   #######
#######################

目的：
	自数据库中提取产品类目目录树，包括路径和树的信息，以指定格式交付前端使用

前提：
	阿里数据已导入，即产品类目表数据已导入完毕

文件清单：
	.idea			工作文件夹(隐藏)
	Ali_firstLevelCategory.json	阿里一级类目json文件
	dealJson.py		python源程序
	pathSet.txt		提取的产品类目路径树json文件
	proSetCN.txt		提取的中文版产品类目目录树json文件
	proSetEN.txt		提取的英文版产品类目目录树json文件
	readme.txt		说明文档
	格式要求.png		json格式示例

注：使用前需确认上一次生成的文件已不在当前目录下（pathSet.txt、proSetCN.txt、proSetEN.txt）