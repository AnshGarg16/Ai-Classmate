import google.generativeai as genai
import os
import streamlit as st
from.pydantic_models import Quiz  # Import our defined schema

# Function for the master prompt from Section 3.2
def get_master_prompt(pdf_text: str, difficulty: str, num_questions: int) -> str:
    """
    Generates the master prompt for the Gemini API.
    """
    return f"""
    You are an expert Quiz Generation Bot. Your task is to generate a high-quality, multiple-choice quiz based *only* on the provided text content.

    **Quiz Parameters:**
    1.  **Difficulty:** {difficulty}
    2.  **Number of Questions:** {num_questions}

    **Instructions:**
    -   Generate exactly {num_questions} questions.
    -   The questions must be of {difficulty} difficulty, appropriate for someone studying this material.
    -   All questions, options, and explanations *must* be derived *directly* from the provided text content. Do not use any outside knowledge.
    -   Provide exactly 4 string options for each question.
    -   Provide a brief explanation for the correct answer, citing the reasoning from the text.
    -   You *must* return your response *only* in the structured JSON format that has been provided to you. Do not include any other text or markdown formatting.

    **Provided Text Content:**
    ---
    {pdf_text}
    ---
    """

def configure_gemini_client():
    """
    Configures the Gemini client with the API key.
    It checks Streamlit secrets (for deployment) and environment variables (for Docker).
    References: [23, 47, 48, 49, 50]
    """
    try:
        # st.secrets is Streamlit's native way to handle secrets in deployed apps
        api_key = st.secrets.get("")
        
        if not api_key:
            # Fallback to environment variable (for local Docker)
            api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not found. "
                "Set it in your.env file (for local) or "
                "in Streamlit Cloud secrets (for deployment)."
            )
            
        genai.configure(api_key=api_key)
        
    except Exception as e:
        st.error(f"Failed to configure Gemini client: {e}")
        return None

def generate_quiz_from_text(pdf_text: str, difficulty: str, num_questions: int) -> Quiz:
    """
    Generates a quiz using the Gemini API with forced JSON output.

    Args:
        pdf_text: The full text extracted from the PDF.
        difficulty: The user-selected difficulty ("Easy", "Medium", "Hard").
        num_questions: The user-selected number of questions.

    Returns:
        A Pydantic 'Quiz' object, or None on failure.
    
    References: [7, 8, 9, 19]
    """
    try:
        configure_gemini_client()
        
        # 1. Define the model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        # 2. Build the prompt
        prompt = get_master_prompt(pdf_text, difficulty, num_questions)
        
        # 3. Set the generation config to force JSON output
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=Quiz.model_json_schema()  # Pass the schema from our Pydantic model
        )
        
        # 4. Make the API call
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # 5. Validate and parse the response with Pydantic
        quiz_data = Quiz.model_validate_json(response.text)
        return quiz_data

    except Exception as e:
        st.error(f"An error occurred during quiz generation: {e}")
        if "response" in locals() and hasattr(response, 'text'):
            st.error(f"Raw AI Response (which failed validation): {response.text}")
        else:
            st.error("Failed to get a valid response from the API.")
        return None
