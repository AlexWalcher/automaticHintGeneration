from my_modul import *

import streamlit as st
from streamlit_option_menu import option_menu
from pathlib import Path
import pandas as pd

with st.sidebar:
    selected = option_menu("Main Menu", ["Home", 'Upload file', 'Year question', 'Person question', 'Location question'],
        icons=['house', 'upload', '123', 'person', 'compass'], menu_icon="cast", default_index=0)

if selected == "Home":
    st.title('Automatic Hint Generation using Wikipedia')
    st.subheader('This WebApp takes a question, answer pair and returns a corresponding hint.')

elif selected == "Upload file":
    st.header('You have the option to upload a file with multiple different questions and recieve a corresponding download file with all the hints.')
    st.subheader('Upload:')
    uploaded_file = st.file_uploader("Choose a xlsx file", type=['xlsx', 'csv'])
    if uploaded_file is not None:
      st.write('Thanks for your question, wait a moment until your hint is generated.')
      save_folder = '/content/automaticHintGeneration/tmp'
      file_name = 'testSet_WebApp.xlsx'
      save_path = Path(save_folder, file_name)
      with open(save_path, mode='wb') as w:
        w.write(uploaded_file.getvalue())
        df = pd.read_excel(save_path, sheet_name='Sheet1')
        df.to_excel(save_path)
      if save_path.exists():
        st.success(f'uploaded_file {file_name} is successfully saved!')
        with st.spinner('Wait for it...'):
            file_path = "/content/automaticHintGeneration/tmp/testSet_WebApp.xlsx"
            gen_hints = generate_hints_from_xlsx(file_path)
        st.write('Generated hints:')
        st.write(gen_hints)

elif selected == "Year question":
    st.header('Enter the years-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    with st.form(key="Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        Answer=st.text_input(label='Please enter the corresponding answer') #Collect user feedback
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            with open("/content/automaticHintGeneration/tmp/questionYear.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Wait for it...'):
                file_path = "/content/automaticHintGeneration/tmp/questionYear.txt"
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            st.write(gen_hints)

elif selected == "Location question":
    st.header('Enter the location-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    with st.form(key="Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        Answer=st.text_input(label='Please enter the corresponding answer') #Collect user feedback
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            with open("/content/automaticHintGeneration/tmp/questionLocation.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Wait for it...'):
                file_path = "/content/automaticHintGeneration/tmp/questionLocation.txt"
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            st.write(gen_hints)

elif selected == "Person question":
    st.header('Enter the person-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    with st.form(key="Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        Answer=st.text_input(label='Please enter the corresponding answer') #Collect user feedback
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            with open("/content/automaticHintGeneration/tmp/questionPerson.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Wait for it...'):
                file_path = "/content/automaticHintGeneration/tmp/questionPerson.txt"
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            st.write(gen_hints)
