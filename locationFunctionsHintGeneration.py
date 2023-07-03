imports_path = "/automaticHintGeneration/importsHintGeneration"
import sys
sys.path.insert(0, imports_path)

from importsHintGeneration import *

#file_path = "./tmp/testSet_WebApp.xlsx"
# file_path = "./automaticHintGeneration/testSet.xlsx"
file_path = "testSet.xlsx"
df_list = load_file_path(file_path)
person_df = df_list["person"]
year_df = df_list["year"]
location_df = df_list["location"]

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

"""
Function that is created with help of reusable function from above
Args:     location_question_dict with all locations with their questions
Returns:  dictionary where the keys are the answer-entities and the value is a OrderedDict of all categories with pageviews
"""
def get_categories_with_pv_answerEntities_location(location_questions_dict):
  cat_ranking_location = get_categories(location_questions_dict)
  cat_with_pv_location = get_pageviews_for_categories(cat_ranking_location)
  categories_with_subs_and_pageviews_location = get_dict_for_every_location(cat_ranking_location, cat_with_pv_location)
  new_ordered_dict_location = sorting_dict(categories_with_subs_and_pageviews_location)
  return new_ordered_dict_location

#takes the categories scores dict and chooses the category with the highest score
def create_hint_sentences_unexCategs_location(categories_scores_dict, location_answers_dict):
  most_unexpected_categories_dict = {}
  hint_sentence_unexCateg_dict = {}
  print("categories_scores_dict")
  pprint.pprint(categories_scores_dict,indent=1)
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
def count_categories_location(related_people_with_categories, answer_entities_with_categories):
  category_appereances = {}
  for answerEntityKey, aeCategory in answer_entities_with_categories.items():
    for answerKey, relatedDict in related_people_with_categories.items():
      if answerEntityKey == answerKey:
        inner_dict = {}
        for categ, pvs in aeCategory.items():
          people_list = []
          for relatedPersonKey, catWithPvs in relatedDict.items():
            for relCateg, relPvs in  catWithPvs.items():
              if categ == relCateg:
                rel_location_str = str(relatedPersonKey)
                if rel_location_str not in people_list and categ == relCateg:
                  people_list.append(rel_location_str)
                inner_dict[categ] = (len(people_list),relPvs, people_list)
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
    related_location_pageviews_dict = get_pageviews_from_links(related_location_link_dict)
  #time saving for third part (related locations categories recovery and ordering) - 43m+ (14m-24m)
  most_popular_related_location_with_categories = get_categories_of_people_list(related_location_pageviews_dict)
  #time saving for third part retrieves the categories of the answer-entities - 9m+ (6m)
  answer_entities_with_categories_location = get_categories_with_pv_answerEntities_location(location_answers_dict)
  #pprint.pprint(answer_entities_with_categories_location)
  #time saving for fourth part counts the categories of the answer-entities - 3s
  counted_category_apperances_location = count_categories_location(most_popular_related_location_with_categories, answer_entities_with_categories_location)
  ordered_data = {}
  for key,value in counted_category_apperances_location.items():
    tmp = OrderedDict(value)
    ordered_data[key] = OrderedDict(sorted(tmp.items(), key=lambda x: x[1][0], reverse=True) )
  counted_category_apperances_location = ordered_data
  #pprint.pprint(counted_category_apperances_location)
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
  pprint.pprint(mucd,  sort_dicts=False)
  inter = {}
  for key, value in mucd.items():
    for answer,question in location_answers_dict.items():
      if key == answer:
        sim_score = get_similarity_score(question,value[0])
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
    for propert, sentence in properties_blank_sentences_locations.items():
      locations_identifiers_dict[propert] =  get_property_data(location_infos_wikidata[key], propert)
      #prune the list with multipole entries down to the desired one
      if len(locations_identifiers_dict[propert]) > 1:
        if propert != 'P47' and propert != 'P37' and propert != 'P206' and propert != 'P421' and  propert != 'P463' and propert != 'P793' and propert != 'P38':
          locations_identifiers_dict[propert] = locations_identifiers_dict[propert][-1]
      #if entry not null, search for the id of the entry
      if len(locations_identifiers_dict[propert]) > 0:
        propety = locations_identifiers_dict[propert]
        try:
          e_list = []
          for entry in propety:
            id = entry['id']
            e_list.append(get_entity_name(id))
          locations_identifiers_dict[propert] = e_list
        except Exception as e:
          try:
              e_list = []
              for entry in propety:
                id = entry[0]['id']
                e_list.append(get_entity_name(id))
              locations_identifiers_dict[propert] = e_list
          except Exception as e:
            try:
              e_list = []
              id = propety['id']
              e_list.append(get_entity_name(id))
              locations_identifiers_dict[propert] = e_list
            except Exception as e:
              pass
      if propert == 'P1082':
        locations_identifiers_dict[propert] = locations_identifiers_dict[propert]['amount']
    #now lets choose wich one we use for the sentences (sometimes random for others specific ones)
    for prop, sentence in properties_blank_sentences_locations.items():
      for p, val in locations_identifiers_dict.items():
        if p == prop:
          if len(val) == 0:
            continue
          elif len(val) == 1:
            word = str(val[0])
            properties_blank_sentences_locations[p] = sentence.replace('*', word)
          else:
            if p != 'P1082':
              try:
                test =  locations_identifiers_dict[p]
                random_Words = random.sample(test,3)
                random_Words = ', '.join(random_Words)
              except:
                try:
                  test =  locations_identifiers_dict[p]
                  random_Words = random.sample(test,2)
                  random_Words = ', '.join(random_Words)
                except:
                  random_Words = random.choice(val)
              properties_blank_sentences_locations[p] = sentence.replace('*', random_Words)
            else:
              properties_blank_sentences_locations[p] = sentence.replace('*', locations_identifiers_dict[p] )
    ret[key] = properties_blank_sentences_locations
  return ret

def get_ranking_forfixed_properties():
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
  inter = {}
  ret={}
  for key, value in sol.items():
    for answer,question in location_answers_dict.items():
      if key == answer:
        for code, sentence in value.items():
          sim_score = get_similarity_score(question,sentence)
          inter[code]  = {sentence : sim_score}
        ret[key] = inter
  return ret
