#coding=utf-8
import requests
from resolve import resolve
from bs4 import BeautifulSoup
import MySQLdb as mdb

#cookie中的jessionid来保持单点登录，所以先要获取到cookie
cookie_url="http://210.73.61.34/engine/login_do.jsp?u=guest&p=guest321&cnid=10140"
item_url="http://cowork.cintcm.com/engine/detail?channelid=10140&record="
cookie_get=requests.get(cookie_url,allow_redirects=False)
_cookie=cookie_get.cookies.get_dict()

conn=mdb.connect('192.168.102.16','wbl','wbl','tcmcenter',charset='utf8')
cur=conn.cursor()

#将网页内容存储到本地文件
def store(i,response):
    item='data/item_'+str(i+1)+'.html'
    item_file=open(item,'w')
    item_file.write(response.content)
    item_file.close()
    

#给定url，返回网页内容
def spider(url):
    print "spidering "+url
    response=requests.get(url,cookies=_cookie)
    #store(i,response)
    return response.content

#建立数据库中的表单
def create_mysql():
    key=[u'中文名称']
    url=item_url+'1'
    soup=BeautifulSoup(spider(url))
    table=soup.html.body.findChildren('table')
    tr=table[2].findChildren('tr')
    for i in range(len(tr)):
        td=tr[i].findChildren('td')
        key.append(td[0].contents[0].split('\n')[0])
    sql_create="""create table tcmcenter.tcm( tcmid int not null auto_increment,"""
    for i in range(len(key)-1):
        sql_create=sql_create+key[i]+' text null,'
    sql_create=sql_create+key[-1]+" text null,primary key(tcmid));"
    #print sql_create
    cur.execute(sql_create)
    #设置成MyISAM的形式,但是创建的时候默认是InnoDB，这么做的主要目的是使用InnoDB时不允许row size太大
    sql_alter="""alter table tcmcenter.tcm engine=MyISAM"""
    cur.execute(sql_alter)
    conn.commit()

if __name__=='__main__':
    create_mysql()
    for i in range(100):
        url=item_url+str(i+1)
        resolve(spider(url))
    cur.close()
    conn.close()

    
