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
# file_path='/mount/src/automatichintgeneration/testSet.xlsx'
# # file_path = "/content/automaticHintGeneration/testSet.xlsx"
# df_list = load_file_path(file_path)
# person_df = df_list["person"]
# year_df = df_list["year"]
# location_df = df_list["location"]

def save_as_xlsx_file(year_questions_dict, person_questions_dict, location_questions_dict, generated_hint_sentences):
  year_dict_list =[]
  for answer,question in year_questions_dict.items():
    year_dict = {}
    year_dict['question'] = question
    year_dict['answer'] = answer
    year_dict['category'] = 'Year'
    hint_list=[]
    for typ,value in generated_hint_sentences['years'][answer].items():
      if typ != 'question':
        for sports, hints in value.items():
          for a,b in hints.items():
            hint_list.append(a)
    year_dict['hints'] = hint_list
    year_dict_list.append(year_dict)
  # pprint.pprint(year_dict_list)
  person_dict_list =[]
  for answer, question in person_questions_dict.items():
    person_dict = {}
    person_dict['question'] = question
    person_dict['answer'] = answer
    person_dict['category'] = 'people'
    hint_list=[]
    for cat, value in generated_hint_sentences['people'].items():
      if cat == 'categories':
        for pers,hin in value.items():
          if pers == answer:
            for a,b in hin.items():
              hint_list.append(a)
      elif cat == 'predicates':
        for pers,hin in value.items():
          if pers == answer:
            for a,b in hin.items():
              if a != 'question':
                for c,d in b.items():
                  hint_list.append(c)
    person_dict['hints'] = hint_list
    person_dict_list.append(person_dict)
  # pprint.pprint(person_dict_list)
  location_dict_list =[]
  for answer, question in location_questions_dict.items():
    location_dict = {}
    location_dict['question'] = question
    location_dict['answer'] = answer
    location_dict['category'] = 'location'
    hint_list=[]
    for cat, value in generated_hint_sentences['locations'].items():
      if cat == 'properties':
        for pers,hin in value.items():
          if pers == answer:
            for a,b in hin.items():
              if a != 'question':
                for c,d in b.items():
                  hint_list.append(c)
    location_dict['hints'] = hint_list
    location_dict_list.append(location_dict)
  # pprint.pprint(location_dict_list)
  gen_hints = {}
  gen_hints['years'] = year_dict_list
  gen_hints['people'] = person_dict_list
  gen_hints['locations'] = location_dict_list

  dict_list=[]
  for a in year_dict_list:
    dict_list.append(a)
  for a in person_dict_list:
    dict_list.append(a)
  for a in location_dict_list:
    dict_list.append(a)
  # Convert the list of dictionaries to a pandas DataFrame
  df = pd.DataFrame(dict_list)
  # Define the order of columns (if you want a specific order)
  columns_order = ["question", "answer", "category", "hints"]
  df = df[columns_order]
  # Save the DataFrame to an Excel file
  output_file = "/mount/src/automatichintgeneration/tmp/results.xlsx"
  df.to_excel(output_file, index=False)

  return dict_list


"""# **Generate hints - (putting everything together)**"""
#Function that puts everything together
# Call hint-generation-functions for years, people and locations
# Save the results in a txt file
def generate_hints_from_xlsx(file_path):
  df_list = load_file_path(file_path)
  obj = Test()
  year_df = df_list["year"]
  person_df = df_list["person"]
  location_df = df_list["location"]
  year_questions_dict = dict(zip(year_df['Answer'], year_df['Question']))
  obj.set_year_questions_dict(year_questions_dict)
  person_questions_dict = dict(zip(person_df['Answer'], person_df['Question']))
  obj.set_person_questions_dict(person_questions_dict)
  gl_person_questions_dict_from_txt = person_questions_dict
  location_questions_dict = dict(zip(location_df['Answer'], location_df['Question']))
  obj.set_location_questions_dict(location_questions_dict)
  generated_hint_sentences = {}
  combined_hint_sentences = {}
  #generates the hints for the YEARS question
  years_hints = generate_hints_years(year_questions_dict)

  generated_hint_sentences['years'] = years_hints
  #generates the hints for the PEOPLE question
  people_hints_unexpected_categories = get_person_hints_unexpected_categories(person_questions_dict)
  people_hints_unexpected_predicates = get_person_hints_unexpected_predicates(person_questions_dict)
  people_hints = {}
  # people_hints['categories'] = people_hints_unexpected_categories

  people_hints['categories'] = people_hints_unexpected_categories
  people_hints['predicates'] = people_hints_unexpected_predicates
  generated_hint_sentences['people'] = people_hints
  #generates the hints for the LOCATION question
  # location_hints_unexpected_categories = get_location_hints_unexpected_categories(location_questions_dict)
  location_hints_fixed_properties = get_location_hints_fixed_properties(location_questions_dict)
  location_hints = {}
  # location_hints['categories'] = location_hints_unexpected_categories
  location_hints['properties'] = location_hints_fixed_properties
  generated_hint_sentences['locations'] = location_hints

  #safe results as xlsx to download
  #choose one with the highest, the lowest and a median score
  # dict_list = 
  save_as_xlsx_file(year_questions_dict, person_questions_dict, location_questions_dict, generated_hint_sentences)

  return generated_hint_sentences


def save_file():
  # Read the Excel file into a DataFrame
  df = pd.read_excel("/mount/src/automatichintgeneration/tmp/testSet_WebApp.xlsx")
  # Drop the first column by positional index
  df = df.iloc[:, 1:]
  # Write the updated DataFrame back to the Excel file
  df.to_excel("/mount/src/automatichintgeneration/tmp/testSet_WebApp.xlsx", index=False)
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
  
  # print(question, answer)
  question = question.replace(";", "")

  return question, answer


def generate_hints_from_txt(file_path):
  generated_hint_sentences = {}
  inter = read_properties_from_file(file_path)
  obj = Test()


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
    obj.set_year_questions_dict(year_questions_dict)
    # pprint.pprint(year_questions_dict)
    years_hints = generate_hints_years(year_questions_dict)
    # inter = check_sentences_for_asterisk(years_hints)
    generated_hint_sentences['years'] = years_hints
  elif "Location" in file_path:
    #generates the hints for the LOCATION question
    location_questions_dict = {}
    location_questions_dict[answer] = question
    obj.set_location_questions_dict(location_questions_dict)
    # dataLocation.append(location_questions_dict)
    # pprint.pprint(location_questions_dict)
    # location_hints_unexpected_categories = get_location_hints_unexpected_categories(location_questions_dict)
    location_hints_fixed_properties = get_location_hints_fixed_properties(location_questions_dict)
    location_hints = {}
    # location_hints['categories'] = location_hints_unexpected_categories
    location_hints['properties'] = location_hints_fixed_properties
    generated_hint_sentences['locations'] = location_hints
  elif "Person" in file_path:
    #generates the hints for the PEOPLE question
    person_questions_dict ={}
    person_questions_dict[answer] = question
    obj.set_person_questions_dict(person_questions_dict)
    gl_person_questions_dict_from_txt = person_questions_dict

    # dataPerson.append(person_questions_dict)
    # pprint.pprint(person_questions_dict)
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