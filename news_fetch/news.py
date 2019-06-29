# -*- coding: utf-8 -*-
"""
Created on Sat Jun 29 10:10:04 2019

@author: M.Santhosh Kumar
"""
from news_fetch.utils import *

class google_search:

    def __init__(self, keyword, newspaper_url):

        self.keyword = keyword
        self.newspaper_url = newspaper_url

        random_headers = {'User-Agent': UserAgent().random,'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

        self.search_term = str(self.keyword) + ' site:' + str(self.newspaper_url)

        sys.stdout.write('\r' + 'Google Search Keyword : ' + str(self.search_term) + '\r')
        sys.stdout.flush()

        url = 'https://www.google.com/search?q=' + '+'.join(self.search_term.split())

        soup = BeautifulSoup(get(url, headers=random_headers).text, 'lxml')

        try:
            # Extracts the digits if it the resulted number without comma ','. eg: About 680 results (0.23 seconds)
            max_pages = round([int(s) for s in soup.select_one('div#resultStats').text.split() if s.isdigit()][0]/10)
            max_pages = max_pages + 1
        except:
            # Extracts the digits if it the resulted number without comma ','. eg: About 1,080 results (0.23 seconds)
            max_pages = round(int(''.join(i for i in soup.select_one('div#resultStats').text if i.isdigit()))/10)
            max_pages = max_pages + 1

        url_list = []

        options = Options()
        options.headless = True
        browser = webdriver.Chrome(options=options)
        browser.get(url)

        index = 0

        while True:
            try:
                index +=1
                page = browser.page_source
                soup = BeautifulSoup(page, 'lxml')
                linky = [soup.select('.r')[i].a['href'] for i in range(len(soup.select('.r')))]
                url_list.extend(linky)
                if index == max_pages:
                    break
                browser.find_element_by_xpath('//*[@id="pnnext"]/span[2]').click()
                time.sleep(2)
                sys.stdout.write('\r' + str(index) + ' : ' + str(max_pages) + '\r')
                sys.stdout.flush()
            except:
                pass

        browser.quit()

        self.urls = list(dict.fromkeys(url_list))
        sys.stdout.write('\r' + 'Total google search result urls extracted from the above keyword : ' + str(len(self.urls)) + '\r')
        sys.stdout.flush()

class newspaper:

    def __init__(self, url):
        self.url = url
        article = Article(self.url, request_timeout=10)
        article.download()
        article.parse()
        article.nlp()
        soup = BeautifulSoup(article.html, 'lxml')

        def cleaning_text(text):
            text = re.sub(r'\b(?:(?:https?|ftp)://)?\w[\w-]*(?:\.[\w-]+)+\S*', ' ', text.lower())
            words = re.findall(r'[a-zA-Z0-9:.,]+', text)
            return ' '.join(words)

        def author(soup):
            i = 0
            while True:
                try:
                    meta = json.loads(soup.select('script[type="application/ld+json"]')[i].text)
                    author = meta.get('author')['name']
                    if '' != author:
                        break
                except:
                    pass
                i+=1
                if i == 3:
                    break
            return author

        def date(soup):
            i = 0
            while True:
                try:
                    meta = json.loads(soup.select('script[type="application/ld+json"]')[i].text)
                    date = meta.get('datePublished')
                    if '' != date:
                        break
                except:
                    pass
                i+=1
                if i == 3:
                    break
            return date

        def publisher(soup):
            i = 0
            while True:
                try:
                    meta = json.loads(soup.select('script[type="application/ld+json"]')[i].text)
                    publisher = meta.get('publisher')['name']
                    if '' != publisher:
                        break
                except:
                    pass
                i+=1
                if i == 3:
                    break
            return publisher
        """
        :returns: author Name
        """
        try:
            self.author = author(soup)
        except:
            self.author = None

        """
        :returns: published Date
        """
        try:
            try:
                self.date = date(soup)
            except:
                self.date = article.meta_data['article']['published_time']
        except:
            self.date = None

        """
        :returns: article
        """
        try:
            self.article = cleaning_text(article.text)
        except:
            self.article = None

        """
        :returns: headlines
        """
        try:
            self.headline = cleaning_text(article.title)
        except:
            self.headline = None

        """
        :returns: keywords
        """
        try:
            self.keywords = article.keywords
        except:
            self.keywords = None

        """
        :returns: summary
        """
        try:
            self.summary = cleaning_text(article.summary)
        except:
            self.summary = None

        """
        :returns: description
        """
        try:
            try:
                self.description = cleaning_text(article.meta_description)
            except:
                self.description = cleaning_text(article.meta_data['description'])
        except:
            self.description = None

        """
        :returns: publication
        """
        try:
            try:
                self.publication = publisher(soup)
            except:
                self.publication = article.meta_data['og']['site_name']
        except:
            self.publication = None

        """
        :returns: category
        """
        try:
            try:
                text = cleaning_text((article.url[len(article.source_url):])).split()[1]
                self.category = [item[0] for item in suggest(text)][0]
            except:
                self.category = article.meta_data['article']['section']
        except:
            self.category = None
