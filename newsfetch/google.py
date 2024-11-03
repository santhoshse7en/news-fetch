from selenium import webdriver


class GoogleSearchNewsURLExtractor:
    """Extracts news article URLs from Google search results based on a keyword and site."""

    def __init__(self, keyword, news_domain):
        """Initialize with the search keyword and the target newspaper URL."""
        self.keyword = keyword
        self.news_domain = news_domain
        self.urls = []  # List to store extracted URLs

        # Prepare the search term for Google
        self.search_term = f"'{self.keyword}' site:{self.news_domain}"
        search_url = f"https://www.google.com/search?q={"+".join(self.search_term.split())}"

        # Set up the web driver options
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run in headless mode (no UI)
        options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
        options.add_argument("--incognito")  # Open in incognito mode

        # Start the web driver
        driver = webdriver.Chrome(options=options)
        driver.get(search_url)

        try:
            # Find and collect all news article links on the current page
            links = driver.find_elements("xpath", "//div[@class='yuRUbf']/div/span/a")
            url_list = [link.get_attribute("href") for link in links]

            # Filter out unwanted URLs (e.g., PDFs or XMLs) and remove duplicates
            url_list = list(dict.fromkeys(url_list))
            self.urls = [url for url in url_list if ".pdf" not in url and ".xml" not in url]

        except Exception as e:
            raise ValueError(f"An error occurred during the search: {e}")

        finally:
            driver.quit()  # Ensure the driver is closed at the end
