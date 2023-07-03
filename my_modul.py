# # -*- coding: utf-8 -*-

# import subprocess
# import sys
# from subprocess import STDOUT, check_call
# import os

# def install(package):
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])
# def apt_install(package):
#     check_call(['apt-get', 'install', '-y', package], stdout=open(os.devnull,'wb'), stderr=STDOUT)

# directory = "tmp" # Directory
# parent_dir = "/automaticHintGeneration" # Parent Directory path
# path = os.path.join(parent_dir, directory) # Path

# install('selenium')
# apt_install('firefox')
# apt_install('firefox-geckodriver')
# install('sparqlwrapper')
# install('pageviewapi')
# install('sentence-transformers')
# install('wikipedia')
# install('requests')
# install('lxml')
# install('pageviewapi')
# install('Wikipedia-API')
# install('wikidata')

# #new imports
# import random
# import spacy
# import time
# import requests
# import re
# import difflib
# import pprint
# import itertools
# import wikipedia
# import lxml.etree as ET
# import xml.etree.ElementTree as ET
# import urllib.request
# import pandas as pd
# pd.set_option('display.max_colwidth',1000)
# from SPARQLWrapper import SPARQLWrapper, JSON
# sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
# import bs4
# from bs4 import BeautifulSoup, NavigableString, Tag
# from sentence_transformers import SentenceTransformer
# from sklearn.metrics.pairwise import cosine_similarity
# from selenium import webdriver
# from bs4 import BeautifulSoup
# from urllib.parse import urlparse, parse_qs
# from collections import OrderedDict
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity
# import collections.abc as collections
# from collections.abc import Mapping
# import wikipediaapi
# import wikidata
# import pandas as pd
# import torch
# from transformers import AutoTokenizer, AutoModel
# from collections import OrderedDict

# from pathlib import Path
# import subprocess
# subprocess.call(["npm","init"])
# subprocess.call(["npm","install"])

# #Streamlit imports:
# install('streamlit')
# install('streamlit-option-menu')
# import streamlit as st
# from streamlit_option_menu import option_menu

# print("\n")
# print("finished imports")
# print("\n")

imports_path = "/automaticHintGeneration/importsHintGeneration"
import sys
sys.path.insert(0, imports_path)

from importsHintGeneration import *

# def load_file_path(file_path):
#   #file_path = "./automaticHintGeneration/testSet.xlsx"
#   df = pd.ExcelFile(file_path).parse("Sheet1")
#   dataPerson = []
#   dataYear = []
#   dataLocation = []
#   df_list = {}
#   for index, row in df.iterrows():
#     if(row["Category"] == "Person"):
#       dataPerson.append([row["Question"], row["Answer"]])
#     elif(row["Category"] == "Year"):
#       dataYear.append([row["Question"], row["Answer"]])
#     elif(row["Category"] == "Location"):
#       dataLocation.append([row["Question"], row["Answer"]])
#   person_df = pd.DataFrame(dataPerson, columns=["Question", "Answer"])
#   year_df = pd.DataFrame(dataYear, columns=["Question", "Answer"])
#   location_df = pd.DataFrame(dataLocation, columns=["Question", "Answer"])
#   df_list["person"] = person_df
#   df_list["year"] = year_df
#   df_list["location"] =location_df
#   pprint.pprint(df_list, indent=1)
#   return df_list

#file_path = "./tmp/testSet_WebApp.xlsx"
# file_path = "./automaticHintGeneration/testSet.xlsx"
file_path = "testSet.xlsx"
df_list = load_file_path(file_path)
person_df = df_list["person"]
year_df = df_list["year"]
location_df = df_list["location"]

from yearsFunctionsHintGeneration import *

from peopleFunctionsHintGeneration import *

from locationFunctionsHintGeneration import *

"""# **Generate hints - (putting everything together)**"""
#Function that puts everything together
# Call hint-generation-functions for years, people and locations
# Save the results in a txt file
def generate_hints_from_xlsx(file_path):
  df_list = load_file_path(file_path)
  year_df = df_list["year"]
  person_df = df_list["person"]
  location_df = df_list["location"]
  year_questions_dict = dict(zip(year_df['Answer'], year_df['Question']))
  person_questions_dict = dict(zip(person_df['Answer'], person_df['Question']))
  location_questions_dict = dict(zip(location_df['Answer'], location_df['Question']))
  generated_hint_sentences = {}
  combined_hint_sentences = {}
  #generates the hints for the YEARS question
  years_hints = generate_hints_years(year_questions_dict)
  generated_hint_sentences['years'] = years_hints
  #generates the hints for the PEOPLE question
  people_hints_unexpected_categories = get_person_hints_unexpected_categories(person_questions_dict)
  people_hints_unexpected_predicates = get_person_hints_unexpected_predicates(person_questions_dict)
  people_hints = {}
  people_hints['categories'] = people_hints_unexpected_categories
  people_hints['predicates'] = people_hints_unexpected_predicates
  generated_hint_sentences['people'] = people_hints
  #generates the hints for the LOCATION question
  location_hints_unexpected_categories = get_location_hints_unexpected_categories(location_questions_dict)
  location_hints_fixed_properties = get_location_hints_fixed_properties(location_questions_dict)
  location_hints = {}
  location_hints['categories'] = location_hints_unexpected_categories
  location_hints['properties'] = location_hints_fixed_properties
  generated_hint_sentences['locations'] = location_hints
  return generated_hint_sentences

def save_file():
  # Read the Excel file into a DataFrame
  df = pd.read_excel("./tmp/testSet_WebApp.xlsx")
  # Drop the first column by positional index
  df = df.iloc[:, 1:]
  # Write the updated DataFrame back to the Excel file
  df.to_excel('"./tmp/testSet_WebApp.xlsx"', index=False)
  return True
