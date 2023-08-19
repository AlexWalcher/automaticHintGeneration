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

# apt_install('apt-transport-https')
# install('selenium')
# apt_install('firefox')
# install('webdrivermanager')
# # apt_install('firefox-geckodriver')
# # install('geckodriver-autoinstaller')
# install('sparqlwrapper')
# install('pageviewapi')
# install('sentence-transformers')
# install('wikipedia')
# install('requests')
# install('lxml')
# install('pageviewapi')
# install('Wikipedia-API')
# install('wikidata')

#new imports
import random
import copy
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
from selenium.webdriver import Firefox

# python -m spacy download en
import spacy
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import spacy.cli
# Download the larger English model (en_core_web_md)
spacy.cli.download("en_core_web_md")
# Alternatively, download the smaller English model (en_core_web_sm)
spacy.cli.download("en_core_web_sm")


from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from collections import OrderedDict
import collections.abc as collections
from collections.abc import Mapping
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import torch
from transformers import AutoTokenizer, AutoModel
from webdrivermanager import GeckoDriverManager

from pathlib import Path
import subprocess
subprocess.call(["npm","init"])
subprocess.call(["npm","install"])

#Streamlit imports:
# install('streamlit')
# install('streamlit-option-menu')
import streamlit as st
from streamlit_option_menu import option_menu

print("\n")
print("finished imports")
print("\n")


gl_person_questions_dict_from_txt = {}
# gl_location_questions_dict = {}
# gl_year_questions_dict = {}

class Test:
  def __init__(self):
    self.gl_person_questions_dict = {}
    self.gl_location_questions_dict = {}
    self.gl_year_questions_dict = {}

  def get_person_questions_dict(self):
    return self.gl_person_questions_dict

  def set_person_questions_dict(self, value):
    self.gl_person_questions_dict = value

  def get_location_questions_dict(self):
    return self.gl_location_questions_dict

  def set_location_questions_dict(self, value):
    self.gl_location_questions_dict = value

  def get_year_questions_dict(self):
    return self.gl_year_questions_dict

  def set_year_questions_dict(self, value):
    self.gl_year_questions_dict = value
