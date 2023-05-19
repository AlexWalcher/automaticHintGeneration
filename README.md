# Automatic hint generation using Wikipedia

**Ongoing project: At the moment the program is extended and updated constantly.**

This project is part of my ongoing **Bachelor Thesis** at the **University of Innsbruck**: 
[*Adam Jatowt and Alex Walcher: Automatic hint generation using Wikipedia*](https://ds-informatik.uibk.ac.at/doku.php?id=current_topics)

### **Goals:**
A user should be able to insert questions with the correct answers and the corresponding types of questions. (<question, answer, type> - pairs) Then the program returns a file with automatically generated hints. The input should be possbile manually or by uploading a *.xlsx file*. 

This program should be able to handle three general types of questions: 

 - **Location-Questions: Where?** 
 - **Person-Questions: Who?** 
 - **Year-Questions: When?** 

### **Limitations:**
It does achieve this by retrieving data from Wikidata and Wikipedia, therefor the answer to the question should always be a Wikipedia-entity.

### **Planned features:**

- create a **App or Webapp** for easy and future use of the software
- add pools of popular events for years questions
- add new approaches to find important pieces of information for years questions
- optimize and adjust the qrank and utility score 
- introduce a **difficulty setting** that refers to the difficulty of a generated hint (weak-, medium-, strong- hint)
- introduce a **"obviousness" metric** to understand if the generated hint is too strong/good and gives away the answer to easy
- introduce a **"same infromation" metric** to filter out hints that doesn't lead you closer to the answer

### **Added features:**
- introduced and improved category and information retrieval as well as pageview calculation
- introduced a popular-sports-events pool for years-questions
- introduced a unexpectedness metric to find unexpected/unusual/surprising categories for person-questions

This project is based on [Calvin Gehrer's automaticHintGeneration](https://github.com/calvingehrer/automaticHintGeneration#readme) and will be extended and optimized by me during my Bachelor Thesis in colaboration with Univ.-Prof. Adam Jatowt, PhD as supervisor. 
