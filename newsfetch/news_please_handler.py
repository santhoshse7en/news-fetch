from urllib.parse import unquote

from newsplease import NewsPlease
from helpers import clean_text, unicode


class NewsPleaseHandler:
    """Handle interactions with the NewsPlease library."""

    def __init__(self, url: str):
        self.url = url
        self.__news_please = self.__safe_execute(lambda: NewsPlease.from_url(self.url, timeout=6))

    @staticmethod
    def __safe_execute(func):
        """Executes a function and returns None if it raises an exception."""
        try:
            return func()
        except Exception:
            # Optional: log the exception here
            return None

    def is_valid(self) -> bool:
        """Check if the NewsPlease instance is valid."""
        return self.__news_please is not None

    @property
    def authors(self) -> list:
        """Return authors from NewsPlease instance."""
        return self.__news_please.authors if self.is_valid() else []

    @property
    def date_publish(self) -> str:
        """Return publication date from NewsPlease instance."""
        return str(self.__news_please.date_publish) if self.is_valid() else None

    @property
    def date_modify(self) -> str:
        """Return modification date from NewsPlease instance."""
        return str(self.__news_please.date_modify) if self.is_valid() else None

    @property
    def date_download(self) -> str:
        """Return download date from NewsPlease instance."""
        return str(self.__news_please.date_download) if self.is_valid() else None

    @property
    def image_url(self) -> str:
        """Return image URL from NewsPlease instance."""
        return self.__news_please.image_url if self.is_valid() else None

    @property
    def filename(self) -> str:
        """Return filename from NewsPlease instance."""
        return unquote(self.__news_please.filename) if self.is_valid() else None

    @property
    def title_page(self) -> str:
        """Return title page from NewsPlease instance."""
        return self.__news_please.title_page if self.is_valid() else None

    @property
    def title_rss(self) -> str:
        """Return RSS title from NewsPlease instance."""
        return self.__news_please.title_rss if self.is_valid() else None

    @property
    def language(self) -> str:
        """Return language from NewsPlease instance."""
        return self.__news_please.language if self.is_valid() else None

    @property
    def summary(self) -> str:
        """Return description from NewsPlease instance."""
        return self.__news_please.description if self.is_valid() else None

    @property
    def article(self) -> str:
        """Return cleaned article text from the NewsPlease instance."""
        return unicode(clean_text(self.__news_please.maintext)) if self.is_valid() else None

    @property
    def source_domain(self) -> str:
        """Return source domain from NewsPlease instance."""
        return self.__news_please.source_domain if self.is_valid() else None

    @property
    def headline(self) -> str:
        """Return headline from NewsPlease instance."""
        return unicode(self.__news_please.title) if self.is_valid() else None
