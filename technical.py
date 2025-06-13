import os
import re
import logging
import json
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TECHNICAL_RESULTS_FILE = "tech_results.json"

# ------------------- Generate Questions -------------------
def generate_technical_questions(domain, num_questions=10):
    """
    Generate a list of beginner to intermediate-level technical interview questions
    based on the specified job domain.
    """
    logging.info(f"Generating {num_questions} technical questions for domain: '{domain}'")

    prompt = (
        f"You are a technical interviewer. Generate {num_questions} unique, non-repetitive, "
        f"theoretical interview questions related to the job domain: '{domain}'. "
        f"Make sure these are beginner to intermediate level and relevant for a mock interview. "
        f"Return only a numbered list of questions. Do not include any introduction, explanations, or extra text."
    )

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates technical interview questions."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content.strip()
        logging.debug(f"Raw response from model: {content}")

        questions = [
            q.strip().split('. ', 1)[-1]
            for q in content.split('\n')
            if q.strip() and re.match(r"^\d+\.", q.strip())
        ]

        if questions:
            logging.info(f"Generated {len(questions)} questions successfully.")
            return questions[:num_questions]
        else:
            logging.warning("No questions extracted from the model response.")
            return ["Failed to generate questions."]

    except Exception as e:
        logging.error(f"Error generating technical questions: {e}")
        return [f"Error generating questions: {e}"]

# ------------------- Evaluate Answer -------------------
def evaluate_technical_answer(question, answer, domain):
    import streamlit as st  # Needed for session and display

    logging.info(f"Assessing technical answer for domain '{domain}'")
    logging.debug(f"Question: {question}")
    logging.debug(f"Answer: {answer}")

    prompt = (
        f"You are evaluating a technical interview answer.\n\n"
        f"Domain: {domain}\n"
        f"Question: {question}\n"
        f"Candidate's Answer: {answer}\n\n"
        f"Evaluate this answer out of 10 based on:\n"
        f"1. Correctness\n"
        f"2. Keyword relevance\n\n"
        f"Return strictly the score (out of 10) and 1-2 lines of feedback. Example:\n"
        f"Score: 7/10\nFeedback: Correct concept but lacks depth."
    )

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": "You are a technical interview evaluator."},
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content.strip()
        logging.debug(f"Raw evaluation result: {result}")
        st.write(f"Raw LLM response: {result}")  # Optional: for debug

        score_match = re.search(r"Score:\s*(\d+)/10", result)
        feedback_match = re.search(r"Feedback:\s*(.+)", result, re.DOTALL)

        if not score_match or not feedback_match:
            st.warning("⚠️ Unable to extract score/feedback from LLM response.")
            return 0, "LLM returned an unrecognized format."

        score = int(score_match.group(1))
        feedback = feedback_match.group(1).strip()

        candidate_id = st.session_state.get("candidate_id", "default_user")
        store_technical_result_to_json(question, answer, score, feedback, domain, candidate_id)

        return score, feedback

    except Exception as e:
        st.error(f"❌ LLM evaluation failed: {e}")
        logging.error(f"Error evaluating technical answer: {e}")
        return 0, f"Error evaluating technical answer: {e}"

# ------------------- Store Result -------------------
def store_technical_result_to_json(question, answer, score, feedback, domain, candidate_id="default_user"):
    """
    Appends the technical evaluation result to a JSON file.
    """
    result_entry = {
        "timestamp": datetime.now().isoformat(),
        "candidate_id": candidate_id,
        "domain": domain,
        "question": question,
        "answer": answer,
        "score": score,
        "feedback": feedback
    }

    try:
        if os.path.exists(TECHNICAL_RESULTS_FILE):
            with open(TECHNICAL_RESULTS_FILE, "r") as file:
                data = json.load(file)
        else:
            data = []

        data.append(result_entry)

        with open(TECHNICAL_RESULTS_FILE, "w") as file:
            json.dump(data, file, indent=4)

        logging.info(f"Stored technical result for candidate '{candidate_id}'.")

    except Exception as e:
        logging.error(f"Failed to store technical result: {e}")
