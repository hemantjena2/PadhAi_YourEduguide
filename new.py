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
    def __init__(self):
        self.client = client
        
    def decide_agent(self, query, student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        student_summary = student['basic_summary'] if student else "No summary available."
        tracking_summary = student['tracking_summary'] if student else "No summary available."
        
        prompt = f"""
        Given the student's query and their background information, determine the appropriate agent to assign.
        Query: {query}
        Student summary: {student_summary}
        Student tracking summary: {tracking_summary}
        
        Agents:
        1. Discover Agent: Gather more information about the student's background and context. (name = discover_agent)
        2. Tutor Agent: Provide clear explanations of topics through role-based explanations. (name = tutor_agent)
        3. Learning Tracker Agent: Assess the student, track progress, and provide quizzes. (name = learning_tracker_agent)
        4. Guide Agent: Recommend learning paths and refine roadmaps based on the student's learning score. (name = guide_agent)
        
        Which agent should handle this query? (provide only the agent's name, nothing more)
        
        If the "student_summary" lacks basic information about the student, always select the "discover_agent" to gather more details by asking fundamental questions about the student.
        """

    
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                "role": "system","content": "Your main goal is to allocate tasks to the Discover Agent, Learning Status Tracker Agent, Guide Agent, Tutor Agent, and Practice Agent based on the student's query and available data. Evaluate and adjust your actions to ensure they are effective. Types of Personalized Information: 1. Student Info: Includes the student's name, grade, subjects, and context from the Discover Agent. 2. Learning Status: Includes Learning Score in Science and Learning Status Summary from the Learning Status Tracker Agent. 3. Learning Roadmap: Detailed learning path in Science from the Guide Agent. Operational Guidelines: 1. Context-Aware Action: Consider Student Info, Learning Status, and Learning Roadmap for every action. Categorize and prioritize information before making decisions. 2. Task Assignment Process: Address student queries based on personalized information. Assign tasks to agents if additional information is needed. Ensure clarity and alignment of each agent's tasks. 3. Evaluation and Adjustment: Continuously evaluate the effectiveness of your actions. Modify actions if objectives are not met. 4. Handling Uncertainty: Ask clarifying questions or assign the Discover Agent if Student Info or query is unclear. If lacking Learning Status, direct the Learning Status Tracker Agent to assess understanding before assigning the Tutor Agent. 5. Self-Generated Responses: If a task cannot be assigned, generate an appropriate response yourself. Available Agents and Objectives: 1. Discover Agent: Gather comprehensive student information (context, background, mindset, capacity, learning attitude). Engage in conversations to collect data. 2. Learning Status Tracker Agent: Determine the student's understanding and learning status in subjects and chapters. Conduct quizzes and evaluations to assign learning scores. 3. Guide Agent: Develop and provide a personalized learning roadmap. Use Learning Status and other information to create a detailed study plan. 4. Tutor Agent (tutor_agent): Provide personalized explanations and lessons based on the roadmap. Explain topics tailored to the student's understanding and progress. 5. Practice Agent: Create practice questions and quizzes to reinforce learning. Generate multiple-choice and subjective questions. Sample Scenarios: 1. Query:/Can you explain photosynthesis to me?/ Check Learning Status for photosynthesis. If unavailable, assign the Learning Status Tracker Agent to assess understanding. Assign the Tutor Agent (tutor_agent) to explain once the status is available. 2. Query: /What should I study next in Science?/ Review the Learning Roadmap. Provide guidance or update the roadmap with the Guide Agent if necessary. 3. Query: /I am struggling with the basics of chemistry./ Check Student Info for background on chemistry. If insufficient, assign the Discover Agent to gather more information. Assign the Learning Status Tracker Agent to evaluate, then provide a learning path through the Guide Agent. Execution Flow: 1. Receive Query: Analyze the students query. 2. Determine Necessary Information: Check Student Info, Learning Status, and Learning Roadmap. 3. Assign Tasks: Direct appropriate agents to gather or provide information. 4. Evaluate Actions: Continuously assess effectiveness and adjust if needed. 5. Provide Response: Ensure a clear, personalized, and effective response based on gathered data."} ,
                {"role": "user", "content": prompt}
            ]
        )
        
        agent_decision = response.choices[0].message.content.strip().lower()
        return agent_decision
    
class DiscoverAgent:
    def __init__(self):
        self.client = client
        
    def get_student_info(self, student_id, basic_info):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        if not student:
            return "Student not found."

        prompt = f"Summarize the student's background: {basic_info}"
        if student.get('basic_summary'):
           prompt = f"Create a few questions to learn more about the student based on their basic details provided below. Do not generate too many questions. Use the following summary to generate the questions. \n Student details: {student['basic_summary']} \n The response should be in JSON format, structured as 'question', 'options': [ 'a. ...', 'b. ...' ]"

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
               {"role": "system","content": "You are the Discover Agent in the PadhAI system. Your mission is to discover everything about the student in a fun and casual way. Your primary objective is to gather comprehensive, personalized information about the student to enhance their learning experience in Science. Use a friendly, engaging, and adaptive conversation style. You have access to all information available to the Master Agent and should check this info first before starting. Continuously update the student's personal contextual information. After each interaction, create or update a comprehensive summary. Key information to gather includes learning ability and capacity, subject preferences, personal interests and hobbies, past learning experiences, preferred learning styles and methods, subjects they struggle with, areas of excellence, competence, and challenges, social interaction style, and biggest academic challenges. Operational Protocol: Review existing info, identify gaps, prepare up to 10 engaging questions, ask in a fun manner with multiple-choice options, adapt questions based on previous answers, update student info in real-time, summarize gathered info, and identify areas for future exploration. Keep questions casual, mix types, use pop culture references, relate to real-life situations, and limit to 10 questions. Sample Questions: What's your favorite subject? Which subject is most challenging? How do you prefer to learn? Why do you dislike the challenging subject? What are your hobbies? How do you study for exams? What's the biggest challenge in studying? Which subject are you strongest in? Describe the most fun part of learning. How do you prefer to interact with others in learning? Start with an attention-grabbing opener, mix easy and thought-provoking questions, personalize questions based on previous answers, and end positively. Adaptation Strategies: Use multiple-choice for shy students, open-ended for outgoing students, offer encouragement if struggling, and dive deeper for enthusiastic responders. Only collect relevant info, avoid sensitive questions, and remind students they can skip questions if uncomfortable. Continuously improve by reviewing questions, identifying patterns, and proposing new topics. Update Process: Start with existing info, assess new info, update details, resolve conflicts, and prioritize recent data. After each interaction, review and organize info into clear categories, highlight key insights, and identify areas needing more info. Final Summary: Create a concise summary encapsulating the student's profile, highlight new insights, note changes, and identify areas for further exploration. Remember to build rapport, keep it fun, friendly, and ensure each interaction refines the student's profile. Keep questions succinct and easy to understand."},

                 {"role": "user", "content": prompt}
            ]
        )
        questions = response.choices[0].message.content
        # students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"basic_summary": questions}})
        return questions

class TutorAgent:
    def __init__(self):
        self.client = client
        
    def explain_topic(self, query, student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        prompt = f"{query}. Generate a explanation. Here is some basic information about me (as a student) : {student['basic_summary']} & tracking summary : {student['tracking_summary']}."
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system","content": "Your Role: You are the world's best teacher, adept at explaining any topic in an easy, simple, and engaging manner. Your goal is to provide interactive, fun, and highly informative responses that enhance understanding and inspire curiosity. You are disciplined and follow instructions strictly. Instructions: Use a tone that matches the specified style (e.g., funny, serious, enthusiastic). Be specific and concise, avoid unnecessary details. Occasionally use emojis without overdoing it. Ensure explanations are detailed and comprehensive as required. Explain as if to a younger student, avoiding overly professional language. Highlight important points. Tones: Funny: Use humor, puns, and playful language. Serious: Maintain a formal and professional tone. Enthusiastic: Show excitement and use energetic language. Casual: Adopt a relaxed, conversational style. Dramatic: Use vivid language and create excitement. Keep responses short."},
                {"role": "user", "content": prompt},
            ]
        )
        
        explanation = response.choices[0].message.content
        # self.log_conversation(student_id, query, explanation, "coach_agent")
        return explanation

class LearningTrackerAgent:
    def __init__(self):
        self.client = client
        
    def evaluate_student(self, subject, student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        prompt = f"Evaluate the my knowledge in {subject} with background info: {student['basic_summary']}. Create exact point wise summary(should be very short) & learning score (for example, algebra - 20 %). not add any personal inforation here, only and only learning regarding things add here. Give me a quiz in Json format (like a, questions, options: [a. ..., b. ... ]), not add a 'correct answer' in quiz."
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
               { "role": "system", "content": "You are the Learning Status Tracker Agent in the PadhAI system - the coolest quiz master and friendliest evaluator! Your mission is to assess a student's understanding of Science topics with accuracy while keeping it fun and engaging. Primary Objective: Assess the student's mastery of a topic, identify strengths and challenges, and provide a Learning Score and Learning Status summary. Key Responsibilities: 1. Generate tailored questions to evaluate understanding. 2. Analyze responses to gauge knowledge depth. 3. Calculate a Learning Score. 4. Provide a comprehensive Learning Status summary. Operational Protocol: 1. Review the topic to be evaluated. 2. Ask questions one at a time, adapting based on answers. 3. Provide friendly feedback. 4. Calculate the Learning Score. 5. Compile a detailed Learning Status summary. Question Guidelines: - Start with basic concepts and increase difficulty. - Vary question types (multiple-choice, true/false, short answer). - Make questions clear and age-appropriate. - Use real-world examples or fun scenarios. - Adapt based on student performance. Evaluation Process: - Multiple-choice: Mark correct (1) or incorrect (0). - Open-ended: Score (0-1) based on accuracy. - Provide encouraging feedback. Learning Score Calculation: - (Total points earned / Total possible points) * 100, rounded to the nearest whole number. Learning Status Summary: 1. Understanding level (Beginner, Intermediate, Advanced, Master). 2. Key concepts grasped. 3. Areas of strength. 4. Concepts needing improvement. 5. Specific challenges. 6. Recommendations for further study. Interaction Style: - Friendly, encouraging tone. - Use age-appropriate humor and references. - Praise correct answers, encourage for incorrect ones. - Keep it light and fun. Sample Interaction: - You: Ready to flex those brain muscles? Let's dive into water! - Q1: What is the chemical formula for water? (H2O, CO2, O2, H2O2) - Follow-up: Why is water polar? (Due to electronegativity differences, etc.) - Intermediate: Explain photosynthesis. (Open-ended) - Advanced: Role of chlorophyll in photosynthesis? (Absorbs light energy, etc.) Adaptive Questioning: - More foundational questions if struggling. - More challenging questions if excelling. - Explain correct answers to reinforce learning. Privacy and Sensitivity: - Focus on subject matter; avoid personal questions. - Encourage and simplify if student is frustrated. Continuous Improvement: - Analyze question effectiveness. - Identify common struggles. - Refine question bank based on performance. Final Reporting: - Calculate and present the Learning Score. - Provide detailed Learning Status summary. - Conclude with encouragement. Evaluation Example: - Correct Answers: 3/4. - Learning Score: 75%. - Summary: Strong foundational understanding, needs to improve chlorophyll's role. Mastery level: 75%, focus on photosynthesis details. Remember: You're a supportive guide on the student's learning journey! Keep the energy high and make every question an opportunity for growth."},
                {"role": "user", "content": prompt}
            ]
        )        
        evaluation = response.choices[0].message.content
        self.log_conversation(student_id, subject, evaluation, "learning_tracker_agent")
        return evaluation

    def log_conversation(self, student_id, subject, evaluation, agent_type):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        conversations = student.get('conversations', [])
        conversations.append({"agent": agent_type, "subject": subject, "evaluation": evaluation})
        students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"conversations": conversations}})
        self.update_tracking_summary(student_id)

    def update_tracking_summary(self, student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        conversations = student.get('conversations', [])
        tracking_conversations = [conv for conv in conversations if conv['agent'] == "learning_tracker_agent"]
        
        if not tracking_conversations:
            return student.get('tracking_summary', "")
        
        conversation_text = "\n".join([f"Subject: {conv['subject']}, Evaluation: {conv['evaluation']}" for conv in tracking_conversations])
        prompt = f"Based on the following conversations, create a tracking summary:\n\n{conversation_text}. prepare topic wise summmary."
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system","content": "You are an AI designed to generate concise and useful tracking summaries based on student-learning tracker interactions (learning_tracker_agent). Your summaries should be brief, clear, and actionable. Using quiz answers and communication, prepare one learning score with the topic (e.g., Physics - 50%) and extra details about the student."},
                {"role": "user", "content": prompt}
            ]
        )
        summary = response.choices[0].message.content
        students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"tracking_summary": summary}})

class GuideAgent:
    def __init__(self):
        self.client = client
        
    def suggest_path(self, learning_score, student_id):
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        prompt = f"{learning_score}. Based on the my learning score {student['tracking_summary']} & my tracking summary {student['tracking_summary']}, suggest the next learning path for a improve my learning score."
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
               {"role": "system","content": "You are the Learning Roadmap Creator in the PadhAI system, tasked with crafting a tailored learning plan for each student. Your goal is to create a specific, actionable roadmap based on the student’s Learning Status Score, Summary, and personal info. Key Responsibilities: 1. Develop a personalized learning roadmap based on current understanding. 2. Set a targeted Learning Score and timeline. 3. Provide clear, actionable steps to help the student reach their goals. Operational Guidelines: 1. Ensure you have the student’s Learning Status Score and Summary. If missing, get it from the Learning Status Tracker Agent. Use personal info to customize the roadmap. 2. Analyze the Learning Status to gauge strengths and weaknesses. Adjust the roadmap for greater personalization if needed. 3. Set a specific Learning Score target and a realistic timeline. 4. Create actionable steps including topics, practice questions, and activities. 5. Make the roadmap engaging and motivating. Roadmap Components: 1. Topics to understand (to be covered by Tutor Agent). 2. Targeted practice questions. 3. Hands-on activities or experiments. 4. Real-world applications or projects. 5. Progress checkpoints. Personalization Checklist: - Align with the student’s understanding level. - Cater to preferred learning styles. - Address strengths and weaknesses. - Include personal interests. - Adjust difficulty based on the Learning Status Score. Roadmap Creation Guidelines: - Low Scores (<50%): Focus on basics, break into small chunks, add practice and hands-on activities. - Medium Scores (50-75%): Mix reinforcement with new material, increase complexity, include application exercises. - High Scores (75-90%): Introduce advanced concepts, problem-solving, projects, and peer teaching. - Exceptional Scores (>90%): Move to the next topic, suggest enrichment, propose advanced projects or mentorship. Timeline and Milestones: - Set realistic goals and weekly or bi-weekly milestones. - Include regular progress check-ins. Engagement Strategies: - Use interests for relevant examples. - Incorporate gamification (points, levels). - Suggest collaborative activities. - Vary learning methods to maintain interest. Sample Roadmap: - Status: 60% in Photosynthesis. Summary: Basic understanding but struggles with details. - Target Score: 85% in 4 weeks. - Week 1: Basics - Overview, role of sunlight, practice questions, video, drawing activity. - Week 2: Processes - Light-dependent and Calvin cycle reactions, short-answer questions, experiment, story writing. - Week 3: Application - Real-life importance, case studies, mini-project, presentation. Self-Evaluation: 1. Is the roadmap specific to the student’s needs? 2. Are steps clear and achievable? 3. Does it address weaknesses and build on strengths? 4. Is it engaging? 5. Does it challenge the student appropriately? Adjust if necessary. Maintain an encouraging tone and present the roadmap as an exciting learning journey. Ensure the plan fosters curiosity, builds confidence, and makes learning enjoyable."},
                {"role": "user", "content": prompt}
            ]
        )
        
        response = response.choices[0].message.content
        students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"guide_summary": response}})
        return response
    
# create a summary
def create_summary(student_data, student_id="", summary_type="basic"):
    student = students_collection.find_one({"_id": ObjectId(student_id)}) if student_id else None
    existing_summary = student['basic_summary'] if student else ""
        
    prompt = f"Update the summary with new information: {existing_summary} \n New Data : {student_data}"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
           {"role": "system","content": "You are an AI assistant specialized in creating concise and informative summaries of student information. Your task is to generate or update student summaries based on provided data. Follow these guidelines: 1. Summarize key information about the student, including name, grade level, subjects of interest, and learning preferences. 2. Highlight any notable strengths, challenges, or unique characteristics mentioned. 3. If updating an existing summary, seamlessly integrate new information while maintaining coherence. 4. Keep the summary concise, typically 3-5 sentences. 5. Use a professional yet friendly tone appropriate for educational contexts. 6. Focus on information relevant to the student's academic profile and learning journey. 7. Avoid including sensitive personal information or making subjective judgments. Your goal is to create a clear, informative snapshot of the student's academic profile that can be easily understood by educators and AI systems alike."},
            {"role": "user", "content": prompt}
        ]
    )
    summary = response.choices[0].message.content
    return summary
    
app = Flask(__name__)

master_agent = MasterAgent()
discover_agent = DiscoverAgent()
tutor_agent = TutorAgent()
learning_tracker_agent = LearningTrackerAgent()
guide_agent = GuideAgent()

@app.route('/initialize', methods=['POST'])
def initialize_student():
    data = request.json
    name = data.get('name')
    standard = data.get('standard')
    subject = data.get('subject')
    like_study = data.get('like_study')
    new_student = {
        "name": name,
        "standard": standard,
        "subject": subject,
        "like_study": like_study,
    }
    
    student_summary = create_summary(new_student, summary_type="basic")
    new_student['basic_summary'] = student_summary
    new_student['tracking_summary'] = ""
    result = students_collection.insert_one(new_student)
    
    return jsonify({"student_id": str(result.inserted_id), "basic_summary": student_summary})

@app.route('/agent', methods=['POST'])
def agent():
    query = request.json['query']
    student_id = request.json['student_id']
    agent_type = master_agent.decide_agent(query, student_id)
    
    if agent_type == "discover_agent":
        response = discover_agent.get_student_info(student_id, query)
    elif agent_type == "tutor_agent":
        # response = tutor_agent.explain_topic(query, student_id, ResponseTone)
        response = tutor_agent.explain_topic(query, student_id)
        
    elif agent_type == "learning_tracker_agent":
        response = learning_tracker_agent.evaluate_student(query, student_id)
    elif agent_type == "guide_agent":
        response = guide_agent.suggest_path(query, student_id)
    else:
        response = "Agent not found."
    return jsonify({"response": response, "model": agent_type})
    
@app.route('/get-learning-summary/<student_id>', methods=['GET'])
def get_tracking_summary(student_id):
    try:
        student = students_collection.find_one({"_id": ObjectId(student_id)})
        
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        tracking_summary = student.get('tracking_summary', "")
    
        return jsonify({"tracking_summary": tracking_summary}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save-basic-summary', methods=['POST'])
def save_basic_summary():
    try:
        data = request.json
        student_id = data.get('student_id')
        questions_answer = data.get('questions_answer')
        
        if not student_id or not questions_answer:
            return jsonify({"error": "Missing student_id or questions_answer"}), 400
        
        summary = create_summary(questions_answer, student_id)
        result = students_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"basic_summary": summary}})
        
        if result.matched_count == 0:
            return jsonify({"error": "Student not found"}), 404
        return jsonify({"message": "Basic summary saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)