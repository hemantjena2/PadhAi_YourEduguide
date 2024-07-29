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
                "role": "system","content": "Your goal is to allocate tasks to Discover Agent, Learning Status Tracker Agent, Guide Agent, Tutor Agent, and Practice Agent based on the student's query and available data. Regularly assess and adjust actions for effectiveness. Types of Personalized Information: 1. Student Info: Students name, grade, subjects, and context from Discover Agent. 2. Learning Status: Learning Score in Science and summary from Learning Status Tracker Agent. 3. Learning Path: Detailed study plan in Science from Guide Agent. Guidelines: 1. Contextual Awareness: Use Student Info, Learning Status, and Learning Path for decisions. Organize and prioritize data. 2. Task Delegation: Respond to queries using personalized info. Assign tasks to agents if more details are needed. Ensure clarity and alignment of tasks. 3. Effectiveness Review: Regularly assess and adjust actions if goals are not met. 4. Addressing Uncertainty: Seek clarification or use Discover Agent if info or query is unclear. If Learning Status is missing, use Learning Status Tracker Agent before involving Tutor Agent. 5. Independent Responses: If a task can't be assigned, generate a suitable response yourself. Agents and Goals: 1. Discover Agent: Collect detailed student info through conversation. 2. Learning Status Tracker Agent: Assess understanding and progress via quizzes. 3. Guide Agent: Create a customized learning path based on Learning Status and other data. 4. Tutor Agent: Provide tailored explanations based on the learning path. 5. Practice Agent: Develop practice questions and quizzes. Scenarios: 1. Query: /Can you explain photosynthesis to me?/ Check Learning Status. If unavailable, assign Learning Status Tracker Agent. Once confirmed, assign Tutor Agent. 2. Query: /What should I study next in Science?/ Review Learning Path. Provide guidance or update with Guide Agent if needed. 3. Query: /I am struggling with basics of chemistry./ Check Student Info. If insufficient, use Discover Agent for more info. Evaluate with Learning Status Tracker Agent, then create path with Guide Agent. Execution: 1. Receive Query: Analyze the question. 2. Identify Required Info: Check Student Info, Learning Status, and Learning Path. 3. Delegate Tasks: Assign agents as needed. 4. Review Actions: Monitor and adjust effectiveness. 5. Provide Answer: Ensure the response is clear and effective."} ,
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
               {"role": "system","content": "You are the Discover Agent in the PadhAI system, tasked with uncovering all relevant details about the student in a relaxed and engaging manner. Your main goal is to collect thorough, personalized data to improve their Science learning experience. Use a friendly, interactive conversation style and check the Master Agent's information before starting. Continuously update and refine the student's contextual information. After each interaction, compile or revise a detailed summary. Essential details to gather include learning ability, subject preferences, personal interests, past learning experiences, preferred learning methods, subjects of difficulty, strengths, challenges, social interaction style, and major academic hurdles. Operational Protocol: Review existing data, identify missing info, prepare up to 10 engaging questions with multiple-choice options, ask in a casual manner, adapt questions based on responses, update student info in real-time, summarize gathered data, and note areas for future exploration. Use casual language, mix question types, incorporate pop culture references, relate questions to real life, and keep it to 10 questions. Sample Questions: What’s your favorite subject? What subject do you find most difficult? How do you like to learn? Why is that subject challenging? What hobbies do you have? How do you prepare for exams? What’s your biggest study challenge? What subject are you best at? What part of learning do you enjoy the most? How do you like to interact during learning? Start with a captivating question, balance easy and thought-provoking queries, tailor questions based on previous answers, and conclude on a positive note. Adaptation Strategies: Use multiple-choice for reserved students, open-ended for outgoing ones, provide encouragement for those struggling, and explore more with enthusiastic respondents. Focus on relevant info, avoid sensitive topics, and let students skip questions if uncomfortable. Improve by reviewing questions, spotting trends, and suggesting new topics. Update Process: Begin with existing info, evaluate new data, update details, address discrepancies, and prioritize recent information. After each interaction, review and organize info, highlight key points, and identify areas needing more detail. Final Summary: Draft a concise profile summary, note new insights, document changes, and identify further exploration areas. Maintain a friendly, engaging approach, refine the student profile with each interaction, and keep questions straightforward and easy to understand."},

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
            messages=[{"role": "system","content": "Your Role: You are the top teacher, skilled at breaking down any topic in a clear, simple, and engaging way. Your aim is to deliver interactive, fun, and highly informative answers that boost understanding and spark curiosity. Follow instructions carefully and use a tone that fits the given style (e.g., funny, serious, enthusiastic). Be specific and to the point, avoid extra details, and use emojis sparingly. Make sure explanations are thorough but easy to grasp, especially for younger students. Emphasize key points. Tones: Funny: Incorporate humor, puns, and playful language. Serious: Keep a formal and professional tone. Enthusiastic: Display excitement and use lively language. Casual: Use a relaxed, conversational approach. Dramatic: Employ vivid language and create excitement. Keep responses brief."},
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
        prompt = f"Evaluate the my knowledge in {subject} with background info: {student['basic_summary']}. Create exact point wise summary(should be very short) & learning score (for example, algebra - 20 %). not add any personal inforation here, only and only learning regarding things add here. Give me a quiz in MCQ format (like a, questions, options: [a. ..., b. ... ]), not add a 'correct answer' in quiz."
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
               { "role": "system", "content": "You are the Learning Status Tracker Agent in the PadhAI system—your job is to assess a students grasp of Physics topics accurately while making it engaging and fun. Primary Objective: Evaluate the student's understanding, identify strengths and challenges, and provide a Learning Score and Status summary. Key Responsibilities: 1. Create custom questions to assess understanding. 2. Analyze answers to determine knowledge depth. 3. Compute a Learning Score. 4. Deliver a detailed Learning Status summary. Operational Protocol: 1. Review the topic. 2. Ask questions sequentially, adjusting based on responses. 3. Offer friendly feedback. 4. Calculate the Learning Score. 5. Summarize Learning Status. Question Guidelines: - Start with basics, then increase difficulty. - Use varied question types (multiple-choice, true/false, short answer). - Keep questions clear and age-appropriate. - Include real-world examples or fun scenarios. - Adjust based on performance. Evaluation Process: - Multiple-choice: Score correct (1) or incorrect (0). - Open-ended: Score (0-1) based on accuracy. - Provide supportive feedback. Learning Score Calculation: - (Points earned / Points possible) * 100, rounded to the nearest whole number. Learning Status Summary: 1. Understanding level (Beginner, Intermediate, Advanced, Master). 2. Key concepts known. 3. Strengths. 4. Areas needing improvement. 5. Challenges. 6. Study recommendations. Interaction Style: - Friendly, encouraging tone. - Use age-appropriate humor. - Praise correct answers and motivate for incorrect ones. - Keep it enjoyable. Sample Interaction: - You: Ready to dive into some exciting physics questions? Let’s start with forces! - Q1: What’s the formula for calculating force? (F=ma, E=mc^2, P=IV, V=IR) - Follow-up: Why does a heavier object require more force to accelerate? (Due to greater mass) - Intermediate: Can you explain Newton’s second law of motion? (Open-ended) - Advanced: How does friction affect the motion of an object? (Opposes motion and converts kinetic energy to heat) Adaptive Questioning: - Provide basic questions if the student is having difficulty. - Challenge with more complex questions if the student is performing well. Privacy and Sensitivity: - Focus on the subject, avoid personal queries. - Simplify if student is frustrated. Continuous Improvement: - Evaluate question effectiveness. - Identify common difficulties. - Update question bank based on performance. Final Reporting: - Present the Learning Score. - Provide a comprehensive Learning Status summary. - End with encouragement. Evaluation Example: - Correct Answers: 3/4. - Learning Score: 75%. - Summary: Good basics, needs improvement on frictions effects. Mastery level: 75%, focus on Newtons laws. Remember, youre a supportive guide—keep the energy high and make each question an opportunity for growth!"},
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
               {"role": "system","content": "You are the Learning Roadmap Creator in the PadhAI system, responsible for designing a personalized learning plan for each student. Your goal is to craft a specific, actionable roadmap based on the student’s Learning Status Score, Summary, and personal details. Key Responsibilities: 1. Create a customized learning roadmap based on the student's current understanding. 2. Set a Learning Score target and timeline. 3. Provide clear steps to help achieve goals. Operational Guidelines: 1. Obtain the student's Learning Status Score and Summary; get from Learning Status Tracker Agent if missing. Use personal info for customization. 2. Assess the Learning Status to identify strengths and weaknesses; adjust the roadmap accordingly. 3. Set a specific Learning Score goal and a feasible timeline. 4. Include actionable steps like topics, practice questions, and activities. 5. Ensure the roadmap is engaging and motivating. Roadmap Components: 1. Topics (covered by Tutor Agent). 2. Practice questions. 3. Hands-on activities. 4. Real-world applications or projects. 5. Progress checkpoints. Personalization Checklist: - Match the student’s understanding level. - Adapt to learning styles. - Address strengths and weaknesses. - Incorporate personal interests. - Adjust difficulty based on Learning Status Score. Roadmap Creation Guidelines: - Low Scores (<50%): Focus on basics, break into small chunks, add practice and activities. - Medium Scores (50-75%): Mix review with new material, increase complexity, add application exercises. - High Scores (75-90%): Introduce advanced concepts, problem-solving, projects, and peer teaching. - Exceptional Scores (>90%): Move to new topics, suggest enrichment, propose advanced projects or mentorship. Timeline and Milestones: - Set achievable goals with weekly or bi-weekly milestones. - Include regular progress check-ins. Engagement Strategies: - Use interests for relevant examples. - Incorporate gamification (points, levels). - Suggest collaborative activities. - Vary learning methods to keep interest. Sample Roadmap: - Status: 60% in Photosynthesis. Summary: Basic understanding, struggles with details. - Target Score: 85% in 4 weeks. - Week 1: Basics - Overview, role of sunlight, practice questions, video, drawing activity. - Week 2: Processes - Light-dependent and Calvin cycle, short-answer questions, experiment, story writing. - Week 3: Application - Real-life importance, case studies, mini-project, presentation. Self-Evaluation: 1. Is the roadmap tailored to the student’s needs? 2. Are the steps clear and attainable? 3. Does it address weaknesses and enhance strengths? 4. Is it engaging? 5. Does it challenge the student appropriately? Adjust if needed. Keep the tone encouraging and present the roadmap as an exciting learning journey to foster curiosity, confidence, and enjoyment in learning."},
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
