from newsfetch.newspaper_handler import ArticleHandler
from newsfetch.news_please_handler import NewsPleaseHandler
from newsfetch.soup_handler import SoupHandler

class Newspaper:
    """Class to scrape and extract information from a news article."""

    def __init__(self, url: str) -> None:
        """Initialize the Newspaper object with the given URL."""
        self.url = url
        self.__news_please = NewsPleaseHandler(url)
        self.__article = ArticleHandler(url)
        self.__soup = SoupHandler(url)

        # Validate initialization
        self.__validate_initialization()

        # If article is available, download and parse it
        if self.__article.is_valid():
            self.__article.download_and_parse()

        # Extract data attributes
        self.headline = self.__extract_headline()
        self.article = self.__extract_article()
        self.authors = self.__extract_authors()
        self.date_publish = self.__extract_date_publish()
        self.date_modify = self.__extract_date_modify()
        self.date_download = self.__extract_date_download()
        self.image_url = self.__extract_image_url()
        self.filename = self.__extract_filename()
        self.title_page = self.__extract_title_page()
        self.title_rss = self.__extract_title_rss()
        self.language = self.__extract_language()
        self.publication = self.__extract_publication()
        self.category = self.__extract_category()
        self.keywords = self.__extract_keywords()
        self.summary = self.__extract_summary()
        self.source_domain = self.__extract_source_domain()
        self.source_favicon_url = self.__extract_source_favicon_url()
        self.description = self.__extract_description()

        self.get_dict = self.__serialize()

    def __validate_initialization(self):
        """Raise an error if no valid data is found."""
        if not (self.__news_please.is_valid() or self.__article.is_valid() or self.__soup.is_valid()):
            raise ValueError("Sorry, the page you are looking for doesn't exist.")

    @staticmethod
    def __extract(*sources):
        """Generic method to extract the first valid value from provided sources."""
        for source in sources:
            value = source  # Accessing the property directly
            if value:
                return value
        return None

    def __extract_authors(self):
        """Extract the authors from the article or the news source."""
        return self.__extract(self.__news_please.authors, self.__article.authors, self.__soup.authors)

    def __extract_date_publish(self):
        """Extract the publication date of the article."""
        return self.__extract(self.__news_please.date_publish, self.__article.date_publish, self.__soup.date_publish)

    def __extract_date_modify(self):
        """Extract the modification date of the article."""
        return self.__news_please.date_modify

    def __extract_date_download(self):
        """Extract the date the article was downloaded."""
        return self.__news_please.date_download

    def __extract_image_url(self):
        """Extract the URL of the article's image."""
        return self.__news_please.image_url

    def __extract_filename(self):
        """Extract the filename of the article."""
        return self.__news_please.filename

    def __extract_article(self):
        """Extract the article content."""
        return self.__extract(self.__news_please.article, self.__article.article)

    def __extract_title_page(self):
        """Extract the title of the article page."""
        return self.__news_please.title_page

    def __extract_title_rss(self):
        """Extract the RSS title of the article."""
        return self.__news_please.title_rss

    def __extract_language(self):
        """Extract the language of the article."""
        return self.__news_please.language

    def __extract_publication(self):
        """Extract the publication name of the article."""
        return self.__extract(self.__article.publication, self.__soup.publisher)

    def __extract_category(self):
        """Extract the category of the article."""
        return self.__extract(self.__article.category, self.__soup.category)

    def __extract_headline(self):
        """Extract the headline of the article."""
        return self.__extract(self.__news_please.headline, self.__article.headline)

    def __extract_keywords(self):
        """Extract the keywords associated with the article."""
        return self.__article.keywords or []

    def __extract_summary(self):
        """Extract the summary of the article."""
        return self.__article.summary

    def __extract_source_domain(self):
        """Extract the source domain of the article."""
        return self.__news_please.source_domain

    def __extract_source_favicon_url(self):
        """Extract the source favicon URL of the article."""
        return self.__article.meta_favicon

    def __extract_description(self):
        """Extract the description of the article."""
        return self.__extract(self.__news_please.summary, self.__article.summary)

    def __serialize(self):
        """Return a dictionary representation of the article's data."""
        return {
            "headline": self.headline,
            "author": self.authors,
            "date_publish": self.date_publish,
            "date_modify": self.date_modify,
            "date_download": self.date_download,
            "language": self.language,
            "image_url": self.image_url,
            "filename": self.filename,
            "description": self.description,
            "publication": self.publication,
            "category": self.category,
            "source_domain": self.source_domain,
            "source_favicon_url": self.source_favicon_url,
            "article": self.article,
            "summary": self.summary,
            "keyword": self.keywords,
            "title_page": self.title_page,
            "title_rss": self.title_rss,
            "url": self.url
        }
