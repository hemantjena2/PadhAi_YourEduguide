import streamlit as st
import requests
import json

# Configure the app
st.set_page_config(page_title="Padh-Ai", page_icon="📚", layout="wide")

# Apply dark theme
st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E1E;
        color: #FFFFFF;
    }
    </style>
    """, unsafe_allow_html=True)

# Session state
if 'step' not in st.session_state:
    st.session_state.step = 'registration'

# Sidebar
st.sidebar.title("Student Information")
if 'student_id' in st.session_state:
    st.sidebar.write(f"Student ID: {st.session_state.student_id}")
    if st.sidebar.button("View Learning Summary"):
        summaries = requests.get(f"http://localhost:5000/get_summary?student_id={st.session_state.student_id}").json()
        for summary in summaries:
            st.sidebar.write(f"Subject: {summary['subject']}")
            st.sidebar.write(f"Learning Path: {summary['path']}")

# Main app
st.title("Padh-Ai")

if st.session_state.step == 'registration':
    st.header("Student Registration")
    with st.form("registration_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=5, max_value=100)
        grade = st.selectbox("Grade", range(1, 13))
        if st.form_submit_button("Register"):
            response = requests.post("http://localhost:5000/init_student", 
                                     json={"name": name, "age": age, "grade": grade})
            if response.status_code == 201:
                st.session_state.student_id = response.json()['student_id']
                st.session_state.step = 'subject_selection'
                st.success("Registration successful!")
            else:
                st.error("Registration failed. Please try again.")

elif st.session_state.step == 'subject_selection':
    st.header("Select a Subject")
    subjects = ["Math", "Science", "History", "Literature"]
    subject = st.selectbox("Choose a subject", subjects)
    if st.button("Confirm Subject"):
        st.session_state.subject = subject
        response = requests.post("http://localhost:5000/interact", 
                                 json={"context": f"Suggest learning path for {subject}", 
                                       "student_id": st.session_state.student_id, 
                                       "subject": subject})
        if response.status_code == 200:
            st.session_state.learning_path = response.json()['response']
            st.session_state.step = 'learning'
        else:
            st.error("Failed to get learning path. Please try again.")

elif st.session_state.step == 'learning':
    st.header(f"Learning Path for {st.session_state.subject}")
    st.write(st.session_state.learning_path)
    
    st.subheader("Topic Explanation")
    topic = st.text_input("Enter a topic you'd like explained:")
    level = st.select_slider("Select difficulty level:", options=["Beginner", "Intermediate", "Advanced"])
    if st.button("Get Explanation"):
        response = requests.post("http://localhost:5000/interact", 
                                 json={"context": "Explain topic", 
                                       "topic": topic, 
                                       "level": level})
        if response.status_code == 200:
            st.write(response.json()['response'])
        else:
            st.error("Failed to get explanation. Please try again.")

# Direct questioning feature
st.header("Ask a Question")
question = st.text_input("Type your question here")
if st.button("Submit Question"):
    response = requests.post("http://localhost:5000/interact", 
                             json={"context": "Answer question", 
                                   "student_id": st.session_state.student_id, 
                                   "question": question})
    if response.status_code == 200:
        st.write(response.json()['response'])
    else:
        st.error("Failed to get answer. Please try again.")

# Knowledge evaluation
if st.button("Evaluate My Knowledge"):
    response = requests.post("http://localhost:5000/interact", 
                             json={"context": "Evaluate knowledge", 
                                   "student_id": st.session_state.student_id, 
                                   "topic": st.session_state.subject})
    if response.status_code == 200:
        st.write("Here's a quiz to evaluate your knowledge:")
        st.write(response.json()['response'])
    else:
        st.error("Failed to generate quiz. Please try again.")