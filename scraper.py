import datetime
from selenium import webdriver
from bs4 import BeautifulSoup
import json
import os
import csv
import time
import sys
import re
import glob

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
                time.sleep(self.sleep_time)
                self.pageNum += 1
        else:
            name_array = self.url[self.url.rindex("/"):].split("-")
            fname = name_array[len(name_array) - 2].lower()

            file_name = "reviews/" + fname + ".csv"
            fieldnames = ['review_page', 'review_title', 'review_content', 'review_language', 'review_date',
                          'user_name', 'user_location', 'user_contribution', 'user_helpfulVote']
            if os.path.isfile(file_name):
                attractive_writer = open(file_name, 'a', newline="", encoding="utf8")
                attractive_csv = csv.writer(attractive_writer)
            else:
                attractive_writer = open(file_name, 'w', newline="", encoding="utf8")
                attractive_csv = csv.writer(attractive_writer)
                attractive_csv.writerow(fieldnames)

            while self.pageNum <= self.lastPage:

                # visit url
                self.url = self.pages[self.pageNum]
                # print("Visit", self.url)
                driver.get(self.url)
                response = driver.page_source

                try:
                    self.parse_review(response, attractive_csv)
                    attractive_writer.flush()
                except:
                    # dump the file if file cannot be parsed properly
                    file_name = fname + "_page" + str(self.pageNum) + ".html"
                    soup = BeautifulSoup(response, 'html.parser')
                    writer = open("raw_html/" + file_name, "w", encoding="utf8")
                    writer.write(soup.prettify())
                    writer.close()

                if len(self.pages) < 2:
                    self.get_review_pages(response)
                    self.extract_additional_info(response)

                #print(self.pages.keys())

                if self.pageNum % 1000 != 0:
                    print("Finish getting page", self.pageNum,
                          "for attraction", fname, end='\r')
                else:
                    print("Finish getting page", self.pageNum,
                          "for attraction", fname,
                          ". Sleep for", self.sleep_time, "seconds", end='\r')
                    time.sleep(self.sleep_time)
                self.pageNum += 1

            attractive_writer.close()
        driver.quit()

    def parse_review (self, response, attractive_csv):
        #response = open("raw_html/national_gallery_singapore_page2.html", "r", encoding="utf8").read()

        json_mark = "window.__WEB_CONTEXT__={pageManifest:"
        json_text = response[response.index(json_mark) + len(json_mark):]
        json_text = json_text[0:json_text.index(";(window.$WP=window.$WP||")-1]
        pageManifest = json.loads(json_text)
        urqlCache = pageManifest["urqlCache"]


        for item_key in iter(urqlCache):
            item = urqlCache[item_key]
            if "locations" in item["data"]:
                item_data = item["data"]["locations"][0]
                if "reviewListPage" in item_data.keys():
                    reviews = item_data["reviewListPage"]["reviews"]
                    break


        for review in reviews:
            review_title = review["title"]
            review_content = review["text"].strip()
            review_content = re.sub('( +|\n|\t)', ' ', review_content) #remove all extra white spaces
            review_language = review["language"]
            review_date = review["createdDate"]

            userProfile = review["userProfile"]
            username = userProfile["username"]
            location_json = userProfile["hometown"]
            location = location_json["fallbackString"]
            if location_json["locationId"] != None:
                location = location_json["location"]["additionalNames"]["long"]
            reviewer_contribution = userProfile["contributionCounts"]["sumAllUgc"]
            reviewer_helpfulVote = userProfile["contributionCounts"]["helpfulVote"]

            attractive_csv.writerow([str(self.pageNum), review_title, review_content, review_language, review_date,
                                     username, location, reviewer_contribution, reviewer_helpfulVote])
            #print(review_title, review_content, review_language, review_date, username, location, reviewer_contribution, reviewer_helpfulVote)



    def parse(self, response):
        #response = open("all_attractions_page29.html", "r", encoding="utf8").read()

        soup = BeautifulSoup(response, 'html.parser')
        #w = open("prettify2.html","w",encoding="utf8")
        #w.write(soup.prettify()) #for easy reading
        #w.close()

        #get attraction name, and url
        file_name = 'attractive_places.csv'
        fieldnames = ['name', 'url', 'reviews','rating','tag']
        if os.path.isfile(file_name):
            attractive_writer = open(file_name, 'a', newline="", encoding="utf8")
            attractive_csv = csv.writer(attractive_writer)
        else:
            attractive_writer = open(file_name, 'w', newline="", encoding="utf8")
            attractive_csv = csv.writer(attractive_writer)
            attractive_csv.writerow(fieldnames)

        # get attraction name, and url
        divs = soup.find_all("div", {"class": "tracking_attraction_title"})
        for div in divs:
            a = div.findChild("a",href=True,recursive=False)
            attraction_name = a.getText()
            attraction_url = self.home + a["href"]

            rs_rating = div.parent.findChild("div", {"class": "listing_rating"}).\
                findChild("div", {"class": "rs rating"})
            num_review = 0
            rating = 0
            if rs_rating != None:
                num_review_href = rs_rating.findChild("span", {"class": "more"}).\
                    findChild("a", href=True)
                num_review = int(num_review_href.getText().replace(",","").
                                 replace("reviews","").replace("review",""))

                bubble_rating = rs_rating.findChildren("span")[0]
                rating = float(bubble_rating["alt"].replace("of 5 bubbles",""))

            tag = ""
            tag_line = div.parent.findChild("div",{"class": "tag_line"} )
            tag_span = tag_line.findChild("span")
            if tag_span != None:
                tag = tag_span.getText()



            attractive_csv.writerow([attraction_name, attraction_url, num_review, rating, tag])

            #file_size = os.stat(file_name).st_size

            #print(file_size)
            #print(name, url)
        attractive_writer.close()

        #print(item_list)

    def get_review_pages(self, response):
        #response = open("national_gallery_singapore.html", "r", encoding="utf8").read()

        soup = BeautifulSoup(response, 'html.parser')
        div = soup.find("div", {"class": "pageNumbers"})

        children = div.findChildren("a", href=True, recursive=False)
        all_numbers = []

        for a in children:
            this_page = int(a.getText())
            self.pages[this_page] = self.home + a['href']
            all_numbers.append(this_page)

        self.lastPage = max(all_numbers)
        all_numbers.remove(self.lastPage)
        max_b4_last = max(all_numbers)

        frame = self.pages[2]
        reg = re.compile("or[0-9]+")
        for this_page in range(max_b4_last, self.lastPage + 1):
            to_replace = re.findall(reg,frame)[0]
            self.pages[this_page] = frame.replace(to_replace, "or" + str((this_page - 1) * 5))


        #print(self.pages)

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

    def delete_reviews(self, review_file, page_numbers):
        reader = open(review_file, "r", encoding="utf8")
        csv_reader = csv.DictReader(reader)

        attractive_writer = open("temp.csv", "w", encoding="utf8", newline="")
        csv_writer = csv.writer(attractive_writer)
        csv_writer.writerow(csv_reader.fieldnames)

        for row in csv_reader:
            if int(row["review_page"]) not in page_numbers:
                csv_writer.writerow(list(row.values()))

        attractive_writer.close()
        reader.close()
        os.remove(review_file)
        os.rename("temp.csv", review_file)

    def extract_additional_info(self, response):
        #response = open("joo_chiat.html","r",encoding="utf8").read()
        file_name = "additional_info.csv"
        fieldnames = ['url', 'latitude', 'longitude', 'rating_1', 'rating_2',
                      'rating_3', 'rating_4', 'rating_5']

        if os.path.isfile(file_name):
            attractive_writer = open(file_name, 'a', newline="", encoding="utf8")
            attractive_csv = csv.writer(attractive_writer)
        else:
            attractive_writer = open(file_name, 'w', newline="", encoding="utf8")
            attractive_csv = csv.writer(attractive_writer)
            attractive_csv.writerow(fieldnames)

        existing_info = open("additional_info.csv","r",encoding="utf8").read()
        if self.url not in existing_info:
            soup = BeautifulSoup(response, 'html.parser')

            values = []
            values.append(self.url)

            json_mark = "window.__WEB_CONTEXT__={pageManifest:"
            json_text = response[response.index(json_mark) + len(json_mark):]
            json_text = json_text[0:json_text.index(";(window.$WP=window.$WP||") - 1]
            pageManifest = json.loads(json_text)
            redux = pageManifest["redux"]["api"]["responses"]
            reg = re.compile("\/data\/1\.0\/location\/[0-9]+")
            to_find = re.findall(reg, json.dumps(redux))[0]
            if to_find in redux.keys():
                location_data = redux[to_find]["data"]
                latitude = location_data["latitude"]
                longitude = location_data["longitude"]
                values.append(latitude); values.append(longitude)
            else:
                values.append("NA"); values.append("NA");

            for i in range(1,6):
                id = "ReviewRatingFilter_" + str(i)
                inp = soup.find("input", {"id": id})
                num = re.sub('[^0-9]', '', inp.parent.getText())
                values.append(num)

            attractive_csv.writerow(values)

        attractive_writer.close()

    def fix_reviews(self):
        name_array = self.url[self.url.rindex("/"):].split("-")
        fname = name_array[len(name_array) - 2].lower()
        file_name = "reviews/" + fname + ".csv"

        flist = glob.glob("raw_html/" + fname + "*.html")
        page_numbers = []
        for fi in flist:
            start_index = fi.index("_page") + 5
            end_index = fi.rindex(".html")
            page_numbers.append(int(fi[start_index:end_index]))

        self.delete_reviews(file_name, page_numbers)

        attractive_writer = open(file_name, "a", encoding="utf8", newline="")
        csv_writer = csv.writer(attractive_writer)

        for fi in flist:
            print(fi)
            response = open(fi, "r", encoding="utf8").read()
            try:
                start_index = fi.index("_page") + 5
                end_index = fi.rindex(".html")
                self.pageNum = int(fi[start_index:end_index])
                self.parse_review(response, csv_writer)
                os.remove(fi)
            except:
                pass
            #sys.exit()

#startcrawl is 1 if you want to crawl first item "gardens by the bay"
def get_urls(start_crawl, end_crawl):
    reader = open("top300.csv", "r", encoding="utf8")
    csv_reader = csv.DictReader(reader)
    urls = {}
    for row in csv_reader:
        if int(row["done"]) == 0:
            if int(row["number"]) in range(start_crawl, end_crawl):
                urls[int(row["number"])] = row["url"]

    return urls

if __name__ == "__main__":
    start_crawl = int(sys.argv[1])
    end_crawl = int(sys.argv[2])

    urls = get_urls(start_crawl, end_crawl)

    vm = int(sys.argv[3])
    sleep = int(sys.argv[4])

    for number in range(start_crawl, end_crawl):
        url = urls[number]
        start_time = datetime.datetime.now()
        rc = ReviewCrawler(vm, url, sleep)
        rc.crawl()
        finish_getting_data = datetime.datetime.now()
        if rc.pageNum % 1000 != 0:
            sleep_time = (rc.pageNum % 1000) * 1.0 / 1000 * 600
            print("Finish crawling", number ,"in",
                  (finish_getting_data - start_time).seconds,
                  "seconds. Now sleep for", sleep_time, "seconds")
            time.sleep(sleep_time)

    '''start_time = datetime.datetime.now()
    vm = int(sys.argv[1])
    sleep = int(sys.argv[2])
    #vm = 0; sleep = 5
    #all_attractions_url = "https://www.tripadvisor.com/Attractions-g294265-Activities-a_allAttractions.true-Singapore.html"
    url2 ="https://www.tripadvisor.com/Attraction_Review-g294265-d6373042-Reviews-Lower_Seletar_Reservoir-Singapore.html"
    rc = ReviewCrawler(vm, url2, sleep)
    rc.crawl()
    #rc.extract_additional_info("test")
    #rc.parse_review("test","test")
    #rc.fix_reviews()'''

    '''finish_getting_data = datetime.datetime.now()  # run time
    print("Finish in", (finish_getting_data - start_time).seconds, "seconds")'''