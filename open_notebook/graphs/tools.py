from datetime import datetime

from langchain.tools import tool


# todo: turn this into a system prompt variable
@tool
def get_current_timestamp() -> str:
    """
    name: get_current_timestamp
    Returns the current timestamp in the format YYYYMMDDHHmmss.
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


import os
import google.generativeai as genai

# Load your Gemini key into both conventions:
gemini_key = os.getenv("GEMINI_API_KEY")
os.environ["GOOGLE_API_KEY"] = gemini_key  # langchain_google_genai expects this
genai.api_key = gemini_key