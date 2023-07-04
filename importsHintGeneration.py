# -*- coding: utf-8 -*-
"""
File that contains all requirements (imports) that are needed for the automaticHintGeneration app
"""

import subprocess
import sys
from subprocess import STDOUT, check_call
import os

#function that allows us to install pip packages via a python file 
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
#function that allows us to install apt-get packages via a python file 
def apt_install(package):
    check_call(['apt-get', 'install', '-y', package], stdout=open(os.devnull,'wb'), stderr=STDOUT)

directory = "tmp" # Directory
parent_dir = "/content/automaticHintGeneration" # Parent Directory path
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
import wikipediaapi
import wikidata
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
import collections.abc as collections
from collections.abc import Mapping
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import AutoTokenizer, AutoModel

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
