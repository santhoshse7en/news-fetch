from newsfetch.helpers import (author, catch, category, date, news_article,
                               publisher, unicode)
from newsfetch.utils import Article, BeautifulSoup, NewsPlease, get, unquote


class newspaper:

    def __init__(self, uri: str) -> bool:

        self.uri = uri

        """
        :return: Initializing the values with 'None', In case if the below values not able to extracted from the target uri
        """

        # NewsPlease Scraper
        newsplease = catch(
            'None', lambda: NewsPlease.from_url(self.uri, timeout=6))

        # Newspaper3K Scraper
        article = catch('None', lambda: Article(self.uri, timeout=6))
        catch('None', lambda: article.download())
        catch('None', lambda: article.parse())
        catch('None', lambda: article.nlp())

        soup = catch('None', lambda: BeautifulSoup(get(self.uri).text, 'lxml'))

        if all([newsplease, article, soup]) == None:
            raise ValueError(
                "Sorry, the page you are looking for doesn't exist'")

        """
        :returns: The News Article
        """
        self.article = catch('None', lambda: news_article(article.text) if article.text !=
                             None else news_article(newsplease.maintext) if newsplease.maintext != None else 'None')

        """
        :returns: The News Authors
        """
        self.authors = catch('list', lambda: newsplease.authors if len(newsplease.authors) != 0 else article.authors if len(
            article.authors) != 0 else unicode([author(soup)]) if author(soup) != None else ['None'])

        """
        :returns: The News Published, Modify, Download Date
        """
        self.date_publish = catch('None', lambda: str(newsplease.date_publish) if str(newsplease.date_publish) != 'None' else article.meta_data[
                                  'article']['published_time'] if article.meta_data['article']['published_time'] != None else date(soup) if date(soup) != None else 'None')

        self.date_modify = catch('None', lambda: str(newsplease.date_modify))

        self.date_download = catch(
            'None', lambda: str(newsplease.date_download))

        """
        :returns: The News Image URL
        """
        self.image_url = catch('None', lambda: newsplease.image_url)

        """
        :returns: The News filename
        """
        self.filename = catch('None', lambda: unquote(newsplease.filename))

        """
        :returns: The News title page
        """
        self.title_page = catch('None', lambda: newsplease.title_page)

        """
        :returns: The News title rss
        """
        self.title_rss = catch('None', lambda: newsplease.title_rss)

        """
        :returns: The News Language
        """
        self.language = catch('None', lambda: newsplease.language)

        """
        :returns: The News Publisher
        """
        self.publication = catch('None', lambda: article.meta_data['og']['site_name'] if article.meta_data['og']['site_name'] != None else publisher(
            soup) if publisher(soup) != None else self.uri.split('/')[2] if self.uri.split('/')[2] != None else 'None')

        """
        :returns: The News Category
        """
        meta_check = any(word in 'section' or 'category' for word in list(
            article.meta_data.keys()))
        self.category = catch('None', lambda: article.meta_data['category'] if meta_check == True and article.meta_data['category'] != {} else article.meta_data['section'] if meta_check ==
                              True and article.meta_data['section'] != {} else article.meta_data['article']['section'] if meta_check == True and article.meta_data['article']['section'] != {} else category(soup) if category(soup) != None else 'None')

        """
        :returns: headlines
        """
        self.headline = catch('None', lambda: unicode(article.title) if article.title != None else unicode(
            newsplease.title) if newsplease.title != None else 'None')

        """
        :returns: keywords
        """
        self.keywords = catch('list', lambda: article.keywords)

        """
        :returns: summary
        """
        self.summary = catch('None', lambda: news_article(article.summary))

        """
        :returns: source domain
        """
        self.source_domain = catch('None', lambda: newsplease.source_domain)

        """
        :returns: description
        """
        self.description = catch('None', lambda: news_article(article.meta_description) if article.meta_description != '' else news_article(
            article.meta_data['description']) if article.meta_data['description'] != {} else news_article(newsplease.description) if newsplease.description != None else None)

        """
        :returns: serializable_dict
        """
        self.get_dict = catch('dict', lambda: {'headline': self.headline,
                                               'author': self.authors,
                                               'date_publish': self.date_publish,
                                               'date_modify': self.date_modify,
                                               'date_download': self.date_download,
                                               'language': self.language,
                                               'image_url': self.image_url,
                                               'filename': self.filename,
                                               'description': self.description,
                                               'publication': self.publication,
                                               'category': self.category,
                                               'source_domain': self.source_domain,
                                               'article': self.article,
                                               'summary': self.summary,
                                               'keyword': self.keywords,
                                               'title_page': self.title_page,
                                               'title_rss': self.title_rss,
                                               'url': self.uri})
