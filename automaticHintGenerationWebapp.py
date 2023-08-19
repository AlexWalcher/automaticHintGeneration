from my_modul import *

import streamlit as st
from streamlit_option_menu import option_menu
from pathlib import Path
import pandas as pd
import tempfile
from tempfile import NamedTemporaryFile


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
    #   save_folder = '/content/automaticHintGeneration/tmp'
      save_folder='/mount/src/automatichintgeneration/tmp'
      file_name = 'testSet_WebApp.xlsx'
      save_path = Path(save_folder, file_name)
      with open(save_path, mode='wb') as w:
        w.write(uploaded_file.getvalue())
        df = pd.read_excel(save_path, sheet_name='Sheet1')
        df.to_excel(save_path)
      if save_path.exists():
        st.success(f'uploaded_file {file_name} is successfully saved!')
        with st.spinner('Generating ...'):
            # file_path = "/content/automaticHintGeneration/tmp/testSet_WebApp.xlsx"
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
        # save_folder = '/content/automaticHintGeneration/tmp/'
        save_folder = '/mount/src/automatichintgeneration/tmp/'
        file_name = 'results.xlsx'
        download_path = Path(save_folder, file_name)
        df_download = pd.read_excel(download_path, sheet_name='Sheet1')

        # st.dataframe(df_download)
        # # Create a download button
        # st.download_button(label="Download XLSX", data=df_download.to_excel, file_name="results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        # filpat = "/content/automaticHintGeneration/tmp/results.xlsx"
        filpat = "/mount/src/automatichintgeneration/tmp/results.xlsx"

        with open(filpat, "rb") as template_file:
            template_byte = template_file.read()

            st.download_button(label="Click to Download Template File",
                        data=template_byte,
                        file_name="template.xlsx",
                        mime='application/octet-stream')

        st.write(gen_hints)

elif selected == "Test":
    uploaded_file = st.file_uploader("File upload", type='xlsx')
    with NamedTemporaryFile(dir='.', suffix='.xlsx') as f:
        f.write(uploaded_file.getbuffer())
        st.write(f.name)


elif selected == "Year question":
    st.header('Enter the years-question with the answer and wait for the corresponding hint to be generated.')
    st.subheader('Input:')
    with st.form(key="Year_Form :", clear_on_submit = True):
        Question=st.text_input(label='Please enter your question') #Collect user feedback
        #Answer=st.number_input(label='Please enter the corresponding answer') #Collect user feedback
        Answer=st.number_input(label='Please enter the corresponding answer', min_value=0, max_value=2050, value=2022, format="%i") #Collect user feedback
        year_as_txt = str(Answer)
        Answer = int(2018)
        submitted = st.form_submit_button('Submit')
        if submitted:
            st.write('Thanks for your question, wait a moment until your hint is generated.')
            # with open("/content/automaticHintGeneration/tmp/questionYear.txt", 'a') as writefile:
            # with open("/mount/src/automatichintgeneration/tmp/questionYear.txt", 'a') as writefile:
            with tempfile.NamedTemporaryFile() as writefile:
                ## Writes the SGY to the temporal file
                # tempSGY.write(uploadedSGY.getbuffer())


                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + year_as_txt
                writefile.write(item + "\n")
                # writefile.close()
                with st.spinner('Generating ...'):
                    # file_path = "/content/automaticHintGeneration/tmp/questionYear.txt"
                    # file_path = "/mount/src/automatichintgeneration/tmp/questionYear.txt"

                    # gen_hints = generate_hints_from_txt(file_path)

                    gen_hints = generate_hints_from_txt(writefile.name)
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
            # with open("/content/automaticHintGeneration/tmp/questionLocation.txt", 'a') as writefile:
            with open("/mount/src/automatichintgeneration/tmp/questionLocation.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                # file_path = "/content/automaticHintGeneration/tmp/questionLocation.txt"
                file_path = "/mount/src/automatichintgeneration/tmp/questionLocation.txt"
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
            # with open("/content/automaticHintGeneration/tmp/questionPerson.txt", 'a') as writefile:
            with open("/mount/src/automatichintgeneration/tmp/questionPerson.txt", 'a') as writefile:
                item = 'Question: ' + str(Question) + '; ' + 'Answer: ' + str(Answer)
                writefile.write(item + "\n")
                writefile.close()
            with st.spinner('Generating ...'):
                # file_path = "/content/automaticHintGeneration/tmp/questionPerson.txt"
                file_path = "/mount/src/automatichintgeneration/tmp/questionPerson.txt"
                gen_hints = generate_hints_from_txt(file_path)
            st.write('Generated hints:')
            st.write(gen_hints)
