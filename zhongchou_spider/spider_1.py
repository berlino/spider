#coding=utf-8
import requests
from bs4 import BeautifulSoup
import codecs
import os
import tablib
import re
import sys

base_url="http://www.zhongchou.cn"
keji_list_url="http://www.zhongchou.cn/browse/id-10000-p-"
gongyi_list_url="http://www.zhongchou.cn/browse/id-23-p-"
chuban_list_url="http://www.zhongchou.cn/browse/id-16-p-"
yule_list_url="http://www.zhongchou.cn/browse/id-10001-p-"
yishu_list_url="http://www.zhongchou.cn/browse/id-22-p-"
nongye_list_url="http://www.zhongchou.cn/browse/id-28-p-"
suzhou_list_url="http://www.zhongchou.cn/deals-difangzhan/t-%E8%8B%8F%E5%B7%9E%E7%AB%99-all--p-"
henan_list_url="http://www.zhongchou.cn/deals-difangzhan/t-%E6%B2%B3%E5%8D%97%E7%AB%99-all--p-"
hubei_list_url="http://www.zhongchou.cn/deals-difangzhan/t-%E6%B9%96%E5%8C%97%E7%AB%99-all--p-"
zhongchouzhizao_list_url="http://www.zhongchou.cn/deals-tags/t-%E4%BC%97%E7%AD%B9%E5%88%B6%E9%80%A0-all--p-"

zhongchouzhong_list_url="http://www.zhongchou.cn/browse/di-p-"
yichenggong_list_url="http://www.zhongchou.cn/browse/ds-p-"

blacklist=["/deal-show/id-74638"]

test_url="http://www.zhongchou.cn/deal-show/id-82048"

column=["title","real_name","support_money","supporter_num","real_get_money","expected_money","real_time","whole_time",
        "comment_num","share_num"]
headers=("url","1_money","1_num","2_money","2_num","3_money","3_num",
             "real_get_money","expected_money","real_time","whole_time","comment_num","share_num","video","image")
data=tablib.Dataset()
data.headers=headers


def spider(url):
    response=requests.get(url)
    if response.status_code==200:
        return response.content
    else:
        print "Failed on "+url
        return 0

def store2txt(filename,**kargs):
    if not os.path.isfile(filename):
        file=codecs.open(filename,'w',encoding="utf8")
        for v in column:
            if v=="support_money":
                for index in range(len(kargs["support_money"])):
                    file.write(str(index+1)+'_money,')
                    file.write(str(index+1)+'_num,')
                continue
            if v=="supporter_num":
                continue
            file.write(v+',')
        file.write('\n')
    else:
        file=codecs.open(filename,'a',encoding="utf8")
    for v in column:
        if v=="support_money":
            for index in range(len(kargs["support_money"])):
                file.write(kargs["support_money"][index])
                file.write(",")
                try:
                    file.write(kargs["supporter_num"][index])
                except IndexError:
                    file.write('0')
                file.write(",")
            if len(kargs["support_money"])<3:
                file.write('0,0,')
            continue
        if v=="supporter_num":
            continue
        file.write(kargs[v]+',')
    file.write('\n')
    file.close()

def store2csv(**kargs):
    tmp_list=[]
    for v in column:
        if v=="support_money":
            for index in range(len(kargs["support_money"])):
                tmp_list.append(kargs["support_money"][index])
                try:
                    tmp_list.append(kargs["supporter_num"][index])
                except IndexError:
                    tmp_list.append('0')
            if len(kargs["support_money"])<3:
                tmp_list.extend(['0','0'])
            continue
        if v=="supporter_num":
            continue
        tmp_list.append(kargs[v])
    data.append(tmp_list)

def resolve_success_time(url):
    time_url=url.replace('show','march')
    #print "Fetch time from "+time_url
    web_content=spider(time_url)
    if web_content==0:
        return ['0','0']
    soup=BeautifulSoup(web_content)
    time_block=soup.find_all("span",{"class":"time-zhou"})
    #print time_block[0].string,time_block[-1].string
    return [time_block[-1].string,time_block[0].string]

#produce title,real_name,support_money,supporter_num, real_get_money,expected_money,real_time,whole_time
def resolve_item(web_content,url):
    if web_content==0:
        return
    soup=BeautifulSoup(web_content)

    #支持的钱
    support_money_tag=soup.find_all('a',{"name":"supp"})[:3]
    support_money=[]
    #print support_money
    for s_i in support_money_tag:
        try:
            support_money.append(s_i["data-money"])
        except KeyError:
            support_money.append("stock")
    #print support_money

    #标题
    mix=soup.find("div",{"class","project-right"})
    mix_children=list(mix.children)
    title=mix_children[1].a.string
    print title

    #支持的人数
    supporters=mix.find_all('p',{"class":"support_info"})
    supporter_num=[]
    for supporter in supporters:
        if supporter.string.find(u"已")>0:
            p1=supporter.string.find(u"限")
            p2=supporter.string.find(u"人")
            tmp_num=supporter.string[p1+1:p2]
        else:
            pos=supporter.string.find(u"人")
            tmp_num=supporter.string[:pos].strip(' \t\n\r')
        supporter_num.append(tmp_num)
    print support_money,supporter_num

    #联系人信息
    name_block=soup.find("em",{"class":"name"})
    real_name=name_block.string
    print real_name

    #需要筹集的资金和已经筹集的资金
    money=soup.find("p",{"class":"czmb clearfix"})
    #print money
    money_children=list(money.children)
    real_get_money=money_children[0].em.string.encode('ascii','ignore')
    expected_money=money_children[1].string[3:].encode('ascii','ignore')
    print real_get_money,expected_money

    #总时间和剩余时间
    time=soup.find("p",{"class":"bfb_ts clearfix"})
    #print time
    time_children=list(time.children)
    time_grandchildren=list(time_children[2].children)
    real_time=time_grandchildren[0]
    if real_time==u"已成功":
        real_time,whole_time=resolve_success_time(url)
    else:
        try:
            real_time=real_time.encode('ascii','ignore')
            whole_time=time_grandchildren[1].string[1:].encode('ascii','ignore')
        except TypeError:
            real_time='0'
            whole_time='0'
    print real_time,whole_time

    #评论数
    comment_block=soup.find_all('a',{"id":"deal_detail_comment"})
    comment_num=comment_block[0].string[3:-1].encode('ascii','ignore')
    print comment_num

    #分享数
    share_block=spider("http://i.jiathis.com/url/shares.php?url="+url)
    if share_block==0:
        return
    share_num='0'
    for s in share_block.split('"'):
        if s.isdigit():
            share_num=s
            print share_num
            break

    #视频
    video_block=soup.find("div",{"class","media-time"})
    if video_block:
        video=1
    else:
        video=0

    #图片
    img_block=soup.find("div",{"class":"content"})
    if img_block.find("img"):
        image=1
    else:
        image=0

    # store2txt(filename,title=title,real_name=real_name,
    #             support_money=support_money,supporter_num=supporter_num,
    #             real_get_money=real_get_money,expected_money=expected_money,
    #             real_time=real_time,whole_time=whole_time,comment_num=comment_num,share_num=share_num)

    try:
        data.append((url,support_money[0],supporter_num[0],support_money[1],supporter_num[1],support_money[2],supporter_num[2],
              real_get_money,expected_money,real_time,whole_time,comment_num,share_num,video,image))
    except IndexError:
        try:
            data.append((url,support_money[0],supporter_num[0],support_money[1],supporter_num[1],'0','0',
              real_get_money,expected_money,real_time,whole_time,comment_num,share_num,video,image))
        except IndexError:
            data.append((url,'0','0','0','0','0','0',
              real_get_money,expected_money,real_time,whole_time,comment_num,share_num,video,image))


def resolve_list(web_content):
    if web_content==0:
        return
    soup=BeautifulSoup(web_content)
    list=soup.find_all("a",{"target":"_blank","class":"item-figure"})
    items=[]
    for item in list:
        items.append(item["href"])
    return items

def test():
    resolve_item(spider(test_url),test_url)

def main():
    print "Begin spidering ..."
    for page_num in range(1,46):
        items=resolve_list(spider(yichenggong_list_url+str(page_num)))
        for item in items:
            url=base_url+item
            if item in blacklist:
                continue
            print "Spidering "+url
            resolve_item(spider(url),url)

if __name__=="__main__":
    #test()
    main()
    file=codecs.open('yichenggong.csv','w',encoding='utf8')
    file.write(data.csv)
    file.close()
