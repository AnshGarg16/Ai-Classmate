# pages/5_Quiz_Generator.py
import streamlit as st
from pages.stream_app.utils import setup_page  # ✅ add this line
from open_notebook.domain.notebook import Notebook
from open_notebook.domain.quiz import generate_questions_from_text, save_question_record, embed_and_store_question

setup_page("🧠 Quiz Generator", only_check_mandatory_models=True)
st.title("🧠 Quiz Generator")
st.write("Test your knowledge based on your study materials.")

# nb = st.selectbox("Choose Notebook", Notebook.get_all(), format_func=lambda x: x.name)
nb = st.selectbox("Choose Notebook", Notebook.get_all(), format_func=lambda x: x.name)
# text_to_use = nb.description + "\n\n" + "\n".join([s.full_text for s in nb.sources])  # or more selective
# num_q = st.slider("Number of questions", 4, 20, 8)
if nb:
    # All the logic that depends on 'nb' must be inside this if-block.
    # text_to_use = nb.description + "\n\n" + "\n".join([s.full_text for s in nb.sources])  # or more selective
    # Safely get all non-None text strings from sources
    source_texts = [s.full_text for s in nb.sources if s and s.full_text]

    # Now join them
    text_to_use = nb.description + "\n\n" + "\n".join(source_texts)
    num_q = st.slider("Number of questions", 4, 20, 8)
# if st.button("Generate Questions"):
#     with st.spinner("Generating..."):
#         questions = generate_questions_from_text(text_to_use, num_questions=num_q)
#         for q in questions:
#             r = save_question_record(q, notebook_id=nb.id)
#             # extract created id as earlier and embed
#             st.success("Saved question: " + q["question_text"][:80])
#     st.success("Done")
    if st.button("Generate Questions"):
    
        # --- START OF FIX ---
        # Check if the text (after stripping whitespace) is empty
        if not text_to_use or not text_to_use.strip():
            st.error("This notebook is empty. Please add a description or sources to generate a quiz.")
        else:
            # Only run if text exists
            with st.spinner("Generating..."):
                questions = generate_questions_from_text(text_to_use, num_questions=num_q)
                
                if questions:
                    for q in questions:
                        r = save_question_record(q, notebook_id=nb.id)
                        # extract created id as earlier and embed
                        st.success("Saved question: " + q["question_text"][:80])
                    st.success("Done")
                else:
                    st.error("Could not generate questions from the provided text.")

else:
    # Display a warning if no notebooks exist or are selected.
    st.warning("No notebooks found. Please create a notebook first to generate a quiz.")
