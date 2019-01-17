*******************************
************  功能  ************
获取阿里产品目录的末级产品目录id集合

*******************************
************  说明  ************
输入：Ali_firstLevelCategory.json     阿里一级产品类目相关json文件 
	来源：https://post.alibaba.com/product/category.htm?catId=145&itemId=&cacheId=239853429-c3e8cbad-ae76-4ebe-ab61-6b00f1bff8eb&from=post   阿里新建产品页面
		根据请求获取的返回数据   https://post.alibaba.com/posting-proxy/product/catenew/AjaxPostCategoryNew.htm?language=en_us&wholesale=&callback=jsonp_1542186923898_52981&ctoken=15ajjoo1uei7x
		需要阿里账号登录
输出：lastCategoryIdSet.txt     文本文件

注：可一次性获取，若重新执行获取需要手动更改  ——  参数： ctoken 、cookie    删除输出文件


*******************************
************  追加  ************
本程序最初是在数据库中无数据情况下写的，所以需要请求ali接口，即在爬取阿里产品类目的程序基础上更改而来，较花时间。
后在爬取阿里产品类目信息的程序中加入了查询数据库从而直接生成末级产品类目id集合的相关代码以替代本程序，由于更改后账号登录限制，故暂未实际测试，若爬取阿里产品类目信息代码无误，能够正常生成末级产品类目id文件，则本项目可放弃。
@lyt