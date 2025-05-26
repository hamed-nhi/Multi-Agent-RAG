# database/populate_db.py
import sqlite3
from pymongo import MongoClient

def populate_sqlite():
    """
    Creates and populates the SQLite database with a more complex schema
    and a larger, more realistic dataset.
    """
    conn = sqlite3.connect('database/employees.db')
    cursor = conn.cursor()

    # --- Drop existing tables to ensure a clean slate ---
    cursor.execute("DROP TABLE IF EXISTS projects")
    cursor.execute("DROP TABLE IF EXISTS employees")
    cursor.execute("DROP TABLE IF EXISTS departments")

    # --- Create new tables with more complexity ---
    cursor.execute('''
    CREATE TABLE departments (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE
    )
    ''')
    cursor.execute('''
    CREATE TABLE employees (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        department_id INTEGER,
        FOREIGN KEY (department_id) REFERENCES departments (id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE projects (
        id INTEGER PRIMARY KEY,
        project_name TEXT NOT NULL,
        employee_id INTEGER,
        status TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    )
    ''')

    # --- Insert new, expanded data ---
    departments_data = [
        (1, 'Engineering'),
        (2, 'Project Management'),
        (3, 'Data Science'),
        (4, 'Human Resources') # New Department
    ]
    cursor.executemany("INSERT INTO departments (id, name) VALUES (?, ?)", departments_data)

    employees_data = [
        # (id, name, role, department_id)
        (1, 'Saba Attar', 'Data Scientist', 3),
        (2, 'Mahesh Deshmukh', 'Project Manager', 2),
        (3, 'Aniruddha Salve', 'Lead Engineer', 1),
        (4, 'Sayali Shivpuje', 'Software Engineer', 1),
        (5, 'Arnab Mitra', 'Senior Data Scientist', 3), # New Employee
        (6, 'Priya Sharma', 'HR Specialist', 4),      # New Employee
        (7, 'Rohan Verma', 'DevOps Engineer', 1)       # New Employee
    ]
    cursor.executemany("INSERT INTO employees (id, name, role, department_id) VALUES (?, ?, ?, ?)", employees_data)

    projects_data = [
        (1, 'Multi-Agent RAG System', 3, 'active'),
        (2, 'Customer Churn Prediction', 1, 'completed'),
        (3, 'Inventory Management Dashboard', 2, 'active'),
        (4, 'API Integration Service', 4, 'paused'),
        (5, 'Real-time Analytics Platform', 5, 'active'),      # New Project
        (6, 'Employee Onboarding Automation', 6, 'planning'), # New Project
        (7, 'CI/CD Pipeline Optimization', 7, 'completed')     # New Project
    ]
    cursor.executemany("INSERT INTO projects (id, project_name, employee_id, status) VALUES (?, ?, ?, ?)", projects_data)

    print("SQLite database 'employees.db' re-populated successfully with expanded dataset.")
    conn.commit()
    conn.close()

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
        }
    ]
    collection.insert_many(papers_data)
    print("MongoDB database 'research_db' re-populated successfully with expanded dataset.")
    client.close()

if __name__ == "__main__":
    print("Starting database population...")
    populate_sqlite()
    populate_mongodb()
    print("Database population finished.")