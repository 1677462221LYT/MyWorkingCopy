************************
********  功能  ********
提取阿里所有产品类目（分层，四级）及其简单属性并导入数据库


************************
********  说明  ********
输入：Ali_firstLevelCategory.json     阿里一级产品类目相关json文件 
	来源：https://post.alibaba.com/product/category.htm?catId=145&itemId=&cacheId=239853429-c3e8cbad-ae76-4ebe-ab61-6b00f1bff8eb&from=post   阿里新建产品页面
	根据请求获取的返回数据   https://post.alibaba.com/posting-proxy/product/catenew/AjaxPostCategoryNew.htm?language=en_us&wholesale=&callback=jsonp_1542186923898_52981&ctoken=15ajjoo1uei7x
	需要阿里账号登录
输出：insertCategoryIntoDataBase.txt     数据库插入语句文件（产品类目表）
          lastCategoryIdSet.txt	末级目录id集合文件

注：可一次性注入，若重新执行注入需要手动更改  ——  参数： ctoken 、cookie    删除输出文件
      若更改数据库连接，需手动更改变量db中的参数
      各级类目json集合 —— 阿里一级产品类目相关json文件、阿里2-4级产品类目所有相关json文件，文件命名：类目ID.json


********************************************
***********  文件夹及文件清单  ************
readme.txt			说明文档
lastCategoryIdSet.txt			末级目录id集合文件
insertCategoryIntoDataBase.txt     	数据库插入语句文件
insertCategoryIntoDataBase.py		python源程序
Ali_firstLevelCategory.json		阿里一级产品类目相关json文件
第一次				第一次爬取数据文件存档

@lyt