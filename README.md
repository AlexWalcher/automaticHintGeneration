# Automatic hint generation using Wikipedia

This project is part of my ongoing **Bachelor Thesis** at the **University of Innsbruck**:
[*Adam Jatowt and Alex Walcher: Automatic hint generation using Wikipedia*](https://ds-informatik.uibk.ac.at/doku.php?id=current_topics)

### **How to use the WebApp on Streamlit-Cloud:**
- open [*WebApp - Automatic hint generation*](https://automatichintgeneration.streamlit.app/)
- for further instructions go to the **Example Usage** Menu

### **How to use the program in Google-Colab:**
- open the file **WebAppHintGeneration.ipynb** and click the **GoogleColab** key
- this opens the Notebook as a GoogleColab project for testing purposes
- just follow the instructions in the Notebook for input and deployment

### **Description:**
A user is able to insert questions with the correct answers and the corresponding questions-type. (<question, answer, type> - pairs) Then the program returns a file with automatically generated hints. The input should be possbile manually via two text-fields or by uploading a *.xlsx file*. 

This program can handle three general types of questions:
 - **Location-Questions: Where?**
 - **Person-Questions: Who?**
 - **Year-Questions: When?**

### **Limitations:**
It does achieve this by retrieving data from Wikidata and Wikipedia, therefor the answer to the question should always be a Wikipedia-entity.
