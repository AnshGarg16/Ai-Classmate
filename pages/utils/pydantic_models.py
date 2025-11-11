from pydantic import BaseModel, Field
from typing import List

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