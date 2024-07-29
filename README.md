# PadhAI - Your EduGuide

PadhAI is an intelligent educational assistant designed to provide personalized learning experiences for students. It uses AI agents to assess knowledge, create learning roadmaps, and offer tailored explanations across various subjects.

## Features

- Student profile initialization
- Subject and topic selection
- Knowledge evaluation
- Personalized learning roadmaps
- Q&A functionality for specific topics
- Dark/light mode toggle

## Backend (Flask API)

The backend is built with Flask and includes the following components:

- MongoDB integration for student data storage
- OpenAI GPT-4 integration for intelligent responses
- Multiple AI agents:
  - Master Agent: Decides which specialized agent to use
  - Discover Agent: Gathers student information
  - Tutor Agent: Provides explanations on topics
  - Learning Tracker Agent: Evaluates student knowledge
  - Guide Agent: Suggests learning paths

## Frontend (Streamlit)

The frontend is built with Streamlit and offers an intuitive user interface for:

- Student registration
- Subject dashboard
- Topic exploration
- Knowledge evaluation
- Roadmap viewing
- Direct Q&A with the AI

## Setup and Installation

1. Clone the repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a .env file in the root directory with the following variables: 
  ```
  OPENAI_API_KEY=your_openai_api_key_here
  MONGODB_URI=your_mongodb_uri_here
  DB_NAME=your_database_name
  COLLECTION_NAME=your_collection_name
  ```
  Replace the placeholders with your actual API key and MongoDB details.
4. Run the Flask backend:
   ```
   python backend.py
   ```
5. Run the Streamlit frontend:
   ```
   streamlit run frontend.py
   ```

## Usage

1. Initialize your student profile
2. Select a subject from the dashboard
3. Explore topics within the subject
4. Use the various features:
   - Evaluate your knowledge
   - View your learning roadmap
   - Ask questions directly to the AI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

