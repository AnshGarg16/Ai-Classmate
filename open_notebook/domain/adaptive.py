# open_notebook/domain/adaptive.py
from datetime import datetime
from open_notebook.database.repository import repo_query, repo_upsert
import random

# fetch candidate questions by difficulty and not recently answered
def fetch_candidate_questions(user_id, difficulty, limit=5, notebook_id=None):
    q = """
    SELECT * FROM quiz_questions
    WHERE difficulty = $difficulty
    """ + (" AND notebook_id = $notebook_id" if notebook_id else "") + " LIMIT $limit;"
    return repo_query(q, {"difficulty": difficulty, "limit": limit, "notebook_id": notebook_id})

# Compute user's proficiency (simple EWMA) - stored in user_proficiency
def update_user_proficiency(user_id, concept, new_score, alpha=0.3):
    # fetch existing
    res = repo_query("SELECT * FROM user_proficiency WHERE user_id = $user_id AND concept = $concept;", {"user_id": user_id, "concept": concept})
    curr = res[0]["result"][0] if res and "result" in res[0] and res[0]["result"] else None
    if curr:
        ewma = float(curr.get("score_ewma", 0))
        ewma = alpha * new_score + (1-alpha)*ewma
        repo_upsert("user_proficiency", {"id": curr["id"], "score_ewma": ewma, "updated_at": datetime.utcnow().isoformat()})
    else:
        repo_create("user_proficiency", {"user_id": user_id, "concept": concept, "score_ewma": new_score, "updated_at": datetime.utcnow().isoformat()})

def select_next_question(user_id, notebook_id=None):
    # simple strategy:
    # - compute an overall proficiency average (if none assume 0.5)
    # - choose difficulty: low proficiency -> easy, high -> hard
    # - fetch candidate questions and pick random one
    p_res = repo_query("SELECT AVG(score_ewma) as avgp FROM user_proficiency WHERE user_id = $user_id;", {"user_id": user_id})
    avgp = 0.5
    if p_res and "result" in p_res[0] and p_res[0]["result"]:
        avgp = float(p_res[0]["result"][0].get("avgp") or 0.5)
    if avgp < 0.45:
        diff = "easy"
    elif avgp > 0.65:
        diff = "hard"
    else:
        diff = "medium"

    cand = fetch_candidate_questions(user_id, diff, limit=20, notebook_id=notebook_id)
    # unwrap Surreal result shape
    candidates = cand[0]["result"] if cand and "result" in cand[0] else []
    if not candidates:
        # fallback: any difficulty
        cand = repo_query("SELECT * FROM quiz_questions LIMIT 20;")
        candidates = cand[0]["result"] if cand and "result" in cand[0] else []
    if not candidates:
        return None
    return random.choice(candidates)
