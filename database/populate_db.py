# database/populate_db.py
import sqlite3
from pymongo import MongoClient
# from elasticsearch import Elasticsearch 
import meilisearch 

# def populate_sqlite():
#     """
#     Creates and populates the SQLite database with a more complex schema
#     and a larger, more realistic dataset.
#     """
#     conn = sqlite3.connect('database/employees.db')
#     cursor = conn.cursor()

#     # --- Drop existing tables to ensure a clean slate ---
#     cursor.execute("DROP TABLE IF EXISTS projects")
#     cursor.execute("DROP TABLE IF EXISTS employees")
#     cursor.execute("DROP TABLE IF EXISTS departments")

#     # --- Create new tables with more complexity ---
#     cursor.execute('''
#     CREATE TABLE departments (
#         id INTEGER PRIMARY KEY,
#         name TEXT NOT NULL UNIQUE
#     )
#     ''')
#     cursor.execute('''
#     CREATE TABLE employees (
#         id INTEGER PRIMARY KEY,
#         name TEXT NOT NULL,
#         role TEXT NOT NULL,
#         department_id INTEGER,
#         FOREIGN KEY (department_id) REFERENCES departments (id)
#     )
#     ''')
#     cursor.execute('''
#     CREATE TABLE projects (
#         id INTEGER PRIMARY KEY,
#         project_name TEXT NOT NULL,
#         employee_id INTEGER,
#         status TEXT,
#         FOREIGN KEY (employee_id) REFERENCES employees (id)
#     )
#     ''')

#     # --- Insert new, expanded data ---
#     departments_data = [
#         (1, 'Engineering'),
#         (2, 'Project Management'),
#         (3, 'Data Science'),
#         (4, 'Human Resources') # New Department
#     ]
#     cursor.executemany("INSERT INTO departments (id, name) VALUES (?, ?)", departments_data)

#     employees_data = [
#         # (id, name, role, department_id)
#         (1, 'Saba Attar', 'Data Scientist', 3),
#         (2, 'Mahesh Deshmukh', 'Project Manager', 2),
#         (3, 'Aniruddha Salve', 'Lead Engineer', 1),
#         (4, 'Sayali Shivpuje', 'Software Engineer', 1),
#         (5, 'Arnab Mitra', 'Senior Data Scientist', 3), # New Employee
#         (6, 'Priya Sharma', 'HR Specialist', 4),      # New Employee
#         (7, 'Rohan Verma', 'DevOps Engineer', 1)       # New Employee
#     ]
#     cursor.executemany("INSERT INTO employees (id, name, role, department_id) VALUES (?, ?, ?, ?)", employees_data)

#     projects_data = [
#         (1, 'Multi-Agent RAG System', 3, 'active'),
#         (2, 'Customer Churn Prediction', 1, 'completed'),
#         (3, 'Inventory Management Dashboard', 2, 'active'),
#         (4, 'API Integration Service', 4, 'paused'),
#         (5, 'Real-time Analytics Platform', 5, 'active'),      # New Project
#         (6, 'Employee Onboarding Automation', 6, 'planning'), # New Project
#         (7, 'CI/CD Pipeline Optimization', 7, 'completed')     # New Project
#     ]
#     cursor.executemany("INSERT INTO projects (id, project_name, employee_id, status) VALUES (?, ?, ?, ?)", projects_data)

#     print("SQLite database 'employees.db' re-populated successfully with expanded dataset.")
#     conn.commit()
#     conn.close()

# def populate_mongodb():
#     """Creates and populates the MongoDB database with an expanded and more realistic dataset."""
#     client = MongoClient('mongodb://localhost:27017/')
#     db = client['research_db']
#     collection = db['papers']

#     collection.delete_many({})
    
#     papers_data = [
#         {
#             "title": "A Collaborative Multi-Agent Approach to RAG",
#             "authors": ["Aniruddha Salve", "Saba Attar", "Mahesh Deshmukh"],
#             "year": 2024,
#             "topic": "Generative AI",
#             "keywords": ["multi-agent", "rag", "database integration"],
#             "publication": {"journal": "arXiv", "type": "preprint"}
#         },
#         {
#             "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
#             "authors": ["Patrick Lewis", "Ethan Perez", "Sebastian Riedel"],
#             "year": 2020,
#             "topic": "NLP",
#             "keywords": ["knowledge-intensive", "open-domain qa", "nlp"],
#             "publication": {"journal": "NeurIPS", "type": "conference paper"}
#         },
#         {
#             "title": "Cognitive Architectures for Language Agents",
#             "authors": ["Theodore R. Sumers", "Shunyu Yao", "Thomas L. Griffiths"],
#             "year": 2024,
#             "topic": "Language Agents",
#             "keywords": ["cognitive science", "language models", "reasoning"],
#             "publication": {"journal": "arXiv", "type": "preprint"}
#         },
#         # --- NEW DATA BELOW ---
#         {
#             "title": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
#             "authors": ["Akari Asai", "Zeqiu Wu", "Yizhong Wang", "Avirup Sil", "Wen-tau Yih"],
#             "year": 2023,
#             "topic": "Generative AI",
#             "keywords": ["self-reflection", "retrieval", "critique", "RAG"],
#             "publication": {"journal": "arXiv", "type": "preprint"}
#         },
#         {
#             "title": "Aligning Large Language Models to a Domain-Specific Graph Database",
#             "authors": ["Yuanyuan Liang", "Keren Tan", "Tingyu Xie", "Yunshi Lan"],
#             "year": 2024,
#             "topic": "Graph Database",
#             "keywords": ["graphdb", "alignment", "LLM"],
#             "publication": {"journal": "arXiv", "type": "preprint"}
#         },
#         {
#             "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
#             "authors": ["Jason Wei", "Xuezhi Wang", "Dale Schuurmans", "Maarten Bosma"],
#             "year": 2022,
#             "topic": "Prompt Engineering",
#             "keywords": ["reasoning", "chain-of-thought", "prompting"],
#             "publication": {"journal": "NeurIPS", "type": "conference paper"}
#         },
#         {
#             "title": "Speculative RAG: Enhancing Retrieval-Augmented Generation",
#             "authors": ["Zhao Wang", "Zhihao Wang", "Thomas Pfister"],
#             "year": 2024,
#             "topic": "AI Efficiency",
#             "keywords": ["speculative decoding", "rag", "latency"],
#             "publication": {"journal": "Journal of AI Research", "type": "journal"}
#         }
#     ]
#     collection.insert_many(papers_data)
#     print("MongoDB database 'research_db' re-populated successfully with expanded dataset.")
#     client.close()

# ... (populate_sqlite and populate_mongodb functions remain here unchanged) ...
def populate_meilisearch():
    """
    Creates and populates the MeiliSearch index with support tickets.
    """
    print("--- POPULATING MEILISEARCH ---")
    try:
        client = meilisearch.Client("http://localhost:7700")
        client.get_indexes() # Check connection
        print("Successfully connected to MeiliSearch.")
    except Exception as e:
        print(f"Error connecting to MeiliSearch: {e}")
        print("Skipping MeiliSearch population. Ensure MeiliSearch server is running.")
        return

    index_name = "support_tickets"
    index = None # Initialize index variable

    try:
        # Try to get the index first
        try:
            index = client.get_index(index_name)
            # If index exists, delete it to start fresh for this script's purpose
            task_delete = client.delete_index(index_name)
            client.wait_for_task(task_delete.task_uid) # Wait for deletion to complete
            print(f"Deleted existing MeiliSearch index: {index_name}")
            index = None # Reset index variable as it's been deleted
        except meilisearch.errors.MeiliSearchApiError as e:
            if e.code == 'index_not_found':
                print(f"MeiliSearch Index '{index_name}' not found, no need to delete.")
            else:
                # For other API errors during deletion, we might want to stop or log
                print(f"Error trying to delete index '{index_name}': {e}. Proceeding to create.")


        # Create the new index
        # Specify 'ticket_id' as the primary key for our documents.
        task_create = client.create_index(index_name, {'primaryKey': 'ticket_id'})
        client.wait_for_task(task_create.task_uid) # Wait for creation to complete
        index = client.get_index(index_name) # Get the index object after creation
        print(f"Created MeiliSearch index: {index_name} with primary key 'ticket_id'.")

        tickets = [
            {"ticket_id": "T001", "description": "MySQL issue: cannot connect", "raised_by": "Sayali Shivpuje", "status": "open"},
            {"ticket_id": "T002", "description": "Neo4j graph visualization not loading", "raised_by": "Aniruddha Salve", "status": "open"},
            {"ticket_id": "T003", "description": "Question about MySQL LEFT JOIN functionality", "raised_by": "Saba Attar", "status": "closed"},
            {"ticket_id": "T004", "description": "Search query for open tickets related to Neo4j raised by Aniruddha Salve", "raised_by": "Aniruddha Salve", "status": "open"},
            {"ticket_id": "T005", "description": "Login problem with new MySQL credentials", "raised_by": "Mahesh Deshmukh", "status": "in_progress"}
        ]

        # Add documents to the index using the correct index object
        if index: # Ensure index object is valid
            task_add_docs = index.add_documents(tickets)
            print(f"Documents submission task created for MeiliSearch index '{index_name}'. Task UID: {task_add_docs.task_uid}")
            client.wait_for_task(task_add_docs.task_uid) # Wait for the documents to be processed
            
            stats = index.get_stats()
            print(f"Verification: MeiliSearch Index '{index_name}' now contains {stats.number_of_documents} documents.")
        else:
            print(f"Failed to get a valid index object for '{index_name}'. Documents not added.")

    except Exception as e:
        print(f"An error occurred during MeiliSearch population: {e}")

if __name__ == "__main__":
    print("Starting database population...")
    # populate_sqlite()
    # populate_mongodb()
    # populate_elasticsearch()
    populate_meilisearch() 

    print("Database population finished.")