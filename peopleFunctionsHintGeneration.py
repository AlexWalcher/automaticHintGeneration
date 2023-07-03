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
  wikipedia = wikipediaapi.Wikipedia("en")
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

#input searched location and returns a dict with number of pages and number of subcategories
def get_categories_ranking(searched_location):
  categories = get_wikipedia_categories(searched_location)
  categories_links = []
  cat_without_articles = []
  bad_list = ['Articles with', 'CS1', 'Wikipedia', 'Webarchive', 'Short', 'Biography', 'Commons', 'Pages', 'Use', 'All', 'Articles', 'Coordinates', 'Engvar', 'Lang', 'Official']
  for c in categories:
    if not any(c.startswith(word) for word in bad_list):
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

#combines the pageviews of the categories of the location together with the sub-categories and pages of those subcategories
def get_dict_for_every_location(cat_ranking, cat_with_pv):
  ret=cat_ranking
  for location, value in cat_ranking.items():
    for location1, value1 in cat_with_pv.items():
      if location == location1:
        tmp = value1
        ret[location] = tmp
  return ret

def get_categories(subject_dict):
  categories_for_subject_dict= {}
  rankings_for_categories_dict = {}
  #creates a dict with all the dicts of each location with its categories and sub-categories
  for subject, question in subject_dict.items():
    try:
      ranking = get_categories_ranking(subject)
      ordict = OrderedDict(ranking)
      rankings_for_categories_dict[subject] = ordict
    except Exception as e:
      pass
  return rankings_for_categories_dict

#given a dictionary with all the categories, the function returns the categories in a OrderedDict with the corresponding pageviews for each category
def get_pageviews_for_categories(cat_dict):
  pageviews_range_url = 'https://pageviews.wmcloud.org/?project=en.wikipedia.org&platform=all-access&agent=user&redirects=0&range=last-year&pages='
  all_cats_with_pvs = {}
  for subject in cat_dict:
    ord_dict = OrderedDict()
    ordered_dict_sub =  cat_dict[subject]
    links_list = [link for link in ordered_dict_sub.keys()]
    pruned_link_parts_list = extract_last_parts(links_list)
    concat_str_for_links = concatenate_elements(pruned_link_parts_list) #combine up to 10 of these links to create a request to pageview
    pageviews_url_list = combine_pv_urls(pageviews_range_url, concat_str_for_links) #now we have a list of pageview links with all the backlinks of the thumbcaption part of the wiki page (REUSED FROM YEARS PART)
    categories_with_pageviews =combine_dicts_from_links(pageviews_url_list) #now we called the links and retreieved the pageviews; saved them as a dictionary
    ordered_categories_with_pageviews = sort_dict_desc(categories_with_pageviews) #now the list is ordered in ascending order
    all_cats_with_pvs[subject] = OrderedDict(categories_with_pageviews)
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

# function that takes a dictionary with an ordered dictionary as the value and prunes the ordered dictionary to keep only the first n entries and deltes certain categories:
def prune_and_ordered_dict(dictionary, n):
  pruned_dict = OrderedDict()
  inter1_dict= OrderedDict()
  bad_categories_list = ['Living_people', 'Living people', '_births', 'births', '_deaths', 'deaths', 'Good_articles', 'Good articles', 'Members','19th', '20th', '21st']
  for key, value in dictionary.items():
    inter3_dict= OrderedDict()
    for link, tuplee in value.items():
      link_str = str(link)
      contains_bad_word = False
      for word in bad_categories_list:
        if word in link_str:
          contains_bad_word = True
          continue
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

#template sentences that are used to create the hint sentences
template_sentence_location = 'The location you are looking for, is a member of the category x'
template_sentence_location2 = 'The location you are looking for, belongs to the category '
template_sentence_person = 'The person you are looking for, is a member of the category x'
template_sentence_person2 = 'The person you are looking for, belongs to the category '

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
  occupation_person_dict = {}
  identifiers = get_wikipedia_identifiers(people_list)
  properties_list = ['occupation']
  for name, pid in identifiers.items():
    inter = get_person_properties(pid, properties_list, people_list)
    occupation_person_dict[name] = inter['occupation'][0]
  return occupation_person_dict

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
  for key,value in person_questions_dict.items():
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
def get_wikipedia_identifiers(person_names):
  base_url = "https://en.wikipedia.org/w/api.php"
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
def get_categories_of_people_list(people_list, limit=5):
  return_dict = {}
  for key,value in people_list.items():
    related_people_orderd = dict(sorted(value.items(), key=lambda x: x[1], reverse=True))   #order the dict after the pageviews in descending order
    top_most_popular_people = dict(itertools.islice(related_people_orderd.items(), 5))      #take the top 5 most known people from the list
    if len(related_people_orderd) == 0 or  len(top_most_popular_people) == 0:
      continue
    categories_of_related_people = get_categories(top_most_popular_people)
    categories_with_pageviews_person = get_pageviews_for_categories(categories_of_related_people)
    categories_with_subs_and_pageviews_person = get_dict_for_every_location(categories_of_related_people, categories_with_pageviews_person)
    new_ordered_dict_related_person = sorting_dict(categories_with_subs_and_pageviews_person)
    copy_new_ordered_dict_person_test = prune_and_ordered_dict(new_ordered_dict_related_person, 10)
    ordered_dict_related_person = sorting_dict(copy_new_ordered_dict_person_test)
    return_dict[key] = ordered_dict_related_person
  return return_dict

"""
Function that is created with help of reusable function from above
Args:     person_question_dict with all people with their questions
Returns:  dictionary where the keys are the answer-entities and the value is a OrderedDict of all categories with pageviews
"""
def get_categories_with_pv_answerEntities(person_questions_dict):
  cat_ranking_person = get_categories(person_questions_dict)
  cat_with_pv_person = get_pageviews_for_categories(cat_ranking_person)
  categories_with_subs_and_pageviews_person = get_dict_for_every_location(cat_ranking_person, cat_with_pv_person)
  new_ordered_dict_person = sorting_dict(categories_with_subs_and_pageviews_person)
  return new_ordered_dict_person

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
        for catLink, tupl in aeCategory.items():
          people_list = []
          for relatedPersonKey, catWithPvs in relatedDict.items():
            for relatedLink, relatedTupl in  catWithPvs.items():
              if catLink == relatedLink:
                rel_pers_str = str(relatedPersonKey)
                if rel_pers_str not in people_list and catLink == relatedLink:
                  people_list.append(rel_pers_str)
                inner_dict[relatedLink] = (len(people_list),relatedTupl, people_list)
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
    IoU_dict[key] = IoU_list
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
          inter_dict[link] = cat_popularity * cat_div
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

#takes the categories scores dict and chooses the category with the highest score
def create_hint_sentences_unexCategs(categories_scores_dict, person_answers_dict):
  people_occupations = get_occupations(person_answers_dict)
  most_unexpected_categories_dict = {}
  hint_sentence_unexCateg_dict = {}
  try:
    for key,value in categories_scores_dict.items():
      categories_scores_dict[key] = OrderedDict(sorted(value.items(), key=lambda x: x[1], reverse=True))
      most_unexpected_categories_dict[key] = (next(iter(value.items())), people_occupations[key])
    occu_str = 'television_presenter'
    for key,value in most_unexpected_categories_dict.items():
      hint_sentence_unexCateg_dict[key] = []
      try:
        if people_occupations[key] == 'Racing':
          occu_str = people_occupations[key]
        else:
          occu_str = people_occupations[key]
      except Exception as e:
        pass
      for sentence in template_sentence_person_list:
        hint_sentence_unexCateg_dict[key].append( sentence.replace('0', occu_str).replace('1', get_category_title(most_unexpected_categories_dict[key][0][0]).split(':')[-1].replace('_', ' ') ))
  except Exception as e: print(e)
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
  for key,value in related_people_dict.items():
    inter_link_list = []
    for item in value:
      inter_link_list.append(item['url'])
    related_people_link_dict[key] = inter_link_list
    related_people_pageviews_dict = get_pageviews_from_links(related_people_link_dict)
  #time saving for third part (related peoples categories recovery and ordering) - 43m+ (14m-24m)
  most_popular_related_people_with_categories = get_categories_of_people_list(related_people_pageviews_dict)
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
        sim_score = get_similarity_score(question,value[0])
        inter[key]  = {value[0] : sim_score}
  return inter

"""### Functions for the unexpected-predicate approach:"""
#list of interesting properties of people
list_of_properties = ['nickname', 'country of citizenship', 'name in native language', 'native language', 'height',
                  'occupation', 'field of work', 'educated at', 'residence', 'work period', 'ethnic group',
                  'notable work', 'member of', 'owner of', 'significant event', 'award received',
                  'date of birth', 'place of birth', 'date of death', 'place of death', 'manner of death',
                  'cause of death', 'social media followers', 'father', 'mother', 'sibling', 'spouse', 'child', 'unmarried partner', 'sport']

properties_blank_sentences = {
  'child': 'The person you are looking for, has / children.',
  'sibling': 'The person you are looking for, has / siblings.',
  'native language': 'The person you are looking for, speaks 0.',
  'occupation': 'The person you are looking for, is occupied as 0.',
  'award received': 'The person you are looking for has won multiple awards in his life, some of them are 0.',
  'ethnic group': 'The person you are looking for was/is a member of the follwoing ethnic group: 0.',
  'nickname': 'The person you are looking for was/is also known under the follwoing nickname: 0.',
  'significant event': 'Some of the most significant events of the searched person were: 0',
  'notable work': 'The person you are looking for was involved in some very notable works, like: 0.',
  'child + sibling': 'The person you are looking for, has / children and * siblings.',
  'date of birth + place of birth': 'The person you are looking for was born on / in *.',
  'date of birth + place of birth + date of death + place of death': 'The person you are looking for was born on / in * and died on - in +.' ,
  'work period' :  'The person you are looking for was most active during / and *.'
  }

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
    properties_person_name_dict[name] = get_person_properties(pid, list_of_properties, person_answers_dict)
  return properties_person_name_dict

"""
Creates hint sentences based on properties of a person and blank sentences.
Args: properties_person_name_dict (dict): A dictionary containing properties of a person mapped to their corresponding values.
      properties_blank_sentences (dict): A dictionary containing blank sentences with placeholders.
Returns: dict: A dictionary containing hint sentences for each person's properties.
"""
def create_hint_sentences_predicates(properties_person_name_dict, properties_blank_sentences, person_answers_dict):
  person_names = []
  for answer, question in person_answers_dict.items():
    person_names.append(answer)
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
    hint_sentence_dict[pers_name] = properties_sentences_dict
  return hint_sentence_dict

def get_person_hints_unexpected_predicates(person_answers_dict):
  properties_person_name_dict = get_properties_predicates_hints(person_answers_dict)
  hint_sentences_predicates = create_hint_sentences_predicates(properties_person_name_dict, properties_blank_sentences, person_answers_dict)
  for key, value in hint_sentences_predicates.items():
    for predicate, sentence in value.items():
      for answer,question in person_answers_dict.items():
        if key == answer:
          sim_score = get_similarity_score(question,sentence)
          hint_sentences_predicates[key][predicate] = {sentence : sim_score}
  return hint_sentences_predicates