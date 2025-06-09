# RMIT ChatBot
# Author: Meidie Fei, Banharith Ly
# Updated: June 2025

import streamlit as st
import streamlit.components.v1 as components
import json
import boto3
import sqlite3
import difflib
import re
from PyPDF2 import PdfReader

st.set_page_config(page_title="RMIT Chatbot", layout="wide")

# === AWS Configuration === #
REGION = "us-east-1"
MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
IDENTITY_POOL_ID = "us-east-1:7771aae7-be2c-4496-a582-615af64292cf"
USER_POOL_ID = "us-east-1_koPKi1lPU"
APP_CLIENT_ID = "3h7m15971bnfah362dldub1u2p"
USERNAME = "s4155089@student.rmit.edu.au" # Replace with your username
PASSWORD = "c5ZvgdeVN7wghQ-"    # Replace with your password

response_cache = {}

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
@st.cache_data
def load_rmit_pages(db_path="rmit_data.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT content FROM pages")
    all_pages = cur.fetchall()
    conn.close()
    return "\n\n".join(page[0] for page in all_pages)

# Load all scraped RMIT content once at startup
rmit_knowledge = load_rmit_pages()

if "messages" not in st.session_state:
    st.session_state.messages = []

# === Helper: Build Prompt from JSON + Structure === #
def build_prompt(full_course_context, user_question, structure_text, rmit_knowledge):
    # Load chat history
    profile = st.session_state.get("user_profile", {})
    memory_context = ""
    history = st.session_state.get("messages", [])
    chat_history = ""

    if profile.get("level"):
        memory_context += f"The user is a {profile['level']} student. "
    if profile.get("discipline"):
        memory_context += f"Their discipline is {profile['discipline']}. "
    if profile.get("name"):
        memory_context += f"Their name is {profile['name']}. "

    for msg in history:
        role = "User" if msg["role"] == "user" else "Advisor"
        chat_history += f"{role}: {msg['content']}\n"

    # Detect if the user's question is about Cyber Security
    def is_cyber_question(text):
        keywords = ["cyber", "bp355", "bp356", "inte", "security"]
        return any(word in text.lower() for word in keywords)

    include_cyber = is_cyber_question(user_question)

    # Optional structure and courses only if needed
    structure_block = ""
    full_course_block = ""
    if include_cyber:
        # Format structure
        course_dict = {c["title"]: c for c in courses}
        if structure and "recommended_courses" in structure:
            structure_block += "### Recommended Study Plan by Year:\n"
            for year, course_titles in structure["recommended_courses"].items():
                structure_block += f"**{year.replace('_', ' ').title()}**:\n"
                for title in course_titles:
                    course = course_dict.get(title)
                    if course:
                        structure_block += f"- {title} ({course['course_code']})\n"
                    else:
                        structure_block += f"- {title} (not found in course list)\n"
                structure_block += "\n"

        # Format courses
        course_list = []
        for course in courses:
            title = course.get("title", "Untitled")
            code = course.get("course_code", "N/A")
            desc = course.get("description", "No description available.")
            course_type = course.get("course_type", "N/A")
            minor = course.get("minor_track", [])
            minor_info = f", Minor: {minor[0]}" if minor else ""
            course_list.append(f"- {title} ({code}): {desc}\n  Type: {course_type}{minor_info}")
        full_course_block = "\n".join(course_list)

    # Assemble the prompt
    prompt = (
        "You are a helpful assistant for RMIT students.\n\n"
        + memory_context
        + "You have access to:\n"
        f"1. Up‐to‐date information scraped from RMIT's official website:\n{rmit_knowledge[:2000]}\n\n"
        "If the question is not clear, ask the student to clarify. Only use knowledge provided.\n"
        f"User: {user_question}\n\n"
    )

    if include_cyber:
        prompt += (
            f"2. Bachelor of Cyber Security course data:\n{full_course_block}\n\n"
            f"3. Recommended study structure:\n{structure_block}\n\n"
        )

    # Use a less echo-prone format
    formatted_history = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            formatted_history += f"\nUser asked: {msg['content']}"
        elif msg["role"] == "assistant":
            formatted_history += f"\nAssistant replied: {msg['content'].splitlines()[0][:100]}..." if msg['content'].strip() else ""

    prompt += f"\n\n(Here is the recent conversation context for your reference only):\n{formatted_history}"

    return prompt

# === Helper: Extract text from multiple PDFs === #
@st.cache_data
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
        "messages": [
            {
                "role": "user",
                "content": prompt_text
            }
        ]
    }

    response = bedrock_runtime.invoke_model(
        body=json.dumps(payload),
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json"
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]

def fuzzy_discipline(text):
    text = text.lower()
    for discipline, keywords in DISCIPLINE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return discipline
    return None

# === Streamlit UI === #
# Load data
with open("courses_data.json", "r", encoding="utf-8") as f1:
    courses = json.load(f1)
with open("cyber_security_program_structure.json", "r", encoding="utf-8") as f2:
    structure = json.load(f2)
with open("discipline_keywords.json") as f:
    DISCIPLINE_KEYWORDS = json.load(f)

# Initialise state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "level": None,
        "discipline": None,
        "name": None
    }

# Header
st.markdown(
    """
    <div style='text-align: center; margin-top: 30px;'>
        <img src="https://www.edigitalagency.com.au/wp-content/uploads/RMIT-University-logo-white-png-1200x422.png" width="220" style="margin-bottom: 10px;">
        <h3 style='font-family: "Segoe UI", sans-serif;'>
            🎓 Welcome to the RMIT Course Advisor<br>
            Get help with subjects, enrolment, and program info across all disciplines.
        </h3>
    </div>
    """,
    unsafe_allow_html=True
)

# Show chat messages
for msg in st.session_state.messages:
    if msg["content"].strip():
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

user_question = st.chat_input("Ask about course enrolment, policies, or RMIT info...")

if user_question:
    text = user_question.lower()

    # Extract name from input
    name_match = re.search(r"my name is ([a-zA-Z\-'\s]+)", user_question, re.IGNORECASE)
    if name_match:
        name = name_match.group(1).strip().title()
        st.session_state.user_profile["name"] = name

    # Level
    if "master" in text:
        st.session_state.user_profile["level"] = "Master"
    elif "bachelor" in text:
        st.session_state.user_profile["level"] = "Bachelor"

    # print("Trying to match discipline from text:", text)

    # Discipline
    tokens = text.split()
    for d, kws in DISCIPLINE_KEYWORDS.items():
        if any(kw in tokens for kw in kws):
            st.session_state.user_profile["discipline"] = d
            break
    else:
        # fallback to fuzzy
        discipline = fuzzy_discipline(text)
        if discipline:
            st.session_state.user_profile["discipline"] = discipline

    # Save and display user message
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    placeholder = st.empty()
    st.session_state.messages.append({"role": "assistant", "content": ""})

    # Build prompt
    full_course_context = "\n".join(
        f"- {c['title']} ({c['course_code']}): {c['description']}" for c in courses
    )
    structure_text = "### Recommended Study Plan by Year:\n"
    for year, titles in structure["recommended_courses"].items():
        structure_text += f"**{year.replace('_',' ').title()}**: " + ", ".join(titles) + "\n"

    # st.sidebar.write("🧠 Memory:", st.session_state.user_profile)

    chat_messages = build_prompt(
        user_question=user_question,
        rmit_knowledge=rmit_knowledge,
        full_course_context=full_course_context,
        structure_text=structure_text
    )

    # === Claude + cache check === #
    chat_key = json.dumps(chat_messages, sort_keys=True)

    if "response_cache" not in st.session_state:
        st.session_state["response_cache"] = {}
    response_cache = st.session_state["response_cache"]

    if chat_key in response_cache:
        response = response_cache[chat_key]
    else:
        response = invoke_bedrock(chat_messages)
        response_cache[chat_key] = response

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response, unsafe_allow_html=False)