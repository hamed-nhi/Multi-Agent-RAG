# agents/executor_and_responder.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser as StringOutputParser
from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY
from tools.db_tools import run_sqlite_query, run_mongodb_query, run_meilisearch_query, run_neo4j_query

# --- Initialize the LLM ---
llm = ChatTogether(
    model=LLM_MODEL,
    together_api_key=TOGETHER_API_KEY
)

# --- Query Execution Node ---
def execute_query(state: GraphState) -> GraphState:
    """
    Executes the generated query and sets flags for refinement if results are not satisfactory.
    """
    print("---EXECUTING QUERY---")
    generated_q = state.get("generated_query")
    data_source = state.get("data_source")
    
    # NEW: Initialize or retrieve refinement-related state variables
    # The original user query is passed along if not already set
    state["original_user_query"] = state.get("original_user_query") or state.get("query")
    # The first generated query (before any refinement attempts)
    state["initial_generated_query"] = state.get("initial_generated_query") or generated_q
    
    current_context = "" 
    current_error = state.get("error") # Preserve error from previous steps if any
    needs_refinement_flag = False # MODIFIED: Default to False

    # Increment attempt count if it exists, otherwise initialize to 1
    attempt_num = state.get("refinement_attempt_count", 0) + 1 # MODIFIED: Start from 0, so first try is 1
    state["refinement_attempt_count"] = attempt_num
    
    print(f"Query execution attempt: {attempt_num}")
    print(f"Query for {data_source}: {generated_q}")

    if not generated_q and data_source not in ["end", "general"]:
        err_msg = f"No query was generated for data source: {data_source}."
        print(err_msg)
        state["error"] = current_error or err_msg 
    elif data_source == 'sqlite':
        current_context = run_sqlite_query.invoke(generated_q)
    elif data_source == 'mongodb':
        current_context = run_mongodb_query.invoke(generated_q)
    elif data_source == 'meilisearch': 
        current_context = run_meilisearch_query.invoke(generated_q)
    elif data_source == 'neo4j': 
        current_context = run_neo4j_query.invoke(generated_q)
    elif data_source in ["end", "general"]:
        print(f"Execution skipped as data_source is '{data_source}'. Prior error (if any): {current_error}")
    else:
        err_msg = f"Unknown data_source type for query execution: {data_source}"
        print(err_msg)
        state["error"] = current_error or err_msg

    print(f"Raw context from tool: '{current_context}', type: {type(current_context)}")

    is_empty_or_no_results = False
    # Check if context indicates an error or "not found" from the tool itself
    if isinstance(current_context, str) and \
       ("An error occurred" in current_context or \
        "Failed to parse" in current_context or \
        "Connection Error" in current_context):
        # This is a hard error from the tool, not just empty results
        print(f"Tool execution resulted in an error: {current_context}")
        state["error"] = current_error or current_context # Prioritize existing error
        state["context"] = f"Error during query execution: {current_context}"
        needs_refinement_flag = False # Do not refine on hard execution errors
    elif isinstance(current_context, str) and \
         (current_context.strip() == "[]" or \
          "No documents found" in current_context or \
          "No records found" in current_context):
        print("Query returned no results or an empty list string.")
        is_empty_or_no_results = True
    elif isinstance(current_context, list) and not current_context: # Actual empty list
        print("Query returned an actual empty list.")
        is_empty_or_no_results = True
    
    # MODIFIED: Logic for setting refinement flag
    # Allow only one refinement attempt for now (attempt_num == 1 means this is the first try)
    MAX_REFINEMENT_ATTEMPTS = 1 # Allow 1 refinement, so total 2 attempts (initial + 1 refined)
    if is_empty_or_no_results and attempt_num <= MAX_REFINEMENT_ATTEMPTS:
        print(f"Query for {data_source} yielded no results. Flagging for refinement (attempt {attempt_num}).")
        needs_refinement_flag = True
        state["last_failed_query"] = generated_q # Store the query that just failed
        state["context"] = "[]" # Set context to empty list for now
        # Error from previous steps is preserved or cleared if we are attempting refinement
        state["error"] = None if needs_refinement_flag else current_error
    elif is_empty_or_no_results and attempt_num > MAX_REFINEMENT_ATTEMPTS:
        print("Max refinement attempts reached. Proceeding with empty/no results.")
        state["context"] = "[]"
        state["error"] = current_error or "Query and its refinement(s) returned no results."
    elif state.get("error"): # If a hard error was already set (and not cleared for refinement)
        state["context"] = state.get("context") or f"Error during query execution: {state.get('error')}"
    else: # Successful execution with data
        state["context"] = current_context
        state["error"] = None # Clear any previous soft errors if we have good context now
        
    state["needs_query_refinement"] = needs_refinement_flag

    print(f"Final context for this step: {state.get('context')}")
    print(f"Needs query refinement: {state.get('needs_query_refinement')}")
    if state.get("error"):
        print(f"Error state after execution: {state['error']}")
    
    return state

# ... (generate_response function remains the same for now) ...
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