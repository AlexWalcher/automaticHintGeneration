from my_modul import *


import streamlit as st
import os.path
import pathlib
from streamlit_option_menu import option_menu
from io import StringIO

from pathlib import Path
import pandas as pd

with st.sidebar:
    selected = option_menu("Main Menu", [ "Home", 'Upload file', 'Year question', 'Person question', 'Location question', 'Example usage'],
        icons=['house', 'upload', '123', 'person', 'compass', 'gear'], menu_icon="cast", default_index=0)

if selected == "Home":
    st.title('Automatic Hint Generation using Wikipedia')
    st.subheader('This WebApp takes a question, answer pair and returns a corresponding hint.')

elif selected == "Upload file":
    st.header('You have the option to upload a file with multiple different questions and recieve a corresponding download file with all the hints.')
    st.subheader('Upload:')
    gen_hints = {}
    uploaded_file = st.file_uploader("Choose a xlsx file", type=['xlsx', 'csv'])
    if uploaded_file is not None:
        st.write('Thanks for your question, wait a moment until your hint is generated.')
    #   save_folder = '/mount/src/automatichintgeneration/tmp/'
        file_name = 'testSet_WebApp.xlsx'
    #   save_path = Path(save_folder, file_name)
        save_path = os.getcwd()
        test_path = os.path.join(save_path, 'data')
        complete_name = test_path + '/testSet_WebApp.xlsx'
        with open(complete_name, mode='wb') as w:
            w.write(uploaded_file.getvalue())
            df = pd.read_excel(complete_name, sheet_name='Sheet1')
            df.to_excel(complete_name)
        if Path(complete_name).exists():
            st.success(f'uploaded_file {file_name} is successfully saved!')
            with st.spinner('Generating ...'):
                file_path = complete_name
                gen_hints = generate_hints_from_xlsx(file_path)
            st.write('Generated hints:')

        file_name = '/results.xlsx'
        # download_path = Path(save_folder, file_name)
        download_path = test_path + file_name
        df_download = pd.read_excel(download_path, sheet_name='Sheet1')

        filpat = download_path

        with open(filpat, "rb") as template_file:
            template_byte = template_file.read()

            st.download_button(label="Click to Download Template File",
                        data=template_byte,
                        file_name="template.xlsx",
                        mime='application/octet-stream')
            
        # n = {'Hints': prin_dat}
        df = pd.DataFrame(data=gen_hints)
        st.table(df)
        # st.write(gen_hints)

    st.write('Example Question:')    
    st.write('The uploaded file should be a Excel (xlsx) file and must contain a Question, Answer and Category cell in the first row of the file.' )
    st.write('Example file:')

    d = {'Question': [ 'Who was the 2022 F1 World Drivers champion?', 'When was the University of Innsbruck founded?', 'What is the capital of Austria?'], 'Answer': ['Max Verstappen', 1669, 'Vienna'], 'Category': ['person', 'year', 'location']}
    df = pd.DataFrame(data=d)
    st.table(df)



elif selected == "Year question":
    st.header('Enter the years-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    gen_hints = {}
    with st.form(key="Year_Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        Answer=st.number_input(label='Please enter the corresponding answer', min_value=0, max_value=2050, value=2022, format="%i") #Collect user feedback
        year_as_txt = str(Answer)
        Answer = int(year_as_txt)
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            save_path = os.getcwd()
            test_path = os.path.join(save_path, 'data')
            complete_name = test_path + '/questionYear.txt'      
            open(complete_name, 'w').close()
            with open(complete_name, 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + year_as_txt
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                file_path = complete_name
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            prin_dat = []
            year_sport = gen_hints['years'][Answer]['sports']
            for prs, hints in year_sport.items():
                for x,y in hints.items():
                    prin_dat.append(x)
            try:
                year_vizgr = gen_hints['years'][Answer]['vizgr']
                for prs, typ in year_vizgr.items():
                    for x,y in typ.items():
                        prin_dat.append(x)
            except Exception as ee:
                print(ee)
            n = {'Hints': prin_dat}
            df = pd.DataFrame(data=n)
            st.table(df)

    st.write('Example Question:')
    d = {'Question': [ 'In what year was the first -Lord of the Rings- book published?'], 'Answer': ['1954']}
    df = pd.DataFrame(data=d)
    st.table(df)
    st.write('Generated hints for example question: ')
    d = {'Hints': [
        'In the same year, West Germany has won the FIFA World Cup.', 
        'In the same year, July 4 the FIFA World Cup is held in Switzerland.',
        'In the same year, west Germany beats Hungary 3–2 to win the FIFA World Cup.',
        "In the same year, william Golding's novel ''Lord of the Flies'' is published in London.",
        'In the same year, the Boeing 707 is released after about two years of development.']}
    df = pd.DataFrame(data=d)
    st.table(df)


elif selected == "Location question":
    st.header('Enter the location-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    gen_hints = {}
    with st.form(key="Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        Answer=st.text_input(label='Please enter the corresponding answer') #Collect user feedback
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            save_path = os.getcwd()
            test_path = os.path.join(save_path, 'data')
            complete_name = test_path + '/questionLocation.txt'

            open(complete_name, 'w').close()
            with open(complete_name, 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                file_path = complete_name
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            prin_dat = []
            try:
                prs_cat = gen_hints['locations']['properties'][Answer]
                for prs, hints in prs_cat.items():
                    if prs != 'question':
                        for x,y in hints.items():
                            prin_dat.append(x)

                n = {'Hints': prin_dat}
                df = pd.DataFrame(data=n)
                st.table(df)
            except Exception as e:
                st.write(gen_hints)
    
    st.write('Example Question:')
    d = {'Question': [ 'General Franco became leader of which country in 1939 after a Civil War?'], 'Answer': ['Spain']}
    df = pd.DataFrame(data=d)
    st.table(df)
    st.write('Generated hints for example question: ')
    d = {'Hints': [
        'Head of government of searched location is Pedro Sánchez.', 
        'The highest point in searched location is Teide.',
        'Some of the next bodies of water of searched location are Cantabrian Sea, Alboran Sea, Atlantic Ocean.',
        "The searched location shares border with France, Arab League, Mauritania.",
        'The capital of searched location is  Madrid.']}
    df = pd.DataFrame(data=d)
    st.table(df)

elif selected == "Person question":
    st.header('Enter the person-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    gen_hints = {}
    # st.write("WTF!")
    with st.form(key="Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        Answer=st.text_input(label='Please enter the corresponding answer') #Collect user feedback
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            save_path = os.getcwd()
            test_path = os.path.join(save_path, 'data')
            complete_name = test_path + '/questionPerson.txt'
            open(complete_name, 'w').close()
            with open(complete_name, 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                file_path = complete_name
                st.write()
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            prin_dat = []

            prs_cat = gen_hints['people']['categories']
            prs_pred = gen_hints['people']['predicates']
            
            for prs, hints in prs_cat.items():
                for x,y in hints.items():
                    prin_dat.append(x)
            for prs, typ in prs_pred.items():
                for i, hint in typ.items():
                    if isinstance(hint, dict):
                        for l,m in hint.items():
                            prin_dat.append(l)
            n = {'Hints': prin_dat}
            df = pd.DataFrame(data=n)
            st.table(df)
    
    st.write('Example Question:')
    d = {'Question': [ 'Who is the owner of the renamed social media platform X?'], 'Answer': ['Elon Musk']}
    df = pd.DataFrame(data=d)
    st.table(df)
    st.write('Generated hints for example question: ')
    d = {'Hints': [
        'The person you are looking for has won multiple awards in his life, some of them are Honorary degree, honorary doctorate and Fellow of the Royal Society.', 
        'The person you are looking for is/was an employee at the following companies: PayPal, SpaceX and Tesla, Inc..',
        'The person you are looking for, is occupied as programmer, engineer and entrepreneur.',
        "The person you are looking for is/was the owner of: Tesla, Inc., X.com and Elon Musk's Tesla Roadster.",
        'The person you are looking for is holding/has held the following positions as an eployee: chief executive officer, chief technology officer and chairperson.',
        'The person you are looking for, has 3 children and 3 siblings.',
        'The person you are looking for was born on 28.06.1971 in Pretoria.']}
    df = pd.DataFrame(data=d)
    st.table(df)

    
elif selected == "Example usage":
    st.title('The following list contains examples for a better understanding of how to use the app.')

    st.subheader('Examples for singel <question, answer> pairs:')
    st.write('Choose the desired type from the Menu on the left: either Year, Person or Location. Then just enter the question with the corresponding answer.' )

    st.write('Question 1:')
    d = {'Question': [ 'Who was 2022 F1 World Drivers champion?'], 'Answer': ['Max Verstappen']}
    df = pd.DataFrame(data=d)
    st.table(df)
    st.write('Generated hints for question 1: ')
    d = {'Hints': [
        'The person you are looking for is/was occupied as racing automobile driver, Formula One driver, racing driver and a member of the category Twitch (service) streamers.', 
        'The person you are looking for, is occupied as racing automobile driver, Formula One driver and racing driver.',
        'The person you are looking for was born on 30.09.1997 in Hasselt.',
        'The person you are looking for has won multiple awards in his life, some of them are Talent of the year, Dutch Sportsman of the year and Lorenzo Bandini Trophy.'        ]}
    df = pd.DataFrame(data=d)
    st.table(df)
    
    st.write('Question 2:')
    d = {'Question': [ 'Who is the owner of the renamed social media platform X?'], 'Answer': ['Elon Musk']}
    df = pd.DataFrame(data=d)
    st.table(df)
    st.write('Generated hints for question 2: ')
    d = {'Hints': [
        'The person you are looking for has won multiple awards in his life, some of them are Honorary degree, honorary doctorate and Fellow of the Royal Society.', 
        'The person you are looking for is/was an employee at the following companies: PayPal, SpaceX and Tesla, Inc..',
        'The person you are looking for, is occupied as programmer, engineer and entrepreneur.',
        "The person you are looking for is/was the owner of: Tesla, Inc., X.com and Elon Musk's Tesla Roadster.",
        'The person you are looking for is holding/has held the following positions as an eployee: chief executive officer, chief technology officer and chairperson.',
        'The person you are looking for, has 3 children and 3 siblings.',
        'The person you are looking for was born on 28.06.1971 in Pretoria.']}
    df = pd.DataFrame(data=d)
    st.table(df)

    st.subheader('For multiple <question, answer> pairs:')
    st.write('Choose the Upload file page from the Menu on the left.' )
    st.write('The uploaded file should be a Excel (xlsx) file and must contain a Question, Answer and Category cell in the first row of the file.' )
    st.write('Example file:')

    d = {'Question': [ 'Who was the 2022 F1 World Drivers champion?', 'When was the University of Innsbruck founded?', 'What is the capital of Austria?'], 'Answer': ['Max Verstappen', 1669, 'Vienna'], 'Category': ['person', 'year', 'location']}
    df = pd.DataFrame(data=d)
    st.table(df)

    st.write('After the calculation, the hints can be downloaded as a Excel file and are printed on the webpage as well.')