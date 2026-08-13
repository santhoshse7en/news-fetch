"""Light NLP helpers (stdlib only)."""

from __future__ import annotations

import re
from collections import Counter

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "this", "they", "their", "have", "had", "but", "not", "or",
    "which", "who", "what", "when", "where", "how", "all", "can", "her", "his",
    "she", "him", "you", "your", "we", "our", "said", "also", "than", "then",
}


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    counts = Counter(w for w in words if w not in _STOPWORDS)
    return [w for w, _ in counts.most_common(max_keywords)]


def summarize(text: str, max_sentences: int = 3) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    return " ".join(sentences[:max_sentences])
