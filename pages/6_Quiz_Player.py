# pages/6_Quiz_Player.py
import streamlit as st
from pages.stream_app.utils import setup_page  # ✅ add this line


from open_notebook.domain.adaptive import select_next_question
from open_notebook.domain.evaluator import evaluate_answer
from open_notebook.domain.notebook import Notebook

setup_page("📝 Adaptive Quiz")

st.title("🧠 Adaptive Quizzing System")
st.write("Test your knowledge based on your study materials.")

nb = st.selectbox("Notebook (optional)", [None] + Notebook.get_all(), format_func=lambda x: x.name if x else "All")
user_id = "student_001"
if st.button("Start Next Question"):
    q = select_next_question(user_id, notebook_id=nb.id if nb else None)
    if not q:
        st.info("No questions available")
    else:
        st.session_state["current_q"] = q
if "current_q" in st.session_state:
    q = st.session_state["current_q"]
    st.markdown(f"**Q:** {q['question_text']}")
    if q['question_type'] == 'mcq':
        choice = st.radio("Pick one:", q['choices'])
    else:
        choice = st.text_area("Your answer")
    if st.button("Submit Answer"):
        out = evaluate_answer(q['question_text'], q.get('correct_answer', ''), choice)
        st.write("**Score:**", out.get("score"))
        st.write("**Justification:**", out.get("justification"))
        st.write("**Concepts:**", ", ".join(out.get("concepts", [])))
        # update proficiency per concept: call update_user_proficiency (implement earlier)
