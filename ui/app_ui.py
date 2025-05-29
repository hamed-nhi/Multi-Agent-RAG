# ui/app_ui.py
import sys
import os
import streamlit as st
import ast 
import pandas as pd 
import io # Required for capturing print statements
import contextlib # Required for capturing print statements
import time # For small delays if needed

# --- Add the project root to the Python path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from graph.builder import app as rag_app 
from tools.db_tools import get_sqlite_connection, get_schema_sqlite

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Agent RAG Explorer",
    page_icon="🧠",
    layout="wide"
)

# --- Session State Initialization ---
default_session_state = {
    "messages": [], "processing_details": {},
    "user_type_for_db_view": "User-Friendly Descriptions",
    "clarification_question": None, "original_query_for_clarification": None,
    "query_from_example_button": None, "is_processing": False,
}
for key, default_value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# --- UI Component Functions (Merged into this file) ---

def display_sidebar():
    st.sidebar.header("About this RAG System")
    st.sidebar.info(
        "This Multi-Agent RAG system, built with LangChain and LangGraph, "
        "demonstrates querying diverse data sources using specialized AI agents. "
        "It can interact with SQLite, MongoDB, MeiliSearch, and Neo4j."
    )
    st.sidebar.markdown("---")
    st.sidebar.subheader("Data Sources & Query Types:")
    st.sidebar.markdown("- **🗄️ SQLite:** Employees, Departments, Projects (SQL)")
    st.sidebar.markdown("- **🍃 MongoDB:** Research Papers (MongoDB JSON Queries)")
    st.sidebar.markdown("- **🔍 MeiliSearch:** Support Tickets (Text Search)")
    st.sidebar.markdown("- **🕸️ Neo4j:** Researcher Collaborations & Projects (Cypher Queries)")
    st.sidebar.markdown("---")
    st.sidebar.caption("Implemented by: [Your Name/Project Alias]")

def display_example_questions():
    st.subheader("Or try one of these example questions:")
    cols_ex = st.columns(4)
    example_sets = {
        "Example 1": ["Who is the lead engineer?", "Status of 'API Integration Service' project?", "Projects for Saba Attar?"],
        "Example 2": ["Keywords for RAG paper by Patrick Lewis?", "Papers on 'Language Agents'?", "Who wrote 'Speculative RAG'?"],
        "Example 3": ["Tickets for MySQL issues?", "Support tickets by Aniruddha Salve?", "Open tickets for Neo4j?"],
        "Example 4": ["Who collaborates with Aniruddha Salve?", "papers about RAG from an author like P. Lewis", "Research field of Patrick Lewis?"],
        
    }
    emojis = ["🗄️", "🍃", "🔍", "🕸️"]
    def handle_example_click(query_text):
        st.session_state.query_from_example_button = query_text
        st.rerun()

    for i, (db_name, questions) in enumerate(example_sets.items()):
        with cols_ex[i]:
            st.markdown(f"##### {emojis[i]} {db_name} Examples")
            for q_idx, q_text in enumerate(questions):
                if st.button(q_text, key=f"{db_name.lower()}_ex_{q_idx}_v11_no_nest"): 
                    handle_example_click(q_text)

def display_processing_journey(processing_details_dict):
    """
    Displays the journey of the query.
    Crucially, this function ITSELF DOES NOT CREATE AN EXPANDER.
    It's designed to be called INSIDE an expander in the main UI.
    """
    details = processing_details_dict
    if not details or not isinstance(details, dict): return

    # Display Backend Process Log first if available
    backend_log = details.get("backend_log")
    if backend_log: 
        st.subheader("📜 Backend Process Log") 
        st.text_area("Log:", value=backend_log, height=200, key="journey_log_area_no_nest", disabled=True)
        st.markdown("---")
    
    st.markdown("##### 🛣️ Your Query's Journey Through Agent States:")
    if details.get("query"):
        st.write("**You Asked:**"); st.info(f"`{details.get('query')}`"); st.markdown("---")

    router_state = details.get("router") 
    if router_state and isinstance(router_state, dict) :
        st.subheader("1️⃣ Routing Decision")
        chosen_ds = router_state.get('data_source', 'N/A')
        ds_emoji_map = {"sqlite": "🗄️", "mongodb": "🍃", "meilisearch": "🔍", "neo4j": "🕸️", "end": "🏁", "general": "💬", "clarification_needed": "❓"}
        emoji = ds_emoji_map.get(chosen_ds, "❓")
        if chosen_ds == "clarification_needed":
            st.warning(f"{emoji} **Clarification Needed:** System requires more information.")
            if router_state.get("clarification_question_text"):
                st.caption("Clarification question that would be asked:")
                st.markdown(f"> _{router_state['clarification_question_text']}_")
        elif chosen_ds == "end" and router_state.get("error"): st.error(f"{emoji} **Routing Halted:** {router_state['error']}")
        elif chosen_ds in ds_emoji_map: st.success(f"{emoji} **Routed to:** {str(chosen_ds).upper()} Database Agent")
        else: st.info(f"{emoji} Router decision: {str(chosen_ds).upper()}")
        st.markdown("---")

    qg_state = details.get("query_generator")
    if qg_state and isinstance(qg_state, dict):
        data_source_for_qg = qg_state.get("data_source", "unknown_ds") 
        generated_q_value = qg_state.get("generated_query", "") 
        if data_source_for_qg not in ["end", "general", "clarification_needed", None] and generated_q_value.strip(): 
            st.subheader(f"2️⃣ Query Generation ({str(data_source_for_qg).upper()} Agent)")
            st.write(f"**Generated Query:**"); lang = "sql" 
            if data_source_for_qg == "mongodb": lang = "json"
            elif data_source_for_qg == "neo4j": lang = "cypher"
            elif data_source_for_qg == "meilisearch": lang = "text"
            st.code(generated_q_value, language=lang, line_numbers=True)
            st.markdown("---")
        elif data_source_for_qg not in ["end", "general", "clarification_needed", None] and not generated_q_value.strip():
             st.warning(f"2️⃣ Query Generation Agent ({str(data_source_for_qg).upper()}): No query was generated.")
             st.markdown("---")

    qr_state = details.get("query_refiner")
    if qr_state and isinstance(qr_state, dict) and qr_state.get("last_failed_query"): 
        st.subheader("✨ Query Refinement Agent")
        original_failed_query = qr_state.get("last_failed_query", "N/A")
        refined_query = qr_state.get("generated_query", "N/A") 
        st.caption("Original query that led to no results:")
        st.code(str(original_failed_query), language="text") 
        st.caption("LLM suggested this refined query:")
        st.code(str(refined_query), language="text") 
        st.markdown("---")

    qe_state = details.get("query_executor")
    if qe_state and isinstance(qe_state, dict):
        data_source_for_qe = qe_state.get("data_source", "unknown_ds") 
        retrieved_context_str = qe_state.get("context", "No context retrieved.") 
        attempt_count = qe_state.get("refinement_attempt_count", 1)
        if data_source_for_qe not in ["end", "general", "clarification_needed", None]:
            st.subheader(f"3️⃣ Query Execution ({str(data_source_for_qe).upper()} - Attempt {attempt_count})")
            executor_error = qe_state.get("error")
            no_results_messages = ["No documents found", "No records found", "[]"]
            is_no_results_str = str(retrieved_context_str)
            is_no_results = is_no_results_str.strip() in no_results_messages or \
                            any(msg.lower() in is_no_results_str.lower() for msg in no_results_messages if "no d" in msg.lower() or "no r" in msg.lower())
            if executor_error and "Query and its refinement(s) returned no results." in executor_error:
                 st.warning("No data found even after query refinement.")
            elif executor_error: st.error(f"Execution Error: {executor_error}")
            elif is_no_results: st.warning("No data found matching the query from the database.")
            else:
                st.success("Data successfully retrieved!")
                with st.popover("View Raw Retrieved Data (JSON/Text)"):
                    try:
                        parsed_context = ast.literal_eval(is_no_results_str) 
                        if isinstance(parsed_context, list) and not parsed_context: st.warning("Retrieved context was an empty list.")
                        else: st.json(parsed_context) 
                    except: st.text(is_no_results_str) 
            st.markdown("---")
    
    rg_state = details.get("response_generator")
    if rg_state and isinstance(rg_state, dict):
        st.subheader("4️⃣ Final Response Formulation")
        if rg_state.get("error"): st.error(f"Response Generation Info/Error: {rg_state.get('error')}")
        else: st.info("The final natural language response (shown in chat) was formulated based on the processed context.")

def display_sqlite_for_normal_user(): st.markdown("DB info: Employees, Departments, Projects. Ask about roles, project statuses, etc.")
def display_sqlite_for_pro_user():
    st.subheader("SQLite Schema & Sample Data")
    try: st.text(get_schema_sqlite.invoke({}))
    except Exception as e: st.error(f"SQLite schema error: {e}")
    st.markdown("---"); st.write("Sample Data (First 5 Rows per Table):")
    conn = None
    try:
        conn = get_sqlite_connection()
        for table in ["departments", "employees", "projects"]:
            st.markdown(f"**Table: `{table}`**")
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 5;", conn)
                if not df.empty: st.dataframe(df, hide_index=True, use_container_width=True)
                else: st.warning(f"Table '{table}' is empty.")
            except Exception as e: st.error(f"Error reading '{table}': {e}")
    except Exception as e: st.error(f"SQLite connection error: {e}")
    finally:
        if conn: conn.close()
def display_mongodb_for_normal_user(): st.markdown("DB info: Research papers (titles, authors, topics, etc.). Ask about papers by topic or author.")
def display_mongodb_for_pro_user(): st.subheader("MongoDB"); st.info("Schema: 'papers' (title, authors, year, topic, keywords, publication). TODO: Show sample docs.")
def display_meilisearch_for_normal_user(): st.markdown("DB info: Support tickets. Search by description, raiser, or status.")
def display_meilisearch_for_pro_user(): st.subheader("MeiliSearch"); st.info("Index: 'support_tickets' (ticket_id, description, raised_by, status). TODO: Show sample docs.")
def display_neo4j_for_normal_user(): st.markdown("DB info: Research network (researchers, fields, collaborations, projects). Ask about collaborations.")
def display_neo4j_for_pro_user(): st.subheader("Neo4j"); st.info("Nodes: Researcher, ProjectOrTopic. Edges: COLLABORATES_WITH, WORKS_ON. TODO: Show sample graph data.")

# --- Main UI Structure ---
display_sidebar()
st.title("Multi-Agent RAG System Explorer 🚀")
st.caption("Ask questions and see how the agents collaborate across diverse data sources!")
st.markdown("---")
display_example_questions()
st.markdown("---")
with st.expander("📖 Browse Database Contents (See what you can ask about!)", expanded=False):
    view_options = ("User-Friendly Descriptions", "Technical View (Schema & Sample Data)")
    idx = 1 if st.session_state.user_type_for_db_view == view_options[1] else 0
    st.session_state.user_type_for_db_view = st.radio("View type:", view_options, index=idx, key="db_view_radio_merged_final_v13", horizontal=True) 
    tabs = st.tabs(["🗄️ SQLite", "🍃 MongoDB", "🔍 MeiliSearch", "🕸️ Neo4j"])
    with tabs[0]:
        if st.session_state.user_type_for_db_view == view_options[0]: display_sqlite_for_normal_user()
        else: display_sqlite_for_pro_user()
    with tabs[1]:
        if st.session_state.user_type_for_db_view == view_options[0]: display_mongodb_for_normal_user()
        else: display_mongodb_for_pro_user()
    with tabs[2]:
        if st.session_state.user_type_for_db_view == view_options[0]: display_meilisearch_for_normal_user()
        else: display_meilisearch_for_pro_user()
    with tabs[3]:
        if st.session_state.user_type_for_db_view == view_options[0]: display_neo4j_for_normal_user()
        else: display_neo4j_for_pro_user()
st.markdown("---")

# --- Chat History Display ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Determine current query to process ---
query_to_process_this_run = None
if st.session_state.clarification_question:
    with st.chat_message("assistant", avatar="🧠"): st.markdown(st.session_state.clarification_question)
    user_clarification_response = st.chat_input("Your clarification:", key="clarification_input_final_v13", disabled=st.session_state.is_processing) 
    if user_clarification_response:
        original_query = st.session_state.original_query_for_clarification
        query_to_process_this_run = f"{original_query} [User clarification: {user_clarification_response}]"
        st.session_state.messages.append({"role": "user", "content": f"(Clarification for: \"{original_query}\")\n{user_clarification_response}"})
        st.session_state.clarification_question = None
        st.session_state.original_query_for_clarification = None
        st.session_state.is_processing = True
else:
    if st.session_state.query_from_example_button:
        query_to_process_this_run = st.session_state.query_from_example_button
        st.session_state.messages.append({"role": "user", "content": query_to_process_this_run})
        st.session_state.query_from_example_button = None
        st.session_state.is_processing = True
    if not query_to_process_this_run:
        user_query_from_chat_input = st.chat_input("Ask your question here...", key="main_chat_input_final_v14", disabled=st.session_state.is_processing) 
        if user_query_from_chat_input:
            query_to_process_this_run = user_query_from_chat_input
            st.session_state.messages.append({"role": "user", "content": query_to_process_this_run})
            st.session_state.is_processing = True

# --- Main Query Processing Block ---
if query_to_process_this_run and st.session_state.is_processing:
    # This is the main try block for the entire query processing and UI updates for the assistant's turn
    try: 
        with st.chat_message("assistant", avatar="🤖"):
            st.session_state.processing_details = {"query": query_to_process_this_run, "backend_log": "", "status_history": []}
            final_response_for_display = "An error occurred during processing."
            
            accumulated_logs_for_this_run = "" 
            status_updates_for_this_run = []   

            with st.status("🚀 Starting RAG process...", expanded=True) as status_ui:
                log_capture_string = io.StringIO()
                with contextlib.redirect_stdout(log_capture_string):
                    try: 
                        inputs = {
                            "query": query_to_process_this_run, "data_source": None, "generated_query": None,
                            "context": None, "response": None, "error": None,
                            "original_user_query": query_to_process_this_run,
                            "initial_generated_query": None, "last_failed_query": None,
                            "needs_query_refinement": False, "refinement_attempt_count": 0,
                            "clarification_question_needed": False, "clarification_question_text": None,
                            "user_clarification_response": None, "original_query_before_clarification": None
                        }
                        final_graph_state = None
                        
                        for output_chunk in rag_app.stream(inputs, {"recursion_limit": 25}):
                            new_logs = log_capture_string.getvalue()
                            if new_logs:
                                accumulated_logs_for_this_run += new_logs
                                log_capture_string.seek(0); log_capture_string.truncate(0)
                            
                            for node_name, node_data in output_chunk.items():
                                status_message = f"Finished node: {node_name}"
                                if node_name == "router": status_message = f"🧠 Router: Decision -> {node_data.get('data_source') if isinstance(node_data, dict) else 'N/A'}"
                                elif node_name == "query_generator": status_message = f"📝 Query Gen: For {node_data.get('data_source') if isinstance(node_data, dict) else 'N/A'}"
                                elif node_name == "query_refiner": status_message = "✨ Query Refiner: Refining..."
                                elif node_name == "query_executor": status_message = f"⏳ Executor: Attempt {node_data.get('refinement_attempt_count', 1) if isinstance(node_data, dict) else 1} done"
                                elif node_name == "response_generator": status_message = "✍️ Response Gen: Formulating..."
                                
                                status_ui.update(label=status_message)
                                st.session_state.processing_details.setdefault("status_history", []).append(status_message)
                                
                                if isinstance(node_data, dict): st.session_state.processing_details[node_name] = node_data.copy()
                                final_graph_state = node_data
                        
                        new_logs = log_capture_string.getvalue() 
                        if new_logs: accumulated_logs_for_this_run += new_logs
                        
                        st.session_state.processing_details["backend_log"] = accumulated_logs_for_this_run
                        st.session_state.processing_details["status_history"] = status_updates_for_this_run 
                        
                        status_ui.update(label="✅ Processing complete!", state="complete", expanded=False)

                        if final_graph_state and isinstance(final_graph_state, dict):
                            if final_graph_state.get("clarification_question_needed") and final_graph_state.get("clarification_question_text"):
                                st.session_state.clarification_question = final_graph_state["clarification_question_text"]
                                st.session_state.original_query_for_clarification = final_graph_state.get("original_query_before_clarification", query_to_process_this_run)
                                final_response_for_display = st.session_state.clarification_question
                            elif final_graph_state.get("error"):
                                error_msg = final_graph_state.get('error')
                                final_response_for_display = f"An issue occurred: {error_msg}"
                                if "Query is general" in error_msg and not st.session_state.clarification_question:
                                    final_response_for_display = "I can help with questions about employees, projects, papers, tickets, or research collaborations. Please be more specific."
                            else:
                                final_response_for_display = final_graph_state.get("response", "Could not formulate a final answer.")
                        else: 
                            final_response_for_display = "Unexpected error: No final state from graph."
                    
                    except Exception as e_graph: 
                        status_ui.update(label=f"⚠️ Error during graph execution: {str(e_graph)}", state="error", expanded=True)
                        final_response_for_display = f"A critical application error occurred during graph processing: {str(e_graph)}"
                        st.session_state.processing_details["application_error"] = str(e_graph)
                        accumulated_logs_for_this_run += log_capture_string.getvalue()
                        st.session_state.processing_details["backend_log"] = accumulated_logs_for_this_run
                        st.session_state.processing_details.setdefault("status_history", []).append(f"ERROR: {str(e_graph)}")
            
            # This block is now OUTSIDE 'with st.status' and 'with contextlib.redirect_stdout'
            # but still INSIDE 'with st.chat_message("assistant")' and the outer 'try'
            
            st.markdown(final_response_for_display)
            st.session_state.messages.append({"role": "assistant", "content": final_response_for_display})

            # If clarification was NOT needed, display the full processing journey
            if not (final_graph_state and isinstance(final_graph_state, dict) and final_graph_state.get("clarification_question_needed")):
                # This is where the expander for processing details is created.
                # The function display_processing_journey will be called inside this expander.
                with st.expander("🔍 Show Processing Details & Agent Steps", expanded=True): 
                    display_processing_journey(st.session_state.processing_details) # This will now include backend_log
        
    # This except block corresponds to the outer try (try block starting after 'if query_to_process_this_run...')
    except Exception as e_outer: 
        critical_error_text = f"A critical UI or application error occurred: {str(e_outer)}"
        # Attempt to display error in UI if possible
        if 'st' in locals() and hasattr(st, 'error'): 
            try:
                st.error(critical_error_text) 
            except st.errors.StreamlitAPIException: 
                 print(f"CRITICAL UI ERROR (cannot display in st.error): {critical_error_text}")
        else: 
            print(critical_error_text) # Fallback to print
        
        if 'st' in locals() and hasattr(st.session_state, 'messages'):
            st.session_state.messages.append({"role": "assistant", "content": critical_error_text})
        if 'st' in locals() and hasattr(st.session_state, 'processing_details'):
            st.session_state.processing_details["application_error"] = str(e_outer)
            # No st.status here as it might be out of scope
            # We can still try to show an expander if st is available
            if 'st' in locals() and hasattr(st, 'expander'):
                with st.expander("🔍 Show Processing Details (Critical Error)", expanded=True):
                    st.error(f"Application Critical Error: {str(e_outer)}")
                    if st.session_state.processing_details: st.json(st.session_state.processing_details)
    
    # This finally block corresponds to the outer try
    finally: 
        st.session_state.is_processing = False 
        st.rerun()
