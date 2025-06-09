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
<<<<<<< Updated upstream
def build_prompt(full_course_context, user_question, structure_text):
    # Load history
=======
def build_prompt(full_course_context, user_question, structure_text, rmit_knowledge, file_text=""):
    # Load chat history
>>>>>>> Stashed changes
    history = st.session_state.get("messages", [])
    # chat_history = ""

<<<<<<< Updated upstream
    for msg in history:
=======
    # for msg in history:
    #     role = "User" if msg["role"] == "user" else "Advisor"
    #     chat_history += f"{role}: {msg['content']}\n"

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
        "You have access to:\n"
        f"1. Up‐to‐date information scraped from RMIT's official website:\n{rmit_knowledge[:2000]}\n\n"
    )

    if include_cyber:
        prompt += (
            f"3. Bachelor of Cyber Security course data:\n{full_course_block}\n\n"
            f"4. Recommended study structure:\n{structure_block}\n\n"
        )

    prompt += f"User asked: {user_question}\n"

    if file_text:
        prompt += f"\nBelow is the content of a file the user uploaded:\n{file_text}"

    # Use a less echo-prone format
    formatted_history = ""
    for msg in st.session_state.messages:
>>>>>>> Stashed changes
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
        "You are a helpful assistant that supports students in selecting courses from the "
        "Bachelor of Cyber Security program at RMIT (codes BP355/BP356). "
        "Recommend only from the official course list. Each course is categorized as core, capstone, minor, or elective. "
        "Use the recommended structure to suggest suitable courses based on study year and interest.\n\n"
        "Do not give personal advice unless the user has provided context. If they greet you or ask general questions like 'who am I?', respond politely and prompt them for more information.\n\n"
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

<<<<<<< Updated upstream
=======
def clear_input():
    st.session_state["custom_chat_input"] = ""
>>>>>>> Stashed changes

# === Streamlit UI === #
st.set_page_config(page_title="RMIT Chatbot", layout="wide")
st.title("RMIT Chatbot")
st.markdown("This assistant helps students select courses and answer RMIT related questions.")

with open("courses_data.json", "r", encoding="utf-8") as f1:
    courses = json.load(f1)
with open("cyber_security_program_structure.json", "r", encoding="utf-8") as f2:
    structure = json.load(f2)
uploaded_pdfs = None

<<<<<<< Updated upstream

st.subheader("💬 Chat with the Course Advisor")
=======
# Initialise state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_upload" not in st.session_state:
    st.session_state.show_upload = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "custom_chat_input" not in st.session_state:
    st.session_state.custom_chat_input = ""
if "processed_input" not in st.session_state:
    st.session_state.processed_input = False

# # Header
# st.markdown(
#     """
#     <div style='text-align: center; margin-top: 30px;'>
#         <img src="https://www.edigitalagency.com.au/wp-content/uploads/RMIT-University-logo-white-png-1200x422.png" width="220" style="margin-bottom: 10px;">
#         <h3 style='font-family: "Segoe UI", sans-serif;'>
#             🎓 Welcome to the RMIT Course Advisor<br>
#             Get help with subjects, enrolment, and program info across all disciplines.
#         </h3>
#     </div>
#     """,
#     unsafe_allow_html=True
# )

# # Show chat messages
# for msg in st.session_state.messages:
#     if msg["content"].strip():
#         with st.chat_message(msg["role"]):
#             st.markdown(msg["content"])

# # Input and upload toggle row
# col1, col2 = st.columns([2, 25], gap="small")

# with col2:
#     uploaded_file = st.session_state.get("uploaded_file", None)
#     user_question = st.text_input(
#     "Ask about course enrolment, policies, or RMIT info...",
#     key="custom_chat_input",
#     label_visibility="collapsed",
#     placeholder="Ask about course enrolment, policies, or RMIT info...",
#     on_change=clear_input
# )

# with col1:
#     if st.button("＋", key="upload_toggle"):
#         st.session_state.show_upload = not st.session_state.get("show_upload", False)

# st.markdown("""
# <style>
# /* Container holding the whole input bar and + button */
# div[data-testid="stHorizontalBlock"] {
#     position: fixed;
#     bottom: 1%;
#     left: 20%;
#     width: 60%;
#     background-color: #1e1e1e;
#     padding: 24px 30px;
#     z-index: 1000;
#     border-top: 1px solid #333;
#     border-radius: 8px;
#     display: flex;
#     align-items: center;
#     box-shadow: 0 -2px 5px rgba(0,0,0,0.3);
    
# }

# /* Full-width text input */
# div[data-testid="stChatInput"] input[type="text"]{
#     width: 100% !important;
#     background: transparent !important;
#     border: none !important;
#     color: white !important;
#     font-size: 18px !important;
#     padding: 10px 12px !important;
# }

# /* Style the + button only inside the input row */
# div[data-testid="stHorizontalBlock"] > div button[kind="secondary"] {
#     width: 40px !important;
#     height: 40px !important;
#     min-width: 0 !important;
#     border-radius: 50% !important;
#     font-size: 22px !important;
#     background-color: #444 !important;
#     color: white !important;
#     border: none !important;
#     margin-left: auto;
# }

# /* Prevent bottom overlap */
# main .block-container {
#     padding-bottom: 80px !important;
# }
# </style>
# """, unsafe_allow_html=True)

# # Show file uploader
# if st.session_state.get("show_upload"):
#     uploaded_file = st.file_uploader(
#         "Upload file",
#         type=["pdf", "png", "jpg", "jpeg", "txt", "csv"],
#         label_visibility="collapsed"
#     )

# if user_question:
#     file_text = ""
#     if uploaded_file is not None:
#         file_text = uploaded_file.read().decode("utf-8", errors="ignore")
#         st.session_state.show_upload = False  # Hide the uploader after sending

#     # Save and display user message
#     with st.chat_message("user"):
#         st.markdown(user_question)
#     st.session_state.messages.append({"role": "user", "content": user_question})

#     placeholder = st.empty()
#     st.session_state.messages.append({"role": "assistant", "content": ""})
#     full_course_context = "\n".join(
#         f"- {c['title']} ({c['course_code']}): {c['description']}" for c in courses
#     )
#     structure_text = "### Recommended Study Plan by Year:\n"
#     for year, titles in structure["recommended_courses"].items():
#         structure_text += f"**{year.replace('_',' ').title()}**: " + ", ".join(titles) + "\n"

#     prompt = build_prompt(
#     full_course_context=full_course_context,
#     user_question=user_question,
#     structure_text=structure_text,
#     rmit_knowledge=rmit_knowledge,
#     file_text=file_text
# )

#     # === Claude + cache check === #
#     if "response_cache" not in st.session_state:
#         st.session_state["response_cache"] = {}
#     response_cache = st.session_state["response_cache"]

#     if prompt in response_cache:
#         response = response_cache[prompt]
#     else:
#         response = invoke_bedrock(prompt)
#         response_cache[prompt] = response

#     st.session_state.messages.append({"role": "assistant", "content": response})
#     with st.chat_message("assistant"):
#         placeholder = st.empty()
#         placeholder.markdown("✍️ Thinking...")
#         placeholder.markdown(response, unsafe_allow_html=False)
#         uploaded_file = None

# user_question = user_question.strip()
# if not user_question:
#     st.stop()

# === Helper function === #
def process_input():
    if st.session_state.processed_input:
        return
    
    user_question = st.session_state.custom_chat_input.strip()
    if not user_question:
        return

    file_text = ""
    uploaded_file = st.session_state.uploaded_file
    if uploaded_file is not None:
        file_text = uploaded_file.read().decode("utf-8", errors="ignore")
        st.session_state.show_upload = False

    # Display user message
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Build prompt
    full_course_context = "\n".join(
        f"- {c['title']} ({c['course_code']}): {c['description']}" for c in courses
    )
    structure_text = "### Recommended Study Plan by Year:\n"
    for year, titles in structure["recommended_courses"].items():
        structure_text += f"**{year.replace('_',' ').title()}**: " + ", ".join(titles) + "\n"

    prompt = build_prompt(
        full_course_context=full_course_context,
        user_question=user_question,
        structure_text=structure_text,
        rmit_knowledge=rmit_knowledge,
        file_text=file_text,
    )

    # Claude + cache check
    if "response_cache" not in st.session_state:
        st.session_state["response_cache"] = {}
    cache = st.session_state["response_cache"]

    if prompt in cache:
        response = cache[prompt]
    else:
        response = invoke_bedrock(prompt)
        cache[prompt] = response

    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response, unsafe_allow_html=False)

    # Reset input
    st.session_state.custom_chat_input = ""
    st.session_state.uploaded_file = None
    st.session_state.processed_input = True

# === UI === #

# Header
st.markdown("""
<div style='text-align: center; margin-top: 30px;'>
    <img src="https://www.edigitalagency.com.au/wp-content/uploads/RMIT-University-logo-white-png-1200x422.png" width="220" style="margin-bottom: 10px;">
    <h3 style='font-family: "Segoe UI", sans-serif;'>
        🎓 Welcome to the RMIT Course Advisor<br>
        Get help with subjects, enrolment, and program info across all disciplines.
    </h3>
</div>
""", unsafe_allow_html=True)

# Show chat history
>>>>>>> Stashed changes
for msg in st.session_state.messages:
    if msg["content"].strip():
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

<<<<<<< Updated upstream
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
=======
# Input + toggle
col1, col2 = st.columns([2, 25], gap="small")
with col1:
    if st.button("＋", key="upload_toggle"):
        st.session_state.show_upload = not st.session_state.get("show_upload", False)

with col2:
    st.text_input(
        "Ask about course enrolment, policies, or RMIT info...",
        key="custom_chat_input",
        placeholder="Ask about course enrolment, policies, or RMIT info...",
        label_visibility="collapsed",
        on_change=process_input
    )

if not st.session_state.custom_chat_input.strip():
    st.session_state.processed_input = False

# Show uploader
if st.session_state.show_upload:
    st.session_state.uploaded_file = st.file_uploader(
        "Upload file",
        type=["pdf", "png", "jpg", "jpeg", "txt", "csv"],
        label_visibility="collapsed"
    )

# Style
st.markdown("""
<style>
div[data-testid="stHorizontalBlock"] {
    position: fixed;
    bottom: 1%;
    left: 20%;
    width: 60%;
    background-color: #1e1e1e;
    padding: 24px 30px;
    z-index: 1000;
    border-top: 1px solid #333;
    border-radius: 8px;
    display: flex;
    align-items: center;
    box-shadow: 0 -2px 5px rgba(0,0,0,0.3);
}
div[data-testid="stChatInput"] input[type="text"] {
    width: 100% !important;
    background: transparent !important;
    border: none !important;
    color: white !important;
    font-size: 18px !important;
    padding: 10px 12px !important;
}
div[data-testid="stHorizontalBlock"] > div button[kind="secondary"] {
    width: 40px !important;
    height: 40px !important;
    min-width: 0 !important;
    border-radius: 50% !important;
    font-size: 22px !important;
    background-color: #444 !important;
    color: white !important;
    border: none !important;
    margin-left: auto;
}
main .block-container {
    padding-bottom: 80px !important;
}
</style>
""", unsafe_allow_html=True)
>>>>>>> Stashed changes
