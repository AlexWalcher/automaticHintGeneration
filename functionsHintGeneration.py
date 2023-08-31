"""
File that contains the functions that are used througout the automaticHintGeneration program.
Most of them are reused/shared between the different hint-types (years, people, locations)
"""

from code import InteractiveInterpreter
from importsHintGeneration import *

def download_spacy_models():
    spacy.cli.download("en_core_web_md")
    spacy.cli.download("en_core_web_sm")

download_spacy_models()

import lxml.etree as ET
import xml.etree.ElementTree as ET
import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from selenium import webdriver
from selenium.webdriver import Firefox
from sklearn.metrics.pairwise import cosine_similarity
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from collections import OrderedDict
import collections.abc as collections
from collections.abc import Mapping
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoTokenizer, AutoModel
from webdrivermanager import GeckoDriverManager


# gl_person_questions_dict_from_txt = {}
# # gl_location_questions_dict = {}
# # gl_year_questions_dict = {}

# class Test:
#   def __init__(self):
#     self.gl_person_questions_dict = {}
#     self.gl_location_questions_dict = {}
#     self.gl_year_questions_dict = {}

#   def get_person_questions_dict(self):
#     return self.gl_person_questions_dict

#   def set_person_questions_dict(self, value):
#     self.gl_person_questions_dict = value

#   def get_location_questions_dict(self):
#     return self.gl_location_questions_dict

#   def set_location_questions_dict(self, value):
#     self.gl_location_questions_dict = value

#   def get_year_questions_dict(self):
#     return self.gl_year_questions_dict

#   def set_year_questions_dict(self, value):
#     self.gl_year_questions_dict = value

sim_score_priority_words = ['World Cup', 'Champions League', 'occupied', 'Spoken language', 'shares border']


def load_file_path(file_path):
  #file_path = "/content/automaticHintGeneration/testSet.xlsx"
  df = pd.ExcelFile(file_path).parse("Sheet1")
  obj = Test()
  dataPerson = []
  dataYear = []
  dataLocation = []
  df_list = {}
  for index, row in df.iterrows():
    if(row["Category"] == "Person"):
      dataPerson.append([row["Question"], row["Answer"]])
    elif(row["Category"] == "Year"):
      dataYear.append([row["Question"], row["Answer"]])
    elif(row["Category"] == "Location"):
      dataLocation.append([row["Question"], row["Answer"]])
  person_df = pd.DataFrame(dataPerson, columns=["Question", "Answer"])
  year_df = pd.DataFrame(dataYear, columns=["Question", "Answer"])
  location_df = pd.DataFrame(dataLocation, columns=["Question", "Answer"])
  df_list["person"] = person_df
  df_list["year"] = year_df
  df_list["location"] =location_df
  year_questions_dict = dict(zip(year_df['Answer'], year_df['Question']))
  obj.set_year_questions_dict(year_questions_dict)
  person_questions_dict = dict(zip(person_df['Answer'], person_df['Question']))
  obj.set_person_questions_dict(person_questions_dict)
  location_questions_dict = dict(zip(location_df['Answer'], location_df['Question']))
  obj.set_location_questions_dict(location_questions_dict)
  # pprint.pprint(df_list, indent=1)
  return df_list


template_sentence_location_list = ['The location you are looking for is/was a member of category 1.']

#template sentences that are used to create the hint sentences
template_sentence_location = 'The location you are looking for, is a member of the category x'
template_sentence_location2 = 'The location you are looking for, belongs to the category '
template_sentence_person = 'The person you are looking for, is a member of the category x'
template_sentence_person2 = 'The person you are looking for, belongs to the category '

#The basic sentences out of which we create the hint-sentences
basic_sentences =  ['In the same year, ', 'In the previous year, ', 'In the following year, ']
sport_sentences = [' has won the UEFA Champions League.', ' has won the UEFA Euro Football Championship.', ' has won the FIFA World Cup.', ' has won the F1 Drivers World Championship.', ]
olympic_sentences = ['In the same year, the Summer Olympics were held in ', 'In the previous year, the Summer Olympics were held in ', 'In the following year, the Summer Olympics were held in ', 'In the same year, the Winter Olympics were held in ', 'In the previous year, the Winter Olympics were held in ', 'In the following year, the Winter Olympics were held in ']

#list of interesting properties of people
list_of_properties = ['nickname', 'country of citizenship', 'name in native language', 'native language', 'height',
                  'occupation', 'field of work', 'educated at', 'residence', 'work period', 'ethnic group',
                  'notable work', 'member of', 'owner of', 'significant event', 'award received', 'employer', 'position held', 'owner of', 
                  'date of birth', 'place of birth', 'date of death', 'place of death', 'manner of death',
                  'cause of death', 'social media followers', 'father', 'mother', 'sibling', 'spouse', 'child', 'unmarried partner', 'sport']

properties_blank_sentences = {
  'owner of': 'The person you are looking for is/was the owner of: 0.',
  'employer': 'The person you are looking for is/was an employee at the following companies: 0.',
  'position held': 'The person you are looking for is holding/has held the following positions as an eployee: 0.',
  'occupation': 'The person you are looking for, is occupied as 0.',
  'award received': 'The person you are looking for has won multiple awards in his life, some of them are 0.',
  'nickname': 'The person you are looking for was/is also known under the follwoing nickname: 0.',
  'significant event': 'Some of the most significant events of the searched person were: 0',
  'notable work': 'The person you are looking for was involved in some very notable works, like: 0.',
  'child + sibling': 'The person you are looking for, has / children and * siblings.',
  'date of birth + place of birth': 'The person you are looking for was born on / in *.',
  'date of birth + place of birth + date of death + place of death': 'The person you are looking for was born on / in * and died on - in +.' ,
  'work period' :  'The person you are looking for was most active during / and *.'
  }

# # #from years
# """
# This sorts the items in the dictionary based on the integer value of the second element in each key-value tuple (i.e. item[1]), in descending order (reverse=True).
# """
# def sort_dict_desc(d):
#   return {k: v for k, v in sorted(d.items(), key=lambda item: int(item[1]), reverse=True)}

# Load pre-trained model and tokenizer
model_name = 'bert-base-uncased'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

#Pre analyze/convert the text for BERNT
def preprocess_text(text):
  # Tokenize the text and add special tokens
  tokens = tokenizer.encode(text, add_special_tokens=True)
  # Convert the tokens to a tensor
  token_tensor = torch.tensor(tokens).unsqueeze(0)
  return token_tensor

# #Calculates a similarity score by comparing the two pieces of text va BERNT
# def get_similarity_score(text1, text2):
#   # Preprocess both texts
#   tensor1 = preprocess_text(text1)
#   tensor2 = preprocess_text(text2)
#   # Pass both tensors to the model to get the embeddings
#   with torch.no_grad():
#     output1 = model(tensor1)
#     output2 = model(tensor2)
#   # Compute the cosine similarity between the two embeddings
#   cosine_sim = torch.nn.functional.cosine_similarity(output1.last_hidden_state.mean(dim=1), output2.last_hidden_state.mean(dim=1), dim=1)
#   return cosine_sim.item()

# Dictionary for thumbcaption part of a year
"""
Given a URL, this function opens the url and retrieves the information stored in a table.
"""
# def get_table_info(url):
#   options = webdriver.FirefoxOptions()
#   #options.headless = True
#   options.add_argument('--headless')
#   #print("get_table_info TEST")
#   try:
#     driver = webdriver.Firefox(options=options)
#     driver.get(url)
#     time.sleep(10) # Wait for the page to load completely
#     soup = BeautifulSoup(driver.page_source, 'html.parser')
#     driver.quit()
#     table = soup.find('table')
#     rows = table.find_all('tr')
#     headers = [header.text.strip() for header in rows[0].find_all('th')]
#     data = []
#   except Exception as e:
#     pass
#   for row in rows[1:]:
#       data.append([cell.text.strip() for cell in row.find_all('td')])
#   return (headers, data)

def fetch_wikidata(params):
  url = 'https://www.wikidata.org/w/api.php'
  try:
    return requests.get(url, params=params)
  except:
    return 'There was and error'

def get_occupation_from_wikidata(people_list):
  # First we need to retrieve the Q-identifier for the pserons wikidata page
  occu_dict={}
  for a,b in people_list.items():
    # print(a,b)
    occu = ''
    occu_list = []
    person_name = (a)

    try:
      params_person_id = {
              'action': 'wbsearchentities',
              'format': 'json',
              'search': person_name,
              'language': 'en'
          }
      data_person_id = fetch_wikidata(params_person_id)
      data_person_id = data_person_id.json()
      person_wikidata_id = data_person_id['search'][0]['id'] # select first search result ID
      # print(person_wikidata_id)

      # Next we need to retrieve the Q-identifiers for the occupations
      params_occupation_id = {
                  'action': 'wbgetentities',
                  'ids':person_wikidata_id, 
                  'format': 'json',
                  'languages': 'en'
              }
      data_occupation_id = fetch_wikidata(params_occupation_id)
      data_occupation_id = data_occupation_id.json()
      # print(data_occupation_id['entities'][person_wikidata_id]['claims'])
      occupation_ids_list = data_occupation_id['entities'][person_wikidata_id]['claims']['P106'] #P106 is property id of occupation 
      # print(occupation_ids_list)
      person_occupations_ids = [v['mainsnak']['datavalue']['value']['id'] for v in occupation_ids_list]
      # print(person_occupations_ids)

      for oc in person_occupations_ids:
        # Next we need to retrieve the value for the corresponding occupation-id
        params_occupation_value = {
                    'action': 'wbsearchentities',
                    'format': 'json',
                    # 'search': person_occupations_ids[0],
                    'search': oc,
                    'language': 'en'
                }
        data_occupation_value = fetch_wikidata(params_occupation_value)
        data_occupation_value = data_occupation_value.json()
        occu = data_occupation_value['search'][0]['display']['label']['value']
        occu_list.append(occu)
    
    except Exception as e:
      print('error: get_occupation_from_wikidata: ', e)
    occu_dict[a] = occu_list
  return occu_dict


def get_table_info(url, table_number=2):
  
  test= url.lower()
  print("get_table_info URL:", url, test)

  html = wikipedia.page(test).html().encode("UTF-8")

  try: 
    df = pd.read_html(html)[ table_number]  # Try 2nd table first as most pages contain contents table first
  except IndexError:
    df = pd.read_html(html)[0]
  return df


"""
This function takes a subject, a wikipedia page, calls the link and retrieves the pageviews.
"""
def get_pageviews(subject):
  wikipedia_api_url = "https://en.wikipedia.org/w/index.php?title="

  page_title=subject.replace(" ", "_")
  url = wikipedia_api_url + page_title + '&action=info'

  try:
    response = requests.get(url)
    if response.status_code == 200:
      page_content = response.text
      soup = BeautifulSoup(page_content, 'html.parser')

      tr_element = soup.find('div', {'class': 'mw-pvi-month'})

      if tr_element:
        value = tr_element.text.strip()
        return value
      else:
        print("Could not find 'mw-pvi-month' element.")
        return None
    else:
      print(f"Failed to fetch page content. Status code: {response.status_code}")
      return None

  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
    return []
  
def get_pageviews_from_list(subject_list):

  ret = {}
  for subject in subject_list:
    pvs = get_pageviews(subject)
    ret[subject] = pvs

  return ret

def get_pageviews_from_linkssssssss(related_people_dict):
  # pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
  return_dict = {}
  for key,value in related_people_dict.items():
    entity_list = []
    for k in value:
      entity_list.append(k['title'])
  
    pvs_list = get_pageviews_from_list(entity_list)
    print(pvs_list)
    return_dict[key] = pvs_list

    # link_list = value
    # pruned_link_parts_list = extract_last_parts(link_list)
    # concat_str_for_links = concatenate_elements(pruned_link_parts_list)             #combine up to 10 of these links to create a request to pageview
    # pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
    # categories_with_pageviews =combine_dicts_from_links(pageviews_url_list)         #now we called the links and retreieved the pageviews; saved them as a dictionary
    # ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews)   #now the list is ordered in ascending order
    # return_dict[key] = ordered_categories_with_pageviews
  return return_dict

"""
This function converts a list into a dict in the way that is needed.
"""
def list_to_dict(lst):
  result = {}
  for sublist in lst:
    if len(sublist) >= 4:
      key = sublist[1]
      value = int(sublist[3].replace(',', ''))
      result[key] = value
  return result


def get_all_related_links(wiki_link):
  # Extract the page title from the Wikipedia link
  title = wiki_link.split('/')[-1]
  
  base_api_url = 'https://en.wikipedia.org/w/api.php'
  params = {
    'action': 'query',
    'titles': title,
    'prop': 'links',
    'pllimit': 'max',
    'format': 'json'
  }
    
  all_related_links = []
  while True:
    response = requests.get(base_api_url, params=params)
    data = response.json()
    if 'query' in data and 'pages' in data['query']:
      page = next(iter(data['query']['pages'].values()))
      if 'links' in page:
        links = page['links']
        all_related_links.extend(links)
    if 'continue' in data:
      params['plcontinue'] = data['continue']['plcontinue']
    else:
      break
          
  return [{'url': f'https://en.wikipedia.org/wiki/{link["title"]}', 'title': link['title']} for link in all_related_links]


# #from people
#retrieves all of the relate links of a wiki page
def get_related_links(wiki_link):
  # Extract the page title from the Wikipedia link
  title = wiki_link.split('/')[-1]
  # Format the API URL to get the page content
  api_url = f'https://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=links&pllimit=max&format=json'
  # Send a GET request to the API
  response = requests.get(api_url)
  if response.status_code == 200:
    data = response.json()
    # Extract the page ID from the API response
    page_id = next(iter(data['query']['pages']))
    # Check if the page exists and has links
    if page_id != '-1' and 'links' in data['query']['pages'][page_id]:
      # Retrieve the links from the API response
      links = data['query']['pages'][page_id]['links']
      # Extract the link titles and URLs
      related_links = [{'url': f'https://en.wikipedia.org/wiki/{link["title"]}', 'title': link['title']} for link in links]
      return related_links
  return []

def get_categories(subject_dict):
  categories_for_subject_dict= {}
  rankings_for_categories_dict = {}
  # r2 = {}
  #creates a dict with all the dicts of each location with its categories and sub-categories
  # people_occupations = get_occupations(subject_dict)
  for subject, question in subject_dict.items():
    try:
      ranking = get_categories_ranking(subject)
      # print(ranking)
      # sor = dict(sorted(ranking.items(), key=lambda x: int(x[1].replace(',', ''))))
      # print("sorted", sor)
      ordict = OrderedDict(ranking)
      rankings_for_categories_dict[subject] = ordict
    except Exception as e:
      print(e)
      pass
    # for k,v in people_occupations.items():
    #   for a,b in ranking.items():
    #     if k == a:
    #       if v not in b:
    #         r2[a]=b
  return rankings_for_categories_dict

#given a dictionary with all the categories, the function returns the categories in a OrderedDict with the corresponding pageviews for each category
# def get_pageviews_for_categories(cat_dict):
#   pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
#   all_cats_with_pvs = {}
#   for subject in cat_dict:
#     ord_dict = OrderedDict()
#     ordered_dict_sub =  cat_dict[subject]
#     links_list = [link for link in ordered_dict_sub.keys()]
#     pruned_link_parts_list = extract_last_parts(links_list)
#     concat_str_for_links = concatenate_elements(pruned_link_parts_list) #combine up to 10 of these links to create a request to pageview
#     pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
#     print(pruned_link_parts_list)
#     print(pageviews_range_url)
#     print(concat_str_for_links)
#     categories_with_pageviews =combine_dicts_from_links(pageviews_url_list) #now we called the links and retreieved the pageviews; saved them as a dictionary
#     ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews) #now the list is ordered in ascending order
#     all_cats_with_pvs[subject] = OrderedDict(categories_with_pageviews)
#   return all_cats_with_pvs

def sorting_dict(sor_dict):
  ret = {}
  l2 = sor_dict
  for loc, value in l2.items():
    if len(sor_dict) == 0:
      continue
    try:
      sorted_dict = OrderedDict(sorted(value.items(), key=lambda x: x[1][2], reverse=True))
    except Exception as e:
      sorted_dict = value
    ret[loc] = sorted_dict
  return ret

#input a url of a category, this returns the tilte
def get_category_title(category_url):
  parts = category_url.split('/')
  title = [part for part in parts if part.startswith('Category:')]
  if title:
    return title[0]
  else:
    return None
  
"""
Function that gets the pageviews of up to 10 links at a time;
Args:     dictionary where the keys are the answer-entities and the value is a link_list
Returns:  dictionary where the keys are the answer-entities and the value is a list with the links and pageviews
"""
def get_pageviews_from_links(link_dict):
  pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
  return_dict = {}
  for key,value in link_dict.items():
    link_list = value
    pruned_link_parts_list = extract_last_parts(link_list)
    concat_str_for_links = concatenate_elements(pruned_link_parts_list)             #combine up to 10 of these links to create a request to pageview
    pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
    categories_with_pageviews =combine_dicts_from_links(pageviews_url_list)         #now we called the links and retreieved the pageviews; saved them as a dictionary
    ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews)   #now the list is ordered in ascending order
    return_dict[key] = ordered_categories_with_pageviews
  return return_dict

"""
Function that takes the 5 most popular related-people from the related_people_pageviews_dict and
retrieves the corresponding wiki-categories with the their pageviews;
Args:     dictionary where the keys are the answer-entities and the value is a dict of related people with their pageviews
Returns:  dictionary where the keys are the answer-entities and the value is
  a dict where the keys are the related-people and the valus are tupples with the 10 most popular categories they appear and with the pageviews of that category
"""
# def get_categories_of_people_list(people_list, limit=5):
#   return_dict = {}
#   for key,value in people_list.items():
#     related_people_orderd = dict(sorted(value.items(), key=lambda x: x[1], reverse=True))   #order the dict after the pageviews in descending order
#     top_most_popular_people = dict(itertools.islice(related_people_orderd.items(), 5))      #take the top 5 most known people from the list
#     if len(related_people_orderd) == 0 or  len(top_most_popular_people) == 0:
#       continue
#     categories_of_related_people = get_categories(top_most_popular_people)
#     categories_with_pageviews_person = get_pageviews_for_categories(categories_of_related_people)
#     categories_with_subs_and_pageviews_person = get_dict_for_every_location(categories_of_related_people, categories_with_pageviews_person)
#     new_ordered_dict_related_person = sorting_dict(categories_with_subs_and_pageviews_person)
#     copy_new_ordered_dict_person_test = prune_and_ordered_dict(new_ordered_dict_related_person, 10)
#     ordered_dict_related_person = sorting_dict(copy_new_ordered_dict_person_test)
#     return_dict[key] = ordered_dict_related_person
#   return return_dict
# def get_categories_of_people_list(people_list, limit=5):
#   return_dict = {}
#   for key,value in people_list.items():
#     related_people_orderd = dict(sorted(value.items(), key=lambda x: x[1], reverse=True))   #order the dict after the pageviews in descending order
#     top_most_popular_people = dict(itertools.islice(related_people_orderd.items(), 5))      #take the top 5 most known people from the list
#     if len(related_people_orderd) == 0 or  len(top_most_popular_people) == 0:
#       continue
#     categories_of_related_people = get_categories(top_most_popular_people)
#     categories_with_pageviews_person = get_pageviews_for_categories(categories_of_related_people)
#     categories_with_subs_and_pageviews_person = get_dict_for_every_location(categories_of_related_people, categories_with_pageviews_person)
#     copy_new_ordered_dict_person_test = prune_and_ordered_dict(categories_with_subs_and_pageviews_person, 10)
#     pprint.pprint(copy_new_ordered_dict_person_test, sort_dicts=False)
#     return_dict[key] = copy_new_ordered_dict_person_test
#   return_dict = order_dict_by_second_entry(return_dict)
#   return return_dict






"""
Calculates the Intersection over Union between the answer-entity and each of the related-person entries seperately
Args: data (dict): A dictionary containing the answer-entity with the corresponding related-people and their most popular categories that they share with ther answer-entity
Returns: dict: A dict where the value is a list of tuple like this: ('Max Verstappen', 'Charles Leclerc', 5, 20, 0.25) (person_a, person_b, num_shared_categories, num_total_categories, num_shared_categories/num_total_categories)
"""
def calculate_IoU_from_countedCategoryDict(counted_category_apperances):
  #first we recover the list of people that are related to answer-entity
  p_dict = {}
  for key,value in counted_category_apperances.items():
    person_list = []
    for link, f_tup in value.items():
      num= f_tup[0]
      tup= f_tup[1]
      p_lst = f_tup[2]
      for person in p_lst:
        if person not in person_list:
          person_list.append(person)
    p_dict[key] = person_list
  iou_between_person_list = {}
  #now calculate the IoU
  for key_cat,value_cat in counted_category_apperances.items():
    for key,value in p_dict.items():
      if key == key_cat:
        inter_list = {}
        for person in value:
          p_count = 0
          for link, f_tup in value_cat.items():
            p_lst = f_tup[2]
            if person in p_lst:
              p_count += 1
          inter_list[person] = p_count
      iou_between_person_list[key_cat] = inter_list
  IoU_dict = {}
  for key, value in iou_between_person_list.items():
    IoU_list = []
    for person, number in value.items():
      num_total_categs = 20
      IoU_list.append((person,number,num_total_categs, number/num_total_categs))
    if IoU_list:
      IoU_dict[key] = IoU_list
    else:
      IoU_dict[key] = [('Placeholder', 0, 20, 1)]

  return IoU_dict

"""
Calculates the avg_diversity_from_IoU
Args:
Returns:
"""
def calculate_avg_diversity_from_IoU(intersection_between_people_with_ae):
  avg_diversity_dict = {}
  for key,value in intersection_between_people_with_ae.items():
    diversity_sum = 0
    pairwise_comparisons = 0
    for item in value:
      all_categs = item[2]
      IoU = item[1]
      diversity_sum += (all_categs - IoU)
      pairwise_comparisons += 1
    try:
      avg_diversity_dict[key] = (diversity_sum / pairwise_comparisons)
    except Exception as e:
      avg_diversity_dict[key] = 0
  return avg_diversity_dict


"""
Calculates the categories score from the category diversity (calculated by calculate_avg_diversity_from_IoU() ) and the cat_popularity (=pageviews)
Args:
Returns:
"""
def calculate_categories_score(counted_category_apperances, avg_diversity_from_IoU):
  categories_scores_dict = {}
  for key,value in counted_category_apperances.items():
    inter_dict={}
    for item in value.items():
      link = item[0]
      cat_popularity = item[1][1]
      for name, cat_div in avg_diversity_from_IoU.items():
        if name == key:
          # print(cat_popularity[1] , cat_div)
          try:
            inter_dict[link] = float(cat_popularity[1]) * float(cat_div)
          except Exception as e:
            inter_dict[link] = 0
            print("error", e)

    categories_scores_dict[key] = inter_dict
  ordered_dicter = {}
  ordered_scores ={}
  for k,v in categories_scores_dict.items():
    ordered_scores[k] = OrderedDict(v)
  for k,v in ordered_scores.items():
    ordered_dicter[k] = OrderedDict(sorted(v.items(), key=lambda x: x[1], reverse=True))
  #modify the scores to give some categories a lower one
  for key,value in ordered_dicter.items():
    for link, score in value.items():
      if '20th' in link or '21st' in link:
        value[link]  = score / 4
  return ordered_dicter

# """
# Calculates the categories score from the category diversity (calculated by calculate_avg_diversity_from_IoU() ) and the cat_popularity (=pageviews)
# Args:
# Returns:
# """
# def calculate_categories_score(counted_category_apperances, avg_diversity_from_IoU):
#   categories_scores_dict = {}
#   for key,value in counted_category_apperances.items():
#     inter_dict={}
#     for item in value.items():
#       link = item[0]
#       cat_popularity = item[1][1]
#       for name, cat_div in avg_diversity_from_IoU.items():
#         if name == key:
#           inter_dict[link] = cat_popularity * cat_div
#     categories_scores_dict[key] = inter_dict
#   ordered_dicter = {}
#   ordered_scores ={}
#   for k,v in categories_scores_dict.items():
#     ordered_scores[k] = OrderedDict(v)
#   for k,v in ordered_scores.items():
#     ordered_dicter[k] = OrderedDict(sorted(v.items(), key=lambda x: x[1], reverse=True))
#   #modify the scores to give some categories a lower one
#   for key,value in ordered_dicter.items():
#     for link, score in value.items():
#       if '20th' in link or '21st' in link:
#         value[link]  = score / 4
#   return ordered_dicter

# #from location
#combines the pageviews of the categories of the location together with the sub-categories and pages of those subcategories
def get_dict_for_every_location(cat_ranking, cat_with_pv):
  ret=cat_ranking
  for location, value in cat_ranking.items():
    for location1, value1 in cat_with_pv.items():
      if location == location1:
        tmp = value1
        ret[location] = tmp
  return ret

"""## **New prediction Methods for locations:**"""
"""
Function that retrieves the related/popular locations of the answer-entities;
Args:     the answer-entity name
Returns:  a list where each entry of the list is a dictionary; the keys and values are the (title and url) of the related locations
"""
def get_related_location_from_location_name(location_name):
  wiki_link = 'https://en.wikipedia.org/wiki'
  related_people_list = []
  modified_text = location_name.replace(' ', '_') #replace spaces with underscores in the name to use it in link
  link = f"{wiki_link}/{modified_text}"
  related_articles = get_related_links(link)
  return related_articles

#combines the pageviews of the categories of the location together with the sub-categories and pages of those subcategories
def get_dict_for_every_location(cat_ranking, cat_with_pv):
  ret=cat_ranking
  for location, value in cat_ranking.items():
    for location1, value1 in cat_with_pv.items():
      if location == location1:
        tmp = value1
        ret[location] = tmp
  return ret

"""
Function that is created with help of reusable function from above
Args:     location_question_dict with all locations with their questions
Returns:  dictionary where the keys are the answer-entities and the value is a OrderedDict of all categories with pageviews
"""
# def get_categories_with_pv_answerEntities_location(location_questions_dict):
#   cat_ranking_location = get_categories(location_questions_dict)
#   cat_with_pv_location = get_pageviews_for_categories(cat_ranking_location)
#   categories_with_subs_and_pageviews_location = get_dict_for_every_location(cat_ranking_location, cat_with_pv_location)
#   new_ordered_dict_location = sorting_dict(categories_with_subs_and_pageviews_location)
#   copy_new_ordered_dict_location = prune_and_ordered_dict(new_ordered_dict_location, 10)
#   ordered_dict_location = sorting_dict(copy_new_ordered_dict_location)

#   return ordered_dict_location

"""
Function that is created with help of reusable function from above
Args:     location_question_dict with all locations with their questions
Returns:  dictionary where the keys are the answer-entities and the value is a OrderedDict of all categories with pageviews
"""
def get_categories_with_pv_answerEntities_location(location_questions_dict):
  cat_ranking_location = get_categories(location_questions_dict)
  cat_with_pv_location = get_pageviews_for_categories(cat_ranking_location)
  categories_with_subs_and_pageviews_location = get_dict_for_every_location(cat_ranking_location, cat_with_pv_location)
  
  intermediate_dict = {}
  intermediate_ordere = {}
  for a,b in categories_with_subs_and_pageviews_location.items():
    inter_list = []
    for key in b.items():
      inter_list.append((key[0], int(key[1].replace(",", ""))))
    intermediate_ordere[a] = OrderedDict(sorted(inter_list, key=lambda x: x[1], reverse=True))

  # new_ordered_dict_location = sorting_dict(categories_with_subs_and_pageviews_location)
  # copy_new_ordered_dict_location = prune_and_ordered_dict(new_ordered_dict_location, 10)
  # ordered_dict_location = sorting_dict(copy_new_ordered_dict_location)

  return intermediate_ordere

#takes the categories scores dict and chooses the category with the highest score
def create_hint_sentences_unexCategs_location(categories_scores_dict, location_answers_dict):
  most_unexpected_categories_dict = {}
  hint_sentence_unexCateg_dict = {}
  try:
    for key,value in categories_scores_dict.items():
      categories_scores_dict[key] = OrderedDict(sorted(value.items(), key=lambda x: x[1], reverse=True))
      most_unexpected_categories_dict[key] = (next(iter(value.items())))
    for key,value in most_unexpected_categories_dict.items():
      hint_sentence_unexCateg_dict[key] = []
      for sentence in template_sentence_location_list:
        hint_sentence_unexCateg_dict[key].append( sentence.replace('1', get_category_title(most_unexpected_categories_dict[key][0]).split(':')[-1].replace('_', ' ') ))
  except Exception as e:
    pass
  return hint_sentence_unexCateg_dict

"""
Counts the occurrences of categories (links) in the input dictionary.
Args: data (dict): A dictionary containing category links as keys and tuples as values.
Returns: dict: A new dictionary where the keys are the category links and the values are
  the corresponding tuples of the category with a middle value indicating how
  often the link/category appeared in the other keys.
"""
# def count_categories_location(related_people_with_categories, answer_entities_with_categories):
#   category_appereances = {}
#   for answerEntityKey, aeCategory in answer_entities_with_categories.items():
#     for answerKey, relatedDict in related_people_with_categories.items():
#       if answerEntityKey == answerKey:
#         inner_dict = {}
#         for categ, pvs in aeCategory.items():
#           people_list = []
#           for relatedPersonKey, catWithPvs in relatedDict.items():
#             for relCateg, relPvs in  catWithPvs.items():
#               if categ == relCateg:
#                 rel_location_str = str(relatedPersonKey)
#                 if rel_location_str not in people_list and categ == relCateg:
#                   people_list.append(rel_location_str)
#                 inner_dict[categ] = (len(people_list),relPvs, people_list)
#     category_appereances[answerEntityKey] = inner_dict
#   for k,v in category_appereances.items():
#     if len(v) == 0:
#       for answerEntityKey, aeCategory in answer_entities_with_categories.items():
#         if k == answerEntityKey:
#           inner_dict={}
#           for a,b in aeCategory.items():
#             inner_dict[a] = (0, b, [])
#           category_appereances[k] = inner_dict
#   return category_appereances


def count_categories_location(related_people_with_categories, answer_entities_with_categories):
  category_appereances = {}
  for answerEntityKey, aeCategory in answer_entities_with_categories.items():
    inner_dict = {}
    for answerKey, relatedDict in related_people_with_categories.items():
      if answerEntityKey == answerKey:

        for cat, pvs in aeCategory.items():
          people_list = []
          # print("cat: "+ str(cat))
          for relatedPersonKey, catWithPvs in relatedDict.items():
            for categ in catWithPvs:
              if categ[0] == cat:
                print(cat, categ, answerEntityKey, relatedPersonKey)
                rel_pers_str = str(relatedPersonKey)
                if rel_pers_str not in people_list and categ[0] == cat:
                  people_list.append(rel_pers_str)
                inner_dict[cat] = (len(people_list),categ, people_list)

    category_appereances[answerEntityKey] = inner_dict

    for k,v in category_appereances.items():
      if len(v) == 0:
        for answerEntityKey, aeCategory in answer_entities_with_categories.items():
          if k == answerEntityKey:
            inner_dict={}
            for a,b in aeCategory.items():
              inner_dict[a] = (0, b, [])
            category_appereances[k] = inner_dict

  return category_appereances


#CREATE A FUNCTION THAT PUTS EVERYTHING TOGETHER - FOR UNEXPECTED CATEGORIES FOR LOCATIONS
"""
1. retrieve all of the related links of a wiki-location-page (limit at first 500);
2. pre prune the list, such that unecessary categories are discarded (for performance reasons)
3. now we have a list of related locations to compare to our answer-location-entity
4. search for the unexpected category: a category that is popular/well-known, but the answer-entity is one of the only entries from the list of related locations that appears in the category
5. rank them via the calculated scores
6. create hint-sentences with them
7. improve upon all of the sentence generation functions
"""
def get_location_hints_unexpected_categories(location_answers_dict):
  related_location_dict = {}
  related_location_link_dict= {}
  related_location_pageviews_dict = {}
  most_popular_related_location_with_categories = {}
  #time saving for first part (related locations recovery) 2m
  for key,value in location_answers_dict.items():
    related_location_dict[key] = get_related_location_from_location_name(key)
  #time saving for second part (related locations with pageviews and ordering) - 16m (6-7m)
  for key,value in related_location_dict.items():
    inter_link_list = []
    for item in value:
      inter_link_list.append(item['url'])
    related_location_link_dict[key] = inter_link_list
    related_location_pageviews_dict = get_pageviews_from_linkssssssss(related_location_link_dict)
  # pprint.pprint(related_location_pageviews_dict)
  #time saving for third part (related locations categories recovery and ordering) - 43m+ (14m-24m)
  most_popular_related_location_with_categories = get_categories_of_people_list(related_location_pageviews_dict, location_answers_dict)
  #time saving for third part retrieves the categories of the answer-entities - 9m+ (6m)
  answer_entities_with_categories_location = get_categories_with_pv_answerEntities_location(location_answers_dict)
  #time saving for fourth part counts the categories of the answer-entities - 3s
  counted_category_apperances_location = count_categories_location(most_popular_related_location_with_categories, answer_entities_with_categories_location)
  ordered_data = {}
  for key,value in counted_category_apperances_location.items():
    tmp = OrderedDict(value)
    ordered_data[key] = OrderedDict(sorted(tmp.items(), key=lambda x: x[1][0], reverse=True) )
  counted_category_apperances_location = ordered_data
  #1. calculate the IoU between max and every other person - (M,C) = 5/20; (M,L) = 2/20; (M,D) = 2/20; (M,A) = 2/20; (M,F) = 2/20;
  intersection_between_locations_with_ae = calculate_IoU_from_countedCategoryDict(counted_category_apperances_location)
  #2. calculate the average diversity between the 6 drivers - (20-5) + (20-2) + (20-2) + (20-2) + (20-2) = 87; (#avg_diversity/#pairwise_comparison) = 87/5 = 17,4
  avg_diversity_from_IoU_location = calculate_avg_diversity_from_IoU(intersection_between_locations_with_ae)
  #3. calculate a type of categoreis_score - categories_score = cat_diversity * cat_popularity(pvs)
  categories_scores_dict_location = calculate_categories_score(counted_category_apperances_location, avg_diversity_from_IoU_location)
  for key,value in categories_scores_dict_location.items():
    categories_scores_dict_location[key] = OrderedDict(sorted(value.items(), key=lambda x: x[1], reverse=True))
  #create some sentences with the occupation and a unexpected category as hints
  mucd = create_hint_sentences_unexCategs_location(categories_scores_dict_location, location_answers_dict)
  inter = {}
  for key, value in mucd.items():
    for answer,question in location_answers_dict.items():
      if key == answer:
        # sim_score = get_similarity_score(question,value[0])
        sim_score = calculate_similarity(question,answer,value[0],sim_score_priority_words)
        inter[key]  = {value[0] : sim_score}
  return inter

"""### location_hints_fixed_properties:"""
"""
Retrieve all data from the Wikidata page of a given location.
Args: location (str): The name of the location.
Returns: dict: A dictionary containing all data from the Wikidata page.
"""
def retrieve_location_data(location):
  # Create the Wikidata API URL
  url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&sites=enwiki&titles={location}&format=json"
  try:
    # Send a GET request to the Wikidata API
    response = requests.get(url)
    data = response.json()
    # Get the QID of the location
    entities = data.get("entities")
    qid = next(iter(entities))
    # Retrieve all data for the location
    location_data = entities[qid]
    return location_data
  except requests.exceptions.RequestException as e:
    pass
  return None

"""
Get the data for a specific property from the retrieved location data.
Args: location_data (dict): The data retrieved from the Wikidata page. property_code (str): The property code (e.g., P35) for the desired property.
Returns: list: A list of property values for the given property code.
"""
def get_property_data(location_data, property_code):
  # Check if the property exists in the location data
  if property_code in location_data.get("claims"):
    # Retrieve the property values
    property_values = location_data["claims"][property_code]
    # Extract the values from the property data
    values = [value["mainsnak"]["datavalue"]["value"] for value in property_values]
    return values
  return []

def get_entity_name(entity_id):
  url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
  response = requests.get(url)
  data = response.json()
  try:
    name = data['entities'][entity_id]['labels']['en']['value']
    return name
  except KeyError:
    return None

def create_hint_sentences(location_answers_dict, locations_identifiers_dict, properties_blank_sentences_locations):
  
  
  ret ={}
  location_infos_wikidata = {}
  for key,value in location_answers_dict.items():
    location_infos_wikidata[key] = retrieve_location_data(key)
    prop_sent = copy.copy(properties_blank_sentences_locations)
    loc_ident = copy.copy(locations_identifiers_dict)
    print(prop_sent )
    print(properties_blank_sentences_locations)
    print(loc_ident )
    print(locations_identifiers_dict)

    for propert, sentence in prop_sent.items():
      loc_ident[propert] =  get_property_data(location_infos_wikidata[key], propert)
      #prune the list with multipole entries down to the desired one
      if len(loc_ident[propert]) > 1:
        if propert != 'P47' and propert != 'P37' and propert != 'P206' and propert != 'P421' and  propert != 'P463' and propert != 'P793' and propert != 'P38':
          loc_ident[propert] = loc_ident[propert][-1]
      #if entry not null, search for the id of the entry
      if len(loc_ident[propert]) > 0:
        propety = loc_ident[propert]
        try:
          e_list = []
          for entry in propety:
            id = entry['id']
            e_list.append(get_entity_name(id))
          loc_ident[propert] = e_list
        except Exception as e:
          try:
              e_list = []
              for entry in propety:
                id = entry[0]['id']
                e_list.append(get_entity_name(id))
              loc_ident[propert] = e_list
          except Exception as e:
            try:
              e_list = []
              id = propety['id']
              e_list.append(get_entity_name(id))
              loc_ident[propert] = e_list
            except Exception as e:
              pass
      try:
        if propert == 'P1082':
          loc_ident[propert] = loc_ident[propert]['amount']
      except Exception as e:
        print(e)
    #now lets choose wich one we use for the sentences (sometimes random for others specific ones)
    for prop, sentence in prop_sent.items():
      for p, val in loc_ident.items():
        if p == prop:
          if len(val) == 0:
            continue
          elif len(val) == 1:
            word = str(val[0])
            prop_sent[p] = sentence.replace('*', word)
          else:
            if p != 'P1082':
              try:
                test =  loc_ident[p]
                random_Words = random.sample(test,3)
                random_Words = ', '.join(random_Words)
              except:
                try:
                  test =  loc_ident[p]
                  random_Words = random.sample(test,2)
                  random_Words = ', '.join(random_Words)
                except:
                  random_Words = random.choice(val)
              prop_sent[p] = sentence.replace('*', random_Words)
            else:
              prop_sent[p] = sentence.replace('*', loc_ident[p] )
    ret[key] = prop_sent
  return ret

def get_ranking_forfixed_properties(counted_category_apperances):
  #1. calculate the IoU between max and every other person - (M,C) = 5/20; (M,L) = 2/20; (M,D) = 2/20; (M,A) = 2/20; (M,F) = 2/20;
  intersection_between_people_with_ae = calculate_IoU_from_countedCategoryDict(counted_category_apperances)
  #2. calculate the average diversity between the 6 drivers - (20-5) + (20-2) + (20-2) + (20-2) + (20-2) = 87; (#avg_diversity/#pairwise_comparison) = 87/5 = 17,4
  avg_diversity_from_IoU = calculate_avg_diversity_from_IoU(intersection_between_people_with_ae)
  #3. calculate a type of categoreis_score - categories_score = cat_diversity * cat_popularity(pvs)
  categories_scores_dict = calculate_categories_score(counted_category_apperances, avg_diversity_from_IoU)
  for key,value in categories_scores_dict.items():
    categories_scores_dict[key] = OrderedDict(sorted(value.items(), key=lambda x: x[1], reverse=True))
  #create some sentences with the occupation and a unexpected category as hints
  mucd = create_hint_sentences_unexCategs_location(categories_scores_dict, person_answers_dict)
  return mucd

def get_location_hints_fixed_properties(location_answers_dict):
  # generate hints by using some fixed properties of the location:
  locations_identifiers_dict = {}
  locations_identifiers_dict['P610'] = {'highest_point': []}
  locations_identifiers_dict['P6'] = {'head_of_government': []}
  locations_identifiers_dict['P17'] = {'country': []}
  locations_identifiers_dict['P30'] = {'continent': []}
  locations_identifiers_dict['P35'] = {'head_of_state': []}
  locations_identifiers_dict['P36'] = {'capital': []}
  locations_identifiers_dict['P38'] = {'currency': []}
  locations_identifiers_dict['P131'] = {'located_on': []}
  locations_identifiers_dict['P1082'] = {'population': []}
  locations_identifiers_dict['P1376'] = {'city_is_capital_of': []}
  locations_identifiers_dict['P47'] = {'share_border': []}
  locations_identifiers_dict['P37'] = {'languages': []}
  locations_identifiers_dict['P206'] = {'body_of_water': []}
  locations_identifiers_dict['P421'] = {'time_zone': []}
  locations_identifiers_dict['P463'] = {'member_of': []}
  locations_identifiers_dict['P793'] = {'significant_event': []}
  locations_identifiers_dict['P1830'] = {'owner_of': []}
  properties_blank_sentences_locations = {
    'P610': 'The highest point in searched location is *.',
    'P6': 'Head of government of searched location is *.',
    'P17': 'The searched location is in country *.',
    'P30': 'The searched location is on continent *.',
    'P35': 'Head of state of searched location is *.',
    'P36': 'The capital of searched location is  *.',
    'P38': 'The currencies used in searched location is/are  *.',
    'P37': 'Spoken language(s) in searched location is/are *.',
    'P47': 'The searched location shares border with *.',
    'P131': 'The searched city is located on  *.',
    'P206': 'Some of the next bodies of water of searched location are *.',
    'P421': 'The searched location is in time-zone *.',
    'P463': 'Searched location is member of *.',
    'P793': 'A significant event happened in this location was *.',
    'P1082': 'The searched location has a population of *.',
    'P1376': 'The searched city is capital of  *.',
    'P1830': 'The searched location is owner of *.',
    }
  location_infos_wikidata = {}
  sol = create_hint_sentences(location_answers_dict, locations_identifiers_dict, properties_blank_sentences_locations)
  # inter = {}
  ret={}
  for key, value in sol.items():
    inter = {}
    for answer,question in location_answers_dict.items():
      if key == answer:
        for code, sentence in value.items():
          if '*' in sentence:
            continue
          else:
            # sim_score = get_similarity_score(question,sentence)
            sim_score = calculate_similarity(question,answer,sentence,sim_score_priority_words)
            inter[code]  = {sentence : sim_score}
    ret[key] = inter
    ret[key]['question'] = question    
  return ret

#people
"""## **New prediction Methods for locations:**"""
"""
Given a list of Wikipedia category names, creates the corresponding Wikipedia category links.
Args: categories (list): A list of Wikipedia category names to create links for.
Returns: category_links (list): A list of Wikipedia category links corresponding to the input categories.
"""
def get_category_links(categories):
  category_links = []
  for category in categories:
    category_link = "https://en.wikipedia.org/wiki/Category:" + category.replace(" ", "_")
    category_links.append(category_link)
  return category_links

"""
Given a list of Wikipedia category names, creates the corresponding Wikipedia category links.
Args: categories (list): A list of Wikipedia category names to create links for.
Returns: category_links (list): A list of Wikipedia category links corresponding to the input categories.
"""
def get_category_with_underscores(categories):
  category_links = []
  for category in categories:
    category_link = category.replace(" ", "_")
    category_links.append(category_link)
  return category_links

"""
Given a list of Wikipedia category names, retrieves the number of entries in each category and returns a dictionary
with the category names as keys and the entry counts as values.
Args: categories (list): A list of Wikipedia category names to retrieve entry counts for.
Returns: category_entry_counts (dict): A dictionary of Wikipedia category names and their respective entry counts.
"""
def get_category_entry_counts(categories):
  category_links = get_category_links(categories)
  category_entry_counts = {}
  for i, category_link in enumerate(category_links):
    response = requests.get(category_link)
    soup = BeautifulSoup(response.content, "html.parser")
    try:
      entry_count_text = soup.find("div", {"id": "catlinks"}).find_all("a")[1].text.strip()
      entry_count = int(entry_count_text.split()[-2])
      category_name = categories[i]
      if category_name:
        category_entry_counts[category_name] = entry_count
    except:
      pass
  return category_entry_counts

"""
Retrieves the categories of a Wikipedia page using the wikipediaapi package.
Args: title (str): The title of the Wikipedia page.
Returns: categories (list): A list of categories associated with the page.
"""
def get_wikipedia_categories(title):
  #wikipedia = wikipediaapi.Wikipedia("en")
  wikipedia = wikipediaapi.Wikipedia('automaticHintGeneration (alex@example.com)','en')
  page = wikipedia.page(title)
  if not page.exists():
    return []
  categories = [c for c in page.categories]
  return [cat.split(":")[1] for cat in categories]

def get_category_subcategories(link):
  # Create a Wikipedia API object
  wiki_api = wikipediaapi.Wikipedia('en')
  # Extract the category name from the link
  category_name = link.split('/')[-1]
  # Retrieve the category page
  category_page = wiki_api.page(f"Category:{category_name}")
  # Find the subcategories section of the page
  subcategories_section = category_page.categorymembers
  # Extract the subcategories from the section
  subcategories = []
  i=0
  for subcategory in subcategories_section.values():
    if i < 100: #threshold for how many entries per category
      i +=1
      if subcategory.ns == wikipediaapi.Namespace.CATEGORY:
        subcategories.append(subcategory.fullurl)
  return subcategories


def get_category_pages(category_title, limit=100):
  params = {
    "action": "query",
    "format": "json",
    "list": "categorymembers",
    "cmtitle": category_title,
    "cmlimit": str(limit) # limit to 100 entries
  }
  pages = []
  while True:
    response = requests.get("https://en.wikipedia.org/w/api.php", params=params).json()
    pages += [p["title"] for p in response["query"]["categorymembers"]]
    if "continue" in response:
      params.update(response["continue"])
    else:
      break
    if len(pages) >= limit: # break the loop if the number of entries exceeds 100
      break
  return pages[:limit] # return only the first 100 entries

"""
Given a list of Wikipedia category names, retrieves the number of entries in each category and returns a dictionary
with the category names as keys and the entry counts as values.
Args: searched_location: The desired location for wich a hint should be created. (The answer to the question)
Returns: dicto (dict): A dictionary of all categories with the subcategories and how many entries there are in each.
"""
def get_cat_with_all_subcats(searched_location):
  #retrieves the list of categories from the location-wikipedia page
  try:
    categories = get_wikipedia_categories(searched_location)
    categories_with_underscore = get_category_with_underscores(categories)
    categories_links = get_category_links(categories)
  except Exception as e:
      pass
  categories_with_links_dict = {}
  for i in range(len(categories_with_underscore)):
    key = categories_with_underscore[i]
    link = categories_links[i]
    categories_with_links_dict[key] = link
  cat_with_subcats_dict = {}
  for category in categories_links:
    try:
      sub_cats = get_category_subcategories(category)
      ct = get_category_title(category)
      pages_list = get_category_pages(ct)
    except Exception as e:
      pass
    filtered_list = [str(entry) for entry in pages_list if not entry.startswith("Category:")]
    new_list = [len(filtered_list), filtered_list]
    if sub_cats is None:
      continue
    else:
      cat_with_subcats_dict[category] = [[len(sub_cats), sub_cats], new_list]
  return cat_with_subcats_dict

#input a url of a category, this returns the tilte
def get_category_title(category_url):
  parts = category_url.split('/')
  title = [part for part in parts if part.startswith('Category:')]
  if title:
    return title[0]
  else:
    return None

# countries_list = ['Afghan', 'Albanian', 'Algerian', 'Andorran', 'Angolan', 'Argentinian', 'Armenian', 'Australian', 'Austrian', 'Azerbaijani', 'Bahamian', 'Bahraini', 'Bangladeshi', 'Barbadian', 'Belarusian', 'Belgian', 'Belizean', 'Beninese', 'Bhutanese', 'Bolivian', 'Bosnian', 'Motswana', 'Brazilian', 'Bruneian', 'Bulgarian', 'Burkinabe', 'Burundian', 'Cambodian', 'Cameroonian', 'Canadian', 'Cape Verdean', 'Central African', 'Chadian', 'Chilean', 'Chinese', 'Colombian', 'Comorian', 'Congolese', 'Congolese', 'Costa Rican', 'Croatian', 'Cuban', 'Cypriot', 'Czech', 'Danish', 'Djiboutian', 'Dominican', 'Dominican', 'East Timorese', 'Ecuadorian', 'Egyptian', 'Salvadoran', 'Equatorial Guinean', 'Eritrean', 'Estonian', 'Swazi', 'Ethiopian', 'Fijian', 'Finnish', 'French', 'Gabonese', 'Gambian', 'Georgian', 'German', 'Ghanaian', 'Greek', 'Grenadian', 'Guatemalan', 'Guinean', 'Guinea-Bissauan', 'Guyanese', 'Haitian', 'Honduran', 'Hungarian', 'Icelander', 'Indian', 'Indonesian', 'Iranian', 'Iraqi', 'Irish', 'Israeli', 'Italian', 'Jamaican', 'Japanese', 'Jordanian', 'Kazakhstani', 'Kenyan', 'I-Kiribati', 'North Korean', 'South Korean', 'Kuwaiti', 'Kyrgyzstani', 'Laotian', 'Latvian', 'Lebanese', 'Basotho', 'Liberian', 'Libyan', 'Liechtensteiner', 'Lithuanian']
countries_list = []
#input searched location and returns a dict with number of pages and number of subcategories
def get_categories_ranking(searched_location):
  categories = get_wikipedia_categories(searched_location)
  categories_links = []
  cat_without_articles = []
  bad_list = ['Articles with', 'CS1', 'Wikipedia', 'Webarchive', 'Short', 'Biography', 'Commons', 'Pages', 'Use', 'All', 'Articles', 'Coordinates', 'Engvar', 'Lang', 'Official']
  for c in categories:
    if not any(c.startswith(word) for word in bad_list) and not any(c.startswith(word) for word in countries_list) :
      cat_without_articles.append(c)
  try:
    categories_links = get_category_links(cat_without_articles)
  except Exception as e:
      pass
  cat_with_amount = {}

  for category in categories_links:
    cat_with_amount[category] =  (0, 0)
  sorted_dict = dict(sorted(cat_with_amount.items(), key=lambda x: x[1], reverse=True))
  return sorted_dict


#input searched location and returns a dict with number of pages and number of subcategories
# def get_categories_ranking(searched_location):
#   categories = get_wikipedia_categories(searched_location)
#   categories_links = []
#   cat_without_articles = []
#   bad_list = ['Articles with', 'CS1', 'Wikipedia', 'Webarchive', 'Short', 'Biography', 'Commons', 'Pages', 'Use', 'All', 'Articles', 'Coordinates', 'Engvar', 'Lang', 'Official']
#   # test[searched_location] = searched_location
#   # print("sl ", searched_location)
#   # print("test ", test)
#   # people_occupations = get_occupations(test)
#   # print("occu get", people_occupations)
#   for c in categories:
#     # contains_bad_word = False
#     # try:
#     #   for word in bad_list:
#     #     if word in c:
#     #       contains_bad_word = True
#     #       continue
#     #   for name, val in people_occupations.items():
#     #     if val in c:
#     #       contains_bad_word = True
#     #       continue
#     # except Exception as e:
#     #   print(e)
#     # if contains_bad_word == False:
#     #   cat_without_articles.append(c)

#     if not any(c.startswith(word) for word in bad_list):
#       # for name, val in people_occupations.items():
#         # if val not in c:
#       cat_without_articles.append(c)
#   try:
#     categories_links = get_category_links(cat_without_articles)
#   except Exception as e:
#       pass
#   cat_with_amount = {}

#   for category in categories_links:
#     cat_with_amount[category] =  (0, 0)
#   sorted_dict = dict(sorted(cat_with_amount.items(), key=lambda x: x[1], reverse=True))
#   return sorted_dict

#extract the category part from the wiki links
def extract_last_parts(links):
  last_parts = []
  for link in links:
    last_part = link.split('/')[-1]
    last_parts.append(last_part)
  return last_parts

#function to concatenate the category links to insert into a pageviews url
def concatenate_elements(elements, n=10):
  result = []
  for i in range(0, len(elements), n):
    group = elements[i:i+n]
    result.append('|'.join(group))
  return result

"""
This function first initializes an empty list url_list that will hold the modified URLs. Then, it uses a for loop to iterate through each combined string in the input list.
For each combined string, it concatenates the base URL with a forward slash and the combined string, and appends the resulting URL to the url_list. Finally, the function returns the url_list at the end.
"""
def combine_pv_urls(base_url, combined_strings):
    url_list = []
    for strin in combined_strings:
      url_list.append(base_url  + strin)
    return url_list

"""
This function takes a list of links, opens each link to get the data, discards the header and converts the data into a dictionary using the list_to_dict() function,
and then updates a combined dictionary with the resulting dictionary from each link. Finally, it returns the combined dictionary.
"""
def combine_dicts_from_links(link_list):
  combined_dict = {}
  for link in link_list:
    try:
      header, data = get_table_info(link)
      link_dict = list_to_dict(data)
      combined_dict.update(link_dict)
    except Exception as e:
      pass
  return combined_dict

def add_values_to_links(links_dict, values_dict):
  new_dict = {}
  for link, value in links_dict.items():
    key = link.split(':')[-1]
    if key in values_dict:
      value += (values_dict[key],)
    new_dict[link] = value
  return new_dict

def combine_catnumbers_pvs(ord_dict, norm_dict):
  for key in ord_dict:
    if key in norm_dict:
      ord_dict[key] = ord_dict[key] + (norm_dict[key],)
  return ord_dict

def add_values_to_linkss(links_dict, values_dict):
  new_dict = {}
  for loc, ord_list in links_dict.items():
    for loc2, ord_list_pv in values_dict.items():
      if loc == loc2:
        new_dict[loc] = combine_catnumbers_pvs(ord_list, ord_list_pv)
  return new_dict

#combines the pageviews of the categories of the location together with the sub-categories and pages of those subcategories
def combine_pv_cats(cat_dict, pv_dict):
  tmp = cat_dict
  for key, value in cat_dict.items():
    for key2, value2 in pv_dict.items():
      category_name = key.split('/')[-1]
      new_string = key2.replace(' ', '_')
      if category_name == new_string:
        org_tup = cat_dict[key]
        new_tup = org_tup + (value2,0)
        tmp[key] = new_tup
        if len(new_tup) < 3:
          continue
  return tmp


# def get_categories(subject_dict):
#   categories_for_subject_dict= {}
#   rankings_for_categories_dict = {}
#   #creates a dict with all the dicts of each location with its categories and sub-categories
#   for subject, question in subject_dict.items():
#     try:
#       ranking = get_categories_ranking(subject)
#       ordict = OrderedDict(ranking)
#       rankings_for_categories_dict[subject] = ordict
#     except Exception as e:
#       pass
#   return rankings_for_categories_dict

#given a dictionary with all the categories, the function returns the categories in a OrderedDict with the corresponding pageviews for each category
# def get_pageviews_for_categories(cat_dict):
#   pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
#   all_cats_with_pvs = {}
#   for subject in cat_dict:
#     ord_dict = OrderedDict()
#     ordered_dict_sub =  cat_dict[subject]
#     links_list = [link for link in ordered_dict_sub.keys()]
#     pruned_link_parts_list = extract_last_parts(links_list)
#     concat_str_for_links = concatenate_elements(pruned_link_parts_list) #combine up to 10 of these links to create a request to pageview
#     pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
#     categories_with_pageviews =combine_dicts_from_links(pageviews_url_list) #now we called the links and retreieved the pageviews; saved them as a dictionary
#     ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews) #now the list is ordered in ascending order
#     all_cats_with_pvs[subject] = OrderedDict(categories_with_pageviews)
#   return all_cats_with_pvs

def get_pageviews_for_categories(cat_dict):
  # pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
  all_cats_with_pvs = {}
  for subject in cat_dict:
    ord_dict = OrderedDict()
    ordered_dict_sub =  cat_dict[subject]
    links_list = [link for link in ordered_dict_sub.keys()]
    pruned_link_parts_list = extract_last_parts(links_list)

    # print('pruned_link_parts_list')
    # pprint.pprint(pruned_link_parts_list)

    pvs = get_pageviews_from_list(pruned_link_parts_list)
    # pprint.pprint(pvs)
    # concat_str_for_links = concatenate_elements(pruned_link_parts_list) #combine up to 10 of these links to create a request to pageview
    # pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
    # print(pruned_link_parts_list)
    # print(pageviews_range_url)
    # print(concat_str_for_links)
    # categories_with_pageviews =combine_dicts_from_links(pageviews_url_list) #now we called the links and retreieved the pageviews; saved them as a dictionary
    # ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews) #now the list is ordered in ascending order
    try:
      sor = dict(sorted(pvs.items(), key=lambda x: int(x[1].replace(',', '')),reverse = True))
    except Exception as e: 
      print(e)
    # print(sor)

    all_cats_with_pvs[subject] = OrderedDict(sor)

  return all_cats_with_pvs


def sorting_dict(sor_dict):
  ret = {}
  l2 = sor_dict
  for loc, value in l2.items():
    if len(sor_dict) == 0:
      continue
    try:
      sorted_dict = OrderedDict(sorted(value.items(), key=lambda x: x[1][2], reverse=True))
    except Exception as e:
      sorted_dict = value
    ret[loc] = sorted_dict
  return ret

# function that takes a dictionary with an ordered dictionary as the value and prunes the ordered dictionary to keep only the first n entries:
def prune_ordered_dict(dictionary, n):
  pruned_dict = OrderedDict()
  for key, value in dictionary.items():
    pruned_dict[key] = OrderedDict(list(value.items())[:n])
  return pruned_dict

# countries_list = ['Afghan', 'Albanian', 'Algerian', 'Andorran', 'Angolan', 'Argentinian', 'Armenian', 'Australian', 'Austrian', 'Azerbaijani', 'Bahamian', 'Bahraini', 'Bangladeshi', 'Barbadian', 'Belarusian', 'Belgian', 'Belizean', 'Beninese', 'Bhutanese', 'Bolivian', 'Bosnian', 'Motswana', 'Brazilian', 'Bruneian', 'Bulgarian', 'Burkinabe', 'Burundian', 'Cambodian', 'Cameroonian', 'Canadian', 'Cape Verdean', 'Central African', 'Chadian', 'Chilean', 'Chinese', 'Colombian', 'Comorian', 'Congolese', 'Congolese', 'Costa Rican', 'Croatian', 'Cuban', 'Cypriot', 'Czech', 'Danish', 'Djiboutian', 'Dominican', 'Dominican', 'East Timorese', 'Ecuadorian', 'Egyptian', 'Salvadoran', 'Equatorial Guinean', 'Eritrean', 'Estonian', 'Swazi', 'Ethiopian', 'Fijian', 'Finnish', 'French', 'Gabonese', 'Gambian', 'Georgian', 'German', 'Ghanaian', 'Greek', 'Grenadian', 'Guatemalan', 'Guinean', 'Guinea-Bissauan', 'Guyanese', 'Haitian', 'Honduran', 'Hungarian', 'Icelander', 'Indian', 'Indonesian', 'Iranian', 'Iraqi', 'Irish', 'Israeli', 'Italian', 'Jamaican', 'Japanese', 'Jordanian', 'Kazakhstani', 'Kenyan', 'I-Kiribati', 'North Korean', 'South Korean', 'Kuwaiti', 'Kyrgyzstani', 'Laotian', 'Latvian', 'Lebanese', 'Basotho', 'Liberian', 'Libyan', 'Liechtensteiner', 'Lithuanian']
countries_list = []

# function that takes a dictionary with an ordered dictionary as the value and prunes the ordered dictionary to keep only the first n entries and deltes certain categories:
# def prune_and_ordered_dict(dictionary, n):
#   pruned_dict = OrderedDict()
#   inter1_dict= OrderedDict()
#   bad_categories_list = ['Living_people', 'Living people', '_births', 'births', '_deaths', 'deaths', 'Good_articles', 'Good articles', 'Members','19th', '20th', '21st', 'Capitals in Europe', 'state capitals']
#   print("dict", dictionary)
#   obj = Test()
#   sp = obj.get_person_questions_dict() 
#   print(sp)
#   sp =   gl_person_questions_dict_from_txt 
#   print(sp)
#   people_occupations = get_occupations(sp)
#   print("occu prune", people_occupations)
#   for key, value in dictionary.items():
#     inter3_dict= OrderedDict()
#     for link, tuplee in value.items():
#       link_str = str(link)
#       contains_bad_word = False
#       try:
#         for word in bad_categories_list:
#           if word in link_str:
#             contains_bad_word = True
#             continue
#         for word in countries_list:
#           if word in link_str:
#             contains_bad_word = True
#             continue
#         for name, val in people_occupations.items():
#           if key == name:
#             if val in link_str:
#               contains_bad_word = True
#               continue    
#       except Exception as e:
#         print("exception in def prune_and_ordered_dict", e)
#       if contains_bad_word == False:
#         inter3_dict[link] = tuplee
#     pruned_dict[key] = inter3_dict
#   for key, value in pruned_dict.items():
#     inter1_dict[key] = OrderedDict(list(value.items())[:n])
#   return inter1_dict

def prune_and_ordered_dict(dictionary, n):
  pruned_dict = OrderedDict()
  inter1_dict= OrderedDict()
  # bad_categories_list = ['Living_people', 'Living people', '_births', 'births', '_deaths', 'deaths', 'Good_articles', 'Good articles', 'Members','19th', '20th', '21st', 'Capitals in Europe', 'state capitals']
  bad_categories_list = ['Living_people', 'Living people', '_births', 'births', '_deaths', 'deaths', 'Good_articles', 'Good articles', 'Members','19th', 'Capitals in Europe', 'state capitals']
  print(dictionary)
  people_occupations = get_occupation_from_wikidata(dictionary)
  print("occu", people_occupations)
  
  for key, value in dictionary.items():
    inter3_dict= OrderedDict()
    for link, tuplee in value.items():
      link_str = str(link)
      contains_bad_word = False
      try:
        for word in bad_categories_list:
          if word in link_str:
            contains_bad_word = True
            continue
        for word in countries_list:
          if word in link_str:
            contains_bad_word = True
            continue
        for name, val in people_occupations:
          if key == name:
            if val in link_str:
              contains_bad_word = True
              continue
      except Exception as e:
        print("prune_and_ordered_dict", e)
      if contains_bad_word == False:
        inter3_dict[link] = tuplee
    pruned_dict[key] = inter3_dict
  for key, value in pruned_dict.items():
    inter1_dict[key] = OrderedDict(list(value.items())[:n])
  return inter1_dict


#find the 20 most appearing categories
def find_most_common_links(data_dict):
  link_count = {}
  for key, value in data_dict.items():
    for link in value:
      if link not in link_count:
        link_count[link] = {"count": 1, "keys": [key]}
      else:
        link_count[link]["count"] += 1
        link_count[link]["keys"].append(key)
  # Sort the links by their count in descending order
  sorted_links = sorted(link_count.items(), key=lambda x: x[1]["count"], reverse=True)
  # Return a list of tuples with the link, count, and keys
  return [(link, data["count"], data["keys"]) for link, data in sorted_links[:20]]


def get_categories_with_pageviews_person(person_questions_dict):
  cat_ranking_person = get_categories(person_questions_dict)
  cat_with_pv_person = get_pageviews_for_categories(cat_ranking_person)
  categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_person, cat_with_pv_person)
  new_ordered_dict_person = sorting_dict(categories_with_subs_and_pageviews_person)
  return new_ordered_dict_person

#retrives the category name from the link
def get_category_name(link):
  category_prefix = "Category:"
  if link.startswith("https://wikipedia.org/wiki/"):
    return link[len("https://wikipedia.org/wiki/" + category_prefix):].replace("_", " ")
  else:
    if link.startswith("https://en.wikipedia.org/wiki/"):
      return link[len("https://en.wikipedia.org/wiki/" + category_prefix):].replace("_", " ")
    else:
      return None

#just get the first 3 categories without any special formula
def get_first_three_categs_location(copy_categories_with_subs_and_pageviews_location):
  first_three_categories_per_location = {}
  for key, value in copy_categories_with_subs_and_pageviews_location.items():
    first_three = dict(itertools.islice(value.items(), 3))
    first_three_categories_per_location[key] = first_three
  hint_sentence_location = {}
  for key, value in first_three_categories_per_location.items():
    inter_hints = []
    for link, tup in value.items():
      cat_name=get_category_name(link)
      if cat_name is not None:
        ok = template_sentence_location2 + cat_name
      else:
        ok = template_sentence_location2
      inter_hints.append(ok)
    hint_sentence_location[key] = inter_hints
  return hint_sentence_location

#just get the first 3 categories without any special formula
def get_first_three_categs_person(copy_categories_with_subs_and_pageviews_location):
  first_three_categories_per_location = {}
  for key, value in copy_categories_with_subs_and_pageviews_location.items():
    first_three = dict(itertools.islice(value.items(), 3))
    first_three_categories_per_location[key] = first_three
  hint_sentence_location = {}
  for key, value in first_three_categories_per_location.items():
    inter_hints = []
    for link, tup in value.items():
      cat_name=get_category_name(link)
      if cat_name is not None:
        ok = template_sentence_person2 + cat_name
      else:
        ok = template_sentence_person2
      inter_hints.append(ok)
    hint_sentence_location[key] = inter_hints
  return hint_sentence_location

#get predicates of a wiki page via wikidataAPI
def get_wikidata_predicates(page_title):
    # First, get the Wikidata item ID of the page
    url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&redirects=1&titles={page_title}&format=json"
    response = requests.get(url).json()
    pages = response["query"]["pages"]
    if "-1" in pages:
        return None
    page_id = next(iter(pages))
    wikidata_id = pages[page_id]["pageprops"]["wikibase_item"]
    # Then, get the predicates and their values of the Wikidata item
    url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={wikidata_id}&format=json&props=claims"
    response = requests.get(url).json()
    entity = response["entities"][wikidata_id]
    predicates = {}
    for claim_id, claim in entity["claims"].items():
        predicate_id = claim["mainsnak"]["property"]
        predicate_value = claim["mainsnak"]["datavalue"]["value"]
        predicates[predicate_id] = predicate_value
    return predicates

# takes a list of all the people and the list of category occurences where all the categories that were assigned to these wiki-pages
# are listed and ranked after how often they occur;
# output: a list where the person is the key and the entries show wich categories the entity shares with wich other entitities and how many they are
def get_people_dict(people_list, occurences_list):
  people_dict = {}
  for person in people_list:
    person_categories = []
    for occurence in occurences_list:
      if person in occurence[2]:
        person_categories.append((occurence[0], occurence[1], occurence[2]))
    people_dict[person] = person_categories
  return people_dict

#returns a dict where for each person in people_list we calculate how often they occur in the same category as the keys in person_dict
# (where already for each person we looked at each of the categories he appears and counted how many other people from people_list appear in these )
def count_people_occurrences(person_dict, people_list):
  # Initialize an empty dictionary to hold the counts
  count_dict = {}
  # Loop through all pairs of drivers and count the number of occurrences
  for key, value in person_dict.items():
    counter = {}
    for person in people_list:
      counter[person] = 0
      for cat in value:
        if person in cat[2]:
          counter[person] += 1
    count_dict[key] = counter
  return count_dict

#sorting
def sort_dict_by_value_desc(d):
  # Sort the inner dictionary by value in descending order
  sorted_dict = []
  sorted_dict = OrderedDict(sorted(d.items(), key=lambda x: x[1], reverse=True))
  return sorted_dict

def get_categories_union(overlap_dict, people_list):
  # Initialize an empty dictionary to hold the counts
  count_dict = {}
  for key, value in overlap_dict.items():
    counter = {}
    for item, number in value.items():
      counter[item] = number_categories_per_person[key] + number_categories_per_person[item] - number
    count_dict[key] = counter
  return count_dict

def get_avg_pairwise_sim(cat_div_union, cat_div_overlap, number_categories_per_person, people_list):
  count_dict = {}
  for key, value in cat_div_union.items():
    inter = {}
    for key1, value1 in cat_div_overlap.items():
      if key == key1:
        for name, number in value.items():
          for name1, number1 in value1.items():
            if name == name1:
              if not number  or not number1:
                inter[name] = 0
              else:
                inter[name] = (number1 / number)
    count_dict[key] = inter
  return count_dict

def get_cat_diversity(shared_categories, copy_new_ordered_dict_person):
  count_dict = {}
  for key, value in copy_new_ordered_dict_person.items():
    for item in value.items():
      pv = 0
      link = item[0]
      trip = item[1]
      if len(trip) == 3:
        pv = trip[2]
      if link not in count_dict:
        count_dict[link] = pv
  return count_dict

def get_categories_with_ranking(person_questions_dict):
  cat_with_pv_person = {}
  cat_ranking_person = get_categories(person_questions_dict)
  cat_with_pv_person = get_pageviews_for_categories(cat_ranking_person)
  categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_person, cat_with_pv_person)
  new_ordered_dict_person = sorting_dict(categories_with_subs_and_pageviews_person)
  return new_ordered_dict_person

#given a name, retrieve the infomration in the short-description part of the wiki page
def get_page_short_description(page_title):
  # Prepare the API request URL
  url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}"
  # Send the API request
  response = requests.get(url)
  data = response.json()
  # Extract the short description from the API response
  short_description = data.get('description', '')
  return short_description

def find_most_similar_category(persons, specific_category, num_similar_categories=3):
  most_similar_categories = {}
  for person, categories in persons.items():
    category_texts = [category_link.split('/')[-1].replace('_', ' ') for category_link in categories.keys()]
    category_texts.append(specific_category[person])  # Add the specific category for comparison
    # Vectorize the category texts
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(category_texts)
    # Calculate cosine similarity between the specific category and other categories
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
      # Calculate cosine similarity between the specific category and other categories
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])[0]
    # Find the most similar categories textually
    similar_indices = similarities.argsort()[-num_similar_categories:][::-1]
    similar_categories = [category_texts[index] for index in similar_indices]
    most_similar_categories[person] = similar_categories
  return most_similar_categories

def get_work_category(similar_categories):
  person_with_work_categories = {}
  person_with_work_category = {}
  strings_to_check = ["births", "deaths"]
  for person, categories in similar_categories.items():
    for strs in strings_to_check:
      for cats in categories:
        if strs in cats:
          categories.remove(cats)
        else:
          continue
      person_with_work_categories[person] = categories
  for person, categories in person_with_work_categories.items():
    person_with_work_category[person] = categories[0]
  return person_with_work_category

def get_container_categories(work_cats):
  for person, categories in work_cats.items():
    wiki_category = categories
    base_url = 'https://en.wikipedia.org/w/api.php'
    params = {
        'action': 'query',
        'titles': wiki_category,
        'prop': 'categories',
        'format': 'json',
        'cllimit': 'max'
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    page_id = next(iter(data['query']['pages'].keys()))
    categories = data['query']['pages'][page_id].get('categories', [])
    container_categories = []
    for category in categories:
        if category['title'].startswith('Category:'):
            container_categories.append(category['title'][9:])
    strings_to_check = ["CatAutoTOC ", "Commons", "Template"]
    for strs in strings_to_check:
      for cats in container_categories:
        if strs in cats:
          container_categories.remove(cats)
        else:
          continue
    work_cats[person] = container_categories
  return work_cats

def replace_spaces_with_underscore(dictionary):
  updated_dict = {}
  for key, value in dictionary.items():
    updated_dict[key] = value.replace(" ", "_")
  return updated_dict

def format_category_dict(category_dict):
  formatted_dict = {}
  for key, value in category_dict.items():
    if isinstance(value, list):
      formatted_value = [f"Category:{v.replace(' ', '_')}" for v in value]
    else:
      formatted_value = f"Category:{value.replace(' ', '_')}"
    formatted_dict[key] = formatted_value
  return formatted_dict

"""
Functions to retrieve the occupation of a person
The wikipedia-api library does not provide a direct method to retrieve the infobox of a Wikipedia page.
However, we can use beautifulsoup4 to parse the HTML content of the Wikipedia page and extract the infobox.
"""
#function that retrieves the infobox using beautifulsoup4
def get_infobox_from_wikipedia(page_title):
  # Format the page title for the Wikipedia URL
  formatted_title = page_title.replace(' ', '_')
  # Construct the Wikipedia page URL
  url = f"https://en.wikipedia.org/wiki/{formatted_title}"
  # Send a GET request to the Wikipedia page
  response = requests.get(url)
  # Check if the page exists
  if response.status_code != 200:
    print(f"Page '{page_title}' does not exist.")
    return None
  # Create a BeautifulSoup object to parse the page content
  soup = BeautifulSoup(response.content, 'html.parser')
  # Find the infobox section of the page
  infobox = soup.find(class_='infobox')
  return infobox

#function that retrieves the infobox from a Wikipedia page and specifically extracts the entries from the "occupation" or "occupations" field:
def get_occupations_from_infobox(page_title):
  # Retrieve the infobox from the Wikipedia page
  infobox = get_infobox_from_wikipedia(page_title)
  # Check if the infobox exists
  if not infobox:
    return []
  # Search for the "occupation" or "occupations" field in the infobox
  occupation_keywords = ['occupation', 'occupations', 'Occupation', 'Occupations']
  occupations = []
  for keyword in occupation_keywords:
    field = infobox.find(string=keyword)
    if field:
      # Retrieve the occupation entries from the field
      tmp_str = field.find_next("td").find_next("div").find_next("ul")
      from_table = extract_list_elements(tmp_str)
      from_field = field.find_next("td").text.strip()
      from_field = from_field.split()
      if len(from_table) > 0:
        for i in from_table:
          occupations.append(i)
      elif len(from_field) > 0:
        for i in from_field:
          occupations.append(i)
      else:
        continue
  return occupations

#extract the elements between the <li> tags
def extract_list_elements(html_string):
  occupations_list = []
  li_entries_list = []
  html_str = str(html_string)
  html_str = html_str.replace("</ul>", "")
  html_str = html_str.replace("<ul>", "")
  html_str = html_str.replace("</li>", "")
  li_entries_list = html_str.split("<li>")
  for i in li_entries_list:
    if len(i) > 0: #check if empty
      if len(i) < 16: #check if entry is a link
        occupations_list.append(i)
  return occupations_list

#searches the occupation for every entry in people list
def get_occupations(people_list):
  print(people_list)
  peop_dict = {}

  if isinstance(people_list, list):
    for item in people_list:
      print("Processing item in list:", item)
      peop_dict[item] = " "
  elif isinstance(people_list, str):
    print("Processing string:", people_list)
    peop_dict[people_list] = " "

  occupation_person_dict = {}
  try:
    identifiers = get_wikipedia_identifiers(people_list)
    properties_list = ['occupation']
    for name, pid in identifiers.items():
      inter = get_person_properties(pid, properties_list, people_list)
      occupation_person_dict[name] = inter['occupation'][0]
  except Exception as e:
    print('get_occupations', e)
  return occupation_person_dict

# #retrieves all of the relate links of a wiki page
# def get_related_links(wiki_link):
#   # Extract the page title from the Wikipedia link
#   title = wiki_link.split('/')[-1]
#   # Format the API URL to get the page content
#   api_url = f'https://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=links&pllimit=max&format=json'
#   # Send a GET request to the API
#   response = requests.get(api_url)
#   if response.status_code == 200:
#     data = response.json()
#     # Extract the page ID from the API response
#     page_id = next(iter(data['query']['pages']))
#     # Check if the page exists and has links
#     if page_id != '-1' and 'links' in data['query']['pages'][page_id]:
#       # Retrieve the links from the API response
#       links = data['query']['pages'][page_id]['links']
#       # Extract the link titles and URLs
#       related_links = [{'url': f'https://en.wikipedia.org/wiki/{link["title"]}', 'title': link['title']} for link in links]
#       return related_links
#   return []

# function to check if the title consists of two words -> discrad a lot of entries for performance reasons
def filter_two_word_titles(links):
  filtered_links = []
  url_concat = ""
  for link in links:
    url = link['url']
    link['url'] = url.replace(' ', '_')
    title = link['title']
    words = title.split()
    if len(words) == 2:
      filtered_links.append(link)
  return filtered_links

#check if a given Wikipedia link corresponds to an entity with the "instance of" (P31) property set to "human" (Q5), indicating it represents a person
def is_person_page(link):
  # Extract the page title from the link
  title = link['title']
  # Query Wikidata API to check if the page corresponds to a person
  wikidata_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&sites=enwiki&titles={title}"
  response = requests.get(wikidata_url).json()
  # Check if the response contains any entities
  if 'entities' in response:
    entities = response['entities']
    # Check if there is an entity with P31 (instance of) set to Q5 (human)
    for entity_id, entity in entities.items():
      if 'claims' in entity and 'P31' in entity['claims']:
        for claim in entity['claims']['P31']:
          if claim['mainsnak']['datavalue']['value']['id'] == 'Q5':
            return True
  return False

#function that calls the is_perso_page() function for every link in the pre discraded list
def check_if_person(links):
  person_links= []
  for link in links:
    if is_person_page(link):
      person_links.append(link)
  return person_links

#function that selects 5 entries at random from a list of related people:
def select_random_entries(related_people_list, num_entries=5):
  random_entries = random.sample(related_people_list, num_entries)
  return random_entries

# takes a list of all the people and the list of category occurences where all the categories that were assigned to these wiki-pages
# are listed and ranked after how often they occur;
# output: a list where the person is the key and the entries show wich categories the entity shares with wich other entitities and how many they are
def get_people_dict(people_list, occurences_list):
  people_dict = {}
  for person in people_list:
    person_categories = []
    for occurence in occurences_list:
      if person in occurence[2]:
        person_categories.append((occurence[0], occurence[1], occurence[2]))
    people_dict[person] = person_categories
  return people_dict

def get_most_known_related_people(related_people_list):
  pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
  ord_dict = OrderedDict()
  link_list = []
  for item in related_people_list:
    link_list.append(item['url'])
  pruned_link_parts_list = extract_last_parts(link_list)
  concat_str_for_links = concatenate_elements(pruned_link_parts_list) #combine up to 10 of these links to create a request to pageview
  pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
  categories_with_pageviews =combine_dicts_from_links(pageviews_url_list) #now we called the links and retreieved the pageviews; saved them as a dictionary
  ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews) #now the list is ordered in ascending order
  ord_dict = ordered_categories_with_pageviews
  return ord_dict

def get_ordered_categories_of_most_related_people(most_related_peoples_list):
  ret = {}
  for k,v in most_related_peoples_list.items():
    related_people_ranked = dict(sorted(v.items(), key=lambda x: x[1], reverse=True))
    top_most_popular_people = dict(itertools.islice(related_people_ranked.items(), 5))#take the top 5 most known people from the list
    cat_ranking_related_person = get_categories(top_most_popular_people)
    cat_with_pv_person = get_pageviews_for_categories(cat_ranking_related_person)
    #categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_person, cat_with_pv_person)
    categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_related_person, cat_with_pv_person)
    new_ordered_dict_related_person = sorting_dict(categories_with_subs_and_pageviews_person)
    copy_new_ordered_dict_person_test = prune_and_ordered_dict(new_ordered_dict_related_person, 20)
    ordered_dict_related_person = sorting_dict(copy_new_ordered_dict_person_test)
    ret[key] = ordered_dict_related_person
  return ret

#get the links of all answer-entities via link creation of the key
def get_rel_pep(person_questions_dict):
  wiki_link = 'https://en.wikipedia.org/wiki/'
  ret = {}
  for key, value in person_questions_dict.items():
    modified_text = key.replace(' ', '_')
    link = f"{wiki_link}/{modified_text}"
    related_articles = get_related_links(link)
    filtered_links = filter_two_word_titles(related_articles)
    related_people_list = check_if_person(filtered_links)
    ret[key] = related_people_list
  return ret

#get the related people with the categories
def get_related_with_categories(person_questions_dict):
  ret = {}
  cat_ranking_person = get_categories(person_questions_dict)
  cat_with_pv_person = get_pageviews_for_categories(cat_ranking_person)
  categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_person, cat_with_pv_person)
  new_ordered_dict_person = sorting_dict(categories_with_subs_and_pageviews_person)
  for key,value in new_ordered_dict_person.items():
    ret[key] = value
  return ret


# def order_dict_by_second_entry(data):
#     ordered_data = {}
#     intermediate_dict = {}
#     for a,b in data.items():
#       intermediate_ordere = {}
#       for key, value in b.items():
#         inter_list = []
#         for cat in value.items():
#           inter_list.append((cat[0], int(cat[1].replace(",", ""))))
#         intermediate_ordere[key] = sorted(inter_list, key=lambda x: x[1], reverse=True)

#       intermediate_dict[a] = intermediate_ordere
#     return intermediate_dict


"""
Converts a date string in the format '+YYYY-MM-DDT00:00:00Z' to 'DD.MM.YYYY' format,
adds it to the list, and returns the modified list.
Args: date_list (list): A list containing a date string in the format '+YYYY-MM-DDT00:00:00Z'.
Returns: list: A modified list with the date string converted to 'DD.MM.YYYY' format.
"""
def convert_date(date_list):
  formatted_list = []
  for date_str in date_list:
    # Extracting year, month, and day from the date string
    year = date_str[1:5]
    month = date_str[6:8]
    day = date_str[9:11]
    # Creating the new formatted date string
    formatted_date = f"{day}.{month}.{year}"
    # Adding the formatted date to the new list
    formatted_list.append(formatted_date)
  return formatted_list

"""
Retrieves properties of a person from Wikidata based on the person's ID.
Args: person_id (str): The ID of the person in Wikidata.
Returns: dict: A dictionary containing the person's properties.
"""
def get_person_properties(person_id, list_of_properties, person_questions_dict):
  excluded_properties = ["P18", "P109", "P989", "P948", "P214"]  # Property IDs to exclude
  url = f"https://www.wikidata.org/w/api.php?action=wbgetclaims&entity={person_id}&format=json"
  response = requests.get(url)
  data = response.json()
  person_names = []
  for answer, question in person_questions_dict.items():
    person_names.append(answer)
  ret = {}
  inter = {}
  properties = {}
  claims = data.get('claims')
  if claims:
    for claim_property_id, claim_list in claims.items():
      for claim in claim_list:
        property_id = claim.get('mainsnak', {}).get('property')
        if property_id in excluded_properties:
          continue
        property_value = claim.get('mainsnak', {}).get('datavalue', {}).get('value')
        if property_id and property_value:
          property_label = get_property_label(property_id)
          if isinstance(property_value, dict) and 'id' in property_value:
            property_value = get_entity_label(property_value['id'])
          if property_label in properties:
            # Append values for properties with multiple claims
            properties[property_label].append(property_value)
          else:
            properties[property_label] = [property_value]
  for property_label, property_values in properties.items():
    if property_label in list_of_properties:
      if 'date' in property_label:
        a = convert_date([value['time'] for value in property_values])
        inter[property_label] = a
      elif 'height' in property_label:
        inter[property_label] = [value['amount'] for value in property_values]
      elif 'social media followers' in property_label:
        inter[property_label] = [value['amount'] for value in property_values]
      elif 'name in native language' in property_label:
        inter[property_label] = [value['text'] for value in property_values]
      elif 'nickname' in property_label:
        inter[property_label] = [value['text'] for value in property_values]
      elif 'significant event' in property_label:
        a = property_values
        for event in property_values:
          for name in person_names:
            if name in event:
              a.remove(event)
        inter[property_label] = a
      else:
        inter[property_label] = property_values
  for property_label, property_values in inter.items():
    d = inter[property_label]
    ret[property_label] = d[:3]
  return ret

"""
Retrieves the human-readable label of an entity from Wikidata.
Args: entity_id (str): The ID of the entity in Wikidata.
Returns: str: The human-readable label of the entity.
"""
def get_entity_label(entity_id):
  url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&format=json"
  response = requests.get(url)
  data = response.json()
  label = data.get('entities', {}).get(entity_id, {}).get('labels', {}).get('en', {}).get('value')
  return label

"""
Retrieves the human-readable label of a property from Wikidata.
Args: property_id (str): The ID of the property in Wikidata.
Returns: str: The human-readable label of the property.
"""
def get_property_label(property_id):
  url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={property_id}&format=json"
  response = requests.get(url)
  data = response.json()
  label = data.get('entities', {}).get(property_id, {}).get('labels', {}).get('en', {}).get('value')
  return label

"""
Retrieves the Wikipedia identifiers for a list of person names.
Args: person_names (list): A list of person names.
Returns: dict: A dictionary mapping person names to their Wikipedia identifiers.
"""
def get_wikipedia_identifiers(person_names, base_url = "https://en.wikipedia.org/w/api.php"):
  # base_url = "https://en.wikipedia.org/w/api.php"
  identifiers = {}
  for person_name in person_names:
    params = {
        "action": "query",
        "format": "json",
        "titles": person_name,
        "prop": "pageprops",
        "ppprop": "wikibase_item"
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    pages = data.get("query", {}).get("pages")
    if pages:
      for page in pages.values():
        if "pageprops" in page:
          wikipedia_id = page["pageprops"].get("wikibase_item")
          if wikipedia_id:
            identifiers[person_name] = wikipedia_id
          else:
            identifiers[person_name] = None
        else:
          print('else')
          base_url = "https://de.wikipedia.org/w/api.php"
          params = {
              "action": "query",
              "format": "json",
              "titles": person_name,
              "prop": "pageprops",
              "ppprop": "wikibase_item"
          }
          response = requests.get(base_url, params=params)
          data = response.json()
          pages = data.get("query", {}).get("pages")
          if pages:
            for page in pages.values():
              if "pageprops" in page:
                wikipedia_id = page["pageprops"].get("wikibase_item")
                if wikipedia_id:
                  identifiers[person_name] = wikipedia_id
                else:
                  identifiers[person_name] = None
  return identifiers

"""
Function that retrieves the related/popular people of the answer-entities;
Args:     the answer-entity name
Returns:  a list where each entry of the list is a dictionary; the keys and values are the (title and url) of the related people
"""
def get_related_people_from_person_name(person_name):
  wiki_link = 'https://en.wikipedia.org/wiki'
  related_people_list = []
  modified_text = person_name.replace(' ', '_') #replace spaces with underscores in the name to use it in link
  link = f"{wiki_link}/{modified_text}"
  related_articles = get_related_links(link)
  # related_articles = get_all_related_links(link)
  filtered_links = filter_two_word_titles(related_articles)
  if len(filtered_links) < 5:
    related_articles = get_all_related_links(link)
    filtered_links = filter_two_word_titles(related_articles)
  related_people_list = check_if_person(filtered_links)
  return related_people_list
"""
Function that gets the pageviews of up to 10 links at a time;
Args:     dictionary where the keys are the answer-entities and the value is a link_list
Returns:  dictionary where the keys are the answer-entities and the value is a list with the links and pageviews
"""
def get_pageviews_from_links(link_dict):
  pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
  return_dict = {}
  for key,value in link_dict.items():
    link_list = value
    pruned_link_parts_list = extract_last_parts(link_list)
    concat_str_for_links = concatenate_elements(pruned_link_parts_list)             #combine up to 10 of these links to create a request to pageview
    pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
    categories_with_pageviews =combine_dicts_from_links(pageviews_url_list)         #now we called the links and retreieved the pageviews; saved them as a dictionary
    ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews)   #now the list is ordered in ascending order
    return_dict[key] = ordered_categories_with_pageviews
  return return_dict

"""
Function that takes the 5 most popular related-people from the related_people_pageviews_dict and
retrieves the corresponding wiki-categories with the their pageviews;
Args:     dictionary where the keys are the answer-entities and the value is a dict of related people with their pageviews
Returns:  dictionary where the keys are the answer-entities and the value is
  a dict where the keys are the related-people and the valus are tupples with the 10 most popular categories they appear and with the pageviews of that category
"""
# def get_categories_of_people_list(people_list, limit=5):
#   return_dict = {}
#   for key,value in people_list.items():
#     related_people_orderd = dict(sorted(value.items(), key=lambda x: x[1], reverse=True))   #order the dict after the pageviews in descending order
#     top_most_popular_people = dict(itertools.islice(related_people_orderd.items(), 5))      #take the top 5 most known people from the list
#     if len(related_people_orderd) == 0 or  len(top_most_popular_people) == 0:
#       continue
#     categories_of_related_people = get_categories(top_most_popular_people)

#     categories_with_pageviews_person = get_pageviews_for_categories(categories_of_related_people)
#     categories_with_subs_and_pageviews_person = get_dict_for_every_location(categories_of_related_people, categories_with_pageviews_person)
#     new_ordered_dict_related_person = sorting_dict(categories_with_subs_and_pageviews_person)
#     copy_new_ordered_dict_person_test = prune_and_ordered_dict(new_ordered_dict_related_person, 10)
#     ordered_dict_related_person = sorting_dict(copy_new_ordered_dict_person_test)
#     return_dict[key] = ordered_dict_related_person
#   return return_dict



def test_occu_func(person_answers_dict, related_people_orderd, top_most_popular_people):
  pprint.pprint(person_answers_dict)
  pprint.pprint(related_people_orderd)
  pprint.pprint(top_most_popular_people)

  people_occupations = get_occupation_from_wikidata(person_answers_dict)
  top_most_popular_people_occupations = get_occupation_from_wikidata(top_most_popular_people)
  # correct_occu = {}
  ret = {}
  for key,value in person_answers_dict.items():
    for ans, occu in people_occupations.items():
      if key == ans:
        desired_occupation = people_occupations[key]
        # has_occu = False
        pers_with_different_occu = {}
        for pers, p_occu in top_most_popular_people_occupations.items():
          if desired_occupation in p_occu:
            print(pers, desired_occupation, p_occu)# has_occu = True
          else: 
            pers_with_different_occu[pers] = p_occu
        print('pers_with_different_occu', pers_with_different_occu)
        if len(pers_with_different_occu) == 5:
          for pn, pvs in related_people_orderd.items():
            if pn not in pers_with_different_occu:
              try:
                pers_occu = get_occupation_from_wikidata({pn : pvs})
              
                if pers_occu[pn] == desired_occupation:
                  top_most_popular_people[pn] = pvs
                  # correct_occu[pn] = pvs
                  print(pers, pers_occu[pn], desired_occupation)
                  break
              except Exception as e:
                continue
        #   for pn, pvs in top_most_popular_people.items():
        #     for a,b in pers_with_different_occu.items():
        # else:
          ret = top_most_popular_people
  print('top_most_popular_people')
  pprint.pprint(top_most_popular_people)
  
  return top_most_popular_people


def get_categories_of_people_list(people_list, person_answers_dict,limit=5):
  return_dict = {}
  newdic = {}
  for a,b in people_list.items():
    innerDic = OrderedDict()
    if b:
      for c,d in b.items():
        try:
          innerDic[c] = int(d.replace(',', ''))
        except Exception as e:
          print("get_categories_of_people_list", e)

      newdic[a] = dict(sorted(innerDic.items(), key = lambda x: x[1], reverse=True))
    else:
      # print("HUPS")
      newdic[a] = {}

  for key,value in newdic.items():
    related_people_orderd = dict(sorted(value.items(), key=lambda x: x[1], reverse=True))   #order the dict after the pageviews in descending order
    pprint.pprint(related_people_orderd)
    #add that certain categories cant be part of the list FOR PERFORMANCE REASONS

    top_most_popular_people = dict(itertools.islice(related_people_orderd.items(), 5))      #take the top 5 most known people from the list
    pprint.pprint(top_most_popular_people)

    # top_most_popular_people = test_occu_func(person_answers_dict, related_people_orderd, top_most_popular_people)
    ttop_most_popular_people = test_occu_func(person_answers_dict, related_people_orderd, top_most_popular_people)


    if len(related_people_orderd) == 0 or  len(ttop_most_popular_people) == 0:
      return_dict[key] = {}
      continue
    categories_of_related_people = get_categories(ttop_most_popular_people)
    categories_with_pageviews_person = get_pageviews_for_categories(categories_of_related_people)
    categories_with_subs_and_pageviews_person = get_dict_for_every_location(categories_of_related_people, categories_with_pageviews_person)
    pprint.pprint(categories_with_subs_and_pageviews_person, sort_dicts=False)
    copy_new_ordered_dict_person_test = prune_and_ordered_dict(categories_with_subs_and_pageviews_person, 10)
    pprint.pprint(copy_new_ordered_dict_person_test, sort_dicts=False)
    return_dict[key] = copy_new_ordered_dict_person_test
  return_dict = order_dict_by_second_entry(return_dict)
  return return_dict


# def get_categories_of_people_list(people_list, limit=5):
#   return_dict = {}

#   newdic = {}
#   for a,b in people_list.items():
#     innerDic = OrderedDict()
#     for c,d in b.items():
#       innerDic[c] = int(d.replace(',', ''))
#   newdic[a] = dict(sorted(innerDic.items(), key = lambda x: x[1], reverse=True))

#   for key,value in newdic.items():
#     related_people_orderd = dict(sorted(value.items(), key=lambda x: x[1], reverse=True))   #order the dict after the pageviews in descending order
#     # pprint.pprint(related_people_orderd)

#     top_most_popular_people = dict(itertools.islice(related_people_orderd.items(), 5))      #take the top 5 most known people from the list
#     # pprint.pprint(top_most_popular_people)

#     if len(related_people_orderd) == 0 or  len(top_most_popular_people) == 0:
#       continue
#     categories_of_related_people = get_categories(top_most_popular_people)
#     categories_with_pageviews_person = get_pageviews_for_categories(categories_of_related_people)
#     categories_with_subs_and_pageviews_person = get_dict_for_every_location(categories_of_related_people, categories_with_pageviews_person)
#     copy_new_ordered_dict_person_test = prune_and_ordered_dict(categories_with_subs_and_pageviews_person, 10)
#     pprint.pprint(copy_new_ordered_dict_person_test, sort_dicts=False)
#     return_dict[key] = copy_new_ordered_dict_person_test
#   return_dict = order_dict_by_second_entry(return_dict)
#   return return_dict

"""
Function that is created with help of reusable function from above
Args:     person_question_dict with all people with their questions
Returns:  dictionary where the keys are the answer-entities and the value is a OrderedDict of all categories with pageviews
"""
# def get_categories_with_pv_answerEntities(person_questions_dict):
#   cat_ranking_person = get_categories(person_questions_dict)
#   cat_with_pv_person = get_pageviews_for_categories(cat_ranking_person)
#   categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_person, cat_with_pv_person)
#   new_ordered_dict_person = sorting_dict(categories_with_subs_and_pageviews_person)
#   return new_ordered_dict_person
def get_categories_with_pv_answerEntities(person_questions_dict):
  cat_ranking_person = get_categories(person_questions_dict)
  cat_with_pv_person = get_pageviews_for_categories(cat_ranking_person)
  categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_person, cat_with_pv_person)
  # new_ordered_dict_person = sorting_dict(categories_with_subs_and_pageviews_person)

  intermediate_dict = {}
  intermediate_ordere = {}
  for a,b in categories_with_subs_and_pageviews_person.items():
    inter_list = []
    for key in b.items():
      inter_list.append((key[0], int(key[1].replace(",", ""))))
    intermediate_ordere[a] = OrderedDict(sorted(inter_list, key=lambda x: x[1], reverse=True))

  bad_categories_list = ['Living_people', 'Living people', '_births', 'births', '_deaths', 'deaths', 'Good_articles', 'Good articles', 'Members','19th', 'Capitals in Europe', 'state capitals']


  for k,v in intermediate_ordere.items():
    inter_list = []
    for a,b in v.items():
      contains_word = False 
      for bad_word in bad_categories_list:
        if bad_word in a:
          contains_word = True
      if contains_word == True: 
        print(a,b)
      if contains_word == False: 
        inter_list.append((a,b))
    intermediate_ordere[k] = OrderedDict(sorted(inter_list, key=lambda x: x[1], reverse=True))

  return intermediate_ordere




def order_dict_by_second_entry(data):
    ordered_data = {}
    intermediate_dict = {}
    for a,b in data.items():
      intermediate_ordere = {}
      for key, value in b.items():
        inter_list = []
        for cat in value.items():
          inter_list.append((cat[0], int(cat[1].replace(",", ""))))
        intermediate_ordere[key] = sorted(inter_list, key=lambda x: x[1], reverse=True)

      intermediate_dict[a] = intermediate_ordere
    return intermediate_dict












"""
Counts the occurrences of categories (links) in the input dictionary.
Args: data (dict): A dictionary containing category links as keys and tuples as values.
Returns: dict: A new dictionary where the keys are the category links and the values are
  the corresponding tuples of the category with a middle value indicating how
  often the link/category appeared in the other keys.
"""
# def count_categories(related_people_with_categories, answer_entities_with_categories):
#   category_appereances = {}
#   for answerEntityKey, aeCategory in answer_entities_with_categories.items():
#     inner_dict = {}
#     for answerKey, relatedDict in related_people_with_categories.items():
#       if answerEntityKey == answerKey:
#         for catLink, tupl in aeCategory.items():
#           people_list = []
#           for relatedPersonKey, catWithPvs in relatedDict.items():
#             for relatedLink, relatedTupl in  catWithPvs.items():
#               if catLink == relatedLink:
#                 rel_pers_str = str(relatedPersonKey)
#                 if rel_pers_str not in people_list and catLink == relatedLink:
#                   people_list.append(rel_pers_str)
#                 inner_dict[relatedLink] = (len(people_list),relatedTupl, people_list)
#     category_appereances[answerEntityKey] = inner_dict
#   for k,v in category_appereances.items():
#     if len(v) == 0:
#       for answerEntityKey, aeCategory in answer_entities_with_categories.items():
#         if k == answerEntityKey:
#           inner_dict={}
#           for a,b in aeCategory.items():
#             inner_dict[a] = (0, b, [])
#           category_appereances[k] = inner_dict
#   return category_appereances
"""
Counts the occurrences of categories (links) in the input dictionary.
Args: data (dict): A dictionary containing category links as keys and tuples as values.
Returns: dict: A new dictionary where the keys are the category links and the values are
  the corresponding tuples of the category with a middle value indicating how
  often the link/category appeared in the other keys.
"""
def count_categories(related_people_with_categories, answer_entities_with_categories):

  category_appereances = {}
  for answerEntityKey, aeCategory in answer_entities_with_categories.items():
    inner_dict = {}
    for answerKey, relatedDict in related_people_with_categories.items():
      if answerEntityKey == answerKey:
        for cat, pvs in aeCategory.items():
          people_list = []
          # print("cat: "+ str(cat))
          for relatedPersonKey, catWithPvs in relatedDict.items():
            for categ in catWithPvs:
              if categ[0] == cat:
                print(cat, categ, answerEntityKey, relatedPersonKey)
                rel_pers_str = str(relatedPersonKey)
                if rel_pers_str not in people_list and categ[0] == cat:
                  people_list.append(rel_pers_str)
                inner_dict[cat] = (len(people_list),categ, people_list)

    category_appereances[answerEntityKey] = inner_dict

    for k,v in category_appereances.items():
      if len(v) == 0:
        for answerEntityKey, aeCategory in answer_entities_with_categories.items():
          if k == answerEntityKey:
            inner_dict={}
            for a,b in aeCategory.items():
              inner_dict[a] = (0, b, [])
            category_appereances[k] = inner_dict

  return category_appereances





"""
Calculates the Intersection over Union between the answer-entity and each of the related-person entries seperately
Args: data (dict): A dictionary containing the answer-entity with the corresponding related-people and their most popular categories that they share with ther answer-entity
Returns: dict: A dict where the value is a list of tuple like this: ('Max Verstappen', 'Charles Leclerc', 5, 20, 0.25) (person_a, person_b, num_shared_categories, num_total_categories, num_shared_categories/num_total_categories)
"""
def calculate_IoU_from_countedCategoryDict(counted_category_apperances):
  #first we recover the list of people that are related to answer-entity
  p_dict = {}
  for key,value in counted_category_apperances.items():
    person_list = []
    for link, f_tup in value.items():
      num= f_tup[0]
      tup= f_tup[1]
      p_lst = f_tup[2]
      for person in p_lst:
        if person not in person_list:
          person_list.append(person)
    p_dict[key] = person_list
  iou_between_person_list = {}
  #now calculate the IoU
  for key_cat,value_cat in counted_category_apperances.items():
    for key,value in p_dict.items():
      if key == key_cat:
        inter_list = {}
        for person in value:
          p_count = 0
          for link, f_tup in value_cat.items():
            p_lst = f_tup[2]
            if person in p_lst:
              p_count += 1
          inter_list[person] = p_count
      iou_between_person_list[key_cat] = inter_list
  IoU_dict = {}
  for key, value in iou_between_person_list.items():
    IoU_list = []
    for person, number in value.items():
      num_total_categs = 20
      IoU_list.append((person,number,num_total_categs, number/num_total_categs))
    if IoU_list:
      IoU_dict[key] = IoU_list
    else:
      IoU_dict[key] = [('Placeholder', 0, 20, 1)]
  return IoU_dict

"""
Calculates the avg_diversity_from_IoU
Args:
Returns:
"""
def calculate_avg_diversity_from_IoU(intersection_between_people_with_ae):
  avg_diversity_dict = {}
  for key,value in intersection_between_people_with_ae.items():
    diversity_sum = 0
    pairwise_comparisons = 0
    for item in value:
      all_categs = item[2]
      IoU = item[1]
      diversity_sum += (all_categs - IoU)
      pairwise_comparisons += 1
    try:
      avg_diversity_dict[key] = (diversity_sum / pairwise_comparisons)
    except Exception as e:
      avg_diversity_dict[key] = 0
  return avg_diversity_dict

"""
Calculates the categories score from the category diversity (calculated by calculate_avg_diversity_from_IoU() ) and the cat_popularity (=pageviews)
Args:
Returns:
"""
# def calculate_categories_score(counted_category_apperances, avg_diversity_from_IoU):
#   categories_scores_dict = {}
#   for key,value in counted_category_apperances.items():
#     inter_dict={}
#     for item in value.items():
#       link = item[0]
#       cat_popularity = item[1][1]
#       for name, cat_div in avg_diversity_from_IoU.items():
#         if name == key:
#           inter_dict[link] = cat_popularity * cat_div
#     categories_scores_dict[key] = inter_dict
#   ordered_dicter = {}
#   ordered_scores ={}
#   for k,v in categories_scores_dict.items():
#     ordered_scores[k] = OrderedDict(v)
#   for k,v in ordered_scores.items():
#     ordered_dicter[k] = OrderedDict(sorted(v.items(), key=lambda x: x[1], reverse=True))
#   #modify the scores to give some categories a lower one
#   for key,value in ordered_dicter.items():
#     for link, score in value.items():
#       if '20th' in link or '21st' in link:
#         value[link]  = score / 4
#   return ordered_dicter

template_sentence_person_list = ['The person you are looking for is/was occupied as 0 and a member of the category 1.']

#takes the categories scores dict and chooses the category with the highest score
def create_hint_sentences_unexCategs(categories_scores_dict, person_answers_dict):
  people_occupations = get_occupation_from_wikidata(person_answers_dict)
  most_unexpected_categories_dict = {}
  hint_sentence_unexCateg_dict = {}
  # print('ok')
  try:
    # print("WTF")
    for key,value in categories_scores_dict.items():
      if value:
        categories_scores_dict[key] = OrderedDict(sorted(value.items(), key=lambda x: x[1], reverse=True))
        most_unexpected_categories_dict[key] = (next(iter(value.items())), people_occupations[key])
      else: 
        most_unexpected_categories_dict[key] = OrderedDict()
    occu_str = 'television_presenter'
    # print('most_unexpected_categories_dict')
    # pprint.pprint(most_unexpected_categories_dict)
    for key,value in most_unexpected_categories_dict.items():
      combined_string = ""
      hint_sentence_unexCateg_dict[key] = []
      try:
        # if people_occupations[key] == 'Racing':
        #   occu_str = people_occupations[key]
        # else:
        #   occu_str = people_occupations[key]
        if len(people_occupations[key]) > 1:
          combined_string = ', '.join(people_occupations[key])  # Combine multiple entries with a comma and space
        elif len(entries) == 1:
          combined_string = people_occupations[key][0]
        else:
          combined_string = 'television_presenter'

      except Exception as e:
        pass
      if most_unexpected_categories_dict[key]:
        for sentence in template_sentence_person_list:
          hint_sentence_unexCateg_dict[key].append( sentence.replace('0', combined_string).replace('1', get_category_title(most_unexpected_categories_dict[key][0][0]).split(':')[-1].replace('_', ' ') ))
      else:
        hint_sentence_unexCateg_dict[key] = []

  except Exception as e: print("create_hint_sentences_unexCategs", e)
  return hint_sentence_unexCateg_dict

def get_person_hints_unexpected_categories(person_answers_dict):
  related_people_dict = {}
  related_people_link_dict= {}
  related_people_pageviews_dict = {}
  most_popular_related_people_with_categories = {}
  #time saving for first part (related people recovery) 2m
  for key,value in person_answers_dict.items():
    related_people_dict[key] = get_related_people_from_person_name(key)
  #time saving for second part (related peoples with pageviews and ordering) - 16m (6-7m)
  # for key,value in related_people_dict.items():
  #   inter_link_list = []
  #   for item in value:
  #     inter_link_list.append(item['url'])
  #   related_people_link_dict[key] = inter_link_list
  #   related_people_pageviews_dict = get_pageviews_from_links(related_people_link_dict)

  # pprint.pprint(related_people_dict)
  related_people_pageviews_dict = get_pageviews_from_linkssssssss(related_people_dict)
  pprint.pprint(related_people_pageviews_dict)
  #time saving for third part (related peoples categories recovery and ordering) - 43m+ (14m-24m)
  most_popular_related_people_with_categories = get_categories_of_people_list(related_people_pageviews_dict, person_answers_dict)

  #time saving for third part retrieves the categories of the answer-entities - 9m+ (6m)
  answer_entities_with_categories = get_categories_with_pv_answerEntities(person_answers_dict)
  #time saving for fourth part counts the categories of the answer-entities - 3s
  counted_category_apperances = count_categories(most_popular_related_people_with_categories, answer_entities_with_categories)
  #just for the ordering of the inner list
  ordered_data = {}
  for key,value in counted_category_apperances.items():
    tmp = OrderedDict(value)
    ordered_data[key] = OrderedDict(sorted(tmp.items(), key=lambda x: x[1][0], reverse=True) )
  counted_category_apperances = ordered_data


  #1. calculate the IoU between max and every other person - (M,C) = 5/20; (M,L) = 2/20; (M,D) = 2/20; (M,A) = 2/20; (M,F) = 2/20;
  intersection_between_people_with_ae = calculate_IoU_from_countedCategoryDict(counted_category_apperances)
  #2. calculate the average diversity between the 6 drivers - (20-5) + (20-2) + (20-2) + (20-2) + (20-2) = 87; (#avg_diversity/#pairwise_comparison) = 87/5 = 17,4
  avg_diversity_from_IoU = calculate_avg_diversity_from_IoU(intersection_between_people_with_ae)
  #3. calculate a type of categoreis_score - categories_score = cat_diversity * cat_popularity(pvs)
  categories_scores_dict = calculate_categories_score(counted_category_apperances, avg_diversity_from_IoU)
  for key,value in categories_scores_dict.items():
    categories_scores_dict[key] = OrderedDict(sorted(value.items(), key=lambda x: x[1], reverse=True))
  mucd = create_hint_sentences_unexCategs(categories_scores_dict, person_answers_dict)
  inter = {}
  for key, value in mucd.items():
    for answer,question in person_answers_dict.items():
      if key == answer:
        # sim_score = get_similarity_score(question,value[0])
        if value:
          sim_score = calculate_similarity(question,answer,value[0],sim_score_priority_words)
          inter[key]  = {value[0] : sim_score}
        else:
          inter[key]  = {}
        # inter[key]['question'] = question
  return inter

"""### Functions for the unexpected-predicate approach:"""


"""
Retrieves the Wikipedia identifiers for a list of person names.
Args: None
Returns: dict: A dictionary mapping person names to their Wikipedia identifiers.
"""
def get_properties_predicates_hints(person_answers_dict):
  person_names = []
  for answer, question in person_answers_dict.items():
    person_names.append(answer)
  identifiers = get_wikipedia_identifiers(person_names)
  properties_person_name_dict = {}
  for name, pid in identifiers.items():
    inter = get_person_properties(pid, list_of_properties, person_answers_dict)
    if inter:
      properties_person_name_dict[name] = inter
    else:
      properties_person_name_dict[name] = ''
  return properties_person_name_dict

"""
Creates hint sentences based on properties of a person and blank sentences.
Args: properties_person_name_dict (dict): A dictionary containing properties of a person mapped to their corresponding values.
      properties_blank_sentences (dict): A dictionary containing blank sentences with placeholders.
Returns: dict: A dictionary containing hint sentences for each person's properties.
"""
def create_hint_sentences_predicates(properties_person_name_dict, properties_blank_sentences, person_answers_dict):
  person_names = []
  ques = {}
  for answer, question in person_answers_dict.items():
    person_names.append(answer)
    ques[answer] = question
  hint_sentence_dict = {}
  for pers_name, value in properties_person_name_dict.items():
    properties_sentences_dict = {}
    for proper, entries in value.items():
      if proper in properties_blank_sentences:
        if type(entries) != dict:
          if len(entries) >= 3: #when we want to list 3 items
            first_two = entries[:2]
            intermediate_str = ', '.join(first_two)
            intermediate_str = intermediate_str + ' and '+ str(entries[2])
          elif len(entries) == 2: #when we want to list 2 items
            intermediate_str = str(entries[0]) + ' and '+ str(entries[1])
          elif len(entries) == 1: #when we want to list 1 item
            intermediate_str = entries[0]
          properties_sentences_dict[proper] = properties_blank_sentences[proper].replace('0', str(intermediate_str))
    if 'child' in value:
      properties_sentences_dict['child'] = properties_blank_sentences['child'].replace('/', str(len(value['child'])))
    if 'sibling' in value:
      properties_sentences_dict['sibling'] = properties_blank_sentences['sibling'].replace('/', str(len(value['sibling'])))
    if 'child' in value and 'sibling' in value:
      properties_sentences_dict['child + sibling'] = properties_blank_sentences['child + sibling'].replace('/', str(len(value['child']))).replace('*', str(len(value['sibling'])))
    if 'date of birth' in value and 'place of birth' in value:
      properties_sentences_dict['date of birth + place of birth'] = properties_blank_sentences['date of birth + place of birth'].replace('/', str(value['date of birth'][0])).replace('*', str(value['place of birth'][0]))
    if 'date of birth' in value and 'place of birth' in value and 'date of death' in value and 'place of death' in value:
      properties_sentences_dict['date of birth + place of birth + date of death + place of death'] = properties_blank_sentences['date of birth + place of birth + date of death + place of death'].replace('/', str(value['date of birth'][0])).replace('*', str(value['place of birth'][0])).replace('-', str(value['date of death'][0])).replace('+', str(value['place of death'][0]))
    
    inter = {}
    for k,v in properties_sentences_dict.items():
      if '*' not in v:
        inter[k] = v

    
    # properties_sentences_dict = remove_sentences_with_asterisk(properties_sentences_dict)
    hint_sentence_dict[pers_name] = inter
    for a,b in ques.items():
      if a == pers_name:
        hint_sentence_dict[a]['question'] = b
  return hint_sentence_dict

def get_person_hints_unexpected_predicates(person_answers_dict):
  properties_person_name_dict = get_properties_predicates_hints(person_answers_dict)
  hint_sentences_predicates = create_hint_sentences_predicates(properties_person_name_dict, properties_blank_sentences, person_answers_dict)
  for key, value in hint_sentences_predicates.items():
    # if value:
    for predicate, sentence in value.items():
      for answer,question in person_answers_dict.items():
        if key == answer:
          # sim_score = get_similarity_score(question,sentence)
          sim_score = calculate_similarity(question,answer,sentence,sim_score_priority_words)
          hint_sentences_predicates[key][predicate] = {sentence : sim_score}
          hint_sentences_predicates[key]['question'] = question
  return hint_sentences_predicates

#years
"""
Given a URL, this function opens the url and retrieves the information stored in a table.
"""
def get_table_info_requests(url):
  headers = []
  data = []
  response = requests.get(url)
  soup = BeautifulSoup(response.content, 'html.parser')
  table = soup.find('table')
  rows = table.find_all('tr')
  headers = [header.text.strip() for header in rows[0].find_all('th')]
  data = []
  for row in rows[1:]:
    data.append([cell.text.strip() for cell in row.find_all('td')])
  return (headers, data)





"""
Given a Wikipedia URL, and a section of this article, returns an array of dictionaries containing the href, title, and description of each link on that section of the page.
"""
def get_links_in_section(wikipedia_url, section_heading):
  response = requests.get(wikipedia_url)
  soup = BeautifulSoup(response.content, 'html.parser')
  section = soup.find('span', {'id': section_heading})
  if section is None:
    return None
  section_content = section.parent.find_next_sibling('ul')
  if section_content is None:
    return None
  links = []
  for item in section_content.find_all('li'):
    link = item.find('a')
    if link is not None and link.has_attr('href') and link['href'].startswith('/wiki/'):
      title = link.get('title', '')
      description = item.text.strip()
      url = f"https://en.wikipedia.org{link['href']}"
      links.append({'title': title, 'description': description, 'url': url})
  return links

"""
Given a Wikipedia URL, and a section of this article, returns an array of dictionaries containing the href, title, and description of each link  with its sublinks as well.
"""
def get_links_in_section_with_sublinks(wikipedia_url, section_title):
  response = requests.get(wikipedia_url)
  if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    section_heading = soup.find('span', {'id': section_title})
    if section_heading is None:
      return None
    section = section_heading.parent
    section_content = section.find_next_sibling('ul')
    if section_content is None:
      return None
    links = []
    for item in section_content.find_all('li'):
      link = item.find('a')
      if link is not None:
        link_title = link.get('title')
        link_url = 'https://en.wikipedia.org' + link.get('href')
        link_description = item.text.replace(link_title, '').strip()
        links.append({'title': link_title, 'url': link_url, 'description': link_description})
        for sublink in item.find_all('a', href=True, recursive=False):
          sublink_title = sublink.get('title')
          sublink_url = 'https://en.wikipedia.org' + sublink.get('href')
          sublink_description = sublink.parent.text.replace(sublink_title, '').replace(link_title, '').strip()
          links.append({'title': sublink_title, 'url': sublink_url, 'description': sublink_description})
    return links
  else:
    return None

"""
Returns all backlinks located in the thumbcaption section
"""
def get_wikipedia_backlinks_thumbcaption(url):
  # Load the Wikipedia page HTML
  page_html = requests.get(url).text
  soup = BeautifulSoup(page_html, 'html.parser')
  # Find the image caption on the page
  caption = soup.find('div', class_='thumbcaption')
  backlink_sentences = {}
  backlinks = []
  if caption is not None:
    sentences = caption.text.strip().split('.')
    for sentence in sentences:
      links = caption.find_all('a', href=True, string=re.compile(sentence))
      if len(links) > 0:
        backlinks = []
        for link in links:
          backlink_url = 'https://en.wikipedia.org' + link['href']
          backlink_title = link.get('title', '')
          backlinks.append((backlink_url, backlink_title))
        backlink_sentences[sentence] = backlinks
  return backlink_sentences

"""
This function correctly prunes the links to only include the string after the last / character
"""
def prune_links(links):
  pruned_links = []
  for url, title in links:
    pruned_url = url.split('/')[-1]
    pruned_links.append((pruned_url, title))
  return pruned_links

"""
This function first initializes an empty list combined_list that will hold the combined strings. Then, it uses a for loop to iterate through the input list in increments of 10 tuples at a time.
For each sub-list of up to 10 tuples, it uses the list comprehension and join() method as before to combine the first elements of each tuple into a single string separated by '|'.
Finally, the function appends each combined string to the combined_list and returns it at the end.
"""
def combine_first_elements(my_list):
  combined_list = []
  num_tuples = len(my_list)
  for i in range(0, num_tuples, 10):
    sub_list = my_list[i:i+10]
    combined_str = '|'.join([tup[0] for tup in sub_list])
    combined_list.append(combined_str)
  return combined_list

"""
This function first initializes an empty list url_list that will hold the modified URLs. Then, it uses a for loop to iterate through each combined string in the input list.
For each combined string, it concatenates the base URL with a forward slash and the combined string, and appends the resulting URL to the url_list. Finally, the function returns the url_list at the end.
"""
def add_combined_strings_to_url(base_url, combined_strings):
  url_list = []
  for string in combined_strings:
    url_list.append(base_url + '/' + string)
  return url_list

"""
This will output a list of all the sentences in the thumbcaption, split by ';'.
"""
def get_thumbcaption_sentences(url):
  # Get the HTML content of the page
  page = requests.get(url)
  soup = BeautifulSoup(page.content, 'html.parser')
  # Find the thumbcaption element
  thumbcaption = soup.find('div', class_='thumbcaption')
  # Get all the sentences in the thumbcaption
  try:
    sentences = thumbcaption.text.split('; ')
  except Exception as e:
    print(e)
  return sentences

"""
This function converts a list into a dict in the way that is needed.
"""
def list_to_dict(lst):
  result = {}
  for sublist in lst:
    if len(sublist) >= 4:
      key = sublist[1]
      value = int(sublist[3].replace(',', ''))
      result[key] = value
  return result

"""
This function takes a list of links, opens each link to get the data, discards the header and converts the data into a dictionary using the list_to_dict() function,
and then updates a combined dictionary with the resulting dictionary from each link. Finally, it returns the combined dictionary.
"""
def combine_dicts_from_links(link_list):
  combined_dict = {}
  for link in link_list:
    header, data = get_table_info(link)
    link_dict = list_to_dict(data)
    combined_dict.update(link_dict)
  return combined_dict

"""
This sorts the items in the dictionary based on the integer value of the second element in each key-value tuple (i.e. item[1]), in descending order (reverse=True).
"""
def sort_dict_desc(d):
  return {k: v for k, v in sorted(d.items(), key=lambda item: int(item[1]), reverse=True)}

"""
This function takes in the ord dictionary and the sentences list as arguments.
It initializes an empty list called result that we will append the found sentences to. It then iterates over each key in the ord dictionary and for each key, it iterates over each sentence in the sentences list.
If the key is found in the sentence, the sentence is appended to the result list
"""
def find_sentences(ord, sentences):
  result = []
  for key in ord:
    for sentence in sentences:
      if key in sentence:
        result.append(sentence)
  return result

"""
This function takes a list of sentences and a keyword, removes the keyword from each sentence in the list, and returns the updated list.
"""
def remove_keyword(sentences, keyword):
  updated_sentences = []
  for sentence in sentences:
    updated_sentence = sentence.replace(keyword, "")
    updated_sentences.append(updated_sentence)
  return updated_sentences

"""
This function takes a list of sentences and a list of keyword, removes the keyword from each sentence in the list, and returns the updated list. MAYBE NOT WORKING
Removes one or more keywords from each sentence in the list of sentences.
"""
def remove_keywords(sentences, keywords):
  result = sentences
  for entry in keywords:
    result = remove_keyword(result, entry)
  return result

"""
This function prepends a given string to each sentence in a list.
"""
def prepend_string(sentences, prepend_str):
  new_sentences = []
  for sentence in sentences:
    new_sentence = f"{prepend_str}{sentence}"
    new_sentences.append(new_sentence)
  return new_sentences

"""
This function creates a new list new_sentences and loops over each sentence in the input sentences list.
It then uses a list comprehension and the difflib.SequenceMatcher class to compare the sentence to each sentence already in new_sentences.
If the ratio of similarity between the two sentences is greater than 0.8 (adjust this threshold as needed), it considers the sentence to be similar and skips it. Otherwise, it adds the sentence to new_sentences.
Finally, it returns the new list of unique sentences.
"""
def remove_similar(sentences):
  new_sentences = []
  for sentence in sentences:
    if not any(difflib.SequenceMatcher(None, sentence, s).ratio() > 0.8 for s in new_sentences):
      new_sentences.append(sentence)
  return new_sentences

"""
Calls the wiki years page, retrieve the thumbcaption part and rewrites it to become sentences. Return those sentences as hints.
Args: years_list (list): The years we want the thumbcaption hints from.
Returns:  dict: A dictionary with the most popular events of a year retrieved from the thumbcaption part of a wiki years page.
"""
def thumbcaption_hints_per_year(years_list):
  thumbcaption_hints = {}
  wiki_base_link= 'https://en.wikipedia.org/wiki/'
  pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=all-time&pages='
  for y in years_list:
    years_key = str(y)
    test_link = wiki_base_link + years_key
    sentences_of_thumbcaption = get_thumbcaption_sentences(test_link) #just gets the sentences from the thumbcaption section of a wikipedi years page
    thumbcaption = get_wikipedia_backlinks_thumbcaption(test_link) #get all backlinks of the thumbcapture of the year (those are the most known events)
    thumbcaption_key = next(iter(thumbcaption))
    thumbcaption_val = thumbcaption[thumbcaption_key]
    pruned = prune_links(thumbcaption_val) #prune those backlinks such that only the important part remains
    com = combine_first_elements(pruned) #combine up to 10 of these links to create a request to pageview
    url_list = add_combined_strings_to_url(pageviews_range_url, com) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page
    data=combine_dicts_from_links(url_list) #now we called the links and retreieved the pageviews; saved them as a dictionary
    ord = sort_dict_desc(data) #now the list is ordered in ascending order
    tmp = find_sentences(ord,sentences_of_thumbcaption) #search the corresponding sentence to the keyword (USA and school shooting for example)
    keywords_list = [years_key, 'clockwise ', 'Clockwise ', 'From top left', 'from top-left', 'from top left', 'From top-left', 'from top-left: ', ':', 'from left, clockwise'] #list of keywords that should be removed from the sentences
    t4=remove_keywords(tmp, keywords_list)
    prepend_str = 'In the same year, '
    hints = prepend_string(t4, prepend_str)
    final_hints = remove_similar(hints) #before adjusting the sentences
    thumbcaption_hints[y] = final_hints
  return thumbcaption_hints

"""
Calls the thumbcaption_hints_per_year function for every year and combines those into a dict.
Returns:  dict: A dictionary with the most popular events of a year retrieved from the thumbcaption part of a wiki years page.

"""

def get_year_thumbcaption_hints(qa_dict):
  file_years_list = []
  for index, row in qa_dict.items():
    file_years_list.append(int(index))
  pop_thumb_hints = thumbcaption_hints_per_year(file_years_list)
  return pop_thumb_hints

"""### Dictionary for popular sports events of a year"""
#Some global varaibles for faster execution
#pop_year_hints = {}
#pop_thumb_hints = {}
"""
Given a URL, this function opens the url and retrieves all tables on the page.
"""
# def get_all_tables(url):
#   options = webdriver.FirefoxOptions()
#   # options.set_preference("pdfjs.disabled", True)
#   options.add_argument('--headless')
#   driver = webdriver.Firefox(options=options)
#   driver.get(url)
#   time.sleep(1) # Wait for the page to load completely
#   soup = BeautifulSoup(driver.page_source, 'html.parser')
#   driver.quit()
#   tables = soup.find_all('table')
#   all_tables = []
#   for table in tables:
#     rows = table.find_all('tr')
#     headers = [header.text.strip() for header in rows[0].find_all('th')]
#     data = []
#     for row in rows[1:]:
#       data.append([cell.text.strip() for cell in row.find_all('td')])
#     all_tables.append({'headers': headers, 'data': data})
#   return all_tables


# import pandas as pd
# import wikipedia as wp

def get_all_tables(page_name, table_number=2):

  html = wikipedia.page(page_name).html().encode("UTF-8")
  try: 
      df = pd.read_html(html)[ table_number]  # Try 2nd table first as most pages contain contents table first
      # print(df)
  except IndexError:
      df = pd.read_html(html)[0]
      # print(df)


  return df




"""
Extracts the first element from each sublist in the 'data' list of lists in a dictionary and returns them in a separate list.
Args: data_dict (dict): A dictionary containing a 'data' key with a list of lists as its value.
Returns: A list containing the first element of each sublist in the 'data' list of lists.
"""
def get_first_elements(data_dict):
  data_list = data_dict['data']
  result = []
  for sublist in data_list:
    if len(sublist) > 0:
      if len(sublist[0]) > 0:
        result.append(sublist[0])
  return result

#prune the list of the hole wiki page down to the important table
def prune_dict_list(dict_list, keyw):
  for d in dict_list:
    if 'headers' in d and d['headers'] == [keyw]:
      return d
  return None  # if no dict with the desired key-value pair is found

#replace the \n and create a list of lists
def create_list_from_list_of_lists_key(lst, keyw):
  result = []
  for sublst in lst:
    if sublst:
      new_test = [item.replace(keyw, '') for item in sublst[0].split(keyw)]
      result.append(new_test)
  return result

#replace the : and create a dict; {'year': 'CL-winner'}
def create_dict_from_list_of_lists(lst):
  result_dict = {}
  for sublist in lst:
    for item in sublist:
      if ":" in item:
        key, value = item.split(":")
        key = key.strip().replace("–", "-")
        value = value.strip()
        result_dict[key] = value
      else:
        continue
  return result_dict

#split on the : and creates a dict
def create_dict_from_list(lst):
  result = {}
  for item in lst:
    parts = item.split(":")
    result[parts[0]] = parts[1]
  return result

#splits on [ and creates a dict 1950: 'Farina'
def get_year_with_driver(race_results):
  results_dict = {}
  for result in race_results:
    if result:
      results_dict[result[0].split("[")[0]] = result[1]
  return results_dict

#get rid of the links ('Alberto Ascari[20]' => 'Alberto Ascari')
def clean_driver_names(results_dict):
  for year, driver in results_dict.items():
    results_dict[year] = driver.split('[')[0].strip()
  return results_dict

#deletes the : from the key
def clean_dict_keys(dict_to_clean):
  cleaned_dict = {}
  for key, value in dict_to_clean.items():
    cleaned_dict[key.rstrip(':')] = value
  return cleaned_dict

#function to split on \n but that lets the city names stay together
def create_city_dict(city_list):
  city_dict = {}
  cities = city_list[0].split('\n')
  for city in cities:
    if city:
      year, *city_name = city.strip().split()
      city_dict[year] = ' '.join(city_name)
  return city_dict

def remove_after_first_opening_bracket(s):
  index = s.find('[')
  if index != -1:
      s = s[:index]
  return s




# #get the dict of all the champions league winners
# def champions_league_winners_list():
#   champions_league_url = 'https://en.wikipedia.org/wiki/List_of_European_Cup_and_UEFA_Champions_League_finals#List_of_finals'
#   all = get_all_tables(champions_league_url) #gets all tables of wiki page

#   #first prune of that huge dict
#   keyw= 'showvteEuropean Cup and UEFA Champions League winners'
#   pruned_dict = prune_dict_list(all,keyw)
#   #second prune
#   inter = pruned_dict.get('data')
#   cl_list = inter[2:5] + inter[7:11]
#   tmp1 = create_list_from_list_of_lists_key(cl_list, '\n')
#   tmp2 = create_dict_from_list_of_lists(tmp1)
#   return tmp2

#get the dict of all the champions league winners

#get the dict of all the champions league winners
def champions_league_winners_list():
  champions_league_url = 'List_of_European_Cup_and_UEFA_Champions_League_finals'
  try:
    file = get_all_tables(champions_league_url, 3) #gets all tables of wiki page

    champions_league_dict =  dict(zip(file['Season'], file['Winners']))
    champions_league_dict1 = {}
    # print(champions_league_dict)

    for a,b in champions_league_dict.items():
      old_substring = "â\\x80\\x93"
      new_substring = '/'
      new_string = a.replace(old_substring, new_substring)
      old_substring = "â"
      new_substring = '/'
      new_string1 = new_string.replace(old_substring, new_substring)

      champions_league_dict1[new_string1] = b
  except Exception as e:
    print('ERROR: champions_league_winners_list', e)
    file = get_all_tables(champions_league_url, 2) #gets all tables of wiki page

    champions_league_dict =  dict(zip(file['Season'], file['Winners']))
    champions_league_dict1 = {}
    # print(champions_league_dict)

    for a,b in champions_league_dict.items():
      old_substring = "â\\x80\\x93"
      new_substring = '/'
      new_string = a.replace(old_substring, new_substring)
      old_substring = "â"
      new_substring = '/'
      new_string1 = new_string.replace(old_substring, new_substring)

      champions_league_dict1[new_string1] = b
  return champions_league_dict1

#get the dict of all the champions league winners
def uefa_euros_winners_list():
  euros_url = 'List_of_UEFA_European_Championship_finals#List_of_finals'
  file = get_all_tables(euros_url) #gets all tables of wiki page

  euros_dict =  dict(zip(file['Tournament'], file['Winners']))
  euros_ret = {}
  for a,b in euros_dict.items():
    if '[a]' in a:
      c = a.replace('[a]', '')
      euros_ret[c] = b
    else:
      euros_ret[a] = b


  return euros_ret

  # #first prune of that huge dict
  # keyw= 'showvteEuropean Cup and UEFA Champions League winners'
  # pruned_dict = prune_dict_list(all,keyw)
  # #second prune
  # inter = pruned_dict.get('data')
  # cl_list = inter[2:5] + inter[7:11]
  # tmp1 = create_list_from_list_of_lists_key(cl_list, '\n')
  # tmp2 = create_dict_from_list_of_lists(tmp1)
  # return tmp2

# #get the dict of all the euros winners
# def uefa_euros_winners_list():
#   euros_url = 'https://en.wikipedia.org/wiki/List_of_UEFA_European_Championship_finals#List_of_finals'
#   all = get_all_tables(euros_url) #gets all tables of wiki page
#   #first prune of that huge dict
#   keyw= 'showvteUEFA European Championship winners'
#   pruned_dict = prune_dict_list(all,keyw)
#   #second prune
#   inter = pruned_dict.get('data')
#   tmp1 = create_list_from_list_of_lists_key(inter, '\n')
#   tmp2 = create_dict_from_list_of_lists(tmp1)
#   return tmp2


def uefa_worlds_winners_list():
  worlds_url = 'List_of_FIFA_World_Cup_finals#List_of_final_matches'
  world_file = get_all_tables(worlds_url, 3) #gets all tables of wiki page
  worlds_dict =  dict(zip(world_file['Year'], world_file['Winners']))

  return worlds_dict

# #get the dict of all the wold cup winners
# def uefa_worlds_winners_list():
#   worlds_url = 'https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals#List_of_final_matches'
#   all = get_all_tables(worlds_url) #gets all tables of wiki page
#   tmp3=get_first_elements(all[3])
#   #first prune of that huge dict
#   keyw= 'showvteFIFA World Cup'
#   pruned_dict = prune_dict_list(all,keyw)
#   #second prune
#   inter = pruned_dict.get('data')
#   inter = inter[2]
#   years = [s for s in inter[0].split('\n')]
#   my_dict = dict(zip(years, tmp3))
#   return my_dict

# #get the dict of all the F1 drivers world champions
# def f1_winners_list():
#   euros_url = 'https://en.wikipedia.org/wiki/List_of_Formula_One_World_Drivers%27_Champions#By_season'
#   all = get_all_tables(euros_url) #gets all tables of wiki page
#   lst = all[2].get('data')
#   tmp2 = get_year_with_driver(lst)
#   tmp2 = clean_driver_names(tmp2)
#   return tmp2

def f1_winners_list():
  f1_url = 'List_of_Formula_One_World_Drivers%27_Champions'
  f1_file = get_all_tables(f1_url) #gets all tables of wiki page
  print(f1_file)
  try:
    a = f1_file['Season']['Season']
    b= f1_file['Driver']['Driver']
    for key, value in a.items():
      a[key] = remove_after_first_opening_bracket(value)
    for key, value in b.items():
      b[key] = remove_after_first_opening_bracket(value)
  except Exception as e:
    print(e)

  f1_dict =  dict(zip(a, b))
  return f1_dict


# #get the dict of all summer olympics host cities
# def summer_olympics_hosts_list():
#   summerO_url = 'https://en.wikipedia.org/wiki/Summer_Olympic_Games#List_of_Summer_Olympic_Games'
#   all = get_all_tables(summerO_url) #gets all tables of wiki page
#   lst = all[10].get('data')
#   tmp1 = create_list_from_list_of_lists_key(lst, '\n')
#   tmp1 = tmp1[0]
#   tmp1 = create_dict_from_list(tmp1)
#   tmp1 = clean_dict_keys(tmp1)
#   tmp1 = clean_driver_names(tmp1)
#   return tmp1

def summer_olympics_hosts_list():
  summer_url = 'Summer_Olympic_Games'
  summer_file = get_all_tables(summer_url, 6) #gets all tables of wiki page
  a = summer_file['Olympiad']['Olympiad']
  b = summer_file['Host']['Host']
  for key, value in a.items():
    a[key] = remove_after_first_opening_bracket(value)
  for key, value in b.items():
    b[key] = remove_after_first_opening_bracket(value)

  summer_dict =  dict(zip(a, b))
  return summer_dict

# #get the dict of all winter olympics host cities
# def winter_olympics_hosts_list():
#   winterO_url = 'https://en.wikipedia.org/wiki/Winter_Olympic_Games#List_of_Winter_Olympic_Games'
#   all = get_all_tables(winterO_url) #gets all tables of wiki page
#   lst = all[8].get('data')
#   tmp1 = create_list_from_list_of_lists_key(lst, '\n')
#   tmp1 = tmp1[0]
#   tmp1 = create_dict_from_list(tmp1)
#   tmp1 = clean_dict_keys(tmp1)
#   tmp1 = clean_driver_names(tmp1)
#   return tmp1

def winter_olympics_hosts_list():
  winter_url = 'Winter_Olympic_Games'
  winter_file = get_all_tables(winter_url, 4) #gets all tables of wiki page
  a = winter_file['Year']['Year']['Amateur era']
  b = winter_file['Host']['Host']['Amateur era']

  for key, value in a.items():
    a[key] = remove_after_first_opening_bracket(value)
  for key, value in b.items():
    b[key] = remove_after_first_opening_bracket(value)

  winter_dict =  dict(zip(a, b))
  return winter_dict

# print(winter_olympics_hosts_list())


#write all of the winners of the different sports categories into lists
euro_all = uefa_euros_winners_list() #For Football-Euros
worlds_all = uefa_worlds_winners_list() #For Football-Worlds
f1_all = f1_winners_list() #For Fromula1
summer_olympics_all = summer_olympics_hosts_list() #For OlympicSummerGames
winter_olympics_all = winter_olympics_hosts_list() #For OlympicWinterGames
cl_all = champions_league_winners_list() #For the Champions league,

'''
takes a list of years and then creates a dict of dicts, where (if available) the most popular sports events of that year are saved as hints.
returns a dict with the corresponding sports events from the years in years_list
'''
def popular_sports_per_year(years_list):
  pop_sport_hints_year = {}
  for index in years_list:
    year = int(index)
    year_s = str(year)
    year_dict = {
        'cl': '', 'p_cl': '', 'f_cl': '',
        'euros': '', 'p_euros': '', 'f_euros': '',
        'worlds': '', 'p_worlds': '', 'f_worlds': '',
        'f1': '', 'p_f1': '', 'f_f1': '',
        'summer': '', 'p_summer': '', 'f_summer': '',
        'winter': '', 'p_winter': '', 'f_winter': ''
    }
  # UEFA Champions League: Create the sentences like (In the same-, the following-, the previous-year)
    for key in cl_all:
      if int(key.split('/')[1]) == year % 100:
        result = cl_all[key]
        break
    if result:
      year_dict['cl'] = basic_sentences[0] + result + sport_sentences[0]
    for key in cl_all:
      if int(key.split('/')[1]) == (year - 1) % 100:
        result = cl_all[key]
        break
    if result:
      year_dict['p_cl'] = basic_sentences[1] + result + sport_sentences[0]
    for key in cl_all:
      if int(key.split('/')[1]) == (year + 1) % 100:
        result = cl_all[key]
        break
    if result:
      year_dict['f_cl'] = basic_sentences[2] + result + sport_sentences[0]
  # UEFA EURO Football Championship: Create the sentences like (In the same-, the following-, the previous-year)
    for d in euro_all:
      if year_s in d:
        year_dict['euros'] = basic_sentences[0] + euro_all[year_s] + sport_sentences[1]
    for d in euro_all:
      t = year - 1
      year_int = str(t)
      if year_int in d:
        year_dict['p_euros'] = basic_sentences[1] + euro_all[year_int] + sport_sentences[1]
    for d in euro_all:
      t = year + 1
      year_int = str(t)
      if year_int in d:
        year_dict['f_euros'] = basic_sentences[2] + euro_all[year_int] + sport_sentences[1]
  # FIFA WORLD Football Championship: Create the sentences like (In the same-, the following-, the previous-year)
    for d in worlds_all:
      if year_s in d:
        year_dict['worlds'] = basic_sentences[0] + worlds_all[year_s] + sport_sentences[2]
    for d in worlds_all:
      t = year - 1
      year_int = str(t)
      if year_int in d:
        year_dict['p_worlds'] = basic_sentences[1] + worlds_all[year_int] + sport_sentences[2]
    for d in worlds_all:
      t = year + 1
      year_int = str(t)
      if year_int in d:
        year_dict['f_worlds'] = basic_sentences[2] + worlds_all[year_int] + sport_sentences[2]
  # F1 WORLD Drivers Championship: Create the sentences like (In the same-, the following-, the previous-year)
    for d in f1_all:
      if year_s in d:
        year_dict['f1'] = basic_sentences[0] + f1_all[year_s] + sport_sentences[3]
    for d in f1_all:
      t = year - 1
      year_int = str(t)
      if year_int in d:
        year_dict['p_f1'] = basic_sentences[1] + f1_all[year_int] + sport_sentences[3]
    for d in f1_all:
      t = year + 1
      year_int = str(t)
      if year_int in d:
        year_dict['f_f1'] = basic_sentences[2] + f1_all[year_int] + sport_sentences[3]
  # Summer Olympic Games: Create the sentences like (In the same-, the following-, the previous-year)
    for d in summer_olympics_all:
      if year_s in d:
        year_dict['summer'] = olympic_sentences[0] + summer_olympics_all[year_s]
    for d in summer_olympics_all:
      t = year - 1
      year_int = str(t)
      if year_int in d:
        year_dict['p_summer'] = olympic_sentences[1] + summer_olympics_all[year_int]
    for d in summer_olympics_all:
      t = year + 1
      year_int = str(t)
      if year_int in d:
        year_dict['f_summer'] = olympic_sentences[2] + summer_olympics_all[year_int]
  # Winter Olympic Games: Create the sentences like (In the same-, the following-, the previous-year)
    for a,b in winter_olympics_all.items():
      if str(year) in a:
        year_dict['winter'] = olympic_sentences[3] + b
    for a,b in winter_olympics_all.items():
      t = year - 1
      year_str = str(t)
      if year_str in a:
        year_dict['winter'] = olympic_sentences[4] + b
    for a,b in winter_olympics_all.items():
      t = year + 1
      year_str = str(t)
      if year_str in a:
        year_dict['winter'] = olympic_sentences[5] + b
    #write the entry in the dict
    pop_sport_hints_year[year] = year_dict
  return pop_sport_hints_year

#CALL FUNCTION
#returns a dictionary of the years that occured in the xls file, with its corresponding hints from the most popular sports events of that year.
def get_year_sports_hints(qa_dict):
  file_years_list = []
  for index, row in qa_dict.items():
    file_years_list.append(int(index))
  pop_sport_hints = popular_sports_per_year(file_years_list)
  return pop_sport_hints

# Load pre-trained model and tokenizer
model_name = 'bert-base-uncased'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

#Pre analyze/convert the text for BERNT
def preprocess_text(text):
  # Tokenize the text and add special tokens
  tokens = tokenizer.encode(text, add_special_tokens=True)
  # Convert the tokens to a tensor
  token_tensor = torch.tensor(tokens).unsqueeze(0)
  return token_tensor

#Calculates a similarity score by comparing the two pieces of text va BERNT
def get_similarity_score(text1, text2):
  # Preprocess both texts
  tensor1 = preprocess_text(text1)
  tensor2 = preprocess_text(text2)
  # Pass both tensors to the model to get the embeddings
  with torch.no_grad():
    output1 = model(tensor1)
    output2 = model(tensor2)
  # Compute the cosine similarity between the two embeddings
  cosine_sim = torch.nn.functional.cosine_similarity(output1.last_hidden_state.mean(dim=1), output2.last_hidden_state.mean(dim=1), dim=1)
  return cosine_sim.item()

# calculate_similarity(question,answer,hint,sim_score_priority_words)

# import spacy
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity

# import spacy.cli

# # Download the larger English model (en_core_web_md)
# spacy.cli.download("en_core_web_md")

# # Alternatively, download the smaller English model (en_core_web_sm)
# spacy.cli.download("en_core_web_sm")

# import spacy
# from sklearn.metrics.pairwise import cosine_similarity

# Load the spaCy language model with word embeddings
nlp = spacy.load("en_core_web_md")

def calculate_similarity(question, answer, hint, priority_words=None, priority_weight=1.5):
  if priority_words is None:
    priority_words = []

  # if isinstance(answer, int):
  #   # Convert the integer to a string
  #   answer = str(answer)
  # Calculate the word embeddings for the question and answer
  question_embedding = np.mean([nlp(word).vector for word in question.split()], axis=0)
  answer_embedding = nlp(str(answer)).vector
  # Calculate the similarity scores for each hint
  similarity_scores = []
  hint_embedding = np.mean([nlp(word).vector for word in hint.split()], axis=0)
  similarity_score = cosine_similarity([question_embedding, answer_embedding], [hint_embedding, answer_embedding])
  # Apply a bonus weight if any priority words are present in the hint
  bonus_weight = priority_weight if any(word in hint for word in priority_words) else 1.0
  similarity_score[0, 0] *= bonus_weight

  return similarity_score[0, 0]



"""### Dictionary for historical events from vizgr.org"""
"""
Downloads an XML file from the specified URL and saves it to the specified filename.
Args: url (str): The URL of the XML file to download.
Returns: filename (str): The filename (including the path) to save the downloaded XML file.
"""
def download_xml_file(url, filename):
  response = urllib.request.urlopen(url)
  xml_data = response.read()
  with open(filename, 'wb') as file:
    file.write(xml_data)
  return filename

"""
Parses an XML file and returns the root element.
Args: filename (str): The filename (including the path) of the XML file to parse.
Returns: xml.etree.ElementTree.Element: The root element of the parsed XML.
"""
def parse_xml_file(xml_file):
  tree = ET.parse(xml_file)
  root = tree.getroot()
  result = {}
  result['count'] = root.find('count').text
  events = root.findall('event')
  for event in events:
    event_dict = {}
    event_dict['date'] = event.find('date').text
    event_dict['description'] = event.find('description').text
    event_dict['lang'] = event.find('lang').text
    event_dict['granularity'] = event.find('granularity').text
    result[event_dict['date']] = event_dict
  return result

"""
Retrieves historical information from the specified website using the given start and end dates.
Args: start_date (str): The start date in the format 'YYYY/MM/DD'; end_date (str): The end date in the format 'YYYY/MM/DD'.
Returns: str: The retrieved historical information as a xml file is saved and converted into a dict.
"""
def retrieve_historical_information(start_date, end_date):
  url = f"https://www.vizgr.org/historical-events/search.php?format=xml&begin_date={start_date.replace('/', '')}&end_date={end_date.replace('/', '')}"
  #https://www.vizgr.org/historical-events/search.php?format=xml&begin_date=20120101&end_date=201231
  # filename = "/content/automaticHintGeneration/vizgr_events.xml"
  filename = "vizgr_events.xml"
  saved_file = download_xml_file(url, filename)
  result = parse_xml_file(saved_file)
  return result

"""
Extracts the date and description from the XML string and returns a dictionary.
Args: xml_string (str): The XML data in string format.
Returns:  dict: A dictionary with the date as the key and the description up until the first dot as the value.
"""
def extract_description(xml_file):
  extracted_data = {}
  for key,value in xml_file.items():
    try:
      description = value.get('description')
      pruned_description = '.'.join(description.split('.')[:1])
      extracted_data[key] = pruned_description
    except Exception as e:
      continue
      pass
  return extracted_data

#removes a certin string from a certain sentence
def remove_string(sentence, string_to_remove):
  return sentence.replace(string_to_remove, '')

"""
Function that retrieves the event information from the vizgr.com website.
Returns:  dict: A dictionary with the date as the key and the event descriptions as values.
"""
def get_year_vizgr_hints(qa_dict):
  file_years_list = []
  final_hints = {}
  # for index, row in year_df.iterrows():
  for index, row in qa_dict.items():
    if int(index) < 2012:
      file_years_list.append(int(index))
  for year in file_years_list:
    inter_start_date = str(year) + "0101"
    inter_end_date = str(year) + "1231"
    inter_solution = retrieve_historical_information(inter_start_date, inter_end_date)
    vizgr_hint_descriptions = extract_description(inter_solution)
    vizgr_hint_sentences = {}
    for k,v in vizgr_hint_descriptions.items():
      if len(v) > 15:
        if str(year) in v:
          v = remove_string(v,str(year))
        if v[0].isspace():
          vizgr_hint_sentences[k] = 'In the same year, '+ v[1].lower() + v[2:] + '.'
        else:
          vizgr_hint_sentences[k] = 'In the same year, '+ v[0].lower() + v[1:] + '.'
      vizgr_hint_sentences = remove_sentences_with_asterisk(vizgr_hint_sentences)
    final_hints[year] = vizgr_hint_sentences
  return final_hints


"""### Test the generate_hints_years() function:"""
"""
Function that checks and counts how many words two sentences have in common. (To know if hint is too opbvious/similar to question)
Args: the years-question and the comparable sentence
Returns:  list of common words
"""
def discrad_obvious_hints(question, sentence):
  common_words = []
  words1 = question.lower().split()
  words2 = sentence.lower().split()
  common_words = list(set(words1) & set(words2))
  return common_words

"""
Function that order the hint sentences after their similarity score and discrads too obvious hints. Returns the top 5 most similar ones from each type of years-hint-generation.
Args: the dictionary with all the different years hints sentences
Returns:  OrderedDict
"""
def order_dictionary(my_dict):
  question = ''
  keys_to_delete = []
  ret = {}
  for year, value in my_dict.items():
    new_dict = {}
    for typ, categories in value.items():
      copy_inner_ordered_dict = OrderedDict()
      question = value['question']
      if typ == "question":
        sorted_inner_ordered_dict = categories
      else:
        if typ == "thumbcaption":
          sorted_inner_ordered_dict = categories
        else: #for sports and vizgr
          for a,b in categories.items():
            for c,d in b.items():
              common_word = discrad_obvious_hints(question, c)
              if len(common_word) >= 4:
                key = [typ, a]
                keys_to_delete.append(key)
              else:
                if not c:
                  continue
                else:
                  copy_inner_ordered_dict[a] = b
          sorted_inner_ordered_dict = dict(sorted(copy_inner_ordered_dict.items(), key=lambda item: list(item[1].values())[0], reverse=True)[:5])
      new_dict[typ] = sorted_inner_ordered_dict
    ret[year] = new_dict
  return ret

# """
# Calls the three different function types of generating years hints, combines them into a single dict and calculate the similarity score between question and hint to rank them.
# Returns:  dict: A dictionary with the date as the key and the description up until the first dot as the value.
# Test for utility score of new questions; calculate score via BERT for each question,hint pair and write the score together with the question into the sim_scores dictionary.
# """
def generate_hints_years(qa_dict):
  pop_year_hints = {}
  #pop_thumb_hints = {}
  pop_vizgr_hints = {}

  pop_year_hints = get_year_sports_hints(qa_dict)
  #pop_thumb_hints = get_year_thumbcaption_hints(qa_dict)
  pop_vizgr_hints = get_year_vizgr_hints(qa_dict)
  years_hints = {}

  pprint.pprint(pop_year_hints)
  pprint.pprint(pop_vizgr_hints)



  year_dict = {
    'sports': years_hints,
    'vizgr' : years_hints
  }

  for y in pop_year_hints:
    year_dict= {}
    try:
      if pop_year_hints[y]:
        year_dict['sports'] = pop_year_hints[y]
      #if pop_thumb_hints[y]:
      #  year_dict['thumbcaption'] = pop_thumb_hints[y]
      if pop_vizgr_hints[y]:
        year_dict['vizgr'] = pop_vizgr_hints[y]
    except Exception as e:
      print(e)
      pass
    years_hints[y] = year_dict
  generated_hints_for_years = years_hints
  sim_scores = years_hints
  for y, q in qa_dict.items():
    for year, data in generated_hints_for_years.items():
      if y == year:
        for category, subdata in data.items():
          if category == 'sports':
            for key, value in subdata.items():
              sim_scores[year][category][key] = {}
              if value:
                # similarity_score = get_similarity_score(q,value)
                similarity_score = calculate_similarity(q,y,value,sim_score_priority_words)
                sim_scores[year][category][key][value] = similarity_score
          # elif category == 'thumbcaption':
          #   for i in subdata:
          #     sim_scores[year][category] = {}
          #     similarity_score = get_similarity_score(q,i)
          #     sim_scores[year][category][i] = similarity_score
          elif category == 'vizgr':
            for key, value in subdata.items():
              sim_scores[year][category][key] = {}
              if value:
                # similarity_score = get_similarity_score(q,value)
                similarity_score = calculate_similarity(q,y,value,sim_score_priority_words)
                sim_scores[year][category][key][value] = similarity_score
      else:
        continue
  for y, q in qa_dict.items():
    for year, data in generated_hints_for_years.items():
      if y == year:
        sim_scores[year]['question'] = q
  ordered_dict = order_dictionary(sim_scores)
  return ordered_dict


def check_sentences_for_asterisk(data):
  asterisk_sentences = []
  
  # Recursively search for asterisk in the dictionary
  def search_asterisk(obj):
    if isinstance(obj, dict):
      for key, value in obj.items():
        if isinstance(value, dict):
          search_asterisk(value)
        elif isinstance(value, str) and '*' not in value:
          asterisk_sentences.append(value)
  # Call the recursive search function
  search_asterisk(data)
  
  return asterisk_sentences

def remove_sentences_with_asterisk(data):
  # Recursively remove sentences with asterisk from the dictionary
  def remove_asterisk_sentences(obj):
    if isinstance(obj, dict):
      for key, value in list(obj.items()):
        if isinstance(value, dict):
          remove_asterisk_sentences(value)  # Recursively call the removal function for nested dictionaries
        elif isinstance(value, str) and '*' in value:  # Check if the value is a string containing an asterisk
          del obj[key]  # If asterisk found, remove the key-value pair
  # Create a deep copy of the original data to preserve the input dictionary
  new_data = data.copy()
  # Call the recursive removal function
  remove_asterisk_sentences(new_data)
    
  return new_data