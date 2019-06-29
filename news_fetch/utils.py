from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from selenium import webdriver
from pattern.en import suggest
from newspaper import Article
from bs4 import BeautifulSoup
import chromedriver_binary
from requests import get
import time
import nltk
import json
import sys
import re
