from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser as StringOutputParser 
from langchain_together import ChatTogether

from graph.state import GraphState 
from config import LLM_MODEL, TOGETHER_API_KEY

import re 
import json 
import ast  

def extract_json_from_llm_output(text: str) -> Optional[str]:
    """
    Attempts to extract the last valid JSON object string from a larger text.
    It looks for a string that starts with { and ends with }, capturing the content.
    It prioritizes JSON within markdown-like code blocks if present.
    """
    # Try to find JSON enclosed in ```json ... ```
    match_markdown = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match_markdown:
        potential_json_str = match_markdown.group(1)
        try:
            json.loads(potential_json_str)
            print(f"Extracted JSON from markdown block: {potential_json_str}")
            return potential_json_str
        except json.JSONDecodeError:
            print(f"Markdown JSON block found but invalid: {potential_json_str}")
            # Fall through to other methods if markdown JSON is invalid

    # Try to find the last occurrence of a JSON-like structure
    matches = list(re.finditer(r"(\{.*?\})", text, re.DOTALL)) # Use non-greedy .*?
    if matches:
        potential_json_str = matches[-1].group(1) # Get the last match
        try:
            json.loads(potential_json_str)
            print(f"Extracted JSON (last match via regex): {potential_json_str}")
            return potential_json_str
        except json.JSONDecodeError:
            try:
                evaluated = ast.literal_eval(potential_json_str)
                if isinstance(evaluated, dict): # Ensure it's a dictionary
                    print(f"Extracted dict via ast.literal_eval (last match): {potential_json_str}")
                    return potential_json_str 
            except (SyntaxError, ValueError):
                print(f"Could not parse as JSON or dict via ast (last match): {potential_json_str}")
    
    # Fallback: Simplistic first '{' to last '}' if other methods fail (less reliable)
    try:
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            potential_json_str = text[first_brace : last_brace+1]
            json.loads(potential_json_str) # Validate
            print(f"Extracted JSON (fallback first_brace to last_brace): {potential_json_str}")
            return potential_json_str
    except (json.JSONDecodeError, ValueError, SyntaxError):
        print(f"Fallback JSON extraction failed for text: {text[:200]}...")

    print(f"Could not extract valid JSON from LLM output: {text[:200]}...")
    return None


def route_query(state: GraphState) -> GraphState:
    """
    Routes the user's query to an appropriate data source, triggers clarification if needed,
    and returns a new state object.
    """
    print("---ROUTING QUERY---")
    current_query_for_routing = state["query"] # The query to be routed
    llm = None 
    
    current_state_snapshot = state.copy() 
    # Reset clarification fields for this routing attempt
    current_state_snapshot["clarification_question_needed"] = False
    current_state_snapshot["clarification_question_text"] = None
    # user_clarification_response is handled by the clarification node

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
            - `general`: If the question does not fit into any of the above categories, is a general conversational question, or if it's too vague to route to a specific database.

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

        # Get raw string output first to handle potential extra text from LLM
        router_chain_text_output = prompt | llm | StringOutputParser() 

        print("Attempting to invoke LLM for routing... (Waiting for API response)")
        raw_llm_output = router_chain_text_output.invoke({"query": current_query_for_routing})
        print(f"LLM raw output for routing: '{raw_llm_output}'")

        # Attempt to extract the JSON part from the raw output
        json_string_from_output = extract_json_from_llm_output(raw_llm_output)
        
        updated_values = {"error": None} # Default to no error for this step

        if json_string_from_output:
            try:
                decision_json = json.loads(json_string_from_output) 
                decision = decision_json.get("data_source", "general")
                print(f"Router decision (extracted from JSON): {decision}")

                if decision == "sqlite":
                    updated_values["data_source"] = "sqlite"
                elif decision == "mongodb":
                    updated_values["data_source"] = "mongodb"
                elif decision == "meilisearch":
                    updated_values["data_source"] = "meilisearch"
                elif decision == "neo4j": 
                    updated_values["data_source"] = "neo4j"
                elif decision == "general": 
                    print("Query classified as 'general' by LLM, initiating clarification.")
                    updated_values["data_source"] = "clarification_needed" # NEW data_source state
                    updated_values["clarification_question_needed"] = True
                    updated_values["clarification_question_text"] = (
                        "Your question seems a bit general or ambiguous for a direct database query. "
                        "Could you please specify if you're looking for information about: \n"
                        "1. Employees, Departments, or Projects (company data)? \n"
                        "2. Scientific Research Papers? \n"
                        "3. Support Tickets? \n"
                        "4. Collaborations, research fields, or work done by Researchers? \n"
                        "Please provide more details or rephrase your question focusing on one of these areas."
                    )
                    # Store the query that needs clarification
                    updated_values["original_query_before_clarification"] = current_query_for_routing
                else: # Unexpected value in "data_source" field of JSON
                    updated_values["data_source"] = "end"
                    updated_values["error"] = f"Router JSON contained an unexpected data_source value: {decision}"
            except json.JSONDecodeError as json_err:
                custom_error_msg = f"Failed to parse the extracted JSON from LLM output. Extracted string: '{json_string_from_output}'. Error: {json_err}"
                print(f"JSON PARSING ERROR (after extraction attempt): {custom_error_msg}")
                updated_values["error"] = custom_error_msg
                updated_values["data_source"] = "end"
        else: # JSON could not be extracted from LLM's output
            custom_error_msg = f"LLM output for routing did not contain a recognizable JSON object. Raw output: '{raw_llm_output}'"
            print(f"JSON EXTRACTION FAILED during routing: {custom_error_msg}")
            updated_values["error"] = custom_error_msg
            updated_values["data_source"] = "end"
        
        return {**current_state_snapshot, **updated_values}

    except Exception as e: # Catch other errors like connection errors
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
        else: 
            custom_error_msg = (
                "An unexpected error occurred during the routing phase (e.g., during LLM call). "
                f"Details: {e}"
            )
            print(f"UNEXPECTED ERROR during routing: {custom_error_msg}")
        
        return {
            **current_state_snapshot, 
            "error": custom_error_msg, 
            "data_source": "end"
        }