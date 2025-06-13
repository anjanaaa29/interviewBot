# import os
# from groq import Groq
# from dotenv import load_dotenv
# import logging

# load_dotenv()

# #----logging setup----------
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# #---------groq api key---------------
# try:
#     groq_api_key = os.getenv("GROQ_API_KEY")
#     if not groq_api_key:
#         raise ValueError("GROQ_API_KEY is not set in the environment variables.")
#     client = Groq(api_key=groq_api_key)
#     logger.info("Groq client initialized successfully.")
# except Exception as e:
#     logger.error(f"[Initialization Error] Failed to create Groq client: {e}")
#     client = None

# #---------domain identification function------
# def identify_domain(job_description, client):
#     """
#     Identifies the specific job title or domain from a given job description.
#     Uses LLaMA3-70B through Groq API.
#     """
#     logger.info("Starting domain identification.")
    
#     if not client:
#         logger.error("Groq client is not initialized.")
#         return "Client initialization failed"

#     if not isinstance(job_description, str) or not job_description.strip():
#         logger.warning("Invalid job description input received.")
#         return "Invalid job description"

#     system_prompt = (
#         "You are a job title classification assistant. "
#         "Identify the most accurate and specific job title or domain "
#         "from the given job description. "
#         # "If the input is not a valid job description, respond strictly with: Invalid job description. "
#         "If the user inputs any invalid keywords and if you find it difficult to understand, respond it with 'INVALID'."
#         "Do NOT explain or apologize. Just return the job title or 'Invalid job description'."
#     )

#     try:
#         logger.info("Sending request to Groq LLM API...")
#         stream = client.chat.completions.create(
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": job_description}
#             ],
#             model="llama3-70b-8192",
#             stream=True
#         )

#         response = ""
#         for chunk in stream:
#             delta = getattr(chunk.choices[0], "delta", None)
#             if delta and hasattr(delta, "content") and delta.content:
#                 response += delta.content
#                 logger.debug(f"Received chunk: {delta.content}")

#         response = response.strip()
#         logger.info(f"Domain identification completed: '{response}'")
#         return response

#     except Exception as e:
#         logger.error(f"[Runtime Error] Domain Identification Failed: {e}")
#         return "Error occurred during domain identification"


import os
from groq import Groq
from dotenv import load_dotenv
import logging

load_dotenv()

#----logging setup----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

#---------groq api key---------------
try:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in the environment variables.")
    client = Groq(api_key=groq_api_key)
    logger.info("Groq client initialized successfully.")
except Exception as e:
    logger.error(f"[Initialization Error] Failed to create Groq client: {e}")
    client = None

#---------domain identification function------
def identify_domain(job_description, client):
    """
    Identifies the specific job title or domain from a given job description.
    Uses LLaMA3-70B through Groq API.
    """
    logger.info("Starting domain identification.")
    
    if not client:
        logger.error("Groq client is not initialized.")
        return "Client initialization failed"

    if not isinstance(job_description, str) or not job_description.strip():
        logger.warning("Invalid job description input received.")
        return "Invalid job description"

    system_prompt = (
        "You are a job title classification assistant. "
        "Identify the most accurate and specific job title or domain "
        "from the given job description. "
        "If the input is not a valid job description, respond strictly with: Invalid job description. "
        "Do NOT explain or apologize. Just return the job title or 'Invalid job description'."
    )

    try:
        logger.info("Sending request to Groq LLM API...")
        stream = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": job_description}
            ],
            model="llama3-70b-8192",
            stream=True
        )

        response = ""
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                response += content
                logger.debug(f"Received chunk: {content}")

        response = response.strip()
        logger.info(f"Domain identification completed: '{response}'")
        return str(response)

    except Exception as e:
        logger.error(f"[Runtime Error] Domain Identification Failed: {e}")
        return "Error occurred during domain identification"