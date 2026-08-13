"""Detection helpers."""

from newsfetch.detect.language import detect_language
from newsfetch.detect.page_type import PageTypeResult, detect_page_type

__all__ = ["PageTypeResult", "detect_language", "detect_page_type"]
