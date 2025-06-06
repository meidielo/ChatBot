# RMIT ChatBot
# Author: Meidie Fei, Banharith
# Updated: June 2025

import streamlit as st
import json
import boto3
import sqlite3
from datetime import datetime
from PyPDF2 import PdfReader

# === AWS Configuration === #
REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
IDENTITY_POOL_ID = "us-east-1:7771aae7-be2c-4496-a582-615af64292cf"
USER_POOL_ID = "us-east-1_koPKi1lPU"
APP_CLIENT_ID = "3h7m15971bnfah362dldub1u2p"
USERNAME = "s4155089@student.rmit.edu.au" # Replace with your username
PASSWORD = "c5ZvgdeVN7wghQ-"    # Replace with your password


# === Helper: Get AWS Credentials === #
def get_credentials(username, password):
    idp_client = boto3.client("cognito-idp", region_name=REGION)
    response = idp_client.initiate_auth(
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": password},
        ClientId=APP_CLIENT_ID,
    )
    id_token = response["AuthenticationResult"]["IdToken"]

    identity_client = boto3.client("cognito-identity", region_name=REGION)
    identity_response = identity_client.get_id(
        IdentityPoolId=IDENTITY_POOL_ID,
        Logins={f"cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
    )

    creds_response = identity_client.get_credentials_for_identity(
        IdentityId=identity_response["IdentityId"],
        Logins={f"cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}": id_token},
    )

    return creds_response["Credentials"]

# === load scraped RMIT content from SQLite ===
def load_rmit_pages(db_path="rmit_data.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT content FROM pages")
    all_pages = cur.fetchall()
    conn.close()
    # Join all page text together or keep separate as needed
    return "\n\n".join(page[0] for page in all_pages)

# Load all scraped RMIT content once at startup
rmit_knowledge = load_rmit_pages()

if "messages" not in st.session_state:
    st.session_state.messages = []

# === Helper: Build Prompt from JSON + Structure === #
def build_prompt(full_course_context, user_question, structure_text):
    # Load history
    history = st.session_state.get("messages", [])
    chat_history = ""

    for msg in history:
        if msg["role"] == "user":
            chat_history += f"User: {msg['content']}\n"
        elif msg["role"] == "assistant":
            chat_history += f"Advisor: {msg['content']}\n"

    course_dict = {c["title"]: c for c in courses}

    structure_text = ""
    if structure and "recommended_courses" in structure:
        structure_text += "### Recommended Study Plan by Year:\n"
        for year, course_titles in structure["recommended_courses"].items():
            structure_text += f"**{year.replace('_', ' ').title()}**:\n"
            for title in course_titles:
                course = course_dict.get(title)
                if course:
                    structure_text += f"- {title} ({course['course_code']})\n"
                else:
                    structure_text += f"- {title} (not found in course list)\n"
            structure_text += "\n"

    course_list = []
    for course in courses:
        title = course.get("title", "Untitled")
        code = course.get("course_code", "N/A")
        desc = course.get("description", "No description available.")
        course_type = course.get("course_type", "N/A")
        minor = course.get("minor_track", [])
        minor_info = f", Minor: {minor[0]}" if minor else ""
        course_text = f"- {title} ({code}): {desc}\n  Type: {course_type}{minor_info}"
        course_list.append(course_text)
    full_course_context = "\n".join(course_list)

    prompt = (
        "You are a helpful assistant that supports students in RMIT University related questions"
        "Recommend only from the official course list. Each course is categorized as core, capstone, minor, or elective. "
        "Use the recommended structure to suggest suitable courses based on study year and interest.\n\n"
        "Do not give personal advice unless the user has provided context. If they greet you or ask general questions, respond politely and prompt them for more information.\n\n"
        f"### Degree Structure:\n{structure_text}\n\n"
        f"### All Available Courses:\n{full_course_context}\n\n"
        f"### Conversation History:\n{chat_history}"
    )

    return prompt


# === Helper: Extract text from multiple PDFs === #
def extract_text_from_pdfs(pdf_files):
    all_text = []
    for pdf_file in pdf_files:
        try:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    all_text.append(text.strip())
        except Exception as e:
            all_text.append(f"[Error reading file {pdf_file.name}: {str(e)}]")
    return "\n\n".join(all_text)


# === Helper: Invoke Claude via Bedrock === #
def invoke_bedrock(prompt_text, max_tokens=640, temperature=0.3, top_p=0.9):
    credentials = get_credentials(USERNAME, PASSWORD)

    bedrock_runtime = boto3.client(
        "bedrock-runtime",
        region_name=REGION,
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretKey"],
        aws_session_token=credentials["SessionToken"],
    )

    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "messages": [{"role": "user", "content": prompt_text}]
    }

    response = bedrock_runtime.invoke_model(
        body=json.dumps(payload),
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]


# === Streamlit UI === #
st.markdown("""
<style>
/* Push content up when the mobile keyboard opens */
input:focus, textarea:focus {
    position: fixed !important;
    bottom: 80px !important;
    left: 5%;
    width: 90% !important;
    z-index: 999;
}

/* Ensure bottom spacing to prevent overlap */
.stApp {
    padding-bottom: 120px;
}
</style>
""", unsafe_allow_html=True)

st.set_page_config(page_title="RMIT Chatbot", layout="wide")
st.title("RMIT Chatbot")
st.markdown("This assistant helps students select courses and answer RMIT related questions.")

with open("courses_data.json", "r", encoding="utf-8") as f1:
    courses = json.load(f1)
with open("cyber_security_program_structure.json", "r", encoding="utf-8") as f2:
    structure = json.load(f2)
uploaded_pdfs = None


st.subheader("Chat with the Course Advisor")
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_question = st.chat_input("Ask about course enrolment, policies, or RMIT info...")

if user_question:
    # Save and display user message
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)
    full_course_context = "\n".join(
        f"- {c['title']} ({c['course_code']}): {c['description']}" for c in courses
    )
    structure_text = "### Recommended Study Plan by Year:\n"
    for year, titles in structure["recommended_courses"].items():
        structure_text += f"**{year.replace('_',' ').title()}**: " + ", ".join(titles) + "\n"

    # Add RMIT scraped data into the prompt
    prompt = (
        "You are a helpful AI assistant for RMIT students.\n\n"
        "You have access to:\n"
        f"1. Bachelor of Cyber Security course data:\n{full_course_context}\n\n"
        f"2. Recommended study structure:\n{structure_text}\n\n"
        "3. Up‐to‐date information scraped from RMIT's official website:\n"
        f"{rmit_knowledge[:2000]}  \n"  # only pass first 2k chars, tweak as needed
        "\n### Conversation History:\n"
    )

    # Include chat history in the prompt
    for msg in st.session_state.messages[:-1]:  # exclude the latest, since we add it after
        if msg["role"] == "user":
            prompt += f"User: {msg['content']}\n"
        else:
            prompt += f"Advisor: {msg['content']}\n"

    # Finally add the latest question
    prompt += f"{user_question}\n"

    try:
        # Call Claude (or your chosen model) with the combined prompt
        response = invoke_bedrock(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
    except Exception as e:
        error_msg = f"❌ Error: {e}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        with st.chat_message("assistant"):
            st.markdown(error_msg)