import json
from bs4 import BeautifulSoup
from requests import get

from newsfetch.helpers import safe_execute


class SoupHandler:
    """Handle interactions with BeautifulSoup for HTML parsing."""

    def __init__(self, url: str):
        """Initialize the SoupHandler with a given URL."""
        self.url = url
        self.__soup = safe_execute(lambda: BeautifulSoup(get(self.url).text, "lxml"))

    def is_valid(self) -> bool:
        """Check if the BeautifulSoup instance is valid."""
        return self.__soup is not None

    def extract_metadata(self, metadata_type: str) -> str | list[str] | None:
        """Extract specified metadata from the JSON-LD in the HTML soup.

        metadata_type: one of "author", "date", "date_modify", "category", "publisher".
        Returns None (or an empty list for "author") when nothing is found.
        """
        valid_types = ["author", "date", "date_modify", "category", "publisher"]
        if metadata_type not in valid_types:
            raise ValueError(f"metadata_type must be one of {valid_types}.")

        if not self.is_valid():
            return [] if metadata_type == "author" else None

        meta_elements = self.__soup.select("script[type='application/ld+json']")
        for i in range(min(3, len(meta_elements))):  # Limit to 3 attempts
            try:
                meta = json.loads(meta_elements[i].text)
                meta = self.__normalize(meta)
                result = self.__extract_meta(meta, metadata_type)
                if result:
                    return result  # Return if found
            except (json.JSONDecodeError, IndexError):
                continue  # Skip to the next element if there's an error

        return [] if metadata_type == "author" else None

    @staticmethod
    def __normalize(meta) -> dict:
        """Reduce a JSON-LD payload to the single dict describing the article.

        Handles the plain {"@type": "NewsArticle", ...} shape as well as a
        top-level {"@context": ..., "@graph": [...]} wrapper (used by e.g. BBC)
        and a bare top-level array of objects, preferring whichever entry's
        @type mentions "Article".
        """
        if isinstance(meta, dict) and isinstance(meta.get("@graph"), list):
            meta = meta["@graph"]

        if isinstance(meta, list):
            for item in meta:
                if isinstance(item, dict) and "Article" in str(item.get("@type", "")):
                    return item
            return next((item for item in meta if isinstance(item, dict)), {})

        return meta if isinstance(meta, dict) else {}

    @property
    def authors(self) -> list[str]:
        """Extract author information from the HTML soup using JSON-LD data."""
        return self.extract_metadata("author")

    @property
    def date_publish(self) -> str | None:
        """Extract the publication date from the HTML soup using JSON-LD data."""
        return self.extract_metadata("date")

    @property
    def date_modify(self) -> str | None:
        """Extract the last-modified date from the HTML soup using JSON-LD data."""
        return self.extract_metadata("date_modify")

    @property
    def category(self) -> str | None:
        """Extract the category from the HTML soup using JSON-LD data."""
        return self.extract_metadata("category")

    @property
    def publisher(self) -> str | None:
        """Extract the publisher from the HTML soup using JSON-LD data."""
        return self.extract_metadata("publisher")

    def __extract_meta(self, meta: dict, metadata_type: str) -> str | list[str] | None:
        """Extract specific metadata from the JSON-LD."""
        match metadata_type:
            case "author":
                return self.__extract_authors(meta)
            case "date":
                return self.__extract_date_field(meta, "datePublished")
            case "date_modify":
                return self.__extract_date_field(meta, "dateModified")
            case "category":
                return self.__extract_category(meta)
            case "publisher":
                return self.__extract_publisher(meta)
            case _:
                return None

    @staticmethod
    def __extract_authors(meta: dict) -> list[str]:
        """Extract author information from the metadata."""
        author = meta.get("author")
        if isinstance(author, list):
            names = []
            for a in author:
                if isinstance(a, dict) and a.get("name"):
                    names.append(a["name"])
                elif isinstance(a, str):
                    names.append(a)
            return names
        elif isinstance(author, dict):
            name = author.get("name")
            return [name] if name else []
        elif isinstance(author, str):
            return [author]

        return []

    @staticmethod
    def __extract_date_field(meta: dict, key: str) -> str | None:
        """Extract a date field (e.g. datePublished/dateModified) from the metadata."""
        return meta.get(key) or None

    @staticmethod
    def __extract_category(meta: dict) -> str | None:
        """Extract the category from the metadata."""
        return meta.get("@type") or None

    @staticmethod
    def __extract_publisher(meta: dict) -> str | None:
        """Extract the publisher from the metadata."""
        publisher = meta.get("publisher")
        if isinstance(publisher, dict):
            return publisher.get("name") or None
        elif isinstance(publisher, str):
            return publisher

        return None
