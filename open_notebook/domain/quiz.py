# open_notebook/domain/quiz.py
from datetime import datetime
from typing import List, Optional, Dict, Any
from open_notebook.graphs.utils import provision_langchain_model
from open_notebook.database.repository import repo_create, repo_query, repo_upsert
from open_notebook.domain.models import model_manager
import json

def _extract_model_text(resp):
    # robust extraction of model response text
    try:
        if hasattr(resp, "text"):
            return resp.text
        if hasattr(resp, "content"):
            c = resp.content
            return c() if callable(c) else c
        # fallback to string representation
        return str(resp)
    except Exception:
        return str(resp)

# def generate_questions_from_text(
#     text: str,
#     num_questions: int = 10,
#     difficulty_distribution: Dict[str,int] = None,
#     model_id: Optional[str] = None
# ) -> List[Dict[str,Any]]:
#     """
#     Calls LLM to generate a list of question objects:
#     [{question_text, question_type, choices, correct_answer, difficulty, concepts}]
#     """
#     if difficulty_distribution is None:
#         difficulty_distribution = {"easy": int(num_questions*0.4), "medium": int(num_questions*0.4), "hard": int(num_questions*0.2)}

#     system_prompt = f"""
# You are an educational question generator. Receive content and produce exactly JSON list of questions.
# Return an array of objects with keys:
# question_text, question_type (mcq|short), choices (list or []), correct_answer (string),
# difficulty (easy|medium|hard), concepts (list of up to 5 tags).

# Requirements:
# - Produce {num_questions} questions with difficulty distribution {difficulty_distribution}.
# - For MCQs provide 3-5 plausible choices; label correct_answer with one of choices.
# - Output ONLY valid JSON (no extra commentary).
# CONTENT:
# {text}
# """
#     model = provision_langchain_model(system_prompt, model_id, "transformation", max_tokens=1500)
#     resp = model.invoke(system_prompt)
#     txt = _extract_model_text(resp)

#     # parse JSON robustly
#     try:
#         questions = json.loads(txt)
#     except Exception:
#         # fallback: try to extract first JSON substring
#         import re
#         m = re.search(r"(\[.*\])", txt, re.S)
#         if m:
#             questions = json.loads(m.group(1))
#         else:
#             raise ValueError("Unable to parse question generator response: " + txt)

#     # normalize & return
#     return questions

def generate_questions_from_text(
    text: str,
    num_questions: int = 10,
    difficulty_distribution: Dict[str,int] = None,
    model_id: Optional[str] = None
) -> List[Dict[str,Any]]:
    """
    Calls LLM to generate a list of question objects:
    [{question_text, question_type, choices, correct_answer, difficulty, concepts}]
    """
    if difficulty_distribution is None:
        difficulty_distribution = {"easy": int(num_questions*0.4), "medium": int(num_questions*0.4), "hard": int(num_questions*0.2)}

    system_prompt = f"""
You are an educational question generator. Receive content and produce exactly JSON list of questions.
Return an array of objects with keys:
question_text, question_type (mcq|short), choices (list or []), correct_answer (string),
difficulty (easy|medium|hard), concepts (list of up to 5 tags).

Requirements:
- Produce {num_questions} questions with difficulty distribution {difficulty_distribution}.
- For MCQs provide 3-5 plausible choices; label correct_answer with one of choices.
- Output ONLY valid JSON (no extra commentary).
CONTENT:
{text}
"""
    model = provision_langchain_model(system_prompt, model_id, "transformation", max_tokens=1500)
    resp = model.invoke(system_prompt)
    txt = _extract_model_text(resp)

    # --- START OF FIX ---
    # Add a guard clause to check for an empty model response
    if not txt:
        raise ValueError("Model returned an empty response. Unable to generate questions.")
    # --- END OF FIX ---

    # parse JSON robustly
    try:
        questions = json.loads(txt)
    except Exception:
        # fallback: try to extract first JSON substring
        import re
        
        # This line is now safe because we know 'txt' is a non-empty string
        m = re.search(r"(\[.*\])", txt, re.S) 
        if m:
            questions = json.loads(m.group(1))
        else:
            # Truncate the error message to avoid printing huge unparseable text
            raise ValueError("Unable to parse question generator response: " + txt[:200] + "...")

    # normalize & return
    return questions

def save_question_record(q: Dict[str,Any], notebook_id: Optional[str]=None):
    rec = {
        "question_text": q.get("question_text"),
        "question_type": q.get("question_type","short"),
        "choices": q.get("choices", []),
        "correct_answer": q.get("correct_answer"),
        "difficulty": q.get("difficulty","medium"),
        "concepts": q.get("concepts", []),
        "notebook_id": notebook_id,
        "created_at": datetime.utcnow().isoformat()
    }
    return repo_create("quiz_questions", rec)

def embed_and_store_question(question_id:str, question_text:str):
    EMB = model_manager.embedding_model
    if not EMB:
        return None
    embedding = EMB.embed([question_text])[0]
    # update record with embedding
    repo_upsert("quiz_questions", {"id": question_id, "embedding": embedding})
    return embedding

def unwrap_surreal_result(res):
    if not res:
        return []
    if isinstance(res, list) and len(res)>0:
        return res[0].get("result", [])
    return res
