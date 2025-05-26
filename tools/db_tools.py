
import ast
import sqlite3
from pymongo import MongoClient
from langchain_core.tools import tool

# --- SQLite Tools ---

def get_sqlite_connection():
    """Returns a connection to the SQLite database."""
    return sqlite3.connect('database/employees.db')

@tool
def get_schema_sqlite(db_name: str = 'employees.db') -> str:
    """
    Returns the schema of the SQLite database.
    Use this to understand the tables and columns available for querying.
    """
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    schema_description = "SQLite Database Schema:\n"
    for table_name in tables:
        table_name = table_name[0]
        schema_description += f"\nTable: {table_name}\n"
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        for column in columns:
            schema_description += f"  - {column[1]} ({column[2]})\n"
    conn.close()
    return schema_description

@tool
def run_sqlite_query(query: str) -> str:
    """
    Executes a given SQL query on the 'employees.db' SQLite database.
    Use this to retrieve information about employees and their projects.
    """
    try:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return str(result)
    except Exception as e:
        return f"An error occurred: {e}"

# --- MongoDB Tools ---


def get_mongodb_client():
    """Returns a client connection to the MongoDB."""
    return MongoClient('mongodb://localhost:27017/')

@tool
def run_mongodb_query(query_str: str) -> str: # ورودی را به str تغییر می‌دهیم
    """
    Executes a query on the 'papers' collection in the 'research_db' MongoDB database.
    The query must be provided as a string representation of a Python dictionary.
    Use this to find research papers, authors, or topics.
    Example query_str: "{'year': 2024, 'topic': 'Generative AI'}"
    """
    try:
        client = get_mongodb_client()
        db = client['research_db']
        collection = db['papers']
        
        # Convert the string representation of a dict to an actual dict
        try:
            query_dict = ast.literal_eval(query_str)
            if not isinstance(query_dict, dict):
                raise ValueError("Input is not a valid dictionary structure.")
        except (ValueError, SyntaxError) as e:
            return f"Failed to parse query string. It must be a valid dictionary string. Error: {e}"

        result = list(collection.find(query_dict, {'_id': 0}))
        client.close()

        if not result:
            return "No documents found matching the query."
            
        return str(result)
    except Exception as e:
        return f"An error occurred during MongoDB query execution: {e}"
