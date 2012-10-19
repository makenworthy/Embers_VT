# -*- coding: utf-8 -*-

from __future__ import with_statement
import os
import urllib2
from BeautifulSoup import BeautifulSoup
from datetime import datetime
from boilerpipe.extract import Extractor
import sqlite3 as lite
import sys
import hashlib
import json
from Util import common
import time

companyList = {}
stockNews = {}
con = None
cur = None
config = None
newsAlreadyDownload = None

def initiate():
    global config
    global newsAlreadyDownload
    
    newsAlreadDownloadFilePath = common.get_configuration("model", "NEWS_ALREADY_DOWNLOADED") 
    newsAlreadyDownload = json.load(open(newsAlreadDownloadFilePath))
    
    get_db_connection()
    
def end():
    global config
    global newsAlreadyDownload
    
    newsAlreadDownloadFilePath = common.get_configuration("model", "NEWS_ALREADY_DOWNLOADED") 
    newsAlreadyDownloadStr = json.dumps(newsAlreadyDownload)
    with open(newsAlreadDownloadFilePath,"w") as output:
        output.write(newsAlreadyDownloadStr)
    
    close_db_connection() 
        
def get_db_connection():
    global cur
    global con
    try:
        con = common.getDBConnection()
        con.text_factory = str
        cur = con.cursor()
    except lite.Error, e:
        print "Error: %s" % e.args[0]

def close_db_connection():
    global con
    con.commit()
    if con:
        con.close()    

def get_all_companies():
    "Read Company List Directory from config file"
    global config
    companyListDir = common.get_configuration('info','COMPANY_LIST')
    dirList = os.listdir(companyListDir)
    "Iteratively read the stock member files and store them in a List "
    for fName in dirList:
        stockIndex = fName[4:len(fName)-4]
        companyList[stockIndex] = []
        filePath = companyListDir + "/" + fName
        with open(filePath,'r') as comFile:
            lines = comFile.readlines()
            for line in lines:
                tickerName = line.replace("\n","").split(" ")[0] + ":" + line.replace("\n","").split(" ")[1]
                companyList[stockIndex].append(tickerName)
    return companyList

def get_stock_news():
    "Scrape the news from Bloomberg"
    for stockIndex in companyList:
        stockNews[stockIndex] = []
        for company in companyList[stockIndex]:
            "construct the url for each company"
            companyUrl = "http://www.bloomberg.com/quote/"+company+"/news#news_tab_company_news";
            soup = BeautifulSoup(urllib2.urlopen(companyUrl,timeout=60))
            "Get the News Urls of specifical Company"
            urlElements = soup.findAll(id="news_tab_company_news_panel")
            for urlElement in urlElements:
                elements = urlElement.findAll(attrs={'data-type':"Story"})
                for ele in elements:
                    newsUrl = "http://www.bloomberg.com" + ele["href"]
                    title = ele.string
                    ifExisted = check_article_already_downloaded(title)
                    if ifExisted:
                        continue
                    else:
                        article = get_news_by_url(newsUrl)
                        article["stock_index"] = stockIndex
                        stockNews[stockIndex].append(article)
            
def get_news_by_url(url):
    article = {}
    try:
        soup = BeautifulSoup(urllib2.urlopen(url))
        "Get the title of News"
        title = ""
        titleElements = soup.findAll(id="disqus_title")
        for ele in titleElements:
            title = ele.getText().encode('utf-8')
        article["title"] = title 
        
        "Get the posttime of News,Timezone ET"
        postTime = ""
        postTimeElements = soup.findAll(attrs={'class':"datestamp"})
        for ele in postTimeElements:
            timeStamp = float(ele["epoch"])
        #postTime = datetime.strftime("%Y-%m-%d %H:%M:%S",datetime.fromtimestamp(timeStamp/1000))
        postTime = datetime.fromtimestamp(timeStamp/1000)
        postTimeStr = datetime.strftime(postTime,"%Y-%m-%d %H:%M:%S")
        article["post_time"] = postTimeStr
        
        "Initiate the post date"
        postDay = postTime.date()
        article["post_date"] = postDay;
        
        "Get the author information "
        author = ""
        authorElements = soup.findAll(attrs={'class':"byline"})
        for ele in authorElements:
            author = ele.contents[0].strip().replace("By","").replace("-","").replace("and", ",").strip();
        article["author"] = author
        
        "Get the content of article"
        extractor=Extractor(extractor='ArticleExtractor',url=url)
        content = extractor.getText().encode("utf-8")
        article["content"] =  content
        
        "Initiate the Sources"
        source = "Bloomberg News"
        article["source"] = source
        
        "Initiate the update_time"
        updateTime = datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
        article["update_time"] = updateTime
        
        "Initiate the embers_id"
        embersId = hashlib.sha1(content).hexdigest()
        article["embers_id"] =  embersId

        "settup URL"
        article["url"] =  url
    except:
        print "Error: %s" %sys.exc_info()[0]
        article = {}
    finally:
        return article

def check_article_already_downloaded(title):
    "Check if this article has already been downloaded, if so, then not access the webpage"
    global newsAlreadyDownload
    if title in newsAlreadyDownload:
        return True
    else:
        newsAlreadyDownload.append(title)
        return False
    
def import_news_to_file():
    dailyNewsOutPath = common.get_configuration("info", "DAILY_NEWS_DIR")
    currentDay = time.strftime('%Y-%m-%d',time.localtime())
    dayFile = dailyNewsOutPath + "/" + "Bloomberg-News-" + currentDay
    newsStr = "{}"
    print "StockNews:", stockNews
    if stockNews is not None:
        newsStr = json.dumps(stockNews)
    
    with open(dayFile,"w") as ouput:
        ouput.write(newsStr)    
        
def execute():
    get_all_companies()
    get_stock_news()
    import_news_to_file()
    end()

initiate()
#get_db_connection()
if __name__ == "__main__":
    print "Start Time: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")
    execute()
    print "End Time: ",datetime.strftime(datetime.now(),"%Y-%m-%d %H:%M:%S")