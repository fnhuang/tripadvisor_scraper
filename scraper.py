import datetime
from selenium import webdriver

class ReviewCrawler():
    start_url = 'https://www.tripadvisor.com.sg/Attraction_Review-g294265-d8077179-Reviews-National_Gallery_Singapore-Singapore.html'

    def __init__(self):
        self.html_file = open("national_gallery.html", 'w')

    def selenium(self):
        start_time = datetime.datetime.now()
        url = 'https://www.tripadvisor.com.sg/Attraction_Review-g294265-d8077179-Reviews-National_Gallery_Singapore-Singapore.html'
        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument("--test-type")
        options.add_argument("--disable-notifications")
        # options.add_argument("--headless")

        driver = webdriver.Chrome("chromedriver", options=options)
        # driver = webdriver.PhantomJS("C:\Program Files (x86)\Google\Chrome\phantomjs")
        driver.get(url)


        writer = open("national_gallery.html", "w", encoding="utf8")
        page = driver.page_source
        writer.write(page)
        writer.close()

        finish_getting_data = datetime.datetime.now()
        print("Finish getting data in", (finish_getting_data - start_time).microseconds, "microsec")

    def parse(self, response):
        url = response.url
        self.html_file.write(response.body.decode("utf-8"))
        self.html_file.close()
        yield {
            'url': url
        }

rc = ReviewCrawler()
rc.selenium()
