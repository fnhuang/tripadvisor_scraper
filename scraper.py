import datetime
from selenium import webdriver
from bs4 import BeautifulSoup
import json
import os
import csv
import time
import sys

class ReviewCrawler():

    def __init__(self, linux_vm, url, sleep_time):
        self.linux_vm = linux_vm #crawl on cloud?
        self.pages = {1:url} #page numbers and url
        self.pageNum = 1 #the page crawled
        self.url = url #the url crawled
        self.lastPage = 1000000
        self.home = self.url[0:url.index(".com/") + 4]
        self.sleep_time = sleep_time #in seconds

    def crawl(self):
        #set up selenium
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--test-type")
        options.add_argument("--disable-notifications")

        #when in linux vm add these lines
        #solves devtoolactiveport problem
        if self.linux_vm == 1:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            driver = webdriver.Chrome("/usr/bin/chromedriver", options=options)
        else: #when in windows
            driver = webdriver.Chrome("C:\Program Files (x86)\Google\Chrome\chromedriver", options=options)

        #driver = webdriver.PhantomJS("C:\Program Files (x86)\Google\Chrome\phantomjs")

        #links to reviews, not the reviews
        if "allAttractions" in self.url:
            while self.pageNum <= self.lastPage: #up to last page only
                start_time = datetime.datetime.now()  # run time

                #visit url
                self.url = self.pages[self.pageNum]
                #print("Visit", self.url)
                driver.get(self.url)
                response = driver.page_source

                #dump the file
                #fname = "all_attractions_page" + str(self.pageNum) + ".html"
                #writer = open(fname, "w", encoding="utf8")
                #writer.write(response)
                #writer.close()

                #parse the response
                self.parse(response)
                self.get_pages(response)

                finish_getting_data = datetime.datetime.now() #run time
                print("Finish getting page", self.pageNum ,"in",
                      (finish_getting_data - start_time).seconds, "seconds")
                time.sleep(10)
                self.pageNum += 1


    def parse(self, response):
        #content = open("all_attractions_page1.html", "r", encoding="utf8").read()

        soup = BeautifulSoup(response, 'html.parser')
        #print(soup.prettify()) #for easy reading

        #get attraction name, and url
        file_name = 'attractive_places.csv'
        fieldnames = ['name', 'url']
        if os.path.isfile(file_name):
            attractive_writer = open(file_name, 'a', newline="")
            attractive_csv = csv.writer(attractive_writer)
        else:
            attractive_writer = open(file_name, 'w', newline="")
            attractive_csv = csv.writer(attractive_writer)
            attractive_csv.writerow(fieldnames)

        # get attraction name, and url
        divs = soup.find_all("div", {"class": "tracking_attraction_title"})
        for div in divs:
            a = div.findChildren("a",href=True,recursive=False)[0]
            attraction_name = a.getText()
            attraction_url = self.home + a["href"]
            attractive_csv.writerow([attraction_name, attraction_url])

            #file_size = os.stat(file_name).st_size

            #print(file_size)
            #print(name, url)
        attractive_writer.close()

        #print(item_list)

    def get_pages(self, response):
        #content = open("all_attractions_page1.html", "r", encoding="utf8").read()


        soup = BeautifulSoup(response, 'html.parser')
        divs = soup.find("div", {"class": "pageNumbers"})

        children = divs.findChildren("a", href=True, recursive=False)
        all_numbers = []
        for a in children:
            this_page = int(a['data-page-number'])
            self.pages[this_page] = self.home + a['href']
            all_numbers.append(this_page)

        self.lastPage = max(all_numbers)
            #print("Found the URL:", a['data-page-number'], a['href'])

        #print(self.pages)

all_attractions_url = "https://www.tripadvisor.com/Attractions-g294265-Activities-a_allAttractions.true-Singapore.html"
rc = ReviewCrawler(0, all_attractions_url, 5)
rc.crawl()
