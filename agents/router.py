# agents/router.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY

# import requests # This import is not currently used, can be removed if not needed later

def route_query(state: GraphState) -> GraphState:
    """
    Routes the user's query to the appropriate data source: SQLite, MongoDB, MeiliSearch, or Neo4j.
    Includes improved error handling for API connection issues.
    """
    print("---ROUTING QUERY---")
    query = state["query"]
    llm = None # Initialize llm
    
    try:
        # Initialize the LLM
        llm = ChatTogether(
            model=LLM_MODEL,
            together_api_key=TOGETHER_API_KEY
        )

        # Updated prompt to include more specific details for Neo4j
        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert routing assistant. Your only task is to classify a user's question into one of the following categories.

            Here are the available data source categories:
            - `sqlite`: For any questions about company employees, their roles, departments, projects they work on, or project statuses.
            - `mongodb`: For any questions about scientific research papers, their authors, publication years, topics, or keywords.
            - `meilisearch`: For searching and finding information within support tickets, such as ticket descriptions, who raised them, or their current status.
            - `neo4j`: For questions about relationships between researchers, their collaborations, their research fields, or the projects/topics they work on (e.g., "Who collaborates with X?", "What is the research field of Y?", "What projects does Z work on?").
            - `general`: If the question does not fit into any of the above categories and is a general conversational question.

            Analyze the user's question provided below.
            User Question: "{query}"

            Respond with a single, raw JSON object containing one key, "data_source", and the value should be one of the five categories: "sqlite", "mongodb", "meilisearch", "neo4j", or "general".
            Do not provide any explanation, preamble, or any text other than the JSON object itself.

            Example for sqlite:
            User Question: Who is the project manager?
            JSON Response: {{"data_source": "sqlite"}}
            
            Example for mongodb:
            User Question: What papers were published in 2024 about AI?
            JSON Response: {{"data_source": "mongodb"}}

            Example for meilisearch:
            User Question: Find tickets related to MySQL issues.
            JSON Response: {{"data_source": "meilisearch"}}
            
            Example for neo4j (collaboration):
            User Question: Who are the collaborators of Aniruddha Salve?
            JSON Response: {{"data_source": "neo4j"}}

            Example for neo4j (research field):
            User Question: What is the research field of Patrick Lewis?
            JSON Response: {{"data_source": "neo4j"}}
            """
        )

        parser = JsonOutputParser()
        router_chain = prompt | llm | parser

        # Get the decision from the LLM
        print("Attempting to invoke LLM for routing...")
        decision_json = router_chain.invoke({"query": query})
        decision = decision_json.get("data_source", "general")
        print(f"Router decision: {decision}")

        # Updated logic to include neo4j
        if decision == "sqlite":
            state["data_source"] = "sqlite"
        elif decision == "mongodb":
            state["data_source"] = "mongodb"
        elif decision == "meilisearch":
            state["data_source"] = "meilisearch"
        elif decision == "neo4j": # New condition for Neo4j
            state["data_source"] = "neo4j"
        elif decision == "general":
            state["data_source"] = "end"
            state["error"] = "Query is general and not related to specific data sources."
        else:
            state["data_source"] = "end"
            state["error"] = f"Router made an unexpected decision: {decision}"

    # Error handling block remains the same
    except Exception as e:
        error_message_str = str(e).lower()
        custom_error_msg = "" 

        if "connection" in error_message_str or \
           "timeout" in error_message_str or \
           "network" in error_message_str or \
           "service unavailable" in error_message_str or \
           "Max retries exceeded with url" in error_message_str:
            custom_error_msg = (
                "Failed to connect to the LLM service (Together AI). "
                "Please check your internet connection and API key validity. "
                f"Details: {e}"
            )
            print(f"CONNECTION ERROR during routing: {custom_error_msg}")
        elif "invalid json output" in error_message_str: 
            problematic_output = error_message_str.split('invalid json output:')[-1].strip()
            custom_error_msg = (
                f"LLM output was not valid JSON. LLM Output: '{problematic_output}'. "
                f"Details: {e}"
            )
            print(f"JSON PARSING ERROR during routing: {custom_error_msg}")
        else: 
            custom_error_msg = (
                "An unexpected error occurred during the routing phase. "
                f"Details: {e}"
            )
            print(f"UNEXPECTED ERROR during routing: {custom_error_msg}")
        
        state["error"] = custom_error_msg
        state["data_source"] = "end" 

    return state