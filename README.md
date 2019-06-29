[![PyPI Version](https://img.shields.io/pypi/v/news_fetch.svg)](https://pypi.org/project/news_fetch)
[![Coverage Status](https://coveralls.io/repos/github/santhoshse7en/news_fetch/badge.svg?branch=master)](https://coveralls.io/github/santhoshse7en/news_fetch?branch=master)
[![License](https://img.shields.io/pypi/l/news_fetch.svg)](https://pypi.python.org/pypi/news_fetch/)
[![Documentation Status](https://readthedocs.org/projects/pip/badge/?version=latest&style=flat)](https://santhoshse7en.github.io/news_fetch_doc)

# news_fetch

news_fetch scrape all the news related attributes with helps [Google Search](https://www.google.com/) and [Newspaper3K](https://pypi.org/project/newspaper3k/) which reduce the NaN or '' or [] or None values while scraping.

| Source         | Link                                         |
| ---            |  ---                                         |
| PyPI:          | https://pypi.org/project/news_fetch/             |
| Repository:    | https://santhoshse7en.github.io/news_fetch/      |
| Documentation: | https://santhoshse7en.github.io/news_fetch_doc/  |

## Dependencies

- beautifulsoup4
- selenium
- chromedriver-binary
- fake_useragent
- pandas
- pattern



## Dependencies Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install following
```bash
pip install -r requirements.txt
```

## Usage

Download it by clicking the green download button here on [Github](https://github.com/santhoshse7en/news_fetch/archive/master.zip). To extract URLs from targeted website call google_crawler function, you only need to parse argument of keyword and newspaper website.

```python
>>> from news_fetch.news import google_search
>>> google = google_search('Alcoholics Anonymous', 'https://timesofindia.indiatimes.com/')
```

**Directory of google search results urls**

![google](https://user-images.githubusercontent.com/47944792/60381562-67363380-9a74-11e9-99ea-51c27bf08abc.PNG)

To scrape the all news details call news_crawler function

```python
>>> from news_fetch.news import newspaper
>>> news = newspaper('https://www.bbc.co.uk/news/world-48810070')
```

**Directory of news_crawler**

![news](https://user-images.githubusercontent.com/47944792/60381950-969b6f00-9a79-11e9-8167-c9cb45033c91.PNG)

```python
>>> news.headline

'g20 summit: trump and xi agree to restart us china trade talks'
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
