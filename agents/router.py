# agents/router.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser # We are using JSON output
from langchain_together import ChatTogether
from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY

import requests


def route_query(state: GraphState) -> GraphState:
    """
    Routes the user's query to the appropriate data source: SQLite, MongoDB, or MeiliSearch.
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
            # We can add a timeout here if the library supports it,
            # e.g., client_kwargs={"timeout": 10} if using requests directly
        )

        prompt = ChatPromptTemplate.from_template(
            """
            You are an expert routing assistant. Your only task is to classify a user's question into one of the following categories.

            Here are the available data source categories:
            - `sqlite`: For any questions about company employees, their roles, departments, projects they work on, or project statuses.
            - `mongodb`: For any questions about scientific research papers, their authors, publication years, topics, or keywords.
            - `meilisearch`: For searching and finding information within support tickets, such as ticket descriptions, who raised them, or their current status.
            - `general`: If the question does not fit into any of the above categories and is a general conversational question.

            Analyze the user's question provided below.
            User Question: "{query}"

            Respond with a single, raw JSON object containing one key, "data_source", and the value should be one of the four categories: "sqlite", "mongodb", "meilisearch", or "general".
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
            """
        )

        parser = JsonOutputParser()
        router_chain = prompt | llm | parser

        # Get the decision from the LLM
        print("Attempting to invoke LLM for routing...")
        decision_json = router_chain.invoke({"query": query})
        decision = decision_json.get("data_source", "general")
        print(f"Router decision: {decision}")

        if decision == "sqlite":
            state["data_source"] = "sqlite"
        elif decision == "mongodb":
            state["data_source"] = "mongodb"
        elif decision == "meilisearch":
            state["data_source"] = "meilisearch"
        elif decision == "general":
            state["data_source"] = "end"
            state["error"] = "Query is general and not related to specific data sources."
        else:
            state["data_source"] = "end"
            state["error"] = f"Router made an unexpected decision: {decision}"

    # Attempt to catch more specific connection-related errors if possible.
    # The exact exception type might depend on the underlying HTTP library used by ChatTogether.
    # We'll start with a general check in the message.
    except Exception as e:
        error_message_str = str(e).lower()
        custom_error_msg = "" # Initialize custom_error_msg

        # Check for common connection error indicators in the error message
        if "connection" in error_message_str or \
           "timeout" in error_message_str or \
           "network" in error_message_str or \
           "service unavailable" in error_message_str or \
           "Max retries exceeded with url" in error_message_str: # Added another common indicator
            custom_error_msg = (
                "Failed to connect to the LLM service (Together AI). "
                "Please check your internet connection and API key validity. "
                f"Details: {e}"
            )
            print(f"CONNECTION ERROR during routing: {custom_error_msg}")
        elif "invalid json output" in error_message_str: # Handling JSON parsing error specifically
            # Extract the problematic output if possible for better debugging
            problematic_output = error_message_str.split('invalid json output:')[-1].strip()
            custom_error_msg = (
                f"LLM output was not valid JSON. LLM Output: '{problematic_output}'. "
                f"Details: {e}"
            )
            print(f"JSON PARSING ERROR during routing: {custom_error_msg}")
        else: # For other types of errors during routing
            custom_error_msg = (
                "An unexpected error occurred during the routing phase. "
                f"Details: {e}"
            )
            print(f"UNEXPECTED ERROR during routing: {custom_error_msg}")
        
        state["error"] = custom_error_msg
        state["data_source"] = "end" # Ensure workflow terminates correctly on error

    return state




# def route_query(state: GraphState) -> GraphState:
    """
    Routes the user's query to the appropriate data source: SQLite, MongoDB, or MeiliSearch.
    """
    print("---ROUTING QUERY---")
    query = state["query"]

    # Initialize the LLM
    llm = ChatTogether(
        model=LLM_MODEL,
        together_api_key=TOGETHER_API_KEY
    )

    # Updated prompt to include MeiliSearch and its specific use case
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert routing assistant. Your only task is to classify a user's question into one of the following categories.

        Here are the available data source categories:
        - `sqlite`: For any questions about company employees, their roles, departments, projects they work on, or project statuses.
        - `mongodb`: For any questions about scientific research papers, their authors, publication years, topics, or keywords.
        - `meilisearch`: For searching and finding information within support tickets, such as ticket descriptions, who raised them, or their current status.
        - `general`: If the question does not fit into any of the above categories and is a general conversational question.

        Analyze the user's question provided below.
        User Question: "{query}"

        Respond with a single, raw JSON object containing one key, "data_source", and the value should be one of the four categories: "sqlite", "mongodb", "meilisearch", or "general".
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
        """
    )

    # The parser expects a JSON output
    parser = JsonOutputParser()

    # Create the routing chain
    router_chain = prompt | llm | parser

    try:
        # Get the decision from the LLM
        decision_json = router_chain.invoke({"query": query})
        decision = decision_json.get("data_source", "general") # Default to 'general' if key is missing
        print(f"Router decision: {decision}")

        # Update the state with the decision, now including meilisearch
        if decision == "sqlite":
            state["data_source"] = "sqlite"
        elif decision == "mongodb":
            state["data_source"] = "mongodb"
        elif decision == "meilisearch": # New condition for MeiliSearch
            state["data_source"] = "meilisearch"
        elif decision == "general": # Explicitly handle 'general' to go to 'end'
            state["data_source"] = "end"
            state["error"] = "Query is general and not related to specific data sources."
            # Or you might want a different handling for general queries later
        else: # Catch any other unexpected decision
            state["data_source"] = "end"
            state["error"] = f"Router made an unexpected decision: {decision}"

    except Exception as e:
        print(f"An error occurred during routing: {e}")
        state["data_source"] = "end"
        state["error"] = "Failed to parse the router's decision or an unexpected error occurred."

    return state