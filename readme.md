# Cyber Security Course Advisor Deployment Guide

**Authors:** Meidie Fei (s4155089), Banharith Ly (s4045086)

**Purpose:** This guide supports assessment of the RMIT Cyber Security Course Advisor project. It details how to set up and run the chatbot, review its knowledge integration, and evaluate its deployment using AWS Bedrock.

---

## Project Overview

This project is a browser-based chatbot built with Streamlit and powered by Claude (via AWS Bedrock). It helps students in the **Bachelor of Cyber Security (BP355/BP356)** program explore courses, program structure, and RMIT resources. 
And have advanced to crawl the RMIT website for information for the knowledge base. Though we only limit the crawler for the first 2000 words as such there would be lack of information. 
However, with the information gathered the bot would be able to answer more than just **Bachelor of Cyber Security (BP355/BP356)**. Furthermore, the user can upload files for the knowledge base.
We also implemented a login in with 'demo' and 'demo' as the credentials, and a clear chat button to restart and restore the chatbot as a blank state.

---

## Folder Structure

```
cyber_security_chatbot/
├── app.py                         <- Main chatbot interface
├── data_crawler.py               <- Crawler script for scraping RMIT public pages
├── rmit_data.db                  <- SQLite DB containing scraped RMIT knowledge
├── courses_data.json             <- Course metadata (title, code, description)
├── cyber_security_program_structure.json <- Recommended structure by year
├── requirements.txt              <- Python package dependencies
├── rmit_bachelor_courses.json  <- Course from Bachelor including the points, title, code, and location
├── rmit_courses.json   <- Course from Master including the points, title, code, and location
```

---
#################################################################
**####Important####:THE LOGIN INFO FOR THE CHATBOT IS demo and demo**

## Python & Environment Setup

### Required Version: Python 3.11

Check your version:

```bash
python --version
```

If not 3.11, download from [python.org](https://www.python.org/downloads/release/python-3110/).

### Set up a virtual environment

```bash
cd cyber_security_chatbot
py -3.11 -m venv .venv
.\.venv\Scripts\activate      # On Windows
source .venv/bin/activate      # On macOS/Linux
```

### Install all dependencies

```bash
pip install -r requirements.txt
```

Note: If you plan to use the crawler to update `rmit_data.db`, ensure **BeautifulSoup** is installed:

```bash
pip install beautifulsoup4 requests
```

## Running the Chatbot

### Step 1: Start the app

```bash
streamlit run app.py
```

The chatbot will open in your browser at:
[http://localhost:8501]

### Step 2: Use the interface

* Ask questions about enrolment, policies, or program structure and you can upload pdf or json files
* The chatbot responds using JSON course data, recommended plans, and scraped public RMIT content

---

## Data Crawling (Dynamic Knowledge Base)

To refresh the scraped content:

```bash
python data_crawler.py
```

This will update `rmit_data.db` with the latest text from RMIT's public website (no login-required content).

---

## Example Prompts

*** Enter demo,demo for login ***
* "What is the entry requirements for bachelor of IT?"
* "Provide me a contact information"
* "I'm doing the bachelor of Information technology I would like to know what to enrol for the first year"

The assistant responds using structured context and scraped information.

---

## Testing Notes

* Data limit: First \~2000 words of `rmit_data.db` are passed to Claude to avoid token overload. As such some information isn't accessible for Claude and there are missing information. 
* Claude is instructed to avoid repeating user questions or listing irrelevant information unless directly asked.

---

## Troubleshooting

| Issue                          | Solution                               |
| ------------------------------ | -------------------------------------- |
| `streamlit` not found          | Activate virtual environment           |
| Chatbot shows nothing          | Check console logs for token errors    |
| Model echoes question + answer | Prompt fix: remove `Advisor:` from end |
| SQLite error                   | Ensure `rmit_data.db` is created first |

---

## Complete

The chatbot now meets the brief: integrates course metadata, supports live user queries, and enhances responses with scraped RMIT data.

Please refer to `data_crawler.py` for knowledge base update logic.