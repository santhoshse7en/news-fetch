import re
from collections import Counter
from typing import Callable, TypeVar

from unidecode import unidecode

T = TypeVar("T")


def unicode(text: str) -> str:
    return unidecode(text).strip()


def safe_execute(func: Callable[[], T]) -> T | None:
    """Run func and return None if it raises an exception."""
    try:
        return func()
    except Exception:
        return None


def clean_text(article: str) -> str:
    """Clean the article text by removing extra whitespace and newlines."""
    # Remove extra whitespace and newlines
    cleaned_article = re.sub(r'\s+', ' ', article).strip()
    return cleaned_article


_STOPWORDS = {'and', 'the', 'is', 'in', 'of', 'to', 'a', 'for', 'was', 'that', 'on', 'as', 'with', 'it', 'this',
              'are', 'by', 'an'}


def extract_keywords(article: str, max_keywords: int = 10) -> list[str]:
    """Extract the most frequent non-stopword keywords from the article."""
    words = re.findall(r'\b\w+\b', article.lower())
    word_counts = Counter(word for word in words if word not in _STOPWORDS)
    return [word for word, _ in word_counts.most_common(max_keywords)]


def summarize_article(article: str, max_sentences: int = 3) -> str:
    """Summarize the article by extracting the first few sentences."""
    sentences = re.split(r'(?<=[.!?]) +', article)
    summary = ' '.join(sentences[:max_sentences])  # Take the first few sentences
    return summary
