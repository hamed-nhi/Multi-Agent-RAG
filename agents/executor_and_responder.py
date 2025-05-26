# agents/executor_and_responder.py
from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers.string import StringOutputParser
# from langchain_core.output_parsers import StringOutputParser
from langchain_core.output_parsers import StrOutputParser as StringOutputParser

from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY
from tools.db_tools import run_sqlite_query, run_mongodb_query

# --- Initialize the LLM ---
llm = ChatTogether(
    model=LLM_MODEL,
    together_api_key=TOGETHER_API_KEY
)

# --- Query Execution Node ---

def execute_query(state: GraphState) -> GraphState:
    """
    Executes the generated query on the appropriate database and retrieves the context.
    """
    print("---EXECUTING QUERY---")
    query = state["generated_query"]
    data_source = state["data_source"]
    
    context = ""
    if data_source == 'sqlite':
        context = run_sqlite_query.invoke(query)
    elif data_source == 'mongodb':
        context = run_mongodb_query.invoke(query)
    
    print(f"Retrieved Context: {context}")
    
    # Update the state with the retrieved data
    state["context"] = context
    return state

# # --- Response Generation Node ---

# def generate_response(state: GraphState) -> GraphState:
#     """
#     Generates a natural language response to the user based on the retrieved context.
#     """
#     print("---GENERATING RESPONSE---")
#     user_query = state["query"]
#     context = state["context"]

#     # Prompt engineering to synthesize a final answer
#     prompt = ChatPromptTemplate.from_template(
#         """
#         You are a helpful AI assistant. You need to answer the user's original question based on the provided data context.
#         Keep your answer concise and directly address the question.

#         **Original Question:**
#         {question}

#         **Data Context from Database:**
#         {context}

#         If the context is empty or contains an error, inform the user that you couldn't find the requested information.
        
#         **Your Answer:**
#         """
#     )

#     # Create the response generation chain
#     response_chain = prompt | llm | StringOutputParser()
    
#     # Generate the final response
#     response = response_chain.invoke({"question": user_query, "context": context})
    
#     print(f"Final Response: {response}")
    
#     # Update the state
#     state["response"] = response
#     return state



# # agents/executor_and_responder.py

# # ... (کدهای دیگر فایل) ...

def generate_response(state: GraphState) -> GraphState:
    """
    Generates a natural language response to the user based on the retrieved context.
    """
    print("---GENERATING RESPONSE---")
    user_query = state["query"]
    context = state["context"]

    # --- NEW, IMPROVED PROMPT ---
    prompt = ChatPromptTemplate.from_template(
     """
        You are a helpful AI assistant. Your task is to answer the user's original question based on the data context provided below.
        The context is the direct output from a database query. It might be a list of tuples, a list of dictionaries, or an empty list.

        **Original Question:**
        {question}

        **Data Context from Database:**
        {context}

        - If the context contains data, formulate a clear and direct answer from it.
        - If the context is empty (like `[]` or `[()]` or `None`) or explicitly states that no documents were found, or contains an error message, politely inform the user that the requested information could not be found in the database. Do NOT provide any examples, hypothetical scenarios, or additional information beyond stating that the data was not found.
        
        **Your Answer:**
        """
    )

    # ... (بقیه کدهای تابع بدون تغییر) ...
    response_chain = prompt | llm | StringOutputParser()
    response = response_chain.invoke({"question": user_query, "context": context})
    print(f"Final Response: {response}")
    state["response"] = response
    return state