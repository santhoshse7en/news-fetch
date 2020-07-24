from newsfetch.helpers import (get_chrome_web_driver, get_web_driver_options,
                               set_automation_as_head_less,
                               set_browser_as_incognito,
                               set_ignore_certificate_error)
from newsfetch.utils import (BeautifulSoup, Options, UserAgent, get, re,
                             webdriver)


class google_search:

    def __init__(self, keyword, newspaper_url):

        self.keyword = keyword
        self.newspaper_url = newspaper_url

        random_headers = {'User-Agent': UserAgent().random,
                          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

        self.search_term = f'{self.keyword} site:{self.newspaper_url}'


        url = f"https://www.google.com/search?q={'+'.join(self.search_term.split())}"


        options = get_web_driver_options()
        set_automation_as_head_less(options)
        set_ignore_certificate_error(options)
        set_browser_as_incognito(options)
        driver = get_chrome_web_driver(options)
        driver.get(url)

        try:

            url_list = []

            if len(driver.find_elements_by_xpath('//div[@id="result-stats"]')) != 0:

                options = get_web_driver_options()
                set_automation_as_head_less(options)
                set_ignore_certificate_error(options)
                set_browser_as_incognito(options)
                driver = get_chrome_web_driver(options)
                driver.get(url)

                results = driver.find_elements_by_xpath('//div[@id="result-stats"]')[0].text
                results = results[:results.find('results')]
                max_pages = round(int(int(''.join(i for i in results if i.isdigit())) / 10))

            url_list = []

            if max_pages != 0:

                browser = webdriver.Chrome(chrome_options=options)
                driver.get(url)

                index = 0

                while True:
                    try:
                        index += 1
                        links = driver.find_elements_by_xpath('//div[@class="r"]/a')
                        linky = [link.get_attribute('href') for link in links]
                        url_list.extend(linky)
                        if index == max_pages:
                            break
                        driver.find_element_by_xpath(
                            '//*[@id="pnnext"]/span[2]').click()
                        time.sleep(2)
                        sys.stdout.write('\r%s : %s\r' % (str(index), str(max_pages)))
                        sys.stdout.flush()
                    except:
                        pass

                driver.quit()
            else:
                raise ValueError('Your search - %s - did not match any documents.' % str(self.search_term))

            url_list = list(dict.fromkeys(url_list))
            url_list = [url for url in url_list if '.pdf' not in url]
            self.urls = [url for url in url_list if '.xml' not in url]

        except:
            raise ValueError('Your search - %s - did not match any documents.' % str(self.search_term))
