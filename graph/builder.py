from langgraph.graph import StateGraph, END
from .state import GraphState 
from agents.router import route_query
from agents.query_generator import generate_query
from agents.executor_and_responder import execute_query, generate_response
from agents.query_refiner import suggest_refined_query 

def should_route_or_end(state: GraphState) -> str: # Renamed for clarity
    """
    Conditional edge after router.
    Determines if we should proceed to query generation (if a specific DB is chosen),
    end the graph (if clarification is needed, so UI can take over), or end directly.
    """
    print("---CONDITION: After Router---")
    
    # Handle hard errors from the router itself first
    # The router's error handling already sets data_source to "end" and populates "error"
    if state.get("data_source") == "end" and state.get("error"):
        if "Failed to connect" in state.get("error", "") or \
           "JSON PARSING ERROR" in state.get("error", "") or \
           "UNEXPECTED ERROR" in state.get("error", ""):
            print(f"Router encountered a critical error: {state.get('error')}. Ending graph.")
            return "terminate_graph" # A distinct end path for router critical errors

    data_source = state.get("data_source")

    if data_source in ["sqlite", "mongodb", "meilisearch", "neo4j"]: 
        print(f"Data source '{data_source}' selected by router. Proceeding to query generation.")
        return "to_query_generator" 
    elif data_source == "clarification_needed":
        # If router signals clarification is needed, the graph run should end here.
        # The UI will pick up 'clarification_question_text' from the state.
        print("Router determined clarification is needed. Graph run will end; UI to handle user clarification.")
        return "terminate_for_ui_clarification" # New distinct end path
    else: 
        # This handles cases where router explicitly set data_source to "end" (e.g., for truly unroutable queries not needing clarification)
        # or any other unexpected data_source value.
        print(f"Router output data_source is '{data_source}'. Not routing to a specific agent or clarification. Ending graph.")
        return "terminate_graph" # General end path

def decide_after_execution(state: GraphState) -> str:
    """
    Conditional edge after query_executor.
    Decides whether to refine the query or proceed to response generation.
    Hard errors from executor should lead to response generation to display the error.
    """
    print("---CONDITION: After Query Execution---")
    
    # If a hard error occurred during execution (not just "no results")
    # The execute_query node should set state["error"] appropriately.
    # Let's check for errors that don't indicate "no results" or "refinement already tried"
    current_error = state.get("error")
    is_hard_error = current_error and \
                    "Query and its refinement(s) returned no results." not in current_error and \
                    "Query execution for" not in current_error # This was a generic "no context" error we set

    if is_hard_error:
        print(f"Hard error detected after execution: {current_error}. Proceeding to response generator.")
        return "to_response_generator"

    if state.get("needs_query_refinement", False): 
        print("Query needs refinement. Proceeding to query refiner.")
        return "to_query_refiner"
    else:
        print("Query successful or no further refinement needed/possible. Proceeding to response generation.")
        return "to_response_generator"

# --- Define the graph ---
workflow = StateGraph(GraphState)

# --- Add the nodes ---
workflow.add_node("router", route_query)
workflow.add_node("query_generator", generate_query) 
workflow.add_node("query_executor", execute_query)
workflow.add_node("query_refiner", suggest_refined_query)
workflow.add_node("response_generator", generate_response)
# We do NOT add the 'handle_clarification_needed' node here, as UI will manage that interaction.

# --- Add the edges ---
workflow.set_entry_point("router")

# Conditional edge from the router
workflow.add_conditional_edges(
    "router",
    should_route_or_end, 
    {
        "to_query_generator": "query_generator", 
        "terminate_for_ui_clarification": END, # End the graph; UI handles clarification prompt
        "terminate_graph": END, # General end path for router errors or unroutable queries
    },
)

# Edge from query generator to executor
workflow.add_edge("query_generator", "query_executor")

# Conditional edges from the query executor
workflow.add_conditional_edges(
    "query_executor",
    decide_after_execution, 
    {
        "to_query_refiner": "query_refiner",        
        "to_response_generator": "response_generator" 
    }
)

# Edge from query refiner back to query executor
workflow.add_edge("query_refiner", "query_executor")

# Edge from response generator to the end
workflow.add_edge("response_generator", END)

# --- Compile the graph into a runnable app ---
app = workflow.compile()