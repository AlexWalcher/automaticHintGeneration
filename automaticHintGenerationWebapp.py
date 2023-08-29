from my_modul import *


import streamlit as st
import os.path
import pathlib
from streamlit_option_menu import option_menu

from pathlib import Path
import pandas as pd

with st.sidebar:
    selected = option_menu("Main Menu", ['Test', "Home", 'Upload file', 'Year question', 'Person question', 'Location question'],
        icons=['house', 'house', 'upload', '123', 'person', 'compass'], menu_icon="cast", default_index=0)

if selected == "Tester":
    st.title('Automatic Hint Generation using Wikipedia')
    st.subheader('This WebApp takes a question, answer pair and returns a corresponding hint.')

    uploaded_file = st.file_uploader("Choose a CSV file")
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        data = uploaded_file.getvalue().decode('utf-8').splitlines()         
        st.session_state["preview"] = ''
        for i in range(0, min(5, len(data))):
            st.session_state["preview"] += data[i]
    preview = st.text_area("CSV Preview", "", height=150, key="preview")
    upload_state = st.text_area("Upload State", "", key="upload_state")

    def upload():
        if uploaded_file is None:
            st.session_state["upload_state"] = "Upload a file first!"
        else:
            data = uploaded_file.getvalue().decode('utf-8')
            parent_path = pathlib.Path(__file__).parent.parent.resolve()
            st.write(parent_path)           
            save_path = os.path.join(parent_path, "data")
            complete_name = os.path.join(save_path, uploaded_file.name)
            destination_file = open(complete_name, "w")
            destination_file.write(data)
            destination_file.close()
            st.session_state["upload_state"] = "Saved " + complete_name + " successfully!"

    st.button("Upload file to Sandbox", on_click=upload)

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
      save_folder = '/mount/src/automatichintgeneration/tmp/'
      file_name = 'testSet_WebApp.xlsx'
      save_path = Path(save_folder, file_name)
      with open(save_path, mode='wb') as w:
        w.write(uploaded_file.getvalue())
        df = pd.read_excel(save_path, sheet_name='Sheet1')
        df.to_excel(save_path)
      if save_path.exists():
        st.success(f'uploaded_file {file_name} is successfully saved!')
        with st.spinner('Generating ...'):
            file_path = "/mount/src/automatichintgeneration/tmp/testSet_WebApp.xlsx"
            gen_hints = generate_hints_from_xlsx(file_path)
        st.write('Generated hints:')
        # for key, value in gen_hints.items():
        #     if key == "years":
        #         for year, hint_type in value.items():
        #             for k, v in hint_type.items():
        #                 st.write(v)
        #     else:
        #         for pel, hint_type in value.items():
        #             for per, val in hint_type.items():
        #                 if isinstance(val, dict):
        #                     for k, v in val.items():
        #                         st.write(v)
        #                     else:
        #                         st.write(val)
        save_folder = '/mount/src/automatichintgeneration/tmp/'
        file_name = 'results.xlsx'
        download_path = Path(save_folder, file_name)
        df_download = pd.read_excel(download_path, sheet_name='Sheet1')

        # st.dataframe(df_download)
        # # Create a download button
        # st.download_button(label="Download XLSX", data=df_download.to_excel, file_name="results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        filpat = "/mount/src/automatichintgeneration/tmp/results.xlsx"

        with open(filpat, "rb") as template_file:
            template_byte = template_file.read()

            st.download_button(label="Click to Download Template File",
                        data=template_byte,
                        file_name="template.xlsx",
                        mime='application/octet-stream')

        st.write(gen_hints)

elif selected == "Year question":
    st.header('Enter the years-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    gen_hints = {}
    with st.form(key="Year_Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        #Answer=st.number_input(label='Please enter the corresponding answer') #Collect user feedback
        Answer=st.number_input(label='Please enter the corresponding answer', min_value=0, max_value=2050, value=2022, format="%i") #Collect user feedback
        year_as_txt = str(Answer)
        Answer = int(2018)
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            open("/mount/src/automatichintgeneration/tmp/questionYear.txt", 'w').close()
            with open("/mount/src/automatichintgeneration/tmp/questionYear.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + year_as_txt
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                file_path = "/mount/src/automatichintgeneration/tmp/questionYear.txt"
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            st.write(gen_hints)

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
            open("/mount/src/automatichintgeneration/tmp/questionLocation.txt", 'w').close()
            with open("/mount/src/automatichintgeneration/tmp/questionLocation.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                file_path = "/mount/src/automatichintgeneration/tmp/questionLocation.txt"
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            st.write(gen_hints)

elif selected == "Person question":
    st.header('Enter the person-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    gen_hints = {}
    st.write("WTF!")
    with st.form(key="Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        Answer=st.text_input(label='Please enter the corresponding answer') #Collect user feedback
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            open("/mount/src/automatichintgeneration/tmp/questionPerson.txt", 'w').close()
            with open("/mount/src/automatichintgeneration/tmp/questionPerson.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                file_path = "/mount/src/automatichintgeneration/tmp/questionPerson.txt"
                st.write()
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            st.write(gen_hints)