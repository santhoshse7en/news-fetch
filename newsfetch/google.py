from newsfetch.utils import (BeautifulSoup, Options, UserAgent, get, re, sys,
                              webdriver)


class google_search:

    def __init__(self, keyword, newspaper_url):

        self.keyword = keyword
        self.newspaper_url = newspaper_url

        random_headers = {'User-Agent': UserAgent().random,
                          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

        self.search_term = '%s site:%s' % (str(self.keyword), str(self.newspaper_url))

        sys.stdout.write('\r Google Search Keyword : %s\r' % str(self.search_term))
        sys.stdout.flush()

        url = '%s%s' % ('https://www.google.com/search?q=', '+'.join(self.search_term.split()))

        soup = BeautifulSoup(get(url, headers=random_headers).text, 'lxml')

        if soup.select_one('p[role="heading"]') is None:
            try:
                # Extracts the digits if it the resulted number without comma ','. eg: About 680 results (0.23 seconds)
                max_pages = round([int(s) for s in soup.select_one(
                    'div#resultStats').text.split() if s.isdigit()][0]/10)
                max_pages = max_pages + 1
            except:
                # Extracts the digits if it the resulted number without comma ','. eg: About 1,080 results (0.23 seconds)
                sk = re.findall(
                    r'[0-9,.]+', soup.select_one('div#resultStats').text)[0]
                max_pages = round(
                    int(''.join(i for i in sk if i.isdigit()))/10)
                max_pages = max_pages + 1
        else:
            max_pages = 0

        url_list = []

        if max_pages != 0:
            options = Options()
            options.add_argument(
                '--user-data-dir=/User/supremesprite/Library/Application Support/Google/Chrome/')
            options.add_argument('--profile-directory=Default')
            options.add_argument('--user-data-dir=C:/Temp/ChromeProfile')
            #options.headless = True
            browser = webdriver.Chrome(chrome_options=options)
            browser.get(url)

            index = 0

            while True:
                try:
                    index += 1
                    page = browser.page_source
                    soup = BeautifulSoup(page, 'lxml')
                    linky = [soup.select('.r')[i].a['href']
                             for i in range(len(soup.select('.r')))]
                    url_list.extend(linky)
                    if index == max_pages:
                        break
                    browser.find_element_by_xpath(
                        '//*[@id="pnnext"]/span[2]').click()
                    time.sleep(2)
                    sys.stdout.write('\r%s : %s\r' % (str(index), str(max_pages)))
                    sys.stdout.flush()
                except:
                    pass

            browser.quit()
        else:
            print('Your search - %s - did not match any documents.' % str(self.search_term))

        url_list = list(dict.fromkeys(url_list))
        url_list = [url for url in url_list if '.pdf' not in url]
        self.urls = [url for url in url_list if '.xml' not in url]
        sys.stdout.write('\r Total google search result urls extracted .xml and .pdf link excluded from the above keyword : %s\r' % str(len(self.urls)))
        sys.stdout.flush()
