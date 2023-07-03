# -*- coding: utf-8 -*-

import subprocess
import sys
from subprocess import STDOUT, check_call
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
def apt_install(package):
    check_call(['apt-get', 'install', '-y', package], stdout=open(os.devnull,'wb'), stderr=STDOUT)

directory = "tmp" # Directory
parent_dir = "/automaticHintGeneration" # Parent Directory path
path = os.path.join(parent_dir, directory) # Path

install('selenium')
apt_install('firefox')
apt_install('firefox-geckodriver')
install('sparqlwrapper')
install('pageviewapi')
install('sentence-transformers')
install('wikipedia')
install('requests')
install('lxml')
install('pageviewapi')
install('Wikipedia-API')
install('wikidata')

#new imports
import random
import spacy
import time
import requests
import re
import difflib
import pprint
import itertools
import wikipedia
import lxml.etree as ET
import xml.etree.ElementTree as ET
import urllib.request
import pandas as pd
pd.set_option('display.max_colwidth',1000)
from SPARQLWrapper import SPARQLWrapper, JSON
sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
import bs4
from bs4 import BeautifulSoup, NavigableString, Tag
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from collections import OrderedDict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import collections.abc as collections
from collections.abc import Mapping
import wikipediaapi
import wikidata
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
from collections import OrderedDict

from pathlib import Path
import subprocess
subprocess.call(["npm","init"])
subprocess.call(["npm","install"])

#Streamlit imports:
install('streamlit')
install('streamlit-option-menu')
import streamlit as st
from streamlit_option_menu import option_menu


print("\n")
print("finished imports")
print("\n")
