# agents/executor_and_responder.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser as StringOutputParser # Assuming this alias is what you are using
from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY
# Import all necessary tools, including the new MeiliSearch tool
from tools.db_tools import run_sqlite_query, run_mongodb_query, run_meilisearch_query

# --- Initialize the LLM ---
llm = ChatTogether(
    model=LLM_MODEL,
    together_api_key=TOGETHER_API_KEY
)

# --- Query Execution Node ---
def execute_query(state: GraphState) -> GraphState:
    """
    Executes the generated query on the appropriate database (SQLite, MongoDB, or MeiliSearch)
    and retrieves the context.
    """
    print("---EXECUTING QUERY---")
    generated_q = state.get("generated_query")
    data_source = state.get("data_source")
    
    context = "" # Initialize context
    error_message = state.get("error") # Preserve error from router if any

    if not generated_q and data_source not in ["end", "general"]:
        # If no query was generated but we expected one from a specific data source agent
        current_error = f"No query was generated for data source: {data_source}."
        print(current_error)
        state["error"] = error_message or current_error # Prioritize router error
    elif data_source == 'sqlite':
        context = run_sqlite_query.invoke(generated_q)
    elif data_source == 'mongodb':
        context = run_mongodb_query.invoke(generated_q)
    elif data_source == 'meilisearch': # Condition for MeiliSearch
        # The run_meilisearch_query tool expects the search string directly
        context = run_meilisearch_query.invoke(generated_q)
    elif data_source in ["end", "general"]:
        # If router decided to end, or an error occurred before query generation,
        # or it's a general query for which we don't have an executor
        print(f"Execution skipped as data_source is '{data_source}'. Router error (if any): {error_message}")
        # Context remains empty, error (if any) is preserved from router or previous steps
    else:
        current_error = f"Unknown data_source type for query execution: {data_source}"
        print(current_error)
        state["error"] = error_message or current_error

    # --- ADD THIS PRINT STATEMENT FOR DEBUGGING ---
    print(f"Raw context from tool (before type check): '{context}', type: {type(context)}")

    # Check if the context indicates an error from the tool itself or "not found"
    if isinstance(context, str) and ("An error occurred" in context or "Failed to parse" in context or "No documents found" in context):
        tool_message = context # The message from the tool
        print(f"Tool execution resulted in message: {tool_message}")
        
        if "No documents found" in tool_message:
            state["context"] = "[]" # Standardize empty results for the responder
            # Optionally, set a soft error or info message if 'no documents' isn't a hard error
            # For now, we let the responder handle "[]" as "couldn't find info"
        else: # It's a more serious error from the tool
            state["context"] = f"Error during query execution: {tool_message}"
            state["error"] = error_message or tool_message # Prioritize existing error, then tool's error
    elif context is not None : # If context is not one of the string error messages, and not None
        state["context"] = context
    else: # If context is None (e.g. if a tool invoke returned None unexpectedly)
        state["context"] = "[]" # Treat as empty result
        if data_source not in ["end", "general"] and not state.get("error"): # Only set error if not already an end state
             state["error"] = state.get("error") or f"Query execution for {data_source} returned no context."


    print(f"Final context being set to state: {state.get('context')}")
    if state.get("error"):
        print(f"Error state after execution: {state['error']}")
    
    return state

# --- Response Generation Node ---
def generate_response(state: GraphState) -> GraphState:
    """
    Generates a natural language response to the user based on the retrieved context.
    """
    print("---GENERATING RESPONSE---")
    user_query = state["query"]
    # Use state.get("context") in case 'context' was never set (though execute_query should always set it)
    context_from_db = state.get("context", "[]") # Default to empty list string if not found

    # If an error occurred in a previous step, reflect that in the response
    error_message = state.get("error")
    if error_message and "Query is general" not in error_message : # Don't make general query errors too verbose
        # If a significant error happened, we inform the user about that instead of trying to answer
        # based on potentially empty or error-laden context.
        final_response_text = f"I encountered an issue trying to process your request. Error: {error_message}"
        print(f"Error flagged, generating error response: {final_response_text}")
        state["response"] = final_response_text
        return state

    prompt = ChatPromptTemplate.from_template(
        """
        You are a helpful AI assistant. Your task is to answer the user's original question based on the data context provided below.
        The context is the direct output from a database query. It might be a list of tuples, a list of dictionaries, an empty list string like '[]', or a string indicating an error or "No documents found".

        **Original Question:**
        {question}

        **Data Context from Database:**
        {context}

        **Instructions for your response:**
        - If the context contains data (i.e., it's not an empty list string like '[]' and not a 'No documents found' message or an error message):
            - Formulate a clear and direct answer from this data.
            - If the context is a list of items (e.g., multiple tickets, multiple papers), try to present each item clearly, perhaps as a bullet point, highlighting key information from each item.
        - If the context is an empty list string '[]', or explicitly states "No documents found", or indicates an error during query execution:
            - Politely inform the user that the requested information could not be found in the database.
            - Do NOT provide any examples, hypothetical scenarios, or additional information beyond stating that the data was not found or an error occurred.
        - If the original question was very general and the context is empty or indicates 'general query' (and no other specific data source error occurred):
            - You can say: "I can only answer questions about employees, projects, research papers, or support tickets. How can I help you with those?"
        
        **Your Answer:**
        """
    )

    response_chain = prompt | llm | StringOutputParser()
    response = response_chain.invoke({"question": user_query, "context": context_from_db})
    
    print(f"Final Response: {response}")
    state["response"] = response
    return state