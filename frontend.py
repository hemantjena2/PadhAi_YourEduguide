import streamlit as st
import requests
import json

API_ENDPOINT = "http://localhost:5000"

SUBJECT_TOPICS = {
    "Mathematics": ["Algebra", "Calculus", "Geometry"],
    "Science": ["Physics", "Chemistry", "Biology"],
    "English": ["Grammar", "Literature"],
    "Social Studies": ["History", "Geography", "Environment"],
    "Humanities": ["Philosophy", "Psychology"],
    "IT": ["CS", "Programming"]
}

# Add dark/light mode toggle
if 'theme' not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    if st.session_state.theme == "dark":
        st.session_state.theme = "light"
    else:
        st.session_state.theme = "dark"

# Modified CSS to support both dark and light modes
st.markdown(f"""
<style>
    .reportview-container {{
        background-color: {("#282c34" if st.session_state.theme == "dark" else "#ffffff")};
    }}
    .sidebar .sidebar-content {{
        background-color: {("#282c34" if st.session_state.theme == "dark" else "#f0f2f6")};
    }}
    .Widget.stTextInput > div > div > input {{
        color: {("#ffffff" if st.session_state.theme == "dark" else "#000000")};
        background-color: {("#414a4c" if st.session_state.theme == "dark" else "#e6e6e6")};
    }}
    .stButton>button {{
        color: {("#ffffff" if st.session_state.theme == "dark" else "#000000")};
        background-color: #007bff;
    }}
    h1, h2, h3, h4, h5, p {{
        color: {("#d6deeb" if st.session_state.theme == "dark" else "#000000")};
    }}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_subjects():
    return list(SUBJECT_TOPICS.keys())

def initialize_student():
    data = {
        "name": st.session_state.name,
        "standard": st.session_state.standard,
        "subject": st.session_state.subject,
        "like_study": st.session_state.like_study
    }
    try:
        with st.spinner('Initializing student...'):
            response = requests.post(f"{API_ENDPOINT}/initialize", json=data)
        if response.status_code == 200:
            st.success("Student initialized successfully!")
            st.session_state.student_id = response.json()["student_id"]
            st.session_state.basic_summary = response.json()["basic_summary"]
            st.session_state.initialized = True
            
            # Reset subjects list
            st.session_state.subjects = [st.session_state.subject]  # Add the selected subject
            st.session_state.selected_subject = st.session_state.subject
            st.session_state.view_subject = True
            st.session_state.view_topics = True
            
            st.experimental_rerun()
        else:
            st.error("Failed to initialize student. Please try again.")
    except requests.exceptions.RequestException:
        st.error("Network error. Please check your connection and try again.")

def interact_with_agent(prompt):
    data = {
        "query": prompt,
        "student_id": st.session_state.student_id
    }
    try:
        with st.spinner('Getting response...'):
            response = requests.post(f"{API_ENDPOINT}/agent", json=data)
        if response.status_code == 200:
            return response.json()["response"]
        else:
            st.error("Failed to get response from agent. Please try again.")
            return None
    except requests.exceptions.RequestException:
        st.error("Network error. Please check your connection and try again.")
        return None

def get_My_Roadmap(subject):
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

    # Display subjects only if they are present
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
        if st.button("Evaluate My knowledge"):
            st.session_state.view_tracker = True
            st.experimental_rerun()
    
    with col2:
        if st.button("My Roadmap"):
            My_Roadmap = get_My_Roadmap(st.session_state.selected_subject)
            if My_Roadmap:
                st.session_state.My_Roadmap_response = My_Roadmap
                st.session_state.view_My_Roadmap = True
                st.experimental_rerun()
    
    with col3:
        if st.button("Ask Me Anything"):
            st.session_state.view_ask_directly = True
            st.experimental_rerun()

    if st.button("Back to Subjects", key="back_to_subjects"):
        st.session_state.view_topics = False
        st.session_state.view_tracker = False
        st.session_state.view_My_Roadmap = False
        st.session_state.view_ask_directly = False
        st.experimental_rerun()

def learning_score_tracker_view():
    st.subheader(f"Evaluate Your Knowledge About - {st.session_state.selected_subject}")
    topics = SUBJECT_TOPICS.get(st.session_state.selected_subject, [])
    
    st.write("Select a sub-topic to evaluate your knowledge:")
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

def My_Roadmap_view():
    st.subheader(f"Your Roadmap for {st.session_state.selected_subject}")
    st.write(st.session_state.My_Roadmap_response)
    if st.button("Back to Topics"):
        st.session_state.view_My_Roadmap = False
        st.experimental_rerun()

def ask_directly_view():
    st.subheader(f"Ask me anything about {st.session_state.selected_topic}")
    
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

    # Add theme toggle in sidebar
    with st.sidebar:
        st.button("Toggle Theme", on_click=toggle_theme)

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
    if 'view_My_Roadmap' not in st.session_state:
        st.session_state.view_My_Roadmap = False
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
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()

    if not st.session_state.initialized:
        if st.session_state.form_step == 1:
            st.subheader("Step 1: Enter Basic Information")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("What's your name?")
            with col2:
                standards = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"]
                standard = st.selectbox("Which standard are you studying in?", standards)
                
            st.session_state.name = name
            st.session_state.standard = standard
            if st.button("Next", key="next_step1"):
                if name and standard:
                    st.session_state.form_step = 2
                    st.experimental_rerun()
                else:
                    st.warning("Please fill in all fields before proceeding.")

        elif st.session_state.form_step == 2:
            subjects = get_subjects()
            subject = st.selectbox("Which subject are you studying?", subjects)
            st.session_state.subject = subject
            
            if st.button("Next", key="next_step2"):
                st.session_state.form_step = 3
                st.experimental_rerun()

        elif st.session_state.form_step == 3:
            like_study_options = ["I Love it", "I Dislike it", "Interested in some topics but not studying as a whole", "Other"]
            like_study = st.selectbox("Do you like studying?", like_study_options)
            st.session_state.like_study = like_study
            if st.button("Next", key="next_step3"):
                st.session_state.form_step = 4
                st.experimental_rerun()

        elif st.session_state.form_step == 4:
            initialize_student()

    elif st.session_state.view_chatbot:
        chatbot_view()
    elif st.session_state.view_My_Roadmap:
        My_Roadmap_view()
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
