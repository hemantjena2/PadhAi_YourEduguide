import streamlit as st
import requests
import json

API_ENDPOINT = "http://localhost:5000"

SUBJECT_TOPICS = {
    "Mathematics": ["Algebra", "Calculus", "Geometry"],
    "Science": ["Physics", "Chemistry", "Biology"],
    "English": ["Grammar", "Literature"],
    "Social Studies": ["History", "Geography", "Environment"],
    "Humanities": ["Philosophy","Psychology"],
    "IT": ["CS","Programming"]
}

st.markdown("""
<style>
    .reportview-container {
        background-color: #282c34;
    }
    .sidebar .sidebar-content {
        background-color: #282c34;
    }
    .Widget.stTextInput > div > div > input {
        color: white;
        background-color: #414a4c;
    }
    .stButton>button {
        color: white;
        background-color: #007bff;
    }
    h1, h2, h3, h4, h5, p {
        color: #d6deeb;
    }
</style>
""", unsafe_allow_html=True)

def initialize_student():
    data = {
        "name": st.session_state.name,
        "standard": st.session_state.standard,
        "subject": st.session_state.subject,
        "like_study": st.session_state.like_study
    }
    response = requests.post(f"{API_ENDPOINT}/initialize", json=data)
    if response.status_code == 200:
        st.success("Student initialized successfully!")
        st.session_state.student_id = response.json()["student_id"]
        st.session_state.basic_summary = response.json()["basic_summary"]
        st.session_state.initialized = True
        st.experimental_rerun()
    else:
        st.error("Failed to initialize student.")

def interact_with_agent(prompt):
    data = {
        "query": prompt,
        "student_id": st.session_state.student_id
    }
    response = requests.post(f"{API_ENDPOINT}/agent", json=data)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        st.error("Failed to get response from agent.")
        return None

def get_learning_path(subject):
    fixed_prompt = f"Generate a comprehensive learning path for {subject} that covers all major topics and subtopics. Include estimated time frames for each section and suggested resources or activities."
    data = {
        "query": fixed_prompt,
        "student_id": st.session_state.student_id
    }
    response = requests.post(f"{API_ENDPOINT}/agent", json=data)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        st.error("Failed to get learning path from agent.")
        return None

def subject_dashboard():
    st.subheader("Subject Dashboard")
    
    if 'subjects' not in st.session_state:
        st.session_state.subjects = []

    if st.session_state.subjects:
        for idx, subject in enumerate(st.session_state.subjects):
            if st.button(f"View {subject}", key=f"view_{idx}"):
                st.session_state.selected_subject = subject
                st.session_state.view_subject = True
                st.session_state.view_topics = True
                st.experimental_rerun()
    else:
        st.write("No subjects available. Please initialize the student first.")

def topic_view():
    st.subheader(f"Topics in {st.session_state.selected_subject}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Learning Score Tracker"):
            st.session_state.view_tracker = True
            st.experimental_rerun()
    
    with col2:
        if st.button("Learning Path"):
            learning_path = get_learning_path(st.session_state.selected_subject)
            if learning_path:
                st.session_state.learning_path_response = learning_path
                st.session_state.view_learning_path = True
                st.experimental_rerun()
    
    with col3:
        if st.button("Ask Directly"):
            st.session_state.view_ask_directly = True
            st.experimental_rerun()

    if st.button("Back to Subjects", key="back_to_subjects"):
        st.session_state.view_topics = False
        st.session_state.view_tracker = False
        st.session_state.view_learning_path = False
        st.session_state.view_ask_directly = False
        st.experimental_rerun()

def learning_score_tracker_view():
    st.subheader(f"Learning Score Tracker - {st.session_state.selected_subject}")
    topics = SUBJECT_TOPICS.get(st.session_state.selected_subject, [])
    
    st.write("Select a topic to evaluate your knowledge:")
    for topic in topics:
        if st.button(f"{topic}", key=f"topic_{topic}"):
            st.session_state.selected_topic = topic
            st.session_state.view_chatbot = True
            st.session_state.chat_history = []
            initial_prompt = f"user : i want to evaluate my knowledge about {st.session_state.selected_topic}"
            response = interact_with_agent(initial_prompt)
            st.session_state.chat_history.append(("User", initial_prompt))
            st.session_state.chat_history.append(("Agent", response))
            st.experimental_rerun()

    if st.button("Back to Topics", key="back_to_topics"):
        st.session_state.view_tracker = False
        st.experimental_rerun()

def chatbot_view():
    st.subheader(f"Chat about {st.session_state.selected_topic}")
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    for role, message in st.session_state.chat_history:
        if role == "User":
            st.text_input("You:", value=message, key=f"user_{message}")
        else:
            st.text_area("Agent:", value=message, height=500, key=f"agent_{message}")
    
    user_input = st.text_input("Your message:")
    if st.button("Send"):
        if user_input:
            query = f"user : i want to evaluate my knowledge about {st.session_state.selected_topic}\n"
            for role, message in st.session_state.chat_history:
                if role == "Agent":
                    query += f"learning_tracker_agent : {message}\n"
                else:
                    query += f"User : {message}\n"
            query += f"User : answer of questions : {user_input}"
            response = interact_with_agent(query)
            
            st.session_state.chat_history.append(("User", user_input))
            st.session_state.chat_history.append(("Agent", response))
            st.experimental_rerun()
    
    if st.button("Back to Topics"):
        st.session_state.view_chatbot = False
        st.session_state.chat_history = []
        st.experimental_rerun()

def learning_path_view():
    st.subheader(f"Learning Path - {st.session_state.selected_subject}")
    st.write(st.session_state.learning_path_response)
    if st.button("Back to Topics"):
        st.session_state.view_learning_path = False
        st.experimental_rerun()

def ask_directly_view():
    st.subheader(f"Ask Directly about {st.session_state.selected_topic}")
    
    if 'ask_directly_history' not in st.session_state:
        st.session_state.ask_directly_history = []
    
    for role, message in st.session_state.ask_directly_history:
        if role == "User":
            st.text_input("You:", value=message, key=f"ask_user_{message}")
        else:
            st.text_area("Agent:", value=message, height=500, key=f"ask_agent_{message}")
    
    user_question = st.text_input("Your question:")
    if st.button("Send Question"):
        if user_question:
            query = f"user : {user_question}\n"
            for role, message in st.session_state.ask_directly_history:
                if role == "Agent":
                    query += f"response : {message}\n"
                else:
                    query += f"User : {message}\n"
            response = interact_with_agent(query)
            
            st.session_state.ask_directly_history.append(("User", user_question))
            st.session_state.ask_directly_history.append(("Agent", response))
            st.experimental_rerun()
    
    if st.button("Back to Topics"):
        st.session_state.view_ask_directly = False
        st.session_state.ask_directly_history = []
        st.experimental_rerun()

def main():
    st.title("PadhAi - Your EduGuide")

    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    if 'form_step' not in st.session_state:
        st.session_state.form_step = 1
    if 'view_subject' not in st.session_state:
        st.session_state.view_subject = False
    if 'view_topics' not in st.session_state:
        st.session_state.view_topics = False
    if 'view_tracker' not in st.session_state:
        st.session_state.view_tracker = False
    if 'view_chatbot' not in st.session_state:
        st.session_state.view_chatbot = False
    if 'view_learning_path' not in st.session_state:
        st.session_state.view_learning_path = False
    if 'view_ask_directly' not in st.session_state:
        st.session_state.view_ask_directly = False
    if 'subjects' not in st.session_state:
        st.session_state.subjects = []

    with st.sidebar:
        if st.session_state.initialized:
            st.header("Student Info")
            st.write(f"Student ID: {st.session_state.student_id}")
            st.write(f"Basic Summary: {st.session_state.basic_summary}")
            if st.button("Log Out", key="start_over"):
                st.session_state.clear()
                st.experimental_rerun()

    if not st.session_state.initialized:
        if st.session_state.form_step == 1:
            st.subheader("Step 1: Enter Basic Information")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("What's your name?")
            with col2:
                standards = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th","11th","12th"]
                standard = st.selectbox("Which standard are you studying in?", standards)
                
            st.session_state.name = name
            st.session_state.standard = standard
            if st.button("Next", key="next_step1"):
                st.session_state.form_step = 2
                st.experimental_rerun()

        elif st.session_state.form_step == 2:
            subjects = ["Mathematics", "Science", "English", "Social Studies", "Humanities", "IT"]
            subject = st.selectbox("Which subject are you studying?", subjects)
            st.session_state.subject = subject
            st.session_state.subjects.append(subject)
            
            if st.button("Next", key="next_step2"):
                st.session_state.form_step = 3
                st.experimental_rerun()

        elif st.session_state.form_step == 3:
            like_study_options = ["Yes", "No", "Love it", "Dislike it", "Interested in some topics but not studying as a whole", "Other"]
            like_study = st.selectbox("Do you like studying?", like_study_options)
            st.session_state.like_study = like_study
            if st.button("Next", key="next_step3"):
                st.session_state.form_step = 4
                st.experimental_rerun()

        elif st.session_state.form_step == 4:
            initialize_student()

    elif st.session_state.view_chatbot:
        chatbot_view()
    elif st.session_state.view_learning_path:
        learning_path_view()
    elif st.session_state.view_tracker:
        learning_score_tracker_view()
    elif st.session_state.view_ask_directly:
        ask_directly_view()
    elif st.session_state.view_topics:
        topic_view()
    else:
        subject_dashboard()

if __name__ == "__main__":
    main()
