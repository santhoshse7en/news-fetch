[![PyPI version](https://img.shields.io/pypi/v/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch)
[![License](https://img.shields.io/pypi/l/news-fetch.svg?style=flat-square)](https://pypi.python.org/pypi/news-fetch/)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=latest&style=flat-square)](https://santhoshse7en.github.io/news-fetch_doc)

# news-fetch

<img align="right" height="128px" width="128px" src="https://raw.githubusercontent.com/fhamborg/news-please/master/misc/logo/logo-256.png" />

news-fetch is an open-source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website to crawl it completely. News-fetch combines the power of multiple state-of-the-art libraries and tools, such as [news-please](https://github.com/fhamborg/news-please) - [Felix Hamborg](https://www.linkedin.com/in/felixhamborg/) and [Newspaper3K](https://github.com/codelucas/newspaper/) - [Lucas (欧阳象) Ou-Yang](https://www.linkedin.com/in/lucasouyang/). This package consists of both features provided by Felix's work and Lucas' work.

I built this to reduce most of NaN or '' or [] or 'None' values while scraping for some news websites. Platform-independent and written in Python 3. Programmers and developers can very easily use this package to access the news data to their programs.


| Source         | Link                                                                   |
| ---            |  ---                                                                   |
| PyPI:          | https://pypi.org/project/news-fetch/                                   |
| Repository:    | https://santhoshse7en.github.io/news-fetch/                            |
| Documentation: | https://santhoshse7en.github.io/news-fetch_doc/ (**Not Yet Created!**) |

## Dependencies

- [news-please](https://pypi.org/project/news-please/)
- [newspaper3k](https://pypi.org/project/newspaper3k/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)
- [fake_useragent](https://pypi.org/project/fake-useragent/)
- [selenium](https://pypi.org/project/selenium/)
- [chromedriver-binary](https://pypi.org/project/chromedriver-binary/)
- [pandas](https://pypi.org/project/pandas/)

## Extracted information
news-fetch extracts the following attributes from news articles. Also, have a look at an [examplary JSON file](https://github.com/santhoshse7en/news-fetch/blob/master/newsfetch/example/sample.json) extracted by news-please.
* headline
* name(s) of author(s)
* publication date
* publication
* category
* source_domain
* article
* summary
* keyword
* url
* language

## Dependencies Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install following
```bash
pip install -r requirements.txt
```

## Usage

Download it by clicking the green download button here on [Github](https://github.com/santhoshse7en/news-fetch/archive/master.zip). To extract URLs from a targeted website, call the google_search function. You only need to parse the keyword and newspaper link argument.

```python
>>> from newsfetch.google import google_search
>>> google = google_search('Alcoholics Anonymous', 'https://timesofindia.indiatimes.com/')
```

Use the `URLs` attribute to get the links of all the news articles scraped. 

```python
>>> google.urls
```

**Directory of google search results urls**

![google](https://user-images.githubusercontent.com/47944792/88402193-68a56d00-cde8-11ea-8f26-9f7bf19359b2.PNG)


To scrape all the news details, call the newspaper function

```python
>>> from newsfetch.news import newspaper
>>> news = newspaper('https://www.bbc.co.uk/news/world-48810070')
```

**Directory of news**

![newsdir](https://user-images.githubusercontent.com/47944792/60564817-c058dc80-9d7e-11e9-9b3e-d0b5a903d972.PNG)

```python
>>> news.headline

'g20 summit: trump and xi agree to restart us china trade talks'
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
