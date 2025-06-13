import os
import random
import logging
import re
from groq import Groq
from dotenv import load_dotenv
import json
from datetime import datetime

#--------- Logging ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#----- Generate 5 random HR questions -----
def generate_hr_questions():
    """
    Generates 5 basic HR questions using Groq (LLaMA 3 model) to assess confidence and communication.
    """
    prompt = (
        "Generate 5 simple and short HR interview questions. "
        "Each should be under 20 words. Do NOT include any introduction or explanations. "
        "communication skills, and self-awareness. Keep them informal and beginner-friendly."
        "Only return the list of questions, each on a new line."
    )

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are an HR professional preparing screening questions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw_text = response.choices[0].message.content.strip()

        # Split based on line breaks and clean prefixes like "1. ", "2) ", etc.
        questions = []
        for line in raw_text.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Remove numeric prefixes
            question = re.sub(r"^\d+[\.\)]\s*", "", line)
            if question:
                questions.append(question)

        if len(questions) >= 5:
            logging.info("Successfully generated HR questions using Groq.")
            return questions[:5]
        else:
            logging.warning("Groq returned fewer than 5 HR questions.")
            return questions  # Return however many were returned, even if fewer than 5

    except Exception as e:
        logging.error(f"Error generating HR questions from Groq: {e}")
        return []



#----- Evaluate HR answer using LLM -----
def evaluate_hr_answer(question, answer):
    """
    Uses LLM to evaluate the HR answer.
    Returns a score (0-10), feedback, and confidence level.
    """
    logging.info(f"Evaluating answer for question: '{question}'")

    prompt = (
        f"You are an HR evaluator assistant.\n"
        f"Evaluate the following answer to the HR question.\n\n"
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        f"Return the result in this format strictly:\n"
        f"Score: <score out of 10>\n"
        f"Feedback: <feedback on structure, clarity, and content>\n"
        f"Confidence Level: <Low, Medium, High> based on the tone of the answer.\n"
        f"Don't include anything else."
    )

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are an expert HR evaluator."},
                {"role": "user", "content": prompt}
            ]
        )
        result = response.choices[0].message.content.strip()
        logging.debug(f"Raw evaluation result: {result}")

        score_match = re.search(r"^Score:\s*(\d+)", result, re.MULTILINE)
        feedback_match = re.search(r"^Feedback:\s*(.+)", result, re.MULTILINE)
        confidence_match = re.search(r"^Confidence Level:\s*(Low|Medium|High)", result, re.IGNORECASE | re.MULTILINE)

        score = int(score_match.group(1)) if score_match else 0
        score = max(0, min(10, score)) 
        feedback = feedback_match.group(1).strip() if feedback_match else "No feedback provided."
        confidence = confidence_match.group(1).capitalize() if confidence_match else "Low"

        return score, feedback, confidence

    except Exception as e:
        logging.error(f"Error evaluating HR answer: {e}")
        return 0, "Error during evaluation.", "Low"

#----- Store HR result in JSON file -----
def store_hr_result_to_json(question, answer, score, feedback, domain, candidate_id="default_user"):
    """
    Stores the HR evaluation result to a JSON file for dashboard use.
    """
    data = {
        "timestamp": datetime.now().isoformat(),
        "candidate_id": candidate_id,
        "domain": domain,
        "question": question,
        "answer": answer,
        "score": score,
        "feedback": feedback
    }

    filename = "hr_results.json"

    try:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                results = json.load(f)
        else:
            results = []

        results.append(data)

        with open(filename, "w") as f:
            json.dump(results, f, indent=4)

        logging.info(f"Stored HR evaluation result for candidate '{candidate_id}'.")

    except Exception as e:
        logging.error(f"Error storing HR result to JSON: {e}")
