# Cyber Security Course Advisor Deployment Guide

**Authors:** Meidie Fei (s4155089), Banharith Ly (s4045086)

**Purpose:** This guide supports assessment of the RMIT Cyber Security Course Advisor project. It details how to set up and run the chatbot, review its knowledge integration, and evaluate its deployment using AWS Bedrock.

---

## Project Overview

This project is a browser-based chatbot built with Streamlit and powered by Claude (via AWS Bedrock). It helps students in the **Bachelor of Cyber Security (BP355/BP356)** program explore courses, program structure, and RMIT resources.

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
```

---

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

---

## AWS Configuration (for assessors with IAM access)

Open `app.py` and insert your credentials:

```python
USERNAME = "<your RMIT student email>"
PASSWORD = "<temporary password from admin>"
```

If you are not registered in Cognito, contact the instructor for a test account or follow in read-only mode.

---

## Running the Chatbot

### Step 1: Start the app

```bash
streamlit run app.py
```

The chatbot will open in your browser at:
[http://localhost:8501](http://localhost:8501)

### Step 2: Use the interface

* Ask questions about enrolment, policies, or program structure
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

* "What courses should I take in Year 2?"
* "Can I choose electives related to AI?"
* "What are the fees for domestic students?"

The assistant responds using structured context and scraped information.

---

## Testing Notes

* Data limit: First \~2000 words of `rmit_data.db` are passed to Claude to avoid token overload.
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