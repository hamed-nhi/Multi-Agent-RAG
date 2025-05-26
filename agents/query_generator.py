# agents/query_generator.py
from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers.string import StringOutputParser
# from langchain_core.output_parsers import StringOutputParser
from langchain_core.output_parsers import StrOutputParser as StringOutputParser
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
    
    # Get the database schema
    schema = get_schema_sqlite.invoke({}) # We call the tool directly
    
    # Prompt engineering with few-shot examples
    prompt = ChatPromptTemplate.from_template(
         """
        You are a SQLite expert. Based on the database schema and the user's question,
        generate a syntactically correct SQLite query.

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
    
    # Create the generation chain
    query_gen_chain = prompt | llm | StringOutputParser()
    
    # Generate the query
    generated_query = query_gen_chain.invoke({"schema": schema, "question": query})
    
    print(f"Generated SQLite Query: {generated_query}")
    
    # Update the state
    state["generated_query"] = generated_query
    return state

# --- MongoDB Agent ---

def generate_mongodb_query(state: GraphState) -> GraphState:
    """
    Generates a MongoDB query dictionary based on the user's question.
    """
    print("---GENERATING MONGODB QUERY---")
    query = state["query"]
    
    # Prompt engineering with updated schema description, case-insensitive, and partial match examples

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
    # توجه کنید که من پارسر را هم به حالت اول برگرداندم چون در کد شما اینطور بود
    # اگر با StrOutputParser کار نمی‌کند، آن را به StringOutputParser تغییر دهید
    from langchain_core.output_parsers import StrOutputParser as StringOutputParser
    query_gen_chain = prompt | llm | StringOutputParser()
    
    # Generate the query
    generated_query = query_gen_chain.invoke({"question": query})

    print(f"Generated MongoDB Query: {generated_query}")
    
    # Update the state
    state["generated_query"] = generated_query
    return state

# --- Query Generation Node ---

def generate_query(state: GraphState) -> GraphState:
    """

    A central node that decides which query generator (specialized agent) to call.
    """
    data_source = state["data_source"]
    
    if data_source == "sqlite":
        return generate_sqlite_query(state)
    elif data_source == "mongodb":
        return generate_mongodb_query(state)
    else:
        # If no specific data source, just pass the state through
        return state