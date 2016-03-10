#coding=utf-8
from bs4 import BeautifulSoup

soup=BeautifulSoup(open("data/item_42.html"))
table=soup.html.body.findChildren('table')
chinese_name=table[1].findChild('span').contents[0].split('\r\n')[0]

print soup.contents

tr=table[2].findChildren('tr')
for i in range(len(tr)):
    td=tr[i].findChildren('td')
    if td[1].div.contents==[] or td[1].div.contents[0]=='\n':
        print td[0].contents[0].split('\n')[0],u'无'
    else:
        print td[0].contents[0].split('\n')[0],td[1].div.contents[0].split('\n')[0]