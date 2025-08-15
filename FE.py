import streamlit as st
import openai
import google.generativeai as genai
import firebase_admin
from firebase_admin import auth, credentials, firestore
import pyttsx3
import speech_recognition as sr
import os
import json
from dotenv import load_dotenv
import threading
import re

# Load environment variables
load_dotenv()
user_email = ""
user_pass = ""

if os.path.exists("user_credentials.json"):
    try:
        with open("user_credentials.json", "r") as f:
            creds = json.load(f)
        user_email = creds.get("email", "")
        user_pass = creds.get("password", "")
        os.remove("user_credentials.json")  # Clean after use
    except Exception as e:
        st.warning("⚠️ Failed to read saved login credentials.")

# Firebase Initialization
firebase_key_path = r"C:\MajorProject\genailearning-2f273-firebase-adminsdk-fbsvc-d55ab5697b.json"
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_key_path)
    firebase_app = firebase_admin.initialize_app(cred)
else:
    firebase_app = firebase_admin.get_app()

db = firestore.client()

# OpenAI & Gemini API Keys
openai.api_key = "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"
genai.configure(api_key="AIzaSyAPa5BoIbFdeGy7TpS04ml0pILY2EqQmwI")


# Streamlit UI Settings
st.set_page_config(page_title="AI Learning Platform", layout="wide")
st.sidebar.image("C:\\MajorProject\\logo.png", width=200)
st.sidebar.title("📚 AI Learning Platform")

# Authentication System
if "user" not in st.session_state:
    st.session_state["user"] = None

st.sidebar.subheader("User Authentication")
auth_option = st.sidebar.radio("Select Option", ["Login", "Sign Up"])  
user_email = st.sidebar.text_input("Enter Email")
user_password = st.sidebar.text_input("Enter Password", type="password")

if auth_option == "Sign Up":
    confirm_password = st.sidebar.text_input("Confirm Password", type="password")
    if st.sidebar.button("Sign Up"):
        if user_password == confirm_password:
            try:
                user = auth.create_user(email=user_email, password=user_password)
                st.sidebar.success("Account created successfully! Please login.")
            except Exception as e:
                st.sidebar.error(f"Sign Up failed: {str(e)}")
        else:
            st.sidebar.error("Passwords do not match!")

if auth_option == "Login" and st.sidebar.button("Login"):
    try:
        user = auth.get_user_by_email(user_email)
        st.session_state["user"] = user_email
        st.sidebar.success("Logged in successfully!")
    except Exception as e:
        st.sidebar.error("Invalid Credentials")

if st.session_state["user"]:
    st.sidebar.write(f"Welcome, {st.session_state['user']}!")
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.sidebar.success("Logged out successfully!")
        st.rerun()

# Course Selection
st.sidebar.subheader("Select a Course")
courses = ["Python Basics","Java Programming","Machine Learning", "Web Development","Data Science", "Artificial Intelligence", "Deep Learning", "Natural Language Processing", "Computer Vision", "Cybersecurity", "Cloud Computing", "Internet of Things", "DevOps", "Blockchain", "Data Structures & Algorithms", "Operating Systems", "Database Management", "Software Engineering", "Mobile App Development", "Frontend Development", "Backend Development"]
course_name = st.sidebar.selectbox("📖 Courses:", courses)

# AI Course Content Generation
st.title(f"📚 {course_name} - AI Powered Learning")
#if st.button("Generate Course Content"):
#   with st.spinner("Generating AI content..."):
#       model = genai.GenerativeModel("gemini-1.5-pro")
#       response = model.generate_content(f"Generate a detailed learning module for {course_name}")
#       st.write(response.text if response else "Failed to generate content")
if f"{course_name}_content" in st.session_state:
    st.markdown("### 📝 Course Preview")
    st.write(st.session_state[f"{course_name}_content"])

if st.button("Generate Course Content"):
    with st.spinner("Generating AI content..."):
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(f"Generate a detailed learning module for {course_name}")
        
        if response and hasattr(response, "text"):
            st.session_state[f"{course_name}_content"] = response.text
            st.markdown("### 📝 Course Preview")
            st.write(response.text)
        else:
            st.warning("⚠️ Failed to generate course content.")
if st.button("Reset Course Preview"):
    if f"{course_name}_content" in st.session_state:
        del st.session_state[f"{course_name}_content"]
        st.info("Preview reset. Click Generate to create new content.")



# AI Chatbot
st.subheader("🤖 Ask AI a Question")
user_query = st.text_input("Your question:")
if st.button("Get AI Answer"):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Your question: {user_query}")
    
    if response:
        st.session_state["ai_response"] = response.text
    else:
        st.session_state["ai_response"] = "No content available"
    
    st.write(st.session_state["ai_response"])

# Text-to-Speech
engine = pyttsx3.init()
tts_thread = None
def speak(text):
    def _speak():
        engine.say(text)
        engine.runAndWait()

    thread = threading.Thread(target=_speak)
    thread.start()
    return thread
st.subheader("🔊 AI Voice Assistant")
if st.button("🔊 Read Aloud"):
    if "ai_response" in st.session_state:
        if tts_thread and tts_thread.is_alive():
            st.warning("Voice already playing.")
        else:
            tts_thread = speak(st.session_state["ai_response"])
    else:
        st.warning("Please generate an answer first before using text-to-speech.")

if st.button("🛑 Stop Voice"):
    try:
        engine.stop()
        st.info("Voice stopped.")
    except Exception as e:
        st.error("Failed to stop voice.")

# Display persisted AI answer if available
if "ai_response" in st.session_state:
    st.markdown("### 🤖 AI Response:")
    st.text_area("Response", st.session_state["ai_response"], height=150)


# AI Quiz Generation
if "quiz" not in st.session_state:
    st.session_state["quiz"] = None
if "responses" not in st.session_state:
    st.session_state["responses"] = {}
if "submitted" not in st.session_state:
    st.session_state["submitted"] = False

st.subheader("🧠 AI Adaptive Quiz")

# ------------------ Generate Quiz ------------------
if st.button("🎲 Generate Quiz"):
    with st.spinner("Creating AI-powered quiz..."):
        model = genai.GenerativeModel("gemini-1.5-pro")
        response = model.generate_content(
            f"Create a multiple-choice quiz with 10 questions for {course_name}. Format: Each question followed by four options, and end with 'Correct Answer: <answer>' on a new line. Separate questions with two line breaks."
        )

        if response and hasattr(response, "text"):
            quiz_text = response.text.strip()
            st.session_state["quiz"] = quiz_text
            st.session_state["responses"] = {}  # Reset responses
            st.session_state["submitted"] = False
        else:
            st.error("Quiz generation failed!")

# ------------------ Display Quiz Questions ------------------
if st.session_state["quiz"]:
    questions = [q.strip() for q in st.session_state["quiz"].split("\n\n") if q.strip()]

    for idx, question_block in enumerate(questions):
        if question_block:
            q_lines = question_block.split("\n")
            #question_text = q_lines[0]
            question_text = re.sub(r'<[^>]+>', '', q_lines[0])
            options = q_lines[1:5]
            options = [opt.strip() for opt in options]

            # 🔧 FIXED: Extract correct answer letter and convert to index
            correct_letter = None
            for line in q_lines:
                if "Correct Answer:" in line:
                    correct_letter = line.split(":")[-1].strip().lower()
                    break

            # 🔧 FIXED: Map letter to option index
            option_map = {"a": 0, "b": 1, "c": 2, "d": 3}
            correct_index = option_map.get(correct_letter, None)
            correct_option_text = options[correct_index] if correct_index is not None else None

            st.subheader(f"Q{idx + 1}: {question_text}")
            selected_option = st.radio(
                f"Choose an answer:",
                options,
                key=f"q{idx}",
                index=None,
                disabled=st.session_state["submitted"]
            )

            if st.session_state["submitted"]:
                if selected_option:
                    if correct_option_text and selected_option.strip().lower() == correct_option_text.strip().lower():
                        st.success("✅ Correct!")
                        st.session_state["responses"][idx] = True
                    else:
                        st.error(f"❌ Incorrect! Correct answer: {correct_option_text}")
                else:
                    st.warning("⚠️ No answer selected.")

# ------------------ Submit Quiz & Store Score ------------------
# ------------------ Submit Quiz & Store Score ------------------
if st.session_state["quiz"] and not st.session_state["submitted"]:
    if st.button("📨 Submit Quiz"):
        st.session_state["submitted"] = True
        correct_answers = 0
        total_questions = len([q for q in st.session_state["quiz"].split("\n\n") if q.strip()])

        # Evaluate answers immediately after submission
        for idx, question_block in enumerate(st.session_state["quiz"].split("\n\n")):
            if question_block:
                q_lines = question_block.strip().split("\n")
                options = q_lines[1:5]
                correct_answer = None

                for line in q_lines:
                    if "Correct Answer:" in line:
                        correct_answer = line.split(":")[-1].strip()
                option_map = {"a": 0, "b": 1, "c": 2, "d": 3}
                #correct_letter = correct_answer.strip().lower()
                if correct_answer:
                    correct_letter = correct_answer.strip().lower()
                    correct_index = option_map.get(correct_letter)
                else:
                    st.error(f"Correct answer missing for Question {idx+1}")
                    correct_index = None
                correct_index = option_map.get(correct_letter)
                selected_option = st.session_state.get(f"q{idx}")
                if correct_index is not None and selected_option:
                    correct_option = options[correct_index].strip().lower()
                    user_selected = selected_option.strip().lower()
                    if correct_option == user_selected:
                        st.session_state["responses"][idx] = True
                        correct_answers += 1
                    else:
                        st.session_state["responses"][idx] = False
                else:
                    st.session_state["responses"][idx] = False



        # ✅ Show score
        score = f"{correct_answers}/{total_questions}"
        st.success(f"🎯 Your Score: {score}")

        # ✅ Store in Firebase leaderboard
        if user_email:
            db.collection("leaderboard").document(user_email).set(
                {"points": correct_answers}, merge=True
            )
            st.sidebar.success("✅ Your score has been recorded on the leaderboard!")
        else:
            st.sidebar.error("❌ Please log in to save your score.")


# ------------------ Leaderboard ------------------
st.sidebar.subheader("🏆 Leaderboard")
leaderboard_data = db.collection("leaderboard").order_by("points", direction=firestore.Query.DESCENDING).limit(10).stream()
for doc in leaderboard_data:
    st.sidebar.write(f"{doc.id}: {doc.to_dict().get('points', 0)} points")

# ------------------ Achievements ------------------
st.sidebar.subheader("🎖 Your Achievements")
if st.session_state.get("user"):
    user_doc = db.collection("users").document(st.session_state["user"]).get()
    if user_doc.exists:
        st.sidebar.write(user_doc.to_dict().get("badges", "No badges yet"))
    else:
        st.sidebar.write("User data not found.")
else:
    st.sidebar.error("Please log in to view achievements.")

st.success("🚀 AI Adaptive Learning Platform Loaded Successfully!")
