# -*- coding: utf-8 -*-
"""
Created on Sat Jun 29 10:10:04 2019

@author: M.Santhosh Kumar
"""
from newsfetch.utils import *

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

        if soup.select_one('p[role="heading"]') is None:
            try:
                # Extracts the digits if it the resulted number without comma ','. eg: About 680 results (0.23 seconds)
                max_pages = round([int(s) for s in soup.select_one('div#resultStats').text.split() if s.isdigit()][0]/10)
                max_pages = max_pages + 1
            except:
                # Extracts the digits if it the resulted number without comma ','. eg: About 1,080 results (0.23 seconds)
                sk = re.findall(r'[0-9,.]+', soup.select_one('div#resultStats').text)[0]
                max_pages = round(int(''.join(i for i in sk if i.isdigit()))/10)
                max_pages = max_pages + 1
        else:
            max_pages = 0

        url_list = []

        if max_pages != 0:
            options = Options()
            options.add_argument('--user-data-dir=/User/supremesprite/Library/Application Support/Google/Chrome/')
            options.add_argument('--profile-directory=Default')
            options.add_argument('--user-data-dir=C:/Temp/ChromeProfile')
            #options.headless = True
            browser = webdriver.Chrome(chrome_options=options)
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
        else:
            print('Your search - ' + str(self.search_term) + ' - did not match any documents.')

        url_list = list(dict.fromkeys(url_list))
        url_list = [url for url in url_list if '.pdf' not in url]
        self.urls = [url for url in url_list if '.xml' not in url]
        sys.stdout.write('\r' + 'Total google search result urls extracted .xml and .pdf link excluded from the above keyword : ' + str(len(self.urls)) + '\r')
        sys.stdout.flush()

class newspaper:

    def __init__(self, url):
        self.url = url
        try:
            try:
                try:
                    newsplease = NewsPlease.from_url(self.url, timeout=6)
                    article = Article(self.url, timeout=6)
                    article.download()
                    article.parse()
                    article.nlp()
                    soup = BeautifulSoup(article.html, 'lxml')
                except:
                    article = Article(self.url, timeout=6)
                    article.download()
                    article.parse()
                    article.nlp()
                    soup = BeautifulSoup(article.html, 'lxml')
            except:
                newsplease = NewsPlease.from_url(self.url, timeout=6)
                soup = BeautifulSoup(get(self.url).text, 'lxml')
        except:
            try:
                soup = BeautifulSoup(get(self.url).text, 'lxml')
                if 'page not found' in soup.select_one('title').text.lower():
                    sys.stdout.write('\r' + str('Sorry, the page') + ' - ' + str(self.url) + ' - ' + str('you are looking is no longer available.') + '\r')
                    sys.stdout.flush()
                    self.get_dict = 'N/A'
                    self.headline = 'N/A'
                    self.author = 'N/A'
                    self.date = 'N/A'
                    self.description = 'N/A'
                    self.publication = 'N/A'
                    self.section = 'N/A'
                    self.source_domain = 'N/A'
                    self.article = 'N/A'
                    self.summary = 'N/A'
                    self.keywords = 'N/A'
                    self.url = 'N/A'
            except:
                soup = BeautifulSoup(get(self.url).text, 'lxml')

        def cleaning_text(text):
            text = re.sub(r'\b(?:(?:https?|ftp)://)?\w[\w-]*(?:\.[\w-]+)+\S*', ' ', text.lower())
            words = re.findall(r'[a-zA-Z0-9:.,]+', text)
            return ' '.join(words)

        def author(soup):
            try:
                i = 0
                while True:
                    meta = json.loads(soup.select('script[type="application/ld+json"]')[i].text)
                    try:
                        if type(meta) == list:
                            author = meta[0].get('author')['name']
                            if '' != author:
                                break
                        else:
                            author = meta.get('author')['name']
                            if '' != author:
                                break
                    except:
                        for i in range(len(df['@graph'])):
                            if df['@graph'][i].get('author')['name'] != None:
                                date = str(df['@graph'][i].get('author')['name'])
                                break
                    i+=1
                    if i == 3:
                        break
            except:
                author = 'N/A'
            return author

        def date(soup):
            try:
                i = 0
                while True:
                    meta = json.loads(soup.select('script[type="application/ld+json"]')[i].text)
                    df = pd.DataFrame(meta)
                    try:
                        for i in range(len(df['@graph'])):
                            if df['@graph'][i].get('datePublished') != None:
                                date = str(df['@graph'][i].get('datePublished'))
                                break
                    except:
                        if type(meta) == list:
                            date = meta[0].get('datePublished')
                            if '' != date:
                                break
                        else:
                            date = meta.get('datePublished')
                            if '' != date:
                                break
                    i+=1
                    if i == 3:
                        break
            except:
                date = 'N/A'
            return date

        def category(soup):
            try:
                i = 0
                while True:
                    meta = json.loads(soup.select('script[type="application/ld+json"]')[i].text)
                    try:
                        if meta.get('@type') != None:
                            category = meta.get('@type')
                            break
                    except:
                        df = pd.DataFrame(meta)
                        for i in range(len(df['@graph'])):
                            if df['@graph'][i].get('articleSection') != None:
                                category = str(df['@graph'][i].get('articleSection'))
                                break
                    i+=1
                    if i == 3:
                        break
            except:
                try:
                    if article.meta_data['article']['section'] != {}:
                        category = article.meta_data['article']['section']
                except:
                    if article.meta_data['category'] != {}:
                        category = article.meta_data['category']
            return category

        def publisher(soup):
            try:
                i = 0
                while True:
                    meta = json.loads(soup.select('script[type="application/ld+json"]')[i].text)
                    try:
                        if type(meta) == list:
                            publisher = meta[0].get('publisher')['name']
                            if '' != publisher:
                                break
                        else:
                            publisher = meta.get('publisher')['name']
                            if '' != publisher:
                                break
                    except:
                        df = pd.DataFrame(meta)
                        for i in range(len(df['@graph'])):
                            if df['@graph'][i].get('publisher')['name'] != None:
                                category = str(df['@graph'][i].get('publisher')['name'])
                                break
                    i+=1
                    if i == 3:
                        break
            except:
                publisher = 'N/A'
            return publisher

        # Create our list of punctuation marks
        punctuations = string.punctuation

        # Create our list of stopwords
        nlp = spacy.load('en')

        # Load English tokenizer, tagger, parser, NER and word vectors
        parser = English()

        # Creating our tokenizer function
        def spacy_tokenizer(sentence):
            # Creating our token object, which is used to create documents with linguistic annotations.
            mytokens = parser(sentence)

            # Lemmatizing each token and converting each token into lowercase
            mytokens = [ word.lemma_.lower().strip() if word.lemma_ != "-PRON-" else word.lower_ for word in mytokens ]

            text = re.sub(r'\b(?:(?:https?|ftp)://)?\w[\w-]*(?:\.[\w-]+)+\S*', '', ' '.join(mytokens))
            words = re.findall(r'[a-zA-Z0-9:.,]+', ''.join(text))

            # return preprocessed list of tokens
            return ' '.join(words)

        """
        :returns: cleaned article
        """
        try:
            if cleaning_text(' '.join(article.text.replace('’', '').split())) != None:
                self.cleaned_article = spacy_tokenizer(' '.join(cleaning_text(' '.join(article.text.replace('’', '').split())).split()))
            elif cleaning_text(' '.join(newsplease.text.replace('’', '').split())) != None:
                self.cleaned_article = spacy_tokenizer(' '.join(cleaning_text(' '.join(newsplease.text.replace('’', '').split())).split()))
            else:
                self.cleaned_article = 'N/A'
        except:
            self.cleaned_article = 'N/A'

        """
        :returns: author Name
        """
        try:
            if len(newsplease.authors) != 0:
                self.author = newsplease.authors
            elif len(article.authors) != 0:
                self.author = article.authors
            elif author(soup) != None:
                self.author = [author(soup)]
            else:
                self.author = ['N/A']
        except:
            self.author = ['N/A']

        """
        :returns: published Date
        """
        try:
            try:
                if str(newsplease.date_publish) != 'None' or None:
                    self.date = str(newsplease.date_publish)
                elif str(newsplease.date_modify) != 'None' or None:
                    self.date = str(newsplease.date_modify)
                elif str(newsplease.date_download) != 'None' or None:
                    self.date =str(newsplease.date_download)
                elif article.meta_data['article']['published_time'] != None:
                    self.date = article.meta_data['article']['published_time']
            except:
                if date(soup) != None:
                    self.date = date(soup)
                else:
                    self.date = 'N/A'
        except:
            self.date = 'N/A'

        """
        :returns: article
        """
        try:
            if cleaning_text(' '.join(article.text.replace('’', '').split())) != None:
                self.article = ' '.join(cleaning_text(' '.join(article.text.replace('’', '').split())).split())
            elif cleaning_text(' '.join(newsplease.text.replace('’', '').split())) != None:
                self.article = ' '.join(cleaning_text(' '.join(newsplease.text.replace('’', '').split())).split())
            else:
                self.article = 'N/A'
        except:
            self.article = 'N/A'

        """
        :returns: headlines
        """
        try:
            if cleaning_text(article.title) != None:
                self.headline = cleaning_text(article.title)
            elif cleaning_text(newsplease.title) != None:
                self.headline = cleaning_text(newsplease.title)
            else:
                self.headline = 'N/A'
        except:
            self.headline = 'N/A'

        """
        :returns: keywords
        """
        key = []
        try:
            self.keywords = article.keywords
        except:
            self.keywords = ['N/A']

        """
        :returns: summary
        """
        try:
            self.summary = article.summary
        except:
            self.summary = 'N/A'

        """
        :returns: description
        """
        try:
            if cleaning_text(article.meta_description) != '':
                self.description = cleaning_text(article.meta_description)
            elif cleaning_text(article.meta_data['description']) != {}:
                self.description = cleaning_text(article.meta_data['description'])
            elif cleaning_text(newsplease.description) != None:
                self.description = cleaning_text(newsplease.description)
            else:
                self.description = 'N/A'
        except:
            self.description = 'N/A'

        """
        :returns: publication
        """
        try:
            try:
                try:
                    if article.meta_data['og']['site_name'] != None:
                        self.publication = article.meta_data['og']['site_name']
                except:
                    if publisher(soup) != None:
                        self.publication = publisher(soup)
            except:
                if self.url.split('/')[2] != None:
                    self.publication = self.url.split('/')[2]
                else:
                    self.publication = 'N/A'
        except:
            self.publication = 'N/A'

        """
        :returns: source domain
        """
        try:
            self.source_domain = newsplease.source_domain
        except:
            self.source_domain = 'N/A'

        """
        :returns: section
        """
        try:
            self.section = category(soup)
        except:
            try:
                words = re.findall(r'[a-zA-Z]+', ''.join(article.url.split('/')[3]))
                if ' '.join(words) != '':
                    self.section = ' '.join(words).split()[0]
            except:
                self.section = 'N/A'

        """
        :returns: serializable_dict
        """
        try:
            self.get_dict = {'headline' : self.headline,
                             'author' : self.author,
                             'date' : self.date,
                             'description' : self.description,
                             'publication' : self.publication,
                             'category' : self.section,
                             'source_domain' : self.source_domain,
                             'article' : self.article,
                             'cleaned_article' :self.cleaned_article,
                             'summary' : self.summary,
                             'keyword' : self.keywords,
                             'url' : self.url}
        except:
            self.get_dict = {}
