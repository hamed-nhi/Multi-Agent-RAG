
import ast
import sqlite3
from pymongo import MongoClient
import meilisearch
from langchain_core.tools import tool
from neo4j import GraphDatabase
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


# --- Meilisearch Tools ---
def get_meilisearch_client():
    """
    Returns a client connection to the MeiliSearch instance.
    """
    # Ensure your MeiliSearch server is running, typically on http://localhost:7700
    # If you have set a master key, provide it as the second argument.
    client = meilisearch.Client("http://localhost:7700")
    return client

@tool
def run_meilisearch_query(search_query: str, index_name: str = "support_tickets", limit: int = 5) -> str:
    """
    Executes a search query on the specified MeiliSearch index (default: 'support_tickets').
    'search_query' is the text string to search for.
    'limit' specifies the maximum number of search results to return.
    Use this to find support tickets based on their description or other text fields.
    """
    try:
        client = get_meilisearch_client()
        index = client.get_index(index_name)
        
        search_results = index.search(search_query, {'limit': limit})
        
        # --- ADD THIS PRINT STATEMENT ---
        print(f"MeiliSearch raw search_results: {search_results}") 
        
        hits = search_results.get('hits', [])
        
        # --- ADD THIS PRINT STATEMENT ---
        print(f"MeiliSearch extracted hits: {hits}")

        if not hits:
            return "No documents found matching the search query in MeiliSearch."
            
        return str(hits) 
    except Exception as e:
        return f"An error occurred during MeiliSearch query execution: {e}"

def get_neo4j_driver():
    """
    Returns a Neo4j driver instance.
    Remember to close the driver when done: driver.close()
    """
    # Define your Neo4j connection details
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "12345678Az"
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        driver.verify_connectivity()
        # print("Successfully connected to Neo4j for tool setup.") # Optional: for verbose logging
    except Exception as e:
        print(f"Error connecting to Neo4j for tool: {e}")
        # If connection fails, we might want to raise an error or return None
        # For now, the tool will fail later if the driver is None or connection fails
        raise ConnectionError(f"Could not connect to Neo4j: {e}")
    return driver

@tool
def run_neo4j_query(cypher_query: str, database: str = "myraggraphdb") -> str:
    """
    Executes a Cypher query on the specified Neo4j database (default: 'myraggraphdb').
    'cypher_query' is the Cypher query string to execute.
    Use this to find information about researchers, their collaborations, and projects/topics they work on.
    Example: "MATCH (r:Researcher {name: 'Arnab Mitra Utsab'})-[:COLLABORATES_WITH]->(collaborator:Researcher) RETURN collaborator.name"
    """
    driver = None
    try:
        driver = get_neo4j_driver()
        records_list = []
        # For Neo4j, operations that write data need an explicit transaction.
        # For read-only queries, session.run() can be used directly or within a transaction.
        # Using a session ensures resources are managed correctly.
        with driver.session(database=database) as session:
            print(f"Executing Neo4j Cypher query: {cypher_query}") # For debugging
            results = session.run(cypher_query)
            # Convert results to a list of dictionaries for easier processing/display
            for record in results:
                records_list.append(record.data()) # record.data() converts each record to a dict

        if not records_list:
            return "No records found matching the Cypher query in Neo4j."
            
        return str(records_list) # Return the results as a string representation of a list of dicts
    except ConnectionError as ce: # Catching the specific connection error from get_neo4j_driver
        return f"Neo4j Connection Error: {ce}"
    except Exception as e:
        # Catching other potential errors from Neo4j, e.g., CypherSyntaxError
        return f"An error occurred during Neo4j Cypher query execution: {e}"
    finally:
        if driver:
            driver.close()
            # print("Neo4j driver connection closed for tool.") # Optional: for verbose logging