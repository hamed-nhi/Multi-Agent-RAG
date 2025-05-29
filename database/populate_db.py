# database/populate_db.py
import sqlite3
from pymongo import MongoClient
# from elasticsearch import Elasticsearch 
# import meilisearch 
from neo4j import GraphDatabase 
import meilisearch # اطمینان از وارد شدن صحیح
from meilisearch.errors import MeilisearchApiError # وارد کردن مستقیم کلاس خطا
import os

# def populate_sqlite():
    # """
    # Creates and populates the SQLite database with a more complex schema
    # and a larger, more realistic dataset.
    # """
    # # Get the directory where the current script (populate_db.py) is located
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # # Define the path to the database file relative to the script's directory
    # db_path = os.path.join(script_dir, 'employees.db')
    
    # print(f"Attempting to connect to SQLite database at: {db_path}") # For debugging
    
    # conn = sqlite3.connect(db_path) # MODIFIED: Use the calculated absolute path
    # cursor = conn.cursor()

    # # --- Drop existing tables to ensure a clean slate ---
    # cursor.execute("DROP TABLE IF EXISTS projects")
    # cursor.execute("DROP TABLE IF EXISTS employees")
    # cursor.execute("DROP TABLE IF EXISTS departments")

    # # --- Create new tables with more complexity ---
    # cursor.execute('''
    # CREATE TABLE departments (
    #     id INTEGER PRIMARY KEY,
    #     name TEXT NOT NULL UNIQUE
    # )
    # ''')
    # cursor.execute('''
    # CREATE TABLE employees (
    #     id INTEGER PRIMARY KEY,
    #     name TEXT NOT NULL,
    #     role TEXT NOT NULL,
    #     department_id INTEGER,
    #     FOREIGN KEY (department_id) REFERENCES departments (id)
    # )
    # ''')
    # cursor.execute('''
    # CREATE TABLE projects (
    #     id INTEGER PRIMARY KEY,
    #     project_name TEXT NOT NULL,
    #     employee_id INTEGER,
    #     status TEXT,
    #     FOREIGN KEY (employee_id) REFERENCES employees (id)
    # )
    # ''')

    # # --- Insert new, expanded data ---
    # departments_data = [
    #     (1, 'Engineering'),
    #     (2, 'Project Management'),
    #     (3, 'Data Science'),
    #     (4, 'Human Resources') 
    # ]
    # cursor.executemany("INSERT INTO departments (id, name) VALUES (?, ?)", departments_data)

    # employees_data = [
    #     (1, 'Saba Attar', 'Data Scientist', 3),
    #     (2, 'Mahesh Deshmukh', 'Project Manager', 2),
    #     (3, 'Aniruddha Salve', 'Lead Engineer', 1),
    #     (4, 'Sayali Shivpuje', 'Software Engineer', 1),
    #     (5, 'Arnab Mitra', 'Senior Data Scientist', 3), 
    #     (6, 'Priya Sharma', 'HR Specialist', 4),      
    #     (7, 'Rohan Verma', 'DevOps Engineer', 1)       
    # ]
    # # Ensure the INSERT statement matches the number of columns (id, name, role, department_id)
    # cursor.executemany("INSERT INTO employees (id, name, role, department_id) VALUES (?, ?, ?, ?)", employees_data)


    # projects_data = [
    #     (1, 'Multi-Agent RAG System', 3, 'active'),
    #     (2, 'Customer Churn Prediction', 1, 'completed'),
    #     (3, 'Inventory Management Dashboard', 2, 'active'),
    #     (4, 'API Integration Service', 4, 'paused'),
    #     (5, 'Real-time Analytics Platform', 5, 'active'),      
    #     (6, 'Employee Onboarding Automation', 6, 'planning'), 
    #     (7, 'CI/CD Pipeline Optimization', 7, 'completed')     
    # ]
    # cursor.executemany("INSERT INTO projects (id, project_name, employee_id, status) VALUES (?, ?, ?, ?)", projects_data)

    # print("SQLite database 'employees.db' re-populated successfully with expanded dataset.")
    # conn.commit()
    # conn.close()

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

def populate_mongodb():
    """Creates and populates the MongoDB database with an expanded and more realistic dataset."""
    client = MongoClient('mongodb://localhost:27017/')
    db = client['research_db']
    collection = db['papers']

    collection.delete_many({})
    
    papers_data = [
        {
            "title": "A Collaborative Multi-Agent Approach to RAG",
            "authors": ["Aniruddha Salve", "Saba Attar", "Mahesh Deshmukh"],
            "year": 2024,
            "topic": "Generative AI",
            "keywords": ["multi-agent", "rag", "database integration"],
            "publication": {"journal": "arXiv", "type": "preprint"}
        },
        {
            "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
            "authors": ["Patrick Lewis", "Ethan Perez", "Sebastian Riedel"],
            "year": 2020,
            "topic": "NLP",
            "keywords": ["knowledge-intensive", "open-domain qa", "nlp"],
            "publication": {"journal": "NeurIPS", "type": "conference paper"}
        },
        {
            "title": "Cognitive Architectures for Language Agents",
            "authors": ["Theodore R. Sumers", "Shunyu Yao", "Thomas L. Griffiths"],
            "year": 2024,
            "topic": "Language Agents",
            "keywords": ["cognitive science", "language models", "reasoning"],
            "publication": {"journal": "arXiv", "type": "preprint"}
        },
        # --- NEW DATA BELOW ---
        {
            "title": "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection",
            "authors": ["Akari Asai", "Zeqiu Wu", "Yizhong Wang", "Avirup Sil", "Wen-tau Yih"],
            "year": 2023,
            "topic": "Generative AI",
            "keywords": ["self-reflection", "retrieval", "critique", "RAG"],
            "publication": {"journal": "arXiv", "type": "preprint"}
        },
        {
            "title": "Aligning Large Language Models to a Domain-Specific Graph Database",
            "authors": ["Yuanyuan Liang", "Keren Tan", "Tingyu Xie", "Yunshi Lan"],
            "year": 2024,
            "topic": "Graph Database",
            "keywords": ["graphdb", "alignment", "LLM"],
            "publication": {"journal": "arXiv", "type": "preprint"}
        },
        {
            "title": "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
            "authors": ["Jason Wei", "Xuezhi Wang", "Dale Schuurmans", "Maarten Bosma"],
            "year": 2022,
            "topic": "Prompt Engineering",
            "keywords": ["reasoning", "chain-of-thought", "prompting"],
            "publication": {"journal": "NeurIPS", "type": "conference paper"}
        },
        {
            "title": "Speculative RAG: Enhancing Retrieval-Augmented Generation",
            "authors": ["Zhao Wang", "Zhihao Wang", "Thomas Pfister"],
            "year": 2024,
            "topic": "AI Efficiency",
            "keywords": ["speculative decoding", "rag", "latency"],
            "publication": {"journal": "Journal of AI Research", "type": "journal"}
        },
        {
            "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks", # Paper [user_provided_document_id_3]
            "authors": ["Patrick Lewis", "Ethan Perez", "Sebastian Riedel"], # Paper [user_provided_document_id_3]
            "year": 2020, # Paper [user_provided_document_id_3]
            "topic": "NLP", # Paper [user_provided_document_id_3]
            "keywords": ["knowledge-intensive", "open-domain qa", "nlp", "RAG"], # <--- "RAG" اینجا اضافه شد
            "publication": {"journal": "NeurIPS", "type": "conference paper"} # Paper [user_provided_document_id_3]
        },
    ]
    collection.insert_many(papers_data)
    print("MongoDB database 'research_db' re-populated successfully with expanded dataset.")
    client.close()




# def populate_meilisearch():
#     """
#     Creates and populates the MeiliSearch index with support tickets.
#     Uses a more robust error check for 'index_not_found'.
#     """
#     print("--- POPULATING MEILISEARCH ---")
#     try:
#         client = meilisearch.Client("http://localhost:7700")
#         client.get_indexes() 
#         print("Successfully connected to MeiliSearch.")
#     except Exception as e:
#         print(f"Error connecting to MeiliSearch: {e}")
#         print("Skipping MeiliSearch population. Ensure MeiliSearch server is running.")
#         return

#     index_name = "support_tickets"
#     index_uid = index_name # In MeiliSearch, index_name is often referred to as index_uid
#     index = None 

#     try:
#         # Try to delete the index first if it exists, to ensure a clean state for the script
#         try:
#             print(f"Attempting to delete existing MeiliSearch index if present: {index_uid}")
#             task_delete = client.delete_index(index_uid)
#             client.wait_for_task(task_delete.task_uid) 
#             print(f"Successfully deleted existing MeiliSearch index: {index_uid}")
#         except MeilisearchApiError as e:
#             # More robust check for "index_not_found"
#             # Check common ways the error might be presented by the SDK
#             error_str_lower = str(e).lower()
#             is_index_not_found = 'index_not_found' in error_str_lower or \
#                                  (hasattr(e, 'message') and 'index_not_found' in e.message.lower()) or \
#                                  (hasattr(e, 'error_code') and e.error_code == 'index_not_found') # Keep original check as a fallback
            
#             if is_index_not_found:
#                 print(f"MeiliSearch Index '{index_uid}' not found, no need to delete.")
#             else:
#                 # For other API errors during deletion attempt, we might want to log or handle
#                 print(f"MeiliSearch API error while trying to delete index '{index_uid}' (will attempt to create anyway): {e}")
#         except Exception as e_general: # Catch other general errors during delete
#              print(f"Unexpected error during index deletion for '{index_uid}': {e_general}. Proceeding to create.")

#         # Create the new index
#         print(f"Attempting to create MeiliSearch index: {index_uid} with primary key 'ticket_id'.")
#         # create_index will raise an error if the index already exists and it wasn't deleted.
#         # If the delete failed for reasons other than "not_found", this might error out, which is okay.
#         task_create = client.create_index(index_uid, {'primaryKey': 'ticket_id'})
#         client.wait_for_task(task_create.task_uid) 
#         index = client.get_index(index_uid) 
#         print(f"Successfully created MeiliSearch index: {index_uid}.")

#         tickets = [
#             {"ticket_id": "T001", "description": "MySQL issue: cannot connect", "raised_by": "Sayali Shivpuje", "status": "open"},
#             {"ticket_id": "T002", "description": "Neo4j graph visualization not loading", "raised_by": "Aniruddha Salve", "status": "open"},
#             {"ticket_id": "T003", "description": "Question about MySQL LEFT JOIN functionality", "raised_by": "Saba Attar", "status": "closed"},
#             {"ticket_id": "T004", "description": "Search query for open tickets related to Neo4j raised by Aniruddha Salve", "raised_by": "Aniruddha Salve", "status": "open"},
#             {"ticket_id": "T005", "description": "Login problem with new MySQL credentials", "raised_by": "Mahesh Deshmukh", "status": "in_progress"}
#         ]

#         if index: 
#             task_add_docs = index.add_documents(tickets)
#             print(f"Documents submission task created for MeiliSearch index '{index_uid}'. Task UID: {task_add_docs.task_uid}")
#             client.wait_for_task(task_add_docs.task_uid) 
            
#             stats = index.get_stats()
#             print(f"Verification: MeiliSearch Index '{index_uid}' now contains {stats.number_of_documents} documents.")
#         else:
#             print(f"Failed to get a valid index object for '{index_uid}' after creation. Documents not added.")

#     except MeilisearchApiError as e_api: # Catch API errors during create/add_documents
#         print(f"A MeiliSearch API error occurred during population: {e_api}")
#         print(f"Error Code: {getattr(e_api, 'error_code', 'N/A')}, Message: {getattr(e_api, 'message', str(e_api))}")
#     except Exception as e_general:
#         print(f"An unexpected error occurred during MeiliSearch population: {e_general}")


# def populate_neo4j():
#     """
#     Creates and populates the Neo4j database with a sample research network.
#     """
#     print("--- POPULATING NEO4J ---")
#     # Define your Neo4j connection details
#     NEO4J_URI = "bolt://localhost:7687"
#     NEO4J_USER = "neo4j"
#     NEO4J_PASSWORD = "12345678Az" # !!! IMPORTANT: REPLACE WITH YOUR ACTUAL PASSWORD !!!

#     driver = None  # Initialize driver to None
#     try:
#         driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
#         driver.verify_connectivity() # Check connection
#         print("Successfully connected to Neo4j.")

#         with driver.session(database="myraggraphdb") as session: # Specify the database name
#             # Clear existing data to start fresh (optional, but good for repeatable script)
#             session.run("MATCH (n) DETACH DELETE n")
#             print("Cleared existing data from Neo4j database 'myraggraphdb'.")

#             # --- Create Nodes (Researchers) ---
#             # Based on names from the paper and our project
#             researchers_data = [
#                 {"name": "Aniruddha Salve", "field": "Generative AI"},
#                 {"name": "Saba Attar", "field": "Data Science"},
#                 {"name": "Mahesh Deshmukh", "field": "Project Management"},
#                 {"name": "Sayali Shivpuje", "field": "Software Engineering"},
#                 {"name": "Arnab Mitra Utsab", "field": "Data Science"}, # From paper's examples
#                 {"name": "Patrick Lewis", "field": "NLP"},          # Famous RAG author
#                 {"name": "Theodore R. Sumers", "field": "Language Agents"} # From paper's references
#             ]

#             for researcher in researchers_data:
#                 session.run("CREATE (r:Researcher {name: $name, field: $field})",
#                             name=researcher["name"], field=researcher["field"])
#             print(f"Created {len(researchers_data)} Researcher nodes.")

#             # --- Create Relationships (COLLABORATES_WITH, WORKS_ON) ---
#             # This is just sample data, you can make it more complex
            
#             # COLLABORATES_WITH
#             collaborations = [
#                 ("Aniruddha Salve", "Saba Attar"),
#                 ("Aniruddha Salve", "Mahesh Deshmukh"),
#                 ("Saba Attar", "Arnab Mitra Utsab"),
#                 ("Patrick Lewis", "Theodore R. Sumers") # Fictional collaboration for example
#             ]
#             for r1_name, r2_name in collaborations:
#                 session.run("""
#                     MATCH (r1:Researcher {name: $r1_name})
#                     MATCH (r2:Researcher {name: $r2_name})
#                     CREATE (r1)-[:COLLABORATES_WITH]->(r2)
#                 """, r1_name=r1_name, r2_name=r2_name)
#             print(f"Created {len(collaborations)} COLLABORATES_WITH relationships.")

#             # WORKS_ON (linking researchers to projects/topics - simplified as nodes for now)
#             # First, create some project/topic nodes
#             projects_topics_data = [
#                 {"name": "Multi-Agent RAG", "domain": "Generative AI"},
#                 {"name": "AI in Healthcare", "domain": "Healthcare AI"}, # From paper example [cite: 88, 89]
#                 {"name": "Knowledge-Intensive NLP", "domain": "NLP"}
#             ]
#             for pt in projects_topics_data:
#                 # Using a generic 'ProjectOrTopic' label for simplicity
#                 session.run("CREATE (pt:ProjectOrTopic {name: $name, domain: $domain})",
#                             name=pt["name"], domain=pt["domain"])
#             print(f"Created {len(projects_topics_data)} ProjectOrTopic nodes.")
            
#             # Now, link researchers to these
#             works_on_relations = [
#                 ("Aniruddha Salve", "Multi-Agent RAG"),
#                 ("Saba Attar", "Multi-Agent RAG"),
#                 ("Arnab Mitra Utsab", "AI in Healthcare"), # Example from paper [cite: 88]
#                 ("Patrick Lewis", "Knowledge-Intensive NLP"),
#                 ("Theodore R. Sumers", "AI in Healthcare") # Example for a second researcher on the same project
#             ]
#             for researcher_name, project_name in works_on_relations:
#                 session.run("""
#                     MATCH (r:Researcher {name: $researcher_name})
#                     MATCH (pt:ProjectOrTopic {name: $project_name})
#                     CREATE (r)-[:WORKS_ON]->(pt)
#                 """, researcher_name=researcher_name, project_name=project_name)
#             print(f"Created {len(works_on_relations)} WORKS_ON relationships.")

#         print("Neo4j database 'mygraphdb' populated successfully.")

#     except Exception as e:
#         print(f"An error occurred during Neo4j population: {e}")
#     finally:
#         if driver:
#             driver.close()
#             print("Neo4j connection closed.")



if __name__ == "__main__":
    print("Starting database population...")
    # populate_sqlite()
    populate_mongodb()
    # populate_meilisearch() 
    # populate_neo4j()
    print("Database population finished.")