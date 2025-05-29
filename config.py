# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")

if not TOGETHER_API_KEY:
    raise ValueError("TOGETHER_API_KEY not found in .env file")

# Define the model we will be using (UPDATED LINE)
LLM_MODEL ="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"




# meta-llama/Llama-3.3-70B-Instruct-Turbo