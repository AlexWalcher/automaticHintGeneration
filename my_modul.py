"""
File that contains the final hint generation functions where all of the one from the functionsHintGeneration file are orchestrated to work together.
"""

imports_path = "/content/automaticHintGeneration/importsHintGeneration"
import sys
sys.path.insert(0, imports_path)

from importsHintGeneration import *
from functionsHintGeneration import *

#file_path = "./tmp/testSet_WebApp.xlsx"
# file_path = "./automaticHintGeneration/testSet.xlsx"
file_path = "/content/automaticHintGeneration/testSet.xlsx"
df_list = load_file_path(file_path)
person_df = df_list["person"]
year_df = df_list["year"]
location_df = df_list["location"]

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
  df = pd.read_excel("/content/automaticHintGeneration/tmp/testSet_WebApp.xlsx")
  # Drop the first column by positional index
  df = df.iloc[:, 1:]
  # Write the updated DataFrame back to the Excel file
  df.to_excel("/content/automaticHintGeneration/tmp/testSet_WebApp.xlsx", index=False)
  return True

def read_properties_from_file(file_path):
  question = None
  answer = None
  try:
    with open(file_path, 'r') as file:
      for line in file:
        parts = line.split(';')
        for part in parts:
          if part.strip().startswith('Question:'):
            question = part.replace('Question:', '').strip()
          elif part.strip().startswith('Answer:'):
            answer = part.replace('Answer:', '').strip()
  except FileNotFoundError:
    print(f"File not found at path: {file_path}")
  
  print(question, answer)

  question = question.replace(";", "")

  return question, answer


def generate_hints_from_txt(file_path):
  generated_hint_sentences = {}
  inter = read_properties_from_file(file_path)

  question = inter[0]
  answer = inter[1]
  # print(question, answer)

  if "Year" in file_path:
    #generates the hints for the YEARS question
    # year_questions_dict = dict(zip(answer.item(), question.item()))
    year_as_int = int(answer)
    year_as_txt = str(answer)
    year_questions_dict = {}
    year_questions_dict[year_as_int] = question
    # pprint.pprint(year_questions_dict)
    years_hints = generate_hints_years(year_questions_dict)
    generated_hint_sentences['years'] = years_hints
  elif "Location" in file_path:
    #generates the hints for the LOCATION question
    location_questions_dict = {}
    location_questions_dict[answer] = question
    # dataLocation.append(location_questions_dict)
    # pprint.pprint(location_questions_dict)
    location_hints_unexpected_categories = get_location_hints_unexpected_categories(location_questions_dict)
    location_hints_fixed_properties = get_location_hints_fixed_properties(location_questions_dict)
    location_hints = {}
    location_hints['categories'] = location_hints_unexpected_categories
    location_hints['properties'] = location_hints_fixed_properties
    generated_hint_sentences['locations'] = location_hints
  elif "Person" in file_path:
    #generates the hints for the PEOPLE question
    person_questions_dict ={}
    person_questions_dict[answer] = question
    # dataPerson.append(person_questions_dict)
    pprint.pprint(person_questions_dict)
    people_hints_unexpected_categories = get_person_hints_unexpected_categories(person_questions_dict)
    people_hints_unexpected_predicates = get_person_hints_unexpected_predicates(person_questions_dict)
    people_hints = {}
    people_hints['categories'] = people_hints_unexpected_categories
    people_hints['predicates'] =  people_hints_unexpected_predicates
    generated_hint_sentences['people'] = people_hints
  else:
    print(f"File not found at path: {file_path}")
    pass

  return generated_hint_sentences