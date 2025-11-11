# open_notebook/database/setup_quiz_tables.py
from open_notebook.database.repository import repo_query

def init_quiz_tables():
    print("Creating quiz-related tables in SurrealDB...")
    repo_query("DEFINE TABLE quiz_questions SCHEMALESS;")
    repo_query("DEFINE TABLE quiz_attempts SCHEMALESS;")
    repo_query("DEFINE TABLE user_proficiency SCHEMALESS;")
    repo_query("DEFINE TABLE quiz_sets SCHEMALESS;")
    print("✅ Quiz tables created or already exist.")

if __name__ == "__main__":
    init_quiz_tables()
