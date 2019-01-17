'''
        2018/11/13   14:30
        python版本：3.70
        功能：获取阿里产品目录的末级产品目录id集合
        本代码直接在insertCategoryIntoDataBase.py代码的基础上稍作修改而来
        遇到的问题：
                用postman发起请求可以接受到数据，但用代码请求会报错<ctoken checked error>,还不知道为什么
        注：若需重新执行需手动更改cookie、ctoken参数，必要时用postman转换的代码进行测试
        @lyt
'''
# -*- coding:utf-8 -*-
import json
import sys
import importlib
import requests
import time
importlib.reload(sys)

#可能需要手动修改的参数在这里v
cookie = "ali_apache_id=11.179.217.160.1540172152871.110138.6; cna=ehdUFD0kpUMCAdpqddIjxJD7; ali_ab=218.106.117.210.1540172155756.8; t=1f3534590bddc634e04f73213b60dbe8; gangesweb-buckettest=218.106.117.210.1540172156412.0; UM_distinctid=16699946bf4c63-0bcc78584b2cc8-b79193d-1fa400-16699946bf547c; _ga=GA1.2.21064647.1540279409; __utma=226363722.21064647.1540279409.1542959283.1542959283.1; __utmz=226363722.1542959283.1.1.utmcsr=alibaba.com|utmccn=(referral)|utmcmd=referral|utmcct=/product-detail/Mentorvii-shockproof-tpu-smart-phone-case_60804075629.html; history=company%5E%0A232290982; _m_h5_tk=df10a524eaa48679b95f3cb44261faef_1545799906756; _m_h5_tk_enc=48137728562c39a3fe76eae7efc407ad; acs_usuc_t=acs_rt=f8f3dd5c09344df5ab2fc14cf3c759da; _csrf_token=1545874740000; acs_rt=9a5376a048ed48ad9cd298eddb2bb580; sc_g_cfg_f=sc_b_locale=de_DE&sc_b_site=GLO; _gid=GA1.2.1196566946.1545877402; cookie2=1c350e83e2e68b7d18c088b83039cf77; _tb_token_=e137ee3353d4b; XSRF-TOKEN=6794fb0d-15a7-4f34-90b0-5ff954a188cb; ali_apache_tracktmp=W_signed=Y; _hvn_login=4; csg=98e194a4; xman_us_t=ctoken=ii2aooezsh11&l_source=alibaba&x_user=MiqZhVSZ2e0o5yQkvmB5CyHwtiTPy1zoMJOMFpBsGik=&x_lid=szoreva&sign=y&need_popup=y; JSESSIONID=28E5CE03B40EFBE25DA248B89FEECBD2; xman_f=h4SK1lLJhf8xn7nxfereJeI9BsAYAOUeSOTcZ/nS4GLBpEhQMAr0SWQKekzXenRS5R/cZQHW3yzCGj+3usVkrEz1X8EzzvZhhxlWCkNOK7TOQ4qO/YMuf4Aogv0qKgEb34Vce7gFRzP0aeBEr7RQmD31zteAWfuQ4zQOKSr2XN4qIVnTCe6sIRs+Pb8fbLcB981QOjXn+C5xtYoB+5sZMnW4VpWoAPB29MOe4DcCZUp6DkGXlFMdRWNzGvPALH3IZdPbjdtPb9aGcVklf4z5C9fXohdDRAevFjq71DXtPGfLGF5gLGWtNhLoQCtplaH1bXMkONr9tCoEutbNko6sJzIRdDO0XPmMpzwy6P64a/kZFd7bH6COrkIUPDXdAsuPs1xIg+jGmGE=; ali_apache_track=mt=3|ms=|mid=szoreva; xman_us_f=x_locale=en_US&x_l=1&last_popup_time=1540521185275&x_user=CN|Louis|Liu|cgs|230417156&no_popup_today=n; intl_locale=en_US; xman_t=RAARi2/zldB6pglz+QybpoAUcVroXp6+04lXQRVzmUXKkv7ZJzdYMbDHObomx5jYqUQvjpiEnAreab80f5CWIec++Qx9kSVbW82i1AG4NCUJJpsDeRzYnLxCmLw8YgwKwj6/n4Oa/pIyaIYgcHFumSjHBAZwEXsTmrHlSkTu7oB1/KdXhZpc13+3zE6tA23ZGtKdN9/0l8DwLyznWyocagpBuig9m5kXAC/4w8D8x1YNeMXJV1LtfY0lLCjsO+udZXP4MGj8/bGt99iuD6d2a6yh+EWvCsG1mHc7ZnISqBULZw7eLENJRfB28Y5yMOnXRidlQfsouMNEmDx4+bCz9GEPo9M3cGxIbBJ0QgppsCwexzKfw6teeOUHjCJAty6WyziU1C+MPl0KfSzhdHuWkaBEm+2Y2I4BHB0OtGxKIag+C/Mc5hz/jLAcgOoeQQ8RGk4W57EygporLqQkmAvOqwB8R9/oIDu0/elkR0/0kaNOhBEjwWVsLjCwHdBNqZ+c9hNvhoiruIrTU+56DrkXapeQTf2TtuSTrMab7rkvrmjYyTaGwqAsIQymCzoG3GqI/klMSbD1a1GWZxPfIOECLtdZfXutsaGzSqdEhNd7mJLInnYgvt7NbKf+uv6ucI1U+LkR9Uzs+0k+gbtMdyhH5VlBCifif5kmHw8SbI4WyN5z8N2CW0vmag==; intl_common_forever=ctMdtVzRtoIpEZkB6VUuNRIRpsopxFqS9Xo0lnfN2FiYapBrPj7q6aWaF00jqn0e5Z7nc2iXcUNCKb/ZsuqxGvdYAgvFM5/qDyMDXd1NuZI=; isg=BCMjHggqey5umDDLDNpZdKPhsmcNsLaZ-UkeGVWA_AKNlEK23e9PqkiFiiw_NA9S; l=aBdM4OJ1ysNhITDK9MaTwX2o8707gDfPV-YE1MwHtTEhNPfG7RXy1ltb__wwM0AFwbvXcId29cSw."
ctoken = "ii2aooezsh11"
headers = {
    'Cookie': cookie,
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
    'cache-control': "no-cache",
    'Postman-Token': "4737e26f-20a6-4ada-9aa6-f487bd7e330b"
    }

readFilename="./Ali_firstLevelCategory.json"
url = "https://post.alibaba.com/posting-proxy/product/catenew/ajaxGetProductCatNew.htm"

with open(readFilename,'r',encoding = "UTF-8") as file:
    data=json.load(file).get('data')

writeFileName = "./lastCategoryIdSet.txt"
with open(writeFileName,'a',encoding = 'utf-8') as file:
        for level1 in data.get('cateItems'):
                level1_id=level1.get('catId')
                #一级类目
                catId = str(level1_id)
                payload = ""
                try:
                        querystring = {"catIds":catId,"ctoken":ctoken}
                        response = requests.request("GET", url, data=payload, headers=headers, params=querystring)
                        subData = json.loads(response.text).get('data')
                        for level2 in subData.get(str(level1_id)):
                                level2_id = level2.get('catId')
                                #二级类目
                                if level2.get('isLeaf') is True:
                                        file.write(str(level2_id)+'\n')
                                        continue
                                else:
                                        catId = str(level2_id)
                                        querystring = {"catIds":catId,"ctoken":ctoken}
                                        response2 = requests.request("GET",url, data=payload, headers=headers, params=querystring)
                                        subData2 = json.loads(response2.text).get('data')
                                        for level3 in subData2.get(str(level2_id)):
                                                level3_id = level3.get('catId')
                                                # 三级类目
                                                if level3.get('isLeaf') is True:
                                                        file.write(str(level3_id)+'\n')
                                                        continue
                                                else:
                                                        catId = str(level3_id)
                                                        querystring = {"catIds":catId,"ctoken":ctoken}
                                                        response3 = requests.request("GET",url, data=payload, headers=headers, params=querystring)
                                                        subData3 = json.loads(response3.text).get('data')
                                                        for level4 in subData3.get(str(level3_id)):
                                                                level4_id = level4.get('catId')
                                                                print(level4_id)
                                                                #四级类目
                                                                file.write(str(level4_id)+'\n')
                except Exception as e:
                        traceback.print_exc()
                finally:
                        time.sleep(3)
