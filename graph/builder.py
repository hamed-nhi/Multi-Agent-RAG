# graph/builder.py
from langgraph.graph import StateGraph, END
from .state import GraphState 

from agents.router import route_query
from agents.query_generator import generate_query
from agents.executor_and_responder import execute_query, generate_response
from agents.query_refiner import suggest_refined_query # Ensure this is uncommented

def should_generate_query(state: GraphState) -> str:
    print("---CONDITION: After Router---")
    if state.get("error"): 
        print(f"Router error: {state.get('error')}. Ending.")
        return "end"
    data_source = state.get("data_source")
    if data_source in ["sqlite", "mongodb", "meilisearch", "neo4j"]: 
        print(f"Data source '{data_source}' selected. Proceeding to query generation.")
        return "continue_to_query_generation" 
    else: 
        print(f"Data source is '{data_source}'. Not a queryable source or router decided to end. Ending.")
        return "end"

# Using the full conditional logic function
def decide_after_execution(state: GraphState) -> str:
    print("---CONDITION: After Query Execution---")
    if state.get("error") and \
       "Query and its refinement(s) returned no results." not in state.get("error", "") and \
       "Query execution for" not in state.get("error","") and \
       "connection" not in state.get("error","").lower() and \
       "unauthorized" not in state.get("error","").lower() : 
        print(f"Hard error detected after execution: {state.get('error')}. Proceeding to response generator.")
        return "proceed_to_response"

    if state.get("needs_query_refinement", False): 
        print("Query needs refinement. Proceeding to query refiner.")
        return "refine_query"
    else:
        print("Query successful or no further refinement needed/possible. Proceeding to response generation.")
        return "proceed_to_response"

workflow = StateGraph(GraphState)

workflow.add_node("router", route_query)
workflow.add_node("query_generator", generate_query)
workflow.add_node("query_executor", execute_query)
workflow.add_node("query_refiner", suggest_refined_query) # Ensure this is uncommented
workflow.add_node("response_generator", generate_response)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    should_generate_query,
    {
        "continue_to_query_generation": "query_generator", 
        "end": END,
    },
)
workflow.add_edge("query_generator", "query_executor")

# Using the full conditional edge logic
workflow.add_conditional_edges(
    "query_executor",
    decide_after_execution, 
    {
        "refine_query": "query_refiner",
        "proceed_to_response": "response_generator"
    }
)
workflow.add_edge("query_refiner", "query_executor") # Ensure this is uncommented
workflow.add_edge("response_generator", END)

app = workflow.compile()