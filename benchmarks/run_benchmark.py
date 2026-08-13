"""Simple fixture benchmark for news-fetch."""

from __future__ import annotations

import json
import time
from pathlib import Path

from newsfetch import extract

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "html"
EXPECTATIONS = Path(__file__).parent / "expectations.json"


def main() -> None:
    expectations = json.loads(EXPECTATIONS.read_text(encoding="utf-8"))
    passed = 0
    total = 0
    t0 = time.perf_counter()
    for name, expected in expectations.items():
        total += 1
        html = (FIXTURES / name).read_text(encoding="utf-8")
        article = extract(html, url=expected["url"])
        ok = True
        if "title_contains" in expected and expected["title_contains"].lower() not in (article.title or "").lower():
            ok = False
            print(f"FAIL {name}: title={article.title!r}")
        if "text_contains" in expected and expected["text_contains"].lower() not in (article.text or "").lower():
            ok = False
            print(f"FAIL {name}: text missing {expected['text_contains']!r}")
        if ok:
            passed += 1
            print(f"OK   {name} ({article.content_source})")
    elapsed = time.perf_counter() - t0
    print(f"\n{passed}/{total} passed in {elapsed:.3f}s")


if __name__ == "__main__":
    main()
