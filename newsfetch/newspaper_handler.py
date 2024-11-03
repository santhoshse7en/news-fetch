from newspaper import Article

from helpers import clean_text, extract_keywords, summarize_article, unicode


class ArticleHandler:
    """Handle interactions with the Article class."""

    def __init__(self, url: str):
        self.url = url
        self.__article = self.__initialize_article()

    def __initialize_article(self):
        """Initialize the Article instance."""
        return self.__safe_execute(lambda: Article(self.url))

    @staticmethod
    def __safe_execute(func):
        """Executes a function and returns None if it raises an exception."""
        try:
            return func()
        except Exception:
            # You might want to log the exception here
            return None

    def is_valid(self):
        """Check if the Article instance is valid."""
        return self.__article is not None

    def download_and_parse(self):
        """Download and parse the article."""
        if self.is_valid():
            self.__safe_execute(self.__article.download)
            self.__safe_execute(self.__article.parse)
            self.__safe_execute(self.__article.nlp)

    @property
    def authors(self):
        """Return authors from the Article instance."""
        return self.__article.authors if self.is_valid() else []

    @property
    def date_publish(self):
        """Return publication date from the Article instance."""
        return self.__article.meta_data.get("published_time") if self.is_valid() else None

    @property
    def keywords(self):
        """Return keywords from the Article instance."""
        if not self.is_valid():
            return []

        keywords = self.__process_keywords(self.__article.keywords)

        if not keywords:
            return extract_keywords(self.article)

        return keywords

    @staticmethod
    def __process_keywords(keywords, max_keywords=None):
        """Process keywords to remove duplicates and limit the number."""
        unique_keywords = list(set(keywords))
        return unique_keywords[:max_keywords] if max_keywords is not None else unique_keywords

    @property
    def summary(self):
        """Return summary from the Article instance."""
        summary = self.__article.summary if self.is_valid() else None

        if not summary:
            return unicode(summarize_article(self.article))

        return unicode(summary)

    @property
    def article(self):
        """Return cleaned article text from the Article instance."""
        if self.is_valid():
            return unicode(clean_text(self.__article.text))

    @property
    def publication(self):
        """Return publication name from the Article instance."""
        return self.__article.meta_data.get("og", {}).get("site_name") if self.is_valid() else None

    @property
    def category(self):
        """Return category from the Article instance."""
        if not self.is_valid():
            return None

        return (self.__article.meta_data.get("category") or
                self.__article.meta_data.get("section") or
                self.__article.meta_data.get("article", {}).get("section")) or None

    @property
    def headline(self):
        """Return title from the Article instance."""
        return unicode(self.__article.title) if self.is_valid() else None

    @property
    def meta_favicon(self):
        """Return meta favicon from the Article instance."""
        return self.__article.meta_favicon if self.is_valid() else None
