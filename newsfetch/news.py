from concurrent.futures import ThreadPoolExecutor

from newsfetch.newspaper_handler import ArticleHandler
from newsfetch.soup_handler import SoupHandler

_WORDS_PER_MINUTE = 200

class Newspaper:
    """Class to scrape and extract information from a news article."""

    def __init__(self, url: str) -> None:
        """Initialize the Newspaper object with the given URL."""
        self.url = url
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
        self.image_url = self.__extract_image_url()
        self.language = self.__extract_language()
        self.publication = self.__extract_publication()
        self.category = self.__extract_category()
        self.keywords = self.__extract_keywords()
        self.summary = self.__extract_summary()
        self.source_domain = self.__extract_source_domain()
        self.source_favicon_url = self.__extract_source_favicon_url()
        self.description = self.__extract_description()
        self.word_count = self.__extract_word_count()
        self.reading_time_minutes = self.__extract_reading_time_minutes()

        self.get_dict = self.__serialize()

    @classmethod
    def from_urls(cls, urls: list[str], max_workers: int = 5) -> list["Newspaper | None"]:
        """Scrape multiple URLs concurrently.

        Returns a list the same length and order as `urls`, with None in place
        of any URL that failed (invalid page, network error, etc.) so one bad
        URL doesn't abort the whole batch.
        """
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(cls.__safe_init, urls))

    @classmethod
    def __safe_init(cls, url: str) -> "Newspaper | None":
        try:
            result = cls(url=url)
        except Exception:
            return None
        return result if (result.headline or result.article) else None

    def __validate_initialization(self) -> None:
        """Raise an error if no valid data is found."""
        if not (self.__article.is_valid() or self.__soup.is_valid()):
            raise ValueError("Sorry, the page you are looking for doesn't exist.")

    @staticmethod
    def __extract(*sources: str | list[str] | None) -> str | list[str] | None:
        """Generic method to extract the first valid value from provided sources."""
        for source in sources:
            value = source  # Accessing the property directly
            if value:
                return value
        return None

    def __extract_authors(self) -> list[str]:
        """Extract the authors from the article or the news source."""
        return self.__extract(self.__article.authors, self.__soup.authors)

    def __extract_date_publish(self) -> str | None:
        """Extract the publication date of the article."""
        return self.__extract(self.__article.date_publish, self.__soup.date_publish)

    def __extract_date_modify(self) -> str | None:
        """Extract the modification date of the article."""
        return self.__soup.date_modify

    def __extract_image_url(self) -> str | None:
        """Extract the URL of the article's image."""
        return self.__article.image_url

    def __extract_article(self) -> str | None:
        """Extract the article content."""
        return self.__article.article

    def __extract_language(self) -> str | None:
        """Extract the language of the article."""
        return self.__article.language

    def __extract_publication(self) -> str | None:
        """Extract the publication name of the article."""
        return self.__extract(self.__article.publication, self.__soup.publisher)

    def __extract_category(self) -> str | None:
        """Extract the category of the article."""
        return self.__extract(self.__article.category, self.__soup.category)

    def __extract_headline(self) -> str | None:
        """Extract the headline of the article."""
        return self.__article.headline

    def __extract_keywords(self) -> list[str]:
        """Extract the keywords associated with the article."""
        return self.__article.keywords or []

    def __extract_summary(self) -> str | None:
        """Extract the summary of the article."""
        return self.__article.summary

    def __extract_source_domain(self) -> str | None:
        """Extract the source domain of the article."""
        return self.__article.source_domain

    def __extract_source_favicon_url(self) -> str | None:
        """Extract the source favicon URL of the article."""
        return self.__article.meta_favicon

    def __extract_description(self) -> str | None:
        """Extract the description of the article."""
        return self.__article.summary

    def __extract_word_count(self) -> int:
        """Count the words in the extracted article text."""
        return len(self.article.split()) if self.article else 0

    def __extract_reading_time_minutes(self) -> int:
        """Estimate reading time in minutes at 200 words per minute."""
        return max(1, round(self.word_count / _WORDS_PER_MINUTE)) if self.word_count else 0

    def __serialize(self) -> dict:
        """Return a dictionary representation of the article's data."""
        return {
            "headline": self.headline,
            "author": self.authors,
            "date_publish": self.date_publish,
            "date_modify": self.date_modify,
            "language": self.language,
            "image_url": self.image_url,
            "description": self.description,
            "publication": self.publication,
            "category": self.category,
            "source_domain": self.source_domain,
            "source_favicon_url": self.source_favicon_url,
            "article": self.article,
            "summary": self.summary,
            "keyword": self.keywords,
            "word_count": self.word_count,
            "reading_time_minutes": self.reading_time_minutes,
            "url": self.url
        }
