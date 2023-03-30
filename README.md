# optimizationOfHintGeneration 

**At the moment the program could be in a** *not stable* **version because I reused the existing notebook as a basis and extended it constantly. At the end of my Theisis this shouldn't be the case anymore.**

This project is based on [Calvin Gehrer's automaticHintGeneration](https://github.com/calvingehrer/automaticHintGeneration#readme) and will be extended and optimized by me during my Bachelor Thesis in colaboration with Univ.-Prof. Adam Jatowt, PhD as supervisor. 
Furthermore, a web application will be created for easy and future use of the software.

### **Goals:**
You should be able to insert your question, with it's correct answer and the corresponding type of the question. Then you get a automatically generated hint back. The input should be possbile manually or by uploading a *.xlsx file*. 

This program should be able to handle three general types of questions: 

 - **Location-Questions: Where?** 
 - **Person-Questions: Who?** 
 - **Year-Questions: When?** 

### **Limitations:**
It does achieve this by retrieving data from Wikidata and Wikipedia, therefor the answer to the question should always be a Wikipedia-entity.

### **Added/planned features:**

- create a **App or Webapp** for easy and future use of the software
- rewrite/modify the **backlinks calculations** (use [Pageviews Analysis Website](https://pageviews.wmcloud.org/pageviews/url_structure/)) instead of calculating them by hand
- optimize and adjust the qrank and utility score 
- introduce a improved category ranking further based on popularity
- introduce a **difficulty setting** that refers to the difficulty of a generated hint (weak-, medium-, strong- hint)
- introduce a **"obviousness" metric** to understand if the generated hint is too strong/good and gives away the answer to easy
- introduce a **"same infromation" metric** to filter out hints that doesn't lead you closer to the answer


This project is based on a ongoing **Bachelor Thesis** of the **University of Innsbruck**: 
[*Adam Jatowt and Alex Walcher: Automatic Hint Generation using Wikipedia and Wikidata*](https://ds-informatik.uibk.ac.at/doku.php?id=current_topics)
