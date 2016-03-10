#coding=utf-8

from bs4 import BeautifulSoup
import MySQLdb as mdb

#设置字符集类型，否则会导致中文乱码
conn=mdb.connect('192.168.102.16','wbl','wbl','tcmcenter',charset='utf8')
cur=conn.cursor()

#html could be string or file name end in html
#给定字符串，处理之后存入数据库
def resolve(html,string=True):
    value=[]
    #打开文件，还是直接处理字符串
    if string==False:
        soup=BeautifulSoup(open(html))
    else:
        soup=BeautifulSoup(html)
    table=soup.html.body.findChildren('table')
    chinese_name=table[1].findChild('span').contents[0].split('\r\n')[0]
    value.append(chinese_name)
    print chinese_name
    val_1=u'中文名称'
    #插入的时候注意插入的值需要用引号括起来
    sql_insert=u"""insert into tcm ({0}) values ('{1}')""".format(val_1,chinese_name)
    cur.execute(sql_insert)
    sql_select=u"select tcmid from tcm where {0}='{1}'".format(val_1,chinese_name)
    #print sql_select
    cur.execute(sql_select)
    rows=cur.fetchall()
    tcmid=rows[0][0]
    #print tcmid

    #提取属性以及属性值
    tr=table[2].findChildren('tr')
    for i in range(len(tr)):
        td=tr[i].findChildren('td')
        #在content中为空或者属性不是字符（注意这里的字符类型是在beautifulsoup中定义的字符串类型）
        if td[1].div.contents==[] or td[1].div.contents[0]=='\n' or td[1].div.contents[0]=='\r\n' or type(td[1].div.contents[0])!=type(td[0].contents[0]) :
            val_1=td[0].contents[0].split('\r\n')[0]
            val_2=u'无'
        else:
            val_1=td[0].contents[0].split('\r\n')[0]
            val_2=td[1].div.contents[0].split('\r\n')[0]
        #print u'update infomation no.{0} of {1} {2}'.format(tcmid,val_1,val_2)
        #这里会遇到一个单引号在mysql中截断的问题，所以要用一个slash，但是加两个slash实现转义
        if val_2.find("'"):
            val_2=val_2.replace("'","\\'")
        sql_update=u"""update tcm set {0}='{1}' where tcmid={2}""".format(val_1,val_2,tcmid)
        cur.execute(sql_update)
        conn.commit()

if __name__=='__main__':
    item='data/item_3.html'
    resolve(item,False)
    conn.commit()
    cur.close()
    conn.close()