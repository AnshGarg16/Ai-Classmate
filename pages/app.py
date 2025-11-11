import os
import google.generativeai as genai
import streamlit as st
import fitz  # PyMuPDF
import io
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
load_dotenv()
class QuizQuestion(BaseModel):
    """
    A Pydantic model representing a single multiple-choice question.
    The 'description' in each Field provides a hint to the LLM.
    """
    question_text: str = Field(description="The full text of the multiple-choice question.")
    
    options: List[str] = Field(
        description="A list of exactly 4 potential answers for the question. One must be correct."
    )
    
    correct_answer_index: int = Field(
        description="The 0-based index (0, 1, 2, or 3) corresponding to the correct answer in the 'options' list."
    )
    
    explanation: str = Field(
        description="A brief explanation of why the correct answer is right, based on the provided text."
    )
class QuizQuestion(BaseModel):
    """
    A Pydantic model representing a single multiple-choice question.
    The 'description' in each Field provides a hint to the LLM.
    """
    question_text: str = Field(description="The full text of the multiple-choice question.")
    
    options: List[str] = Field(
        description="A list of exactly 4 potential answers for the question. One must be correct."
    )
    
    correct_answer_index: int = Field(
        description="The 0-based index (0, 1, 2, or 3) corresponding to the correct answer in the 'options' list."
    )
    
    explanation: str = Field(
        description="A brief explanation of why the correct answer is right, based on the provided text."
    )

# --- ADD THIS CLASS ---
class Quiz(BaseModel):
    """
    A Pydantic model representing the entire quiz, containing a list of questions.
    """
    questions: List[QuizQuestion] = Field(description="A list of QuizQuestion objects.")
# ---------------------
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

def extract_text_from_pdf(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> str:
    """
    Extracts text from an in-memory PDF file uploaded via Streamlit.

    Args:
        uploaded_file: The file object from st.file_uploader.

    Returns:
        A single string containing all text from the PDF, or None on failure.
    
    References: 
    """
    try:
        # Read bytes from the Streamlit UploadedFile object
        bytes_data = uploaded_file.getvalue()
        
        # Open the PDF directly from the byte stream
        doc = fitz.open(stream=bytes_data, filetype="pdf")
        
        full_text = ""
        # Iterate through each page to extract text [39]
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Load the page
            full_text += page.get_text()     # Extract text from the page
        
        doc.close()
        
        if not full_text:
            st.warning("The PDF appears to be empty or contains no extractable text.")
            return None
            
        return full_text
        
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None
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
        api_key = st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            
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
        # configure_gemini_client()
        
        # 1. Define the model
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        
        # 2. Build the prompt
        prompt = get_master_prompt(pdf_text, difficulty, num_questions)
        
        # 3. Set the generation config to force JSON output
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json",
            response_schema=Quiz  # <--- Pass the class itself
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
# --- Helper Functions (Define ALL functions first) ---

def initialize_state():
    """
    Initializes all required session state variables if they don't exist.
    This function is called at the beginning of every script rerun.
    """
    # 'app_view' acts as a state machine: 'upload', 'quiz', 'results'
    if 'app_view' not in st.session_state:
        st.session_state.app_view = 'upload'
        
    # 'quiz_data' will store the Pydantic Quiz object from the API
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = None
        
    # 'current_q_index' tracks which question the user is on
    if 'current_q_index' not in st.session_state:
        st.session_state.current_q_index = 0
        
    # 'user_answers' stores the indices of the user's selections
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = []# <--- CORRECTED
        
    # 'score' tracks the number of correct answers
    if 'score' not in st.session_state:
        st.session_state.score = 0

def submit_answer(selected_option_index: int, correct_index: int):
    """
    Processes the user's answer, updates state, and advances the quiz.
    This logic is triggered when the 'Submit Answer' button is clicked.
    """
    # 1. Store the user's answer
    st.session_state.user_answers.append(selected_option_index)
    
    # 2. Check correctness and update score
    if selected_option_index == correct_index:
        st.session_state.score += 1
        st.toast("Correct! 🎉", icon="✅")
    else:
        st.toast("Incorrect.", icon="❌")
    
    # 3. Advance to the next question or the results page
    total_questions = len(st.session_state.quiz_data.questions)
    if st.session_state.current_q_index + 1 < total_questions:
        st.session_state.current_q_index += 1
    else:
        # End of quiz
        # 4. <<< STATE TRANSITION >>>
        st.session_state.app_view = 'results'
        st.balloons()

def render_quiz_view():
    """
    Renders the active quiz question and options.
    """
    try:
        # Get the current question index and total questions
        q_index = st.session_state.current_q_index
        total_questions = len(st.session_state.quiz_data.questions)
        
        # Get the question object from our Pydantic model list
        question_obj = st.session_state.quiz_data.questions[q_index]
        
        # --- Display Progress ---
        st.subheader(f"Question {q_index + 1} of {total_questions}")
        st.progress((q_index + 1) / total_questions) 
        
        # --- Display Question ---
        st.markdown(f"#### {question_obj.question_text}")
        
        # --- Display Options (st.radio) ---
        options = question_obj.options
        
        selected_option = st.radio(
            "Select your answer:",
            options,
            index=None,
            key=f"q_{q_index}_radio"
        )
        
        # --- Submit Button and Logic ---
        if st.button("Submit Answer", type="primary", use_container_width=True):
            if selected_option is not None:
                # Find the index of the selected option
                selected_index = options.index(selected_option)
                
                # Call the state-updating logic
                submit_answer(selected_index, question_obj.correct_answer_index)
                
                # Force an immediate rerun to show the next question or results
                st.rerun() 
            else:
                st.warning("Please select an answer before submitting.")
                
    except Exception as e:
        st.error(f"Error rendering quiz: {e}")
        st.session_state.app_view = 'upload' # Reset to safety
        st.rerun()

def render_results_dashboard():
    """
    Renders the final results dashboard with score, metrics, and answer review.
    """
    st.header("Quiz Results Dashboard 📊")
    
    total_questions = len(st.session_state.quiz_data.questions)
    score = st.session_state.score
    
    if total_questions > 0:
        percentage = (score / total_questions) * 100
    else:
        percentage = 0
    
    # --- Display KPI Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Questions", total_questions)
    col2.metric("Correct Answers", score)
    col3.metric("Final Score", f"{percentage:.1f}%")
    
    st.progress(percentage / 100)
    
    # --- ---
    st.subheader("Answer Review")
    
    review_container = st.container(height=400, border=True)
    
    for i, question_obj in enumerate(st.session_state.quiz_data.questions):
        with review_container.expander(f"**Question {i+1}:** {question_obj.question_text[:50]}..."):
            
            user_answer_index = st.session_state.user_answers[i]
            user_answer_text = question_obj.options[user_answer_index]
            correct_answer_index = question_obj.correct_answer_index
            correct_answer_text = question_obj.options[correct_answer_index]
            
            if user_answer_index == correct_answer_index:
                st.success(f"Your answer: {user_answer_text} (Correct)", icon="✅")
            else:
                st.error(f"Your answer: {user_answer_text} (Incorrect)", icon="❌")
                st.info(f"Correct answer: {correct_answer_text}", icon="🎯")
            
            st.markdown("**Explanation:**")
            st.markdown(f"_{question_obj.explanation}_")
    
    # --- Reset Button ---
    if st.button("Take Another Quiz", type="primary", use_container_width=True):
        # Reset all state variables to their defaults
        st.session_state.app_view = 'upload'
        st.session_state.quiz_data = None
        st.session_state.current_q_index = 0
        st.session_state.user_answers = [] # <--- CORRECTED
        st.session_state.score = 0
        st.rerun()

# --- Main Application ---
st.set_page_config(page_title="QuizGen", layout="wide", page_icon="📚")
st.title("📚 QuizGen: The Adaptive PDF Quiz Generator")

# Configure the Gemini client at the start
# This will handle loading the API key from.env or st.secrets
try:
    configure_gemini_client()
except ValueError as e:
    st.error(e)
    # Stop the app if the key is not found
    st.stop()


# Initialize the app state on every rerun
initialize_state()

# --- Sidebar (Data Ingestion) ---
with st.sidebar:
    st.header("Quiz Configuration")
    pdf_file = st.file_uploader(
        "Upload your PDF", type=["pdf"], help="Upload a PDF document..."
    )
    st.divider()
    difficulty = st.selectbox(
        "Select Difficulty", ["Easy", "Medium", "Hard"], index=1, help="..."
    )
    num_questions = st.slider(
        "Number of Questions", 5, 20, 10, 1, help="..."
    )
    st.divider()
    generate_button = st.button(
        "Generate Quiz", type="primary", disabled=(pdf_file is None), use_container_width=True
    )

# --- Main Logic: "Generate Quiz" Button ---
if generate_button and pdf_file is not None:
    with st.spinner("Analyzing PDF and generating quiz... This may take a moment."):
        # 1. Process PDF
        raw_text = extract_text_from_pdf(pdf_file)
        
        if raw_text:
            # 2. Generate Quiz
            st.session_state.quiz_data = generate_quiz_from_text(
                raw_text, difficulty, num_questions
            )
            
            if st.session_state.quiz_data:
                # 3. Reset state for a new quiz
                st.session_state.current_q_index = 0
                st.session_state.user_answers = [] # <--- CORRECTED
                st.session_state.score = 0
                
                # 4. <<< STATE TRANSITION >>>
                st.session_state.app_view = 'quiz'
                st.rerun() # Force rerun to show the 'quiz' view
            else:
                st.error("Could not generate a quiz from the provided PDF.")
        else:
            st.error("Could not extract text from the PDF.")

# --- Main Area (View Rendering) ---
# This block acts as a "router" based on the app's current state
if st.session_state.app_view == 'upload':
    st.info("Upload a PDF and select your quiz options in the sidebar to begin.")
    # You can replace this with a real image URL if you have one
    # st.image("httpsD://.../placeholder_image.png", caption="QuizGen helps you study any PDF document.")

elif st.session_state.app_view == 'quiz':
    if st.session_state.quiz_data:
        render_quiz_view()  # This will now work
    else:
        st.error("Quiz data is missing. Please generate a new quiz.")
        st.session_state.app_view = 'upload' # Reset
        
elif st.session_state.app_view == 'results':
    render_results_dashboard()  # This will now work