import os
from dotenv import load_dotenv

load_dotenv()

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY not found in .env file")

LLM_MODEL ="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"




# meta-llama/Llama-3.3-70B-Instruct-Turbo