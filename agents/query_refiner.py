# agents/query_refiner.py
import re
from typing import Optional # Import the 're' module for regular expressions
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser as StringOutputParser
from langchain_together import ChatTogether

from graph.state import GraphState
from config import LLM_MODEL, TOGETHER_API_KEY
from tools.db_tools import get_schema_sqlite

llm = ChatTogether(
    model=LLM_MODEL,
    together_api_key=TOGETHER_API_KEY
)


def get_database_schema_for_refinement(data_source: str) -> str:
    # ... (این تابع بدون تغییر باقی می‌ماند) ...
    if data_source == "sqlite":
        try:
            return get_schema_sqlite.invoke({})
        except Exception as e:
            return f"Could not retrieve SQLite schema: {e}"
    elif data_source == "mongodb":
        return (
            "MongoDB 'papers' collection fields: title (string), authors (list of strings), "
            "year (integer), topic (string), keywords (list of strings), "
            "publication (nested object with 'journal' and 'type' string fields)."
        )
    elif data_source == "meilisearch":
        return (
            "MeiliSearch 'support_tickets' index fields: ticket_id (string, primaryKey), "
            "description (text, searchable), raised_by (string, searchable), status (string, searchable/filterable)."
        )
    elif data_source == "neo4j":
        return (
            "Neo4j Graph Database: Nodes: Researcher {name, field}, ProjectOrTopic {name, domain}. "
            "Relationships: (Researcher)-[:COLLABORATES_WITH]->(Researcher), (Researcher)-[:WORKS_ON]->(ProjectOrTopic)."
        )
    return "No schema description available for this data_source."


def extract_json_query_from_text(text: str) -> Optional[str]:
    """
    Attempts to extract the first valid JSON object string from a larger text.
    It looks for text starting with '{' and ending with '}'.
    """
    # Regex to find a string that starts with { and ends with }
    # This is a simple regex and might need to be more robust for complex cases
    # It tries to find the longest possible match for nested structures
    match = re.search(r"(\{.*\})", text, re.DOTALL)
    if match:
        potential_json = match.group(1)
        try:
            # Validate if it's actual JSON by trying to parse it (optional but good)
            import json
            json.loads(potential_json) # This will raise an error if not valid JSON
            return potential_json
        except json.JSONDecodeError:
            # Fallback for more complex structures or if json.loads is too strict
            # For simple dicts ast.literal_eval is often more forgiving
            try:
                import ast
                ast.literal_eval(potential_json)
                return potential_json
            except:
                return None # Not a valid dict/json string
    return None


# def suggest_refined_query(state: GraphState) -> GraphState:
#     """
#     Attempts to refine a failed query.
#     Updates state['generated_query'] with the new query.
#     """
#     print("---REFINING QUERY---")
#     original_user_q = state.get("original_user_query")
#     last_failed_q = state.get("last_failed_query")
#     data_source = state.get("data_source")
    
#     if not original_user_q or not last_failed_q or not data_source:
#         print("Not enough information to refine query. Skipping refinement.")
#         state["needs_query_refinement"] = False 
#         state["error"] = state.get("error") or "Query refinement skipped due to missing information."
#         return state

#     db_schema_or_description = get_database_schema_for_refinement(data_source)

#     # MODIFIED PROMPT: Emphasize ONLY the query, and use markers if necessary
#     prompt_template_str = """
#         You are an expert query refinement assistant.
#         A previous query failed to return the desired results or returned an empty set.
#         Your task is to analyze the original user question, the failed database query,
#         and the database schema/description to suggest a refined query.

#         Original User Question: "{original_user_question}"
#         Database Schema/Description:
#         {database_schema}

#         Previously Failed Query for {data_source_type}:
#         "{failed_query}"

#         Common reasons for query failure include:
#         - Case sensitivity (e.g. for SQLite use LOWER(), for MongoDB/MeiliSearch use regex with "i" option).
#         - Exact matches vs. partial matches (use CONTAINS, LIKE, or $regex).
#         - Incorrect field names or values.
#         - Overly restrictive conditions.
#         - For graph queries (Neo4j), incorrect relationship directions/types.

#         Based on this, provide ONLY the new, refined query string for {data_source_type}.
#         If you believe the original query was optimal and likely failed due to no data existing,
#         or if you cannot make a meaningful refinement, return the original failed query.

#         DO NOT include any explanations, introductions, or any text other than the query itself.
#         The output must be ONLY the query.

#         For MongoDB, the query MUST be a valid Python dictionary string (e.g., '{{"field": "value"}}').
#         For SQLite and Neo4j (Cypher), it MUST be a valid SQL/Cypher string.
#         For MeiliSearch, it MUST be a search text string.

#         Start your response with "REFINED_QUERY_START" and end it with "REFINED_QUERY_END".
#         Example for MongoDB:
#         REFINED_QUERY_START
#         {{"$or": [{{"title": {{"$regex": "rag", "$options": "i"}}}}, {{"keywords": {{"$regex": "rag", "$options": "i"}}}}], "authors": {{"$regex": "lewis", "$options": "i"}}}}
#         REFINED_QUERY_END

#         Refined Query:
#     """
#     # Note: The "Refined Query:" line is a common way to prompt the LLM to start its answer there.
#     # However, the explicit markers are more robust.
    
#     prompt = ChatPromptTemplate.from_template(prompt_template_str)
#     refinement_chain = prompt | llm | StringOutputParser()
    
#     print(f"Attempting to get refined query for {data_source} from LLM...")
#     llm_output_str = refinement_chain.invoke({
#         "original_user_question": original_user_q,
#         "database_schema": db_schema_or_description,
#         "failed_query": last_failed_q,
#         "data_source_type": data_source
#     })

#     print(f"Raw LLM output for refinement: {llm_output_str}")

#     # Attempt to extract the query between markers
#     refined_query_str = llm_output_str # Default to full output
#     try:
#         # Look for the query between REFINED_QUERY_START and REFINED_QUERY_END
#         # This helps strip away any conversational preamble/postamble from the LLM.
#         start_marker = "REFINED_QUERY_START"
#         end_marker = "REFINED_QUERY_END"
        
#         start_index = llm_output_str.find(start_marker)
#         end_index = llm_output_str.find(end_marker)

#         if start_index != -1 and end_index != -1 and start_index < end_index:
#             refined_query_str = llm_output_str[start_index + len(start_marker):end_index].strip()
#         else:
#             # If markers are not found, try to extract JSON if it's MongoDB
#             # This is a fallback in case the LLM doesn't use the markers perfectly.
#             if data_source == "mongodb":
#                 extracted_json = extract_json_query_from_text(llm_output_str)
#                 if extracted_json:
#                     refined_query_str = extracted_json
#                 # else: refined_query_str remains llm_output_str, which might be problematic
#     except Exception as extraction_error:
#         print(f"Error during query extraction from LLM output: {extraction_error}")
#         # Keep llm_output_str as is, let the executor try to parse it

#     refined_query_str = refined_query_str.strip()
#     print(f"Extracted/Refined query: {refined_query_str}")

#     state["generated_query"] = refined_query_str 
#     state["needs_query_refinement"] = False
#     return state

# agents/query_refiner.py
# ... (import ها و تابع get_database_schema_for_refinement و llm instance بدون تغییر) ...

def suggest_refined_query(state: GraphState) -> GraphState:
    """
    Attempts to refine a failed query based on the original user query,
    the last failed query, and the database schema.
    Updates state['generated_query'] with the new query.
    """
    print("---REFINING QUERY---")
    original_user_q = state.get("original_user_query")
    last_failed_q = state.get("last_failed_query")
    data_source = state.get("data_source")
    
    if not original_user_q or not last_failed_q or not data_source:
        # ... (بخش مدیریت خطای اولیه بدون تغییر) ...
        print("Not enough information to refine query. Skipping refinement.")
        state["needs_query_refinement"] = False 
        state["error"] = state.get("error") or "Query refinement skipped due to missing information."
        return state

    db_schema_or_description = get_database_schema_for_refinement(data_source)

    # MODIFIED AND MORE DETAILED PROMPT
    prompt_template_str = """
        You are an expert query refinement assistant.
        A previous query for {data_source_type} failed to return the desired results or returned an empty set.
        Your task is to analyze the original user question, the failed database query,
        and the database schema/description to suggest a single, refined query that is more likely to succeed.

        Original User Question: "{original_user_question}"
        Database Schema/Description:
        {database_schema}
        Previously Failed Query for {data_source_type}:
        "{failed_query}"

        Key Refinement Strategies to Consider:
        1.  **Case Insensitivity:** Always use case-insensitive matching for string comparisons if the database supports it (e.g., LOWER() in SQL, "$options": "i" with $regex in MongoDB).
        2.  **Partial Matches:** If the user provides a partial term, use operators like CONTAINS, LIKE, or $regex. For names like "P. Lewis", consider patterns like "P.*Lewis" or just "Lewis" if the first attempt failed.
        3.  **Acronyms and Full Phrases:** If an acronym is used (e.g., "RAG"), consider that it might refer to a full phrase (e.g., "Retrieval-Augmented Generation") in the database fields, especially in titles. Your refined query should try to match this.
        4.  **Search Across Multiple Fields:** If a term like "RAG" could be in the title OR keywords, use appropriate logic (e.g., $or in MongoDB).
        5.  **Simplify or Broaden Conditions:** If the original query was too restrictive (too many AND conditions), consider if some conditions can be made optional or broadened.
        6.  **Field Correctness:** Double-check if the fields used in the failed query are the most appropriate ones based on the user's question and the schema.

        Based on this, provide ONLY the new, refined query string.
        If you believe the original query was optimal and likely failed due to no data existing,
        or if you cannot make a meaningful refinement based on the strategies above, return the original failed query.

        Output Format Requirements:
        -   Start your response with "REFINED_QUERY_START" on a new line.
        -   The very next line must be the refined query itself, correctly formatted for {data_source_type}.
            -   For MongoDB: a valid Python dictionary string (e.g., '{{"field": "value"}}').
            -   For SQLite/Neo4j: a valid SQL/Cypher string ending with a semicolon.
            -   For MeiliSearch: a simple search text string.
        -   End your response with "REFINED_QUERY_END" on a new line immediately after the query.
        -   DO NOT include any other explanations, introductions, or text outside these markers.

        Example of a complex refinement for MongoDB:
        Original User Question: "papers about RAG by P. Lewis"
        Failed Query: '{{"authors": {{"$regex": "p. lewis", "$options": "i"}}, "keywords": {{"$regex": "rag", "$options": "i"}}}}'
        Refined Query (should be your output if this was the scenario):
        REFINED_QUERY_START
        {{"$and": [{{"authors": {{"$regex": "Lewis", "$options": "i"}}}}, {{"$or": [{{"title": {{"$regex": "Retrieval-Augmented Generation", "$options": "i"}}}}, {{"title": {{"$regex": "RAG", "$options": "i"}}}}, {{"keywords": {{"$regex": "RAG", "$options": "i"}}}}]}}]}}
        REFINED_QUERY_END

        Now, provide your refined query for the input above:
    """
    # Note: The "Refined Query:" line is removed to rely solely on the markers.
    
    prompt = ChatPromptTemplate.from_template(prompt_template_str)
    refinement_chain = prompt | llm | StringOutputParser()
    
    print(f"Attempting to get refined query for {data_source} from LLM...")
    llm_output_str = refinement_chain.invoke({
        "original_user_question": original_user_q,
        "database_schema": db_schema_or_description,
        "failed_query": last_failed_q,
        "data_source_type": data_source
    })

    print(f"Raw LLM output for refinement: {llm_output_str}")

    refined_query_str = llm_output_str # Default to full output
    try:
        start_marker = "REFINED_QUERY_START"
        end_marker = "REFINED_QUERY_END"
        
        start_index = llm_output_str.find(start_marker)
        end_index = llm_output_str.rfind(end_marker) # Use rfind for the last occurrence

        if start_index != -1 and end_index != -1 and start_index < end_index:
            # Add length of start_marker and adjust for newline if present
            actual_start = start_index + len(start_marker)
            # Ensure we only strip what's between markers
            refined_query_str = llm_output_str[actual_start:end_index].strip()
        else:
            # Fallback if markers are not found, try to extract JSON if MongoDB
            if data_source == "mongodb":
                # (تابع extract_json_from_llm_output که قبلاً در router.py داشتیم، اینجا هم می‌تواند مفید باشد)
                # For simplicity, we assume if markers fail, LLM output might be the query itself or still problematic
                print("Warning: Markers not found in refinement output. Using raw output, which might fail.")
                pass # refined_query_str remains llm_output_str
    except Exception as extraction_error:
        print(f"Error during query extraction from LLM output: {extraction_error}")
        # Keep llm_output_str as is, let the executor try to parse it

    refined_query_str = refined_query_str.strip()
    print(f"Extracted/Refined query: {refined_query_str}")

    state["generated_query"] = refined_query_str 
    state["needs_query_refinement"] = False
    return state


#------------------------------------------------------------------------------------------#
# --- Node for Handling Clarification ---
def handle_clarification_needed(state: GraphState) -> GraphState:
    """
    Handles the process of asking the user for clarification when their query is too general.
    This function is designed for command-line interaction.
    """
    print("---CLARIFICATION NEEDED---")
    
    clarification_q_text = state.get("clarification_question_text")
    original_user_q_for_clarification = state.get("original_query_before_clarification")

    if not clarification_q_text or not original_user_q_for_clarification:
        # This should not happen if the router set these fields correctly
        print("Error: Clarification question or original query not found in state. Ending.")
        # Return a new state dictionary with the error
        return {
            **state,
            "error": "Clarification process failed due to missing state information.",
            "data_source": "end",
            "clarification_question_needed": False # Reset flag
        }

    # For command-line interaction: print the clarification question and get input
    print(f"\nSystem: {clarification_q_text}")
    user_clarification_ans = input("Your clarification/response: ")

    # Update the state with the user's clarification
    # And prepare for re-routing
    
    # Combine original query with user's clarification.
    # This is a simple concatenation; more sophisticated merging could be done.
    new_query_after_clarification = f"{original_user_q_for_clarification} [User provided further detail: {user_clarification_ans}]"
    
    print(f"New query after clarification: {new_query_after_clarification}")

    updated_values = {
        "query": new_query_after_clarification, # This new query will be re-routed
        "user_clarification_response": user_clarification_ans,
        "clarification_question_needed": False, # Clarification has been handled
        "clarification_question_text": None,    # Clear the question
        "data_source": None,                    # Reset data_source so router runs fresh on new query
        "error": None,                          # Clear any previous "general query" error from router
        "refinement_attempt_count": 0,          # Reset refinement attempts for the new query cycle
        "needs_query_refinement": False,        # Reset refinement flag
        "initial_generated_query": None,        # Clear previous query generation artifacts
        "last_failed_query": None,
        "generated_query": None,
        "context": None,
        "response": None
    }
    
    # Return a new state dictionary, preserving original_user_query if needed for multiple clarifications (though not implemented here)
    # For now, we assume one round of clarification.
    # original_user_query is part of the state already and will be carried over unless explicitly changed.
    # We need to be careful not to lose the *very first* user query if multiple clarifications happen.
    # Let's ensure original_user_query (the very first one) is preserved if it exists, otherwise use the one before clarification.
    
    # The `state` passed to this function already contains `original_user_query`
    # from the first pass through `execute_query` or from `inputs` if that's where it's first set.
    # The router also sets `original_query_before_clarification`.
    # We are updating `query` with the new combined query.

    # Create a new state by taking the current state and applying updates
    new_state = {**state, **updated_values}
    
    return new_state
