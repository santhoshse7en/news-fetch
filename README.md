[![PyPI version](https://img.shields.io/pypi/v/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch)
[![License](https://img.shields.io/pypi/l/news-fetch.svg?style=flat-square)](https://pypi.python.org/pypi/news-fetch/)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=latest\&style=flat-square)](https://santhoshse7en.github.io/news-fetch_doc)
[![Downloads](https://pepy.tech/badge/news-fetch/month)](https://pepy.tech/project/news-fetch)

# 📰 news-fetch

**news-fetch** extracts structured data from a news article URL with one call: `Newspaper(url=...).get_dict` 🌐. Under the hood it's built on [newspaper4k](https://github.com/AndyTheFactory/newspaper4k), but it isn't just a wrapper around it — it exists to fix the gaps single-engine extraction leaves:

* **JSON-LD backfill.** Many modern news sites (e.g. BBC) don't expose Open Graph tags that newspaper4k relies on for `publication`/`category`, but do embed a `schema.org/NewsArticle` JSON-LD block. news-fetch parses that block directly and fills in `publication`, `category`, and `date_modify` whenever the primary engine comes up empty — no extra dependency required, since it reuses the `beautifulsoup4`/`requests` already in the base install.
* **No NLTK download required.** newspaper4k's built-in summary/keyword extraction (`.nlp()`) needs an NLTK corpus download, which routinely fails behind corporate proxies or strict SSL setups. news-fetch falls back to a dependency-free, pure-stdlib summarizer/keyword extractor when that's unavailable, so `summary`/`keywords` are never empty.
* **Every field, one flat dict, first non-empty value wins.** Instead of learning three different libraries' inconsistent APIs, you get one object where each field is resolved by trying every available engine in priority order and returning the first real value.
* **Site-wide article discovery, no browser automation.** `NewsSiteURLExtractor` finds a news site's recent article URLs (with title/date, when available) via its `robots.txt` sitemap directives, Google News sitemaps, and RSS/Atom feeds — the same techniques real news aggregators use, and safer/more reliable than scraping a search engine.
* **Reading time and word count**, computed for free from the extracted article text.
* **Concurrent batch scraping** via `Newspaper.from_urls([...])` — one bad URL doesn't take down the whole batch; it just comes back as `None`.
* **A minimal, honest dependency footprint.** The whole install is ~50MB: newspaper4k, beautifulsoup4, requests, Unidecode — no Scrapy, no boto3, no Selenium.

---

## 🔗 Project Links

| Source         | Link                                                                                                                       |
| -------------- | -------------------------------------------------------------------------------------------------------------------------- |
| PyPI:          | [https://pypi.org/project/news-fetch/](https://pypi.org/project/news-fetch/)                                               |
| Repository:    | [https://santhoshse7en.github.io/news-fetch/](https://santhoshse7en.github.io/news-fetch/)                                 |
| Documentation: | [https://santhoshse7en.github.io/news-fetch\_doc/](https://santhoshse7en.github.io/news-fetch_doc/) (**Not Yet Created!**) |

## 📦 Dependencies

news-fetch is intentionally lightweight (~50MB): [newspaper4k](https://pypi.org/project/newspaper4k/), [beautifulsoup4](https://pypi.org/project/beautifulsoup4/), [requests](https://pypi.org/project/requests/), and [Unidecode](https://pypi.org/project/Unidecode/). No optional extras.

## 📝 Extracted Information

news-fetch extracts the following attributes from news articles. You can also check out an [example JSON file](https://github.com/santhoshse7en/news-fetch/blob/master/newsfetch/example/sample.json).

* 📰 Headline
* ✍️ Author(s)
* 📅 Publication date
* 🗞️ Publication
* 📂 Category
* 🌍 Source domain
* 📑 Article content
* 📝 Summary
* 🔑 Keywords
* 🌐 URL
* 🌐 Language
* ⏱️ Word count & estimated reading time

## 🔧 Installation

Install from PyPI with [pip](https://pip.pypa.io/en/stable/):

```bash
pip install news-fetch
```

Or install from source:

```bash
git clone https://github.com/santhoshse7en/news-fetch.git
cd news-fetch
pip install .
```

## 🚀 Usage

To scrape all the news details, use the `newspaper` function:

```python
from newsfetch.news import Newspaper

news = Newspaper(url='https://www.thehindu.com/news/cities/Madurai/aa-plays-a-pivotal-role-in-helping-people-escape-from-the-grip-of-alcoholism/article67716206.ece')
print(news.headline)
# Output: 'AA plays a pivotal role in helping people escape from the grip of alcoholism'
print(news.word_count, news.reading_time_minutes)
# Output: 812 4
```

To discover recent article URLs from a news site (via its sitemaps/RSS feeds — no browser required):

```python
from newsfetch.discovery import NewsSiteURLExtractor

site = NewsSiteURLExtractor(news_domain='https://www.bbc.com', limit=10)
for article in site.articles:
    print(article)
# Output: {'url': 'https://www.bbc.com/news/articles/...', 'title': '...', 'date': '2026-07-10T16:56:53Z'}
```

To scrape many URLs at once, with per-URL failures isolated:

```python
from newsfetch.news import Newspaper

results = Newspaper.from_urls(site.urls, max_workers=5)
for result in results:
    if result is not None:
        print(result.headline)
```

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

Make sure to update tests as appropriate.

## 📄 License

This project is licensed under the [MIT License](https://choosealicense.com/licenses/mit/).
