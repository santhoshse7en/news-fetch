import json
from bs4 import BeautifulSoup
from requests import get


class SoupHandler:
    """Handle interactions with BeautifulSoup for HTML parsing."""

    def __init__(self, url: str):
        """Initialize the SoupHandler with a given URL."""
        self.url = url
        self.__soup = self.__safe_execute(lambda: BeautifulSoup(get(self.url).text, "lxml"))

    @staticmethod
    def __safe_execute(func):
        """Executes a function and returns None if it raises an exception."""
        try:
            return func()
        except Exception:
            return None

    def is_valid(self) -> bool:
        """Check if the BeautifulSoup instance is valid."""
        return self.__soup is not None

    def extract_metadata(self, metadata_type: str):
        """Extract specified metadata from the HTML soup ("author", "date", "category", or "publisher")."""
        if metadata_type not in ["author", "date", "category", "publisher"]:
            raise ValueError("metadata_type must be 'author', 'date', 'category', or 'publisher'.")

        if not self.is_valid():
            return "N/A"  # Return if the soup is not valid

        meta_elements = self.__soup.select("script[type='application/ld+json']")
        for i in range(min(3, len(meta_elements))):  # Limit to 3 attempts
            try:
                meta = json.loads(meta_elements[i].text)
                result = self.__extract_meta(meta, metadata_type)
                if result != "N/A":
                    return result  # Return if found
            except (json.JSONDecodeError, IndexError):
                continue  # Skip to the next element if there"s an error

        return "N/A"  # Default return value if nothing is found

    @property
    def authors(self):
        """Extract author information from the HTML soup using JSON-LD data."""
        return self.extract_metadata("author")

    @property
    def date_publish(self):
        """Extract the publication date from the HTML soup using JSON-LD data."""
        return self.extract_metadata("date")

    @property
    def category(self):
        """Extract the category from the HTML soup using JSON-LD data."""
        return self.extract_metadata("category")

    @property
    def publisher(self):
        """Extract the publisher from the HTML soup using JSON-LD data."""
        return self.extract_metadata("publisher")

    def __extract_meta(self, meta, metadata_type):
        """Extract specific metadata from the JSON-LD."""
        if metadata_type == "author":
            return self.__extract_authors(meta)
        elif metadata_type == "date":
            return self.__extract_date(meta)
        elif metadata_type == "category":
            return self.__extract_category(meta)
        elif metadata_type == "publisher":
            return self.__extract_publisher(meta)
        return "N/A"  # Default if type doesn"t match

    @staticmethod
    def __extract_authors(meta):
        """Extract author information from the metadata."""
        authors = []
        if "author" in meta:
            if isinstance(meta["author"], list):
                authors = [a.get("name") for a in meta["author"] if a.get("name")]
            elif isinstance(meta["author"], dict):
                authors = [meta["author"].get("name", "N/A")]
            elif isinstance(meta["author"], str):
                authors = [meta["author"]]

        return authors if authors else ["N/A"]  # Return a list, default to "N/A" if empty

    @staticmethod
    def __extract_date(meta):
        """Extract the publication date from the metadata."""
        if "datePublished" in meta:
            if isinstance(meta, dict):
                return meta["datePublished"]
            elif isinstance(meta, list) and meta:
                return meta[0].get("datePublished", "N/A")

        return "N/A"  # Return "N/A" if no date found

    @staticmethod
    def __extract_category(meta):
        """Extract the category from the metadata."""
        key = "@type"
        if key in meta:
            if isinstance(meta, dict):
                return meta[key]
            elif isinstance(meta, list) and meta:
                return meta[0].get(key, "N/A")

        return "N/A"  # Return "N/A" if no category found

    @staticmethod
    def __extract_publisher(meta):
        """Extract the publisher from the metadata."""
        if "publisher" in meta:
            if isinstance(meta["publisher"], dict):
                return meta["publisher"].get("name", "N/A")
            elif isinstance(meta["publisher"], str):
                return meta["publisher"]

        return "N/A"  # Return "N/A" if no publisher found
