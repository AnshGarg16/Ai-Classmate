# open_notebook/domain/evaluator.py
import json
from open_notebook.graphs.utils import provision_langchain_model
from open_notebook.domain.models import model_manager
from open_notebook.domain.quiz import _extract_model_text
from open_notebook.database.repository import repo_create

EVAL_PROMPT = """
You are an expert grader for educational answers.

Input JSON:
{{"question": {question},
 "correct_answer": {correct},
 "student_answer": {answer},
 "context": {context_if_any}
}}

Return EXACTLY a JSON object with keys:
- score: float between 0.0 and 1.0
- grade: one of ["correct","partially_correct","incorrect"]
- concepts: list of important concept tags covered/missed
- justification: an explanation in 1-4 sentences about what was correct/incorrect and the key concept errors
- hints: short helpful hint(s) if incorrect

Do NOT include any extra text.
"""

def evaluate_answer(question_text, correct_answer, student_answer, context="", model_id=None):
    prompt = EVAL_PROMPT.format(
        question=json.dumps(question_text),
        correct=json.dumps(correct_answer),
        answer=json.dumps(student_answer),
        context=json.dumps(context)
    )
    model = provision_langchain_model(prompt, model_id, "tools", max_tokens=600)
    resp = model.invoke(prompt)
    txt = _extract_model_text(resp)
    # parse JSON
    try:
        out = json.loads(txt)
    except Exception:
        # try to extract JSON substring
        import re
        m = re.search(r"(\{.*\})", txt, re.S)
        if m:
            out = json.loads(m.group(1))
        else:
            out = {"score":0.0, "grade":"incorrect", "concepts":[], "justification":txt, "hints":""}
    # Save attempt to DB
    attempt = {
        "user_id": "student_001",  # replace with real user
        "question_text": question_text,
        "answer_text": student_answer,
        "score": out.get("score", 0.0),
        "justification": out.get("justification", ""),
        "concepts": out.get("concepts", []),
        "created_at": datetime.utcnow().isoformat(),
    }
    repo_create("quiz_attempts", attempt)
    return out
