logr-An Amazing Project
[![PyPI version](https://img.shields.io/pypi/v/news-fetch.svg?style=flat-square)](https://pypi.org/project/news-fetch)
[![License](https://img.shields.io/pypi/l/news-fetch.svg?style=flat-square)](https://pypi.python.org/pypi/news-fetch/)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=latest&style=flat-square)](https://santhoshse7en.github.io/news-fetch_doc)

# news-fetch

<img align="right" height="128px" width="128px" src="https://raw.githubusercontent.com/fhamborg/news-please/master/misc/logo/logo-256.png" />

news-fetch is an open source, easy-to-use news crawler that extracts structured information from almost any news website. It can follow recursively internal hyperlinks and read RSS feeds to fetch both most recent and also old, archived articles. You only need to provide the root URL of the news website to crawl it completely. news-fetch combines the power of multiple state-of-the-art libraries and tools, such as [news-please](https://github.com/fhamborg/news-please) - [Felix Hamborg](https://www.linkedin.com/in/felixhamborg/) and [Newspaper3K](https://github.com/codelucas/newspaper/) - [Lucas (欧阳象) Ou-Yang](https://www.linkedin.com/in/lucasouyang/). This package consist of both features provided my Felix's work and Lucas' work.

I built this to reduce most of NaN or '' or [] or 'None' values while scraping for some newswesites. Platform-independent and written in Python 3. This package can be very easily used by programmers and developers to provide access to the news data to their programs.


| Source         | Link                                             |
| ---            |  ---                                             |
| PyPI:          | https://pypi.org/project/news-fetch/             |
| Repository:    | https://santhoshse7en.github.io/news-fetch/      |
| Documentation: | https://santhoshse7en.github.io/news-fetch_doc/  |

## Dependencies

- news-please
- newspaper3k
- beautifulsoup4
- fake_useragent
- selenium
- chromedriver-binary
- fake_useragent
- pandas

## Extracted information
news-please extracts the following attributes from news articles. Also, have a look at an [examplary json file](https://github.com/santhoshse7en/news-fetch/blob/master/newsfetch/example/sample.json) extracted by news-please.
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

Download it by clicking the green download button here on [Github](https://github.com/santhoshse7en/news-fetch/archive/master.zip). To extract URLs from targeted website call google_search function, you only need to parse argument of keyword and newspaper link.

```python
>>> from newsfetch.google import google_search
>>> google = google_search('Alcoholics Anonymous', 'https://timesofindia.indiatimes.com/')
```

**Directory of Google search results URLs**

![google](https://user-images.githubusercontent.com/47944792/60381562-67363380-9a74-11e9-99ea-51c27bf08abc.PNG)

To scrape the all news details call newspaper function

```python
>>> from newsfetch.news import newspaper
>>> news = newspaper('https://www.bbc.co.uk/news/world-48810070')
```

**Directory of News**

![newsdir](https://user-images.githubusercontent.com/47944792/60564817-c058dc80-9d7e-11e9-9b3e-d0b5a903d972.PNG)

```python
>>> news.headline

'g20 summit: trump and xi agree to restart us china trade talks'
```

## Contribution

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
