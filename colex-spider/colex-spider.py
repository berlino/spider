#coding:utf-8
from Tkinter import *
#import requesocks as requests
import requests
from bs4 import BeautifulSoup
import codecs
from PIL import Image
import cStringIO
import os
import time
import Queue
import threading



MainUrl=u"https://www.colex-export.com"
PROXY1={"http":"socks5://127.0.0.1:1080","https":"socks5://127.0.0.1:1080"}
PROXY2={"http":"http://113.10.188.148:808","https":"https://113.10.188.148:808"}
PROXY3={"http":"http://116.255.208.193:808","https":"https://116.255.208.193:808"}

headers={'user-agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.132 Safari/537.36',
         'X-Requested-With': 'XMLHttpRequest',
         'Referer':'https://www.colex-export.com/colex/en/home',
         'Origin':'https://www.colex-export.com',
         }
API="http://svip.kuaidaili.com/api/getproxy/?orderid=953882825069567&num=12&carrier=2&protocol=2&method=1&sp1=1&quality=2&sort=1&format=json&sep=1"

API_REFRESH="http://svip.kuaidaili.com/api/getproxy/?orderid=953882825069567&num=13&carrier=2&protocol=2&method=1&sp1=1&quality=2&sort=1&dedup=1&format=json&sep=1"

Header=('id','name','price','pc','box')
#s=requests.Session()
#s.proxies=proxies
payload={'m':'CustomerLoginCtrl.requestCustomerLogin','viewLogonid':'di.lu@ccscasbl.org','viewPassword':'nikitamagic8848'}
LoginUrl="https://www.colex-export.com/colex/AppServlet?m=CustomerLoginCtrl.requestCustomerLogin"
#data=tablib.Dataset(encoding='utf-8')
#data.headers=Header
if not os.path.exists("img"):
    os.makedirs('img')

SpiderList=[]

#get proxy from kuaidaili
def GetProxy(api):
    req=requests.get(api)
    json=req.json()
    #ProxyNum=json[u'data'][u'count']
    ProxyList=json[u'data'][u'proxy_list']
    return ProxyList



def ResolveItem(content):
    global MainUrl
    soup2=BeautifulSoup(content,'html.parser')
    try:
        pc=soup2.find('div','colli').contents[-1]
        box=soup2.find('div','order').contents[1].contents[0]
        price=soup2.find('p','price').contents[0]
        price=u"".join(price[-6:-1].split(u","))
        imgUrl=MainUrl+soup2.find('img','img-zoom')['src']
        return [pc[1:-2],box,price,imgUrl]
    except AttributeError:
        return None
    except TypeError:
        return [pc[1:-2],box,price,'0']

def RetrieveImg(iNo,imgUrl,session):
            imgFileName="./img/"+iNo+'.jpg'
            if imgUrl!='0':
                #print iNo+" Getting image from "+imgUrl
                tmpObj=Image.open(cStringIO.StringIO(session.get(imgUrl,verify=False).content))
                tmpObj.save(imgFileName)
                del tmpObj

class Spider(threading.Thread):
    def __init__(self,InQueue,OutQueue,proxy=None):
        threading.Thread.__init__(self)
        self.session=requests.Session()
        self.InQueue=InQueue
        self.OutQueue=OutQueue
        self.proxy=proxy
    def SetProxy(self,proxy):
        self.proxy=proxy
    def run(self):
        while True:
            itemSoup=self.InQueue.get()
            if not self.session.cookies or self.session.proxies!=self.proxy:
                self.session.proxies=self.proxy
                #print threading.currentThread(),self.session.proxies
                r=self.session.get("https://www.colex-export.com/colex/en/home",verify=False)
                r=self.session.post(LoginUrl,data=payload,verify=False,headers=headers)
            iUrl=itemSoup.contents[0]['href']
            iNo=iUrl.split('/')[-2]
            iName=itemSoup.contents[0].contents[0]
            #print iUrl
            try:
                r=self.session.get(iUrl,verify=False)
                tResult=ResolveItem(r.content)
                if tResult:
                    pc,box,price,imgUrl=tResult
                    self.OutQueue.put([iNo,iName,price,pc,box])
                    RetrieveImg(iNo,imgUrl,self.session)
                self.InQueue.task_done()
            # if error occurs,put it into queue for another processing
            except:
                self.InQueue.put(itemSoup)


class Storer(threading.Thread):
    def __init__(self,queue,file=None):
        threading.Thread.__init__(self)
        self.queue=queue
        self.file=file

    def SetFile(self,file):
        self.file=file
    def run(self):
        while True:
            iNo,iName,price,pc,box=self.queue.get()
            self.file.write("%s,%s,%s,%s,%s\n" %(iNo,iName,price,pc,box))
            text.insert(END, u"抓取到"+iNo+u"号商品\n")
            root.update_idletasks()
            self.queue.task_done()


#Refresh the queue
def FetchInfo():
    text.insert(END,u"抓取中\n")
    targetUrl=v2.get()
    filename=targetUrl.split("/")[-1]+".csv"
    file=codecs.open(filename,'w',encoding='utf-8')
    file.write(u'id,name,price,pc,box\n'.encode('utf-8'))
    Storer_1.SetFile(file)
    r=requests.get(targetUrl,verify=False,proxies=PROXY3)
    soup=BeautifulSoup(r.text,'html.parser')
    itemList=soup.find_all('td','description')
    #session is not thread safe,so make request before the queue
    for i in itemList:
        itemQueue.put(i)
    itemQueue.join()
    printQueue.join()
    file.close()
    text.insert(END,u"抓取完毕\n")

def Refresh():
    ReProxy=GetProxy(API_REFRESH)
    for i in range(0,12):
            if i<len(ReProxy):
                SpiderList[i].SetProxy({"https":"https://"+ReProxy[i]})
            else:
                SpiderList[i].SetProxy({"https":"https://"+ReProxy[0]})

root = Tk()
root.title("Colex抓取工具")
v1 = StringVar()
v2 = StringVar()
v3=StringVar()
V_1=Entry(root, width=100,textvariable=v1, stat="readonly")
V_1.grid(row=0)
v1.set("输入网址")
V_2=Entry(root, width=100,textvariable=v2)
V_2.grid(row=1)
v2.set("http://colex-export.com")
B_O=Button(root, text="抓取", fg="blue",bd=2,width=20,command=FetchInfo)
B_O.grid(row=2)
B_O2=Button(root, text="刷新代理", fg="blue",bd=2,width=20,command=Refresh)
B_O2.grid(row=2,sticky=E)



# CheckVar=IntVar()
# CheckVar2=IntVar()
# CheckVar3=IntVar()
# C_O=Checkbutton(root,text=u"使用代理1",variable=CheckVar,onvalue=1,offvalue=0,height=5,width=20)
# C_O.grid(row=3,sticky=W)
# C_O2=Checkbutton(root,text=u"使用代理2",variable=CheckVar2,onvalue=1,offvalue=0,height=5,width=20)
# C_O2.grid(row=3,sticky=N)
# C_O3=Checkbutton(root,text=u"使用代理3",variable=CheckVar3,onvalue=1,offvalue=0,height=5,width=20)
# C_O3.grid(row=3,sticky=E)

proxy_list=GetProxy(API)

# proxy=StringVar()
# proxy.set(proxy_list[0])
# X=apply(OptionMenu,(root,proxy)+tuple(proxy_list))
# X.grid(row=2,sticky=E)

itemQueue=Queue.Queue()
printQueue=Queue.Queue()
for i in range(0,4):
    if i<len(proxy_list):
        tmp={"https":"https://"+proxy_list[i].encode('ascii','ignore')}
        t=Spider(itemQueue,printQueue,tmp)
        print tmp
    else:
        tmp={"https":"https://"+proxy_list[0].encode('ascii','ignore')}
        t=Spider(itemQueue,printQueue,tmp)
        print tmp
    t.setDaemon(True)
    t.start()
    SpiderList.append(t)
Storer_1=Storer(printQueue)
Storer_1.setDaemon(True)
Storer_1.start()

text=Text(root,height=40)
text.grid(row=5)
L_O=Label(root, width=100,text="Xberlino")
L_O.grid(row=6,sticky=W)

root.mainloop()









