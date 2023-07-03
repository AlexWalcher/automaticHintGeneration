#from selenium import webdriver

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

# REUSABLE FUNCTIONS FOR HINT GENERATION
# Dictionary for thumbcaption part of a year
"""
Given a URL, this function opens the url and retrieves the information stored in a table.
"""
def get_table_info(url):
  options = webdriver.FirefoxOptions()
  #options.headless = True
  options.add_argument('--headless')
  #print("get_table_info TEST")
  try:
    driver = webdriver.Firefox(options=options)
    driver.get(url)
    time.sleep(10) # Wait for the page to load completely
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    table = soup.find('table')
    rows = table.find_all('tr')
    headers = [header.text.strip() for header in rows[0].find_all('th')]
    data = []
  except Exception as e:
    pass
  for row in rows[1:]:
      data.append([cell.text.strip() for cell in row.find_all('td')])
  return (headers, data)

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
  if caption is not None:
    # Extract the caption text and any backlinks
    backlink_sentences = {}
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
  sentences = thumbcaption.text.split('; ')
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
    #print(data)
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
  # for index, row in year_df.iterrows():
  for index, row in qa_dict.items():
    file_years_list.append(index)
  pop_thumb_hints = thumbcaption_hints_per_year(file_years_list)
  return pop_thumb_hints


"""### Dictionary for popular sports events of a year"""
#Some global varaibles for faster execution
#pop_year_hints = {}
#pop_thumb_hints = {}

"""
Given a URL, this function opens the url and retrieves all tables on the page.
"""
def get_all_tables(url):
  options = webdriver.FirefoxOptions()
  options.add_argument('--headless')
  driver = webdriver.Firefox(options=options)
  driver.get(url)
  time.sleep(1) # Wait for the page to load completely
  soup = BeautifulSoup(driver.page_source, 'html.parser')
  driver.quit()
  tables = soup.find_all('table')
  all_tables = []
  for table in tables:
    rows = table.find_all('tr')
    headers = [header.text.strip() for header in rows[0].find_all('th')]
    data = []
    for row in rows[1:]:
      data.append([cell.text.strip() for cell in row.find_all('td')])
    all_tables.append({'headers': headers, 'data': data})
  return all_tables

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
    # parts = parts.strip().replace(":", "")
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

#get the dict of all the champions league winners
def champions_league_winners_list():
  champions_league_url = 'https://en.wikipedia.org/wiki/List_of_European_Cup_and_UEFA_Champions_League_finals#List_of_finals'
  all = get_all_tables(champions_league_url) #gets all tables of wiki page
  #first prune of that huge dict
  keyw= 'showvteEuropean Cup and UEFA Champions League winners'
  pruned_dict = prune_dict_list(all,keyw)
  #second prune
  inter = pruned_dict.get('data')
  cl_list = inter[2:5] + inter[7:11]
  tmp1 = create_list_from_list_of_lists_key(cl_list, '\n')
  tmp2 = create_dict_from_list_of_lists(tmp1)
  return tmp2

#get the dict of all the euros winners
def uefa_euros_winners_list():
  euros_url = 'https://en.wikipedia.org/wiki/List_of_UEFA_European_Championship_finals#List_of_finals'
  all = get_all_tables(euros_url) #gets all tables of wiki page
  #first prune of that huge dict
  keyw= 'showvteUEFA European Championship winners'
  pruned_dict = prune_dict_list(all,keyw)
  #second prune
  inter = pruned_dict.get('data')
  tmp1 = create_list_from_list_of_lists_key(inter, '\n')
  tmp2 = create_dict_from_list_of_lists(tmp1)
  return tmp2

#get the dict of all the wold cup winners
def uefa_worlds_winners_list():
  worlds_url = 'https://en.wikipedia.org/wiki/List_of_FIFA_World_Cup_finals#List_of_final_matches'
  all = get_all_tables(worlds_url) #gets all tables of wiki page
  tmp3=get_first_elements(all[3])
  #first prune of that huge dict
  keyw= 'showvteFIFA World Cup'
  pruned_dict = prune_dict_list(all,keyw)
  #second prune
  inter = pruned_dict.get('data')
  inter = inter[2]
  years = [s for s in inter[0].split('\n')]
  my_dict = dict(zip(years, tmp3))
  return my_dict

#get the dict of all the F1 drivers world champions
def f1_winners_list():
  euros_url = 'https://en.wikipedia.org/wiki/List_of_Formula_One_World_Drivers%27_Champions#By_season'
  all = get_all_tables(euros_url) #gets all tables of wiki page
  lst = all[2].get('data')
  tmp2 = get_year_with_driver(lst)
  tmp2 = clean_driver_names(tmp2)
  return tmp2

#get the dict of all summer olympics host cities
def summer_olympics_hosts_list():
  summerO_url = 'https://en.wikipedia.org/wiki/Summer_Olympic_Games#List_of_Summer_Olympic_Games'
  all = get_all_tables(summerO_url) #gets all tables of wiki page
  lst = all[10].get('data')
  tmp1 = create_list_from_list_of_lists_key(lst, '\n')
  tmp1 = tmp1[0]
  tmp1 = create_dict_from_list(tmp1)
  tmp1 = clean_dict_keys(tmp1)
  tmp1 = clean_driver_names(tmp1)
  return tmp1

#get the dict of all winter olympics host cities
def winter_olympics_hosts_list():
  winterO_url = 'https://en.wikipedia.org/wiki/Winter_Olympic_Games#List_of_Winter_Olympic_Games'
  all = get_all_tables(winterO_url) #gets all tables of wiki page
  lst = all[8].get('data')
  tmp1 = create_list_from_list_of_lists_key(lst, '\n')
  tmp1 = tmp1[0]
  tmp1 = create_dict_from_list(tmp1)
  tmp1 = clean_dict_keys(tmp1)
  tmp1 = clean_driver_names(tmp1)
  return tmp1

#The basic sentences out of which we create the hint-sentences
basic_sentences =  ['In the same year, ', 'In the previous year, ', 'In the following year, ']
sport_sentences = [' has won the UEFA Champions League.', ' has won the UEFA Euro Football Championship.', ' has won the FIFA World Cup.', ' has won the F1 Drivers World Championship.', ]
olympic_sentences = ['In the same year, the Summer Olympics were held in ', 'In the previous year, the Summer Olympics were held in ', 'In the following year, the Summer Olympics were held in ', 'In the same year, the Winter Olympics were held in ', 'In the previous year, the Winter Olympics were held in ', 'In the following year, the Winter Olympics were held in ']

#write all of the winners of the different sports categories into lists
cl_all = champions_league_winners_list() #For the Champions league,
euro_all = uefa_euros_winners_list() #For Football-Euros
worlds_all = uefa_worlds_winners_list() #For Football-Worlds
f1_all = f1_winners_list() #For Fromula1
summer_olympics_all = summer_olympics_hosts_list() #For OlympicSummerGames
winter_olympics_all = winter_olympics_hosts_list() #For OlympicWinterGames

'''
takes a list of years and then creates a dict of dicts, where (if available) the most popular sports events of that year are saved as hints.
returns a dict with the corresponding sports events from the years in years_list
'''
def popular_sports_per_year(years_list):
  pop_sport_hints_year = {}
  for index in years_list:
    year = index
    year_s = str(year)
    year_dict = {
        'cl': '', 'p_cl': '', 'f_cl': '',
        'euros': '', 'p_euros': '', 'f_euros': '',
        'worlds': '', 'p_worlds': '', 'f_worlds': '',
        'f1': '', 'p_f1': '', 'f_f1': '',
        'summer': '', 'p_summer': '', 'f_summer': '',
        'winter': '', 'p_winter': '', 'f_winter': '',
        }
  # UEFA Champions League: Create the sentences like (In the same-, the following-, the previous-year)
    for key in cl_all:
      if int(key.split('-')[1]) == year % 100:
        result = cl_all[key]
        break
    if result:
      year_dict['cl'] = basic_sentences[0] + result + sport_sentences[0]
    for key in cl_all:
      if int(key.split('-')[1]) == (year - 1) % 100:
        result = cl_all[key]
        break
    if result:
      year_dict['p_cl'] = basic_sentences[1] + result + sport_sentences[0]
    for key in cl_all:
      if int(key.split('-')[1]) == (year + 1) % 100:
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
    for d in winter_olympics_all:
      if year_s in d:
        year_dict['winter'] = olympic_sentences[3] + winter_olympics_all[year_s]
    for d in winter_olympics_all:
      t = year - 1
      year_int = str(t)
      if year_int in d:
        year_dict['p_winter'] = olympic_sentences[4] + winter_olympics_all[year_int]
    for d in winter_olympics_all:
      t = year + 1
      year_int = str(t)
      if year_int in d:
        year_dict['f_winter'] = olympic_sentences[5] + winter_olympics_all[year_int]
    #write the entry in the dict
    pop_sport_hints_year[year] = year_dict
  return pop_sport_hints_year

#CALL FUNCTION
#returns a dictionary of the years that occured in the xls file, with its corresponding hints from the most popular sports events of that year.
def get_year_sports_hints(qa_dict):
  file_years_list = []
  # for index, row in year_df.iterrows():
  for index, row in qa_dict.items():
    file_years_list.append(index)
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
  # filename = "./automaticHintGeneration/vizgr_events.xml"
  filename = "vizgr_events.xml"
  saved_file = download_xml_file(url, filename)
  result = parse_xml_file(saved_file)
  return result

#put everything together
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
  # for index, row in year_df.iterrows():
  for index, row in qa_dict.items():
    # print(index,row)
    if index < 2014:
      file_years_list.append(index)
  final_hints = {}
  for year in file_years_list:
    inter_start_date = str(year) + "0101"
    inter_end_date = str(year) + "1231"
    #print(inter_start_date, inter_end_date)
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

"""
Calls the three different function types of generating years hints, combines them into a single dict and calculate the similarity score between question and hint to rank them.
Returns:  dict: A dictionary with the date as the key and the description up until the first dot as the value.
Test for utility score of new questions; calculate score via BERT for each question,hint pair and write the score together with the question into the sim_scores dictionary.
"""
def generate_hints_years(qa_dict):
  pop_year_hints = get_year_sports_hints(qa_dict)
  pop_thumb_hints = get_year_thumbcaption_hints(qa_dict)
  pop_vizgr_hints = get_year_vizgr_hints(qa_dict)
  years_hints = {}
  for y in pop_year_hints:
    year_dict = {
        'sports': pop_year_hints[y],
        'thumbcaption': pop_thumb_hints[y],
        'vizgr' : pop_vizgr_hints[y]
    }
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
              similarity_score = get_similarity_score(q,value)
              sim_scores[year][category][key][value] = similarity_score
          elif category == 'thumbcaption':
            for i in subdata:
              sim_scores[year][category] = {}
              similarity_score = get_similarity_score(q,i)
              sim_scores[year][category][i] = similarity_score
          elif category == 'vizgr':
            for key, value in subdata.items():
              sim_scores[year][category][key] = {}
              similarity_score = get_similarity_score(q,value)
              sim_scores[year][category][key][value] = similarity_score
      else:
        continue
  for y, q in qa_dict.items():
    for year, data in generated_hints_for_years.items():
      if y == year:
        sim_scores[year]['question'] = q
  ordered_dict = order_dictionary(sim_scores)
  return ordered_dict

#generates and prints the hints in the testSet.xlms file
qa_dict = dict(zip(year_df['Answer'], year_df['Question']))
years_hints = generate_hints_years(qa_dict)
pprint.pprint(years_hints, indent=1,sort_dicts=False)
