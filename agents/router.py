# agents/router.py
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate 
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser as StringOutputParser
from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY

import re 
import json 
import ast 
def route_query(state: GraphState) -> GraphState:
    """
    Routes the user's query to the appropriate data source and returns a new state object.
    """
    print("---ROUTING QUERY---")
    query = state["query"]
    llm = None 
    
    # Prepare a dictionary to hold the updates to the state
    # Start with the existing state so we don't lose other keys
    # We will return a new dictionary based on this
    current_state_snapshot = state.copy() # Make a shallow copy to start

    try:
        llm = ChatTogether(
            model=LLM_MODEL,
            together_api_key=TOGETHER_API_KEY
        )

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

        print("Attempting to invoke LLM for routing... (Waiting for API response)")
        decision_json = router_chain.invoke({"query": query})
        print("LLM response received for routing.")
        
        decision = decision_json.get("data_source", "general")
        print(f"Router decision: {decision}")

        updated_values = {} # Store what needs to be updated

        if decision == "sqlite":
            updated_values["data_source"] = "sqlite"
            updated_values["error"] = None # Clear previous errors if routing is successful
        elif decision == "mongodb":
            updated_values["data_source"] = "mongodb"
            updated_values["error"] = None
        elif decision == "meilisearch":
            updated_values["data_source"] = "meilisearch"
            updated_values["error"] = None
        elif decision == "neo4j": 
            updated_values["data_source"] = "neo4j"
            updated_values["error"] = None
        elif decision == "general": 
            updated_values["data_source"] = "end" 
            updated_values["error"] = "Query is general and not related to specific data sources."
        else: 
            updated_values["data_source"] = "end"
            updated_values["error"] = f"Router made an unexpected decision: {decision}"
        
        # Return a new state dictionary with the updates
        return {**current_state_snapshot, **updated_values}

    except Exception as e:
        error_message_str = str(e).lower()
        custom_error_msg = "" 

        if "connection" in error_message_str or \
           "timeout" in error_message_str or \
           "network" in error_message_str or \
           "service unavailable" in error_message_str or \
           "max retries exceeded with url" in error_message_str:
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
        
        # Return a new state dictionary with error information
        return {
            **current_state_snapshot, 
            "error": custom_error_msg, 
            "data_source": "end"
        }
        
 # agents/router.py


# ... (یک تابع کمکی برای استخراج JSON، مشابه extract_json_query_from_text در query_refiner.py) ...
def extract_json_from_llm_output(text: str) -> Optional[str]:
    """
    Attempts to extract the first valid JSON object string that starts with '{' and ends with '}'
    from a larger text, often ignoring preceding or succeeding text like <think> tags.
    """
    # This regex tries to find a JSON object, possibly surrounded by other text.
    # It looks for the last occurrence of '{' that has a matching '}'
    # This is a common pattern if the JSON is at the end.
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        potential_json_str = match.group(1)
        try:
            json.loads(potential_json_str) # Validate
            return potential_json_str
        except json.JSONDecodeError:
            # Try ast.literal_eval for simple dicts if json.loads is too strict
            try:
                import ast
                ast.literal_eval(potential_json_str)
                return potential_json_str
            except:
                pass # Not a valid dict/json string by ast either
    
    # Fallback: If the above doesn't work, try finding JSON that might not be the last part
    # This is less robust but can catch JSON embedded within text.
    try:
        # Find the first '{' and try to find a matching '}'
        # This is a simplistic approach and might fail for complex nested structures or multiple JSONs
        first_brace = text.find('{')
        if first_brace != -1:
            # Try to find a balanced brace structure
            open_braces = 0
            for i in range(first_brace, len(text)):
                if text[i] == '{':
                    open_braces += 1
                elif text[i] == '}':
                    open_braces -= 1
                    if open_braces == 0:
                        potential_json_str = text[first_brace : i+1]
                        json.loads(potential_json_str) # Validate
                        return potential_json_str
    except:
        pass # If any error occurs, it's not valid JSON

    return None

    