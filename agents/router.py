# # agents/router.py
# from langchain_core.prompts import ChatPromptTemplate
# # from langchain_core.output_parsers.string import StringOutputParser
# # from langchain_core.output_parsers import StringOutputParser
# from langchain_core.output_parsers import StrOutputParser as StringOutputParser

# from langchain_together import ChatTogether

# from graph.state import GraphState
# from config import LLM_MODEL, TOGETHER_API_KEY

# def route_query(state: GraphState) -> GraphState:
#     """
#     Routes the user's query to the appropriate data source.

#     This node analyzes the user query and decides whether to send it to the
#     SQLite agent, the MongoDB agent, or end the process if the query is general.
#     """
#     print("---ROUTING QUERY---")
#     query = state["query"]

#     # Initialize the LLM
#     llm = ChatTogether(
#         model=LLM_MODEL,
#         together_api_key=TOGETHER_API_KEY
#     )

#     # Prompt engineering: Guide the LLM to make a decision
#     prompt = ChatPromptTemplate.from_template(
#         """
#         You are an expert at routing a user's question to the correct data source.
#         Based on the user's query, decide which data source should be used to answer it.

#         Here are the available data sources:
#         1. `sqlite`: Use this for questions about employees, projects, and their status.
#         2. `mongodb`: Use this for questions about research papers, authors, topics, and keywords.

#         The user query is: "{query}"

#         Return only the name of the selected data source, and nothing else.
#         For example, if the query is about projects, return `sqlite`.
#         If the question is about authors of a paper, return `mongodb`.
#         """
#     )

#     # Create the routing chain
#     router_chain = prompt | llm | StringOutputParser()

#     # Get the decision from the LLM
#     decision = router_chain.invoke({"query": query})
    
#     print(f"Router decision: {decision}")

#     # Update the state with the decision
#     if "sqlite" in decision.lower():
#         state["data_source"] = "sqlite"
#     elif "mongodb" in decision.lower():
#         state["data_source"] = "mongodb"
#     else:
#         # If the model is unsure, we can end the process
#         state["data_source"] = "end"
#         state["error"] = "Could not determine the appropriate data source for the query."

#     return state


################# تغییر مدل و ایجاد یکسری مشکلات و تغییر کد ################


# agents/router.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY

def route_query(state: GraphState) -> GraphState:
    """
    Routes the user's query to the appropriate data source using a robust JSON format.
    """
    print("---ROUTING QUERY---")
    query = state["query"]

    # Initialize the LLM
    llm = ChatTogether(
        model=LLM_MODEL,
        together_api_key=TOGETHER_API_KEY
    )

    # A more robust prompt that asks for JSON output
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert routing assistant. Your only task is to classify a user's question into one of the following categories.

        Here are the available data source categories:
        - `sqlite`: For any questions about company employees, their roles, projects they work on, or project statuses.
        - `mongodb`: For any questions about scientific research papers, their authors, publication years, topics, or keywords.
        - `general`: If the question does not fit into the above categories and is a general conversational question.

        Analyze the user's question provided below.
        User Question: "{query}"

        Respond with a single, raw JSON object containing one key, "data_source", and the value should be one of the three categories: "sqlite", "mongodb", or "general".
        Do not provide any explanation, preamble, or any text other than the JSON object itself.

        Example:
        User Question: Who is the project manager?
        JSON Response: {{"data_source": "sqlite"}}
        """
    )

    # The parser now expects a JSON output
    parser = JsonOutputParser()

    # Create the routing chain
    router_chain = prompt | llm | parser

    try:
        # Get the decision from the LLM
        decision_json = router_chain.invoke({"query": query})
        decision = decision_json.get("data_source", "general")
        print(f"Router decision: {decision}")

        # Update the state with the decision
        if decision == "sqlite":
            state["data_source"] = "sqlite"
        elif decision == "mongodb":
            state["data_source"] = "mongodb"
        else:
            state["data_source"] = "end"
            state["error"] = "Query is not related to available data sources."

    except Exception as e:
        print(f"An error occurred during routing: {e}")
        state["data_source"] = "end"
        state["error"] = "Failed to parse the router's decision."


    return state