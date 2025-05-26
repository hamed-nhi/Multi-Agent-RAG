# agents/query_generator.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser as StringOutputParser # Using the alias
from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY
from tools.db_tools import get_schema_sqlite # We need the schema tool

# --- Initialize the LLM ---
llm = ChatTogether(
    model=LLM_MODEL,
    together_api_key=TOGETHER_API_KEY
)

# --- SQLite Agent ---

def generate_sqlite_query(state: GraphState) -> GraphState:
    """
    Generates a SQL query for the SQLite database based on the user's question.
    """
    print("---GENERATING SQLITE QUERY---")
    query = state["query"]
    
    schema = get_schema_sqlite.invoke({}) # We call the tool directly
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are a SQLite expert. Based on the database schema and the user's question,
        generate a syntactically correct SQLite query.
        IMPORTANT: When comparing string values in WHERE clauses, always use the LOWER() function on both the column and the value to ensure case-insensitive matching. Only use the exact proper noun for matching department names.

        **Database Schema:**
        {schema}

        **User Question:**
        {question}

        **Few-shot Examples:**
        - User Question: List all active projects.
        - SQL Query: SELECT project_name FROM projects WHERE LOWER(status) = LOWER('active');

        - User Question: Which employees are in the Engineering department? {/* Note: Only 'Engineering', not 'Engineering department' */}
        - SQL Query: SELECT T1.name FROM employees AS T1 INNER JOIN departments AS T2 ON T1.department_id = T2.id WHERE LOWER(T2.name) = LOWER('Engineering');
        
        - User Question: Who is the lead engineer?
        - SQL Query: SELECT name FROM employees WHERE LOWER(role) = LOWER('Lead Engineer');
        
        - User Question: What is the status of the project assigned to Saba Attar?
        - SQL Query: SELECT T1.status FROM projects AS T1 INNER JOIN employees AS T2 ON T1.employee_id = T2.id WHERE LOWER(T2.name) = LOWER('Saba Attar');

        **Your Task:**
        Provide only the SQL query and nothing else.

        **SQL Query:**
        """
    )
    
    query_gen_chain = prompt | llm | StringOutputParser()
    generated_query = query_gen_chain.invoke({"schema": schema, "question": query})
    
    print(f"Generated SQLite Query: {generated_query}")
    
    state["generated_query"] = generated_query.strip() # Added strip()
    return state

# --- MongoDB Agent ---

def generate_mongodb_query(state: GraphState) -> GraphState:
    """
    Generates a MongoDB query dictionary based on the user's question.
    """
    print("---GENERATING MONGODB QUERY---")
    query = state["query"]
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are a MongoDB expert. Based on the collection description and the user's question,
        generate a Python dictionary for a .find() query.
        IMPORTANT: For all string value comparisons (e.g., in 'title', 'authors', 'topic', 'keywords', 'publication.journal', 'publication.type'),
        always use the `$regex` operator with the `"$options": "i"` for case-insensitive matching.
        If the user provides only part of a string to search for, use `$regex` to match that part.

        **Collection Description:**
        The 'papers' collection in the 'research_db' database contains documents with these fields:
        - `title` (string)
        - `authors` (list of strings)
        - `year` (integer)
        - `topic` (string)
        - `keywords` (list of strings)
        - `publication` (a nested object with 'journal' and 'type' string fields)

        **User Question:**
        {question}

        **Few-shot Examples:**
        - User Question: Find papers on the topic of generative ai.
        - MongoDB Query: {{"topic": {{"$regex": "generative ai", "$options": "i"}}}}

        - User Question: Who wrote the paper about 'Cognitive Architectures'?
        - MongoDB Query: {{"title": {{"$regex": "Cognitive Architectures", "$options": "i"}}}}
        
        - User Question: Find papers from the neurips conference.
        - MongoDB Query: {{"publication.type": {{"$regex": "conference paper", "$options": "i"}}, "publication.journal": {{"$regex": "neurips", "$options": "i"}}}}

        - User Question: Find papers about RAG by an author named patrick.
        - MongoDB Query: {{"authors": {{"$regex": "patrick", "$options": "i"}}, "keywords": {{"$regex": "rag", "$options": "i"}}}}
        
        - User Question: List papers published in 2024.
        - MongoDB Query: {{"year": 2024}}

        **Your Task:**
        Provide only the Python dictionary for the query and nothing else.

        **MongoDB Query:**
        """
    )
    
    # Create the generation chain
    query_gen_chain = prompt | llm | StringOutputParser()
    
    # Generate the query
    generated_query = query_gen_chain.invoke({"question": query})

    print(f"Generated MongoDB Query: {generated_query}")
    
    # Update the state
    state["generated_query"] = generated_query.strip() # Added strip()
    return state

# --- MeiliSearch Agent ---

def generate_meilisearch_query(state: GraphState) -> GraphState:
    """
    Generates a search string for MeiliSearch based on the user's question.
    """
    print("---GENERATING MEILISEARCH QUERY---")
    query = state["query"]
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert at formulating search queries for a MeiliSearch index containing support tickets.
        Based on the user's question, extract the most relevant keywords or phrases to search for.
        The support tickets have fields like 'ticket_id', 'description', 'raised_by', and 'status'.
        Focus on terms from the 'description' or 'raised_by' fields.

        User Question: "{question}"

        Few-shot Examples:
        - User Question: Find support tickets related to MySQL issues raised by Sayali Shivpuje.
        - MeiliSearch Query String: MySQL Sayali Shivpuje

        - User Question: Retrieve all open tickets related to Neo4j.
        - MeiliSearch Query String: open Neo4j

        - User Question: What tickets has Aniruddha Salve raised about Neo4j and are open?
        - MeiliSearch Query String: Aniruddha Salve Neo4j open

        - User Question: Search for login problems.
        - MeiliSearch Query String: login problem

        Your Task:
        Provide only the MeiliSearch search query string and nothing else.

        MeiliSearch Query String:
        """
    )
    
    query_gen_chain = prompt | llm | StringOutputParser()
    generated_query_string = query_gen_chain.invoke({"question": query})

    print(f"Generated MeiliSearch Query String: {generated_query_string}")
    
    state["generated_query"] = generated_query_string.strip()
    return state
    
# --- Query Generation Node ---

def generate_query(state: GraphState) -> GraphState:
    """
    A central node that decides which query generator (specialized agent) to call:
    SQLite, MongoDB, or MeiliSearch.
    """
    data_source = state.get("data_source") 
    
    print(f"---DECIDING WHICH AGENT TO CALL FOR: {data_source}---")

    if data_source == "sqlite":
        return generate_sqlite_query(state)
    elif data_source == "mongodb":
        return generate_mongodb_query(state)
    elif data_source == "meilisearch":
        return generate_meilisearch_query(state)
    else:
        print(f"No specific query generator for data_source: {data_source}")
        state["generated_query"] = "" 
        return state