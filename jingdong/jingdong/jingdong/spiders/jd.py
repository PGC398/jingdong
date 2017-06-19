import re,os
import json
import urllib.request
import ssl
import scrapy
from sys import path
path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"../..")))
from scrapy.http import Request
from jingdong.items import JingdongItem
from scrapy_redis.spiders import RedisCrawlSpider
from scrapy.spiders import CrawlSpider, Rule
       
class JdSpider(RedisCrawlSpider):
     
    name = "jd"
    redis_key = 'mycrawler:start_urls'
    start_urls = ['https://www.jd.com/']

    def __init__(self, key=None,page=0, *args, **kwargs):
        super(JdSpider, self).__init__(*args, **kwargs)
        self.key=key
        self.page=int(page)*2
        
    def parse(self, response):
        key = "坚果"
        for i in range(1,self.page):
            if i%2 == 1:
                url = "https://search.jd.com/Search?keyword="+str(self.key)+"&enc=utf-8&page="+str(i)
                yield  Request(url=url,callback=self.pages)
            else:
                pass
            

    def pages(self,response):
        goodsid = response.xpath("//li/@data-sku").extract()
        for i in goodsid:
            url = "https://item.jd.com/"+str(i)+".html"
            yield Request(url=url,callback=self.next)

    def next(self,response):
        item = JingdongItem()
        try:
            item["title"] = response.xpath("//title/text()").extract()[0]
            item["link"] = response.url
            id = re.compile(r'[0-9]+').findall(response.url)
            priceurl = "https://p.3.cn/prices/mgets?skuIds=J_"+str(id[0])
            body = urllib.request.urlopen(priceurl).read().decode("utf8","igrone")
            item["price"] = re.compile(r'"p":"(.*?)"').findall(body)[0]
            item["shopname"] = response.xpath("//a[@target='_blank']/@title").extract()[0]
            item["canshu"] = response.xpath("//ul[@class='parameter2 p-parameter-list']/li/text()").extract()

            allcontent=[]
            allnickName=[]
            allreferenceTime=[]
            allreferenceName=[]
            for i in range(0,4):
                commenturl = "https://club.jd.com/comment/productPageComments.action?productId="+str(id[0])+"&score=0&sortType=5&page="+str(i)+"&pageSize=10"
                body = urllib.request.urlopen(commenturl).read().decode("gbk")
                jsDict = json.loads(body)
                item["commentcount"] = jsDict['productCommentSummary']['commentCountStr']
                jsData=jsDict['comments']
                for i in range(0,10):
                    allcontent.append(jsData[i]['content'])
                    allnickName.append(jsData[i]['nickname'])
                    allreferenceTime.append(jsData[i]['referenceTime'])
                    allreferenceName.append(jsData[i]['referenceName'])

            item["nickName"] = allnickName

            item["content"] = allcontent

            item["referenceName"] = allreferenceName

            item["referenceTime"] = allreferenceTime

            yield item
        except:
            pass
        
