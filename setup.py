"""A setuptools based setup module.
See:
https://packaging.python.org/guides/distributing-packages-using-setuptools/
https://santhoshse7en.github.io/news-fetch/
https://santhoshse7en.github.io/news-fetch_doc/
"""
# -*- encoding: utf-8 -*-
from __future__ import absolute_import, print_function

# Always prefer setuptools over distutils
import setuptools

keywords = ['Newspaper', "news-fetch", "without-api", "google_scraper", 'news_scraper', 'bs4', 'lxml', 'news-crawler',
            'news-extractor', 'crawler', 'extractor', 'news', 'news-websites', 'elasticsearch', 'json', 'python', 'nlp', 'data-gathering',
            'news-archive', 'news-articles', 'commoncrawl', 'extract-articles', 'extract-information', 'news-scraper', 'spacy']

setuptools.setup(
    name="news-fetch",
    version="0.2.8",
    author="M Santhosh Kumar",
    author_email="santhoshse7en@gmail.com",
    description="news-fetch is an open source easy-to-use news extractor and basic nlp (cleaning_text, keywords, summary) comes handy that just works",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://santhoshse7en.github.io/news-fetch/",
    keywords=keywords,
    install_requires=['beautifulsoup4', 'pandas', 'selenium', 'news-please', 'newspaper3k',
                      'fake_useragent', 'chromedriver-binary', 'unidecode', 'cchardet'],
    packages=setuptools.find_packages(),
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: End Users/Desktop',
                 'Intended Audience :: Developers',
                 'Intended Audience :: System Administrators',
                 'License :: OSI Approved :: MIT License',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Communications :: Email',
                 'Topic :: Office/Business',
                 'Topic :: Software Development :: Bug Tracking',
                 ],
)
