# graph/builder.py
from langgraph.graph import StateGraph, END
from .state import GraphState
from agents.router import route_query
from agents.query_generator import generate_query
from agents.executor_and_responder import execute_query, generate_response
from tools.db_tools import run_sqlite_query, run_mongodb_query, run_meilisearch_query, run_neo4j_query

def should_continue(state: GraphState) -> str:
    """
    Conditional edge logic.
    
    Determines the next step based on the router's decision.
    If the router chose a data source (sqlite, mongodb, meilisearch, or neo4j), 
    we proceed to query generation. Otherwise, we end the process.
    """
    if state.get("error"): # If there was an error in routing
        return "end"
    
    data_source = state.get("data_source")
    if data_source in ["sqlite", "mongodb", "meilisearch", "neo4j"]:
        return "continue_to_query_generation" 
    else: # This would include "end" from router or any unexpected values
        return "end"

# --- Define the graph ---
workflow = StateGraph(GraphState)

# --- Add the nodes ---
workflow.add_node("router", route_query)
workflow.add_node("query_generator", generate_query)
workflow.add_node("query_executor", execute_query)
workflow.add_node("response_generator", generate_response)

# --- Add the edges ---
workflow.set_entry_point("router")

# Updated conditional edge from the router
workflow.add_conditional_edges(
    "router",
    should_continue,
    {
        "continue_to_query_generation": "query_generator", 
        "end": END,
    },
)

workflow.add_edge("query_generator", "query_executor")
workflow.add_edge("query_executor", "response_generator")
workflow.add_edge("response_generator", END)


# --- Compile the graph into a runnable app ---
app = workflow.compile()









# def should_continue(state: GraphState) -> str:
#     """
#     Conditional edge logic.
    
#     Determines the next step based on the router's decision.
#     If the router chose a data source (sqlite, mongodb, meilisearch), 
#     we proceed to query generation. Otherwise, we end the process.
#     """
#     if state.get("error"): # If there was an error in routing
#         return "end"
    
#     data_source = state.get("data_source")
#     if data_source in ["sqlite", "mongodb", "meilisearch"]: # Added "meilisearch"
#         return "continue_to_query_generation" # Changed the target name for clarity
#     else: # This would include "end" from router or any unexpected values
#         return "end"

# # --- Define the graph ---
# workflow = StateGraph(GraphState)

# # --- Add the nodes ---
# workflow.add_node("router", route_query)
# workflow.add_node("query_generator", generate_query)
# workflow.add_node("query_executor", execute_query)
# workflow.add_node("response_generator", generate_response)

# # --- Add the edges ---
# workflow.set_entry_point("router")

# # Updated conditional edge from the router
# workflow.add_conditional_edges(
#     "router",
#     should_continue,
#     {
#         "continue_to_query_generation": "query_generator", # Updated target name
#         "end": END,
#     },
# )

# workflow.add_edge("query_generator", "query_executor")
# workflow.add_edge("query_executor", "response_generator")
# workflow.add_edge("response_generator", END)


# # --- Compile the graph into a runnable app ---
# app = workflow.compile()
