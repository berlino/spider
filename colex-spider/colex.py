# coding:utf-8

# import requesocks as requests
import requests
from bs4 import BeautifulSoup
import codecs
from PIL import Image
import cStringIO
import os
import time
import Queue
import threading
import re

MainUrl = u"https://www.colex-export.com"
ExtendedUrl = "https://www.colex-export.com/colex/AppServlet?m=PaginationCtrl.requestPage&page=2"
TestUrl = "https://www.colex-export.com/colex/en/branch/1641/st-nicholas--1-"

# PROXY=[{},{"http":"socks5://127.0.0.1:1080","https":"socks5://127.0.0.1:1080"},{"http":"http://113.10.188.148:808","https":"https://113.10.188.148:808"},{"http":"http://116.255.208.193:808","https":"https://116.255.208.193:808"}]
PROXY = [{}]

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.132 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://www.colex-export.com/colex/en/home',
    'Origin': 'https://www.colex-export.com',
}
API = "http://svip.kuaidaili.com/api/getproxy/?orderid=945673754549881&num=12&carrier=2&protocol=2&method=1&sp1=1&quality=2&sort=1&format=json&sep=1"
API_REFRESH = "http://svip.kuaidaili.com/api/getproxy/?orderid=945673754549881&num=13&carrier=2&protocol=2&method=1&sp1=1&quality=2&sort=1&dedup=1&format=json&sep=1"

CSVHeader = ('id', 'name', 'price', 'pc', 'box')

payload = {'m': 'CustomerLoginCtrl.requestCustomerLogin', 'viewLogonid': 'di.lu@ccscasbl.org',
           'viewPassword': 'nikitamagic8848'}
LoginUrl = "https://www.colex-export.com/colex/AppServlet?m=CustomerLoginCtrl.requestCustomerLogin"

# number of spider
SPIDER_NUM = 2

# global queue
proxyQueue = Queue.Queue()
# html desciption queue
itemQueue = Queue.Queue()
# csv header queue
resultQueue = Queue.Queue()
# exclude the using proxies
usingSet = set()


# get proxy from kuaidaili
def GetProxy(api):
    req = requests.get(api)
    json = req.json()
    # ProxyNum=json[u'data'][u'count']
    ProxyList = json[u'data'][u'proxy_list']
    return ProxyList


# Refresh the proxy queue
def Refresh():
    ReProxy = GetProxy(API)
    for p in ReProxy:
        proxyQueue.put({"https": p.encode('ascii', 'ignore')})
        # proxyQueue.task_done()


class Spider(threading.Thread):
    def __init__(self, InQueue, OutQueue, proxy=None):
        threading.Thread.__init__(self)
        self.session = requests.Session()
        self.InQueue = InQueue
        self.OutQueue = OutQueue
        self.proxy = proxy

    # parse the single web page
    def parseItem(self, content):
        global MainUrl
        soup2 = BeautifulSoup(content, 'html.parser')
        pc = soup2.find('div', 'colli').contents[-1]
        pc=pc[1:-2]
        box = soup2.find('div', 'order').contents[1].contents[0]
        priceContent = soup2.find('p', 'price').contents[0]
        price = "".join(re.findall(r'\d+',priceContent))
        # price =''.join([int(s) for s in priceContent if s.isdigit()])
        #price="".join(price[-6:-1].split(u","))

        try:
            empContent = soup2.find('div', 'details').find('li', 'first').contents[1]
            empties = "".join(re.findall(r'\d+',empContent))
            # empties = "".join(tmpEmp.split(","))
            taxContent = soup2.find('div', 'details').find('li', '').contents[-1].contents[0]
            tax= "".join(re.findall(r'\d+',taxContent))
            # tax = "".join(tmpTax.split(","))
        except:
            empties = '0'
            tax = '0'

        try:
            imgurl = MainUrl + soup2.find('img', 'img-zoom')['src']
        except:
            imgurl = '0'

        try:
            date = soup2.find('p', 'date').contents[0]
        except:
            date = '0'

        return pc, box, price, empties, tax, date, imgurl

    # fetch the image
    def retrieveImg(self, iNo, imgUrl, session):
        imgFileName = "./img/" + iNo + '.jpg'
        if imgUrl != '0':
            # print iNo+" Getting image from "+imgUrl
            imgUrl = imgUrl.replace('200x200', '500x500')
            tmpObj = Image.open(cStringIO.StringIO(session.get(imgUrl, verify=False).content))
            tmpObj.save(imgFileName)
            del tmpObj

    # update the proxy of not in use
    def update(self):
        usingSet.remove(self.proxy["https"])
        if proxyQueue.empty():
            Refresh()
        p = proxyQueue.get()
        while p["https"] in usingSet:
            if proxyQueue.empty():
                Refresh()
            p = proxyQueue.get()
        self.proxy = p
        usingSet.add(self.proxy["https"])
        proxyQueue.task_done()
        print "Update to " + self.proxy["https"]

    def run(self):
        while True:
            # queue gets block util queue.put
            itemSoup = self.InQueue.get()
            try:
                if not self.session.cookies or self.session.proxies != self.proxy:
                    self.session.proxies = self.proxy
                    # print threading.currentThread(),self.session.proxies
                    r = self.session.get("https://www.colex-export.com/colex/en/home", verify=False)
                    r = self.session.post(LoginUrl, data=payload, verify=False, headers=headers)
                iUrl = itemSoup.contents[0]['href']
                iNo = iUrl.split('/')[-2]
                iName = itemSoup.contents[0].contents[0]
                # print iUrl
                r = self.session.get(iUrl, verify=False)
                tResult = self.parseItem(r.content)
                if tResult:
                    pc, box, price, empties, tax, date, imgUrl = tResult
                    self.retrieveImg(iNo, imgUrl, self.session)
                    self.OutQueue.put([iNo, iName, price, pc, box, empties, tax, date])
                print threading.currentThread(), iNo
                self.InQueue.task_done()
            # if error occurs,put it into queue for another processing
            except:
                self.InQueue.put(itemSoup)
                # update to another proxy
                self.update()
                self.InQueue.task_done()


class Storer(threading.Thread):
    def __init__(self, queue, file=None):
        threading.Thread.__init__(self)
        self.queue = queue
        self.file = file

    def SetFile(self, file):
        self.file = file

    def run(self):
        while True:
            iNo, iName, price, pc, box, empties, tax, date = self.queue.get()
            self.file.write(u"%s,%s,%s,%s,%s,%s,%s,%s\n" % (iNo, iName, price, pc, box, empties, tax, date))
            self.queue.task_done()


# update queues
def FetchInfo(targetUrl):
    # fetch the filename
    FetchName = targetUrl.split("/")[-1]
    filename = FetchName + ".csv"
    FetchNo = FetchName.split('-')[-2]
    if int(FetchNo) > 50:
        Extended = True
    else:
        Extended = False

    with codecs.open(filename, 'w', encoding='utf-8') as f:
        f.write(u'id,name,price,pc,box,empties,tax,date\n'.encode('utf-8'))
        Storer_1.SetFile(f)

        # update the queues in item table page
        FetchItemSession = requests.Session()
        FetchItemSession.proxies = PROXY[0]
        r = FetchItemSession.get(targetUrl, verify=False)
        soup = BeautifulSoup(r.text, 'html.parser')
        itemList = soup.find_all('td', 'description')
        # session is not thread safe,so make request before the queue
        for i in itemList:
            itemQueue.put(i)
        if Extended:
            r = FetchItemSession.get(ExtendedUrl, verify=False)
            soup = BeautifulSoup(r.text, 'html.parser')
            itemList = soup.find_all('td', 'description')
            print "Extended ", len(itemList)
            for i in itemList:
                itemQueue.put(i)
        itemQueue.join()
        resultQueue.join()


if __name__ == "__main__":
    # img path
    if not os.path.exists("img"):
        os.makedirs('img')

    # proxyqueue for updating the proxy in real time
    proxy_list = GetProxy(API)
    print proxy_list
    for p in proxy_list:
        proxyQueue.put({"https": p.encode('ascii', 'ignore')})

    # set up few spiders and one storer
    # update the item queue and resultqueue,the flow goes well
    for i in xrange(SPIDER_NUM):
        if i < len(proxy_list):
            tmpProxy = proxyQueue.get()
            t = Spider(itemQueue, resultQueue, tmpProxy)
            usingSet.add(tmpProxy["https"])
            # print tmp
        else:
            t = Spider(itemQueue, resultQueue, {})
        t.setDaemon(True)
        t.start()
    Storer_1 = Storer(resultQueue)
    Storer_1.setDaemon(True)
    Storer_1.start()

    FetchInfo(TestUrl)


