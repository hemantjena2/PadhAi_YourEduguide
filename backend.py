from flask import Flask, request, jsonify
from flask_cors import CORS
from bson import ObjectId
from openai import OpenAI 
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# MongoDB setup
ca = certifi.where()
mongo_client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=ca)
db = mongo_client[os.getenv("DB_NAME")]
students_collection = db[os.getenv("COLLECTION_NAME")]

# AI Agents
class MasterAgent:
    def decide_agent(self, context):
        prompt = f"Given the following context, which agent should handle this request? Context: {context}\nOptions: DiscoverAgent, TutorAgent, LearningTrackerAgent, TeacherAgent"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a master agent deciding which specialized agent to use."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()

class DiscoverAgent:
    def gather_info(self, student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        prompt = f"Given this student information, what are some key insights and recommendations? Student: {student}"
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an agent that gathers and analyzes student information."},
                {"role": "user", "content": prompt}
            ]
        )
        insights = response.choices[0].message.content
        students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"insights": insights}})
        return insights

class TutorAgent:
    def explain_topic(self, topic, level):
        prompt = f"Explain the topic '{topic}' at a {level} level."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a knowledgeable tutor explaining academic topics."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class LearningTrackerAgent:
    def evaluate_knowledge(self, student_id, topic):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        prompt = f"Create a short quiz to evaluate knowledge on the topic '{topic}' for a student in grade {student['grade']}."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an agent that creates quizzes to evaluate student knowledge."},
                {"role": "user", "content": prompt}
            ]
        )
        quiz = response.choices[0].message.content
        # Store the quiz
        db.quizzes.insert_one({"student_id": ObjectId(student_id), "topic": topic, "quiz": quiz})
        return quiz

class TeacherAgent:
    def suggest_learning_path(self, student_id, subject):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        prompt = f"Suggest a learning path for a student in grade {student['grade']} studying {subject}. Include key topics and their order."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an experienced teacher creating personalized learning paths."},
                {"role": "user", "content": prompt}
            ]
        )
        learning_path = response.choices[0].message.content
        db.learning_paths.insert_one({"student_id": ObjectId(student_id), "subject": subject, "path": learning_path})
        return learning_path

# API Endpoints
@app.route('/init_student', methods=['POST'])
def init_student():
    student_data = request.json
    student_id = students_collection.insert_one(student_data).inserted_id
    return jsonify({"student_id": str(student_id)}), 201

@app.route('/interact', methods=['POST'])
def interact():
    data = request.json
    master_agent = MasterAgent()
    agent_type = master_agent.decide_agent(data['context'])
    
    if agent_type == "DiscoverAgent":
        agent = DiscoverAgent()
        response = agent.gather_info(data['student_id'])
    elif agent_type == "TutorAgent":
        agent = TutorAgent()
        response = agent.explain_topic(data['topic'], data['level'])
    elif agent_type == "LearningTrackerAgent":
        agent = LearningTrackerAgent()
        response = agent.evaluate_knowledge(data['student_id'], data['topic'])
    elif agent_type == "TeacherAgent":
        agent = TeacherAgent()
        response = agent.suggest_learning_path(data['student_id'], data['subject'])
    else:
        return jsonify({"error": "Invalid agent type"}), 400

    return jsonify({"response": response})

@app.route('/get_summary', methods=['GET'])
def get_summary():
    student_id = request.args.get('student_id')
    summaries = list(db.learning_paths.find({"student_id": ObjectId(student_id)}))
    for summary in summaries:
        summary['_id'] = str(summary['_id'])
        summary['student_id'] = str(summary['student_id'])
    return jsonify(summaries)

if __name__ == '__main__':
    app.run(debug=True)