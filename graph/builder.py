# graph/builder.py
from langgraph.graph import StateGraph, END
from .state import GraphState

# Import all our node functions
from agents.router import route_query
from agents.query_generator import generate_query
from agents.executor_and_responder import execute_query, generate_response

def should_continue(state: GraphState) -> str:
    """
    Conditional edge logic.
    
    Determines the next step based on the router's decision.
    If the router chose a data source, we proceed to query generation.
    Otherwise, we end the process.
    """
    if state.get("error") or state["data_source"] == "end":
        return "end"
    else:
        return "continue"

# --- Define the graph ---
workflow = StateGraph(GraphState)

# --- Add the nodes ---
# The names of the nodes should be descriptive
workflow.add_node("router", route_query)
workflow.add_node("query_generator", generate_query)
workflow.add_node("query_executor", execute_query)
workflow.add_node("response_generator", generate_response)

# --- Add the edges ---
# 1. Set the entry point
workflow.set_entry_point("router")

# 2. Add the conditional edge from the router
workflow.add_conditional_edges(
    "router",
    should_continue,
    {
        "continue": "query_generator",
        "end": END,
    },
)

# 3. Add the standard edges for the main workflow
workflow.add_edge("query_generator", "query_executor")
workflow.add_edge("query_executor", "response_generator")
workflow.add_edge("response_generator", END)


# --- Compile the graph into a runnable app ---
app = workflow.compile()

# To visualize the graph, you can uncomment the following lines
# and ensure you have `pip install Pillow`
# from IPython.display import Image, display
# try:
#     img_data = app.get_graph(xray=True).draw_mermaid_png()
#     with open("graph.png", "wb") as f:
#         f.write(img_data)
#     print("Graph visualization saved to graph.png")
# except Exception as e:
#     print(f"Could not generate graph visualization: {e}")