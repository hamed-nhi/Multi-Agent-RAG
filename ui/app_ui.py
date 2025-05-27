# ui/app_ui.py
import sys
import os
import streamlit as st
import ast # For safely evaluating string representations of lists/dicts

# --- Add the project root to the Python path ---
# This should be one of the first things, before other project imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from graph.builder import app as rag_app # Import your compiled RAG graph
from ui import ui_db_display # Import display functions from our new module

# --- Page Configuration ---
st.set_page_config(
    page_title="Multi-Agent RAG Explorer",
    page_icon="🧠",
    layout="wide"
)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [] 
if "processing_details" not in st.session_state:
    st.session_state.processing_details = {}
if "user_type_for_db_view" not in st.session_state:
    st.session_state.user_type_for_db_view = "کاربر عادی (توضیحات متنی)" # Default user type

# --- UI Layout ---
st.title("Multi-Agent RAG System Explorer 🚀")
st.caption("Ask questions and see how the agents collaborate across diverse data sources!")

# --- Section for Suggested Questions ---
st.markdown("---")
st.subheader("Or try one of these example questions:")

cols_sg = st.columns(4) # Renamed to avoid conflict if 'cols' is used elsewhere

sqlite_examples = [
    "Who is the lead engineer?",
    "What is the status of the 'API Integration Service' project?",
    "List all projects assigned to Saba Attar."
]
mongodb_examples = [
    "What are the keywords for the paper on RAG by Patrick Lewis?",
    "Find papers on the topic of 'Language Agents'.",
    "Who wrote 'Speculative RAG'?"
]
meilisearch_examples = [
    "Find tickets about MySQL issues.",
    "What support tickets were raised by Aniruddha Salve?",
    "Search for open tickets related to Neo4j."
]
neo4j_examples = [
    "Who collaborates with Aniruddha Salve?",
    "What projects is Saba Attar working on?",
    "What is the research field of Patrick Lewis?"
]

with cols_sg[0]:
    st.markdown("##### 🗄️ SQLite Examples")
    for q_idx, q_text in enumerate(sqlite_examples):
        # Using a more robust way to handle button clicks and update input
        if st.button(q_text, key=f"sqlite_ex_{q_idx}_btn"):
            st.session_state.user_query_input_main = q_text
            # No explicit rerun needed, Streamlit's flow will handle it with chat_input

with cols_sg[1]:
    st.markdown("##### 🍃 MongoDB Examples")
    for q_idx, q_text in enumerate(mongodb_examples):
        if st.button(q_text, key=f"mongodb_ex_{q_idx}_btn"):
            st.session_state.user_query_input_main = q_text

with cols_sg[2]:
    st.markdown("##### 🔍 MeiliSearch Examples")
    for q_idx, q_text in enumerate(meilisearch_examples):
        if st.button(q_text, key=f"meilisearch_ex_{q_idx}_btn"):
            st.session_state.user_query_input_main = q_text
        
with cols_sg[3]:
    st.markdown("##### 🕸️ Neo4j Examples")
    for q_idx, q_text in enumerate(neo4j_examples):
        if st.button(q_text, key=f"neo4j_ex_{q_idx}_btn"):
            st.session_state.user_query_input_main = q_text

st.markdown("---")


# --- Section for Browse Database Contents ---
with st.expander("📖 Browse Database Contents (See what you can ask about!)", expanded=False):
    st.write("Select your preferred view:")
    
    # Get current selection from session state or default
    current_view_type_index = 0 # Default to "کاربر عادی"
    if st.session_state.user_type_for_db_view == "کاربر حرفه‌ای (ساختار و داده خام)":
        current_view_type_index = 1

    user_type_selection = st.radio(
        "Choose view type:",
        ("کاربر عادی (توضیحات متنی)", "کاربر حرفه‌ای (ساختار و داده خام)"),
        index=current_view_type_index, # Set default based on session state
        key="db_view_type_radio",
        horizontal=True,
    )
    # Update session state based on radio button interaction
    st.session_state.user_type_for_db_view = user_type_selection


    tab_sqlite, tab_mongodb, tab_meilisearch, tab_neo4j = st.tabs(["🗄️ SQLite", "🍃 MongoDB", "🔍 MeiliSearch", "🕸️ Neo4j"])

    with tab_sqlite:
        st.header("SQLite Data (Employees, Projects, Departments)")
        if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
            ui_db_display.display_sqlite_for_normal_user()
        else: # کاربر حرفه‌ای
            ui_db_display.display_sqlite_for_pro_user()

    with tab_mongodb:
        st.header("MongoDB Data (Research Papers)")
        if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
            ui_db_display.display_mongodb_for_normal_user()
        else: # کاربر حرفه‌ای
            ui_db_display.display_mongodb_for_pro_user()

    with tab_meilisearch:
        st.header("MeiliSearch Data (Support Tickets)")
        if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
            ui_db_display.display_meilisearch_for_normal_user()
        else: # کاربر حرفه‌ای
            ui_db_display.display_meilisearch_for_pro_user()

    with tab_neo4j:
        st.header("Neo4j Data (Research Network)")
        if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
            ui_db_display.display_neo4j_for_normal_user()
        else: # کاربر حرفه‌ای
            ui_db_display.display_neo4j_for_pro_user()

st.markdown("---")


# --- User Input (Main chat input) ---
# Key 'user_query_input_main' is used for the main chat input
# When a suggestion button is clicked, it updates st.session_state.user_query_input_main
# Streamlit automatically reruns, and chat_input will pick up this new value if it's configured to.
# However, chat_input doesn't automatically use a session_state variable as its default value in this way.
# We'll handle the button clicks by directly processing the query.
# For a cleaner approach for buttons, they might directly call the processing logic or set a specific "query_to_run" state.

# If a button set the query, it's in st.session_state.user_query_input_main
# We check if it exists and hasn't been processed yet (e.g., by comparing to a 'last_processed_query' state)
# For simplicity, let's assume if it's set by a button, chat_input will be empty this run, or we use the button value.

query_from_button = st.session_state.get("user_query_input_main")
user_query_from_chat_input = st.chat_input("Ask your question here...", key="chat_input_field") # Use a different key for actual chat input

# Determine the actual query to process
user_query = None
if query_from_button:
    user_query = query_from_button
    st.session_state.user_query_input_main = None # Clear it after use so it doesn't re-trigger
elif user_query_from_chat_input:
    user_query = user_query_from_chat_input


if user_query: # This block executes if user_query has a value (from button or chat_input)
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        details_expander_placeholder = st.empty()
        st.session_state.processing_details = {"query": user_query}
        final_response_text = "Sorry, I encountered an issue."

        try:
            with st.spinner("🧠 The RAG agents are thinking... Please wait."):
                inputs = {"query": user_query, "error": None}
                final_node_output_state = None
                
                for output_chunk in rag_app.stream(inputs, {"recursion_limit": 25}):
                    for node_name, node_data_after_execution in output_chunk.items():
                        if isinstance(node_data_after_execution, dict):
                             st.session_state.processing_details[node_name] = node_data_after_execution.copy()
                        else:
                             st.session_state.processing_details[node_name] = {"output_non_dict": node_data_after_execution}
                        final_node_output_state = node_data_after_execution 

                if final_node_output_state and isinstance(final_node_output_state, dict):
                    if final_node_output_state.get("error"):
                        final_response_text = f"I encountered an issue: {final_node_output_state.get('error')}"
                        if "Query is general" in final_node_output_state.get("error", ""):
                             final_response_text = "I can only answer questions about employees, projects, research papers, support tickets, or research collaborations. How can I help you with those?"
                    else:
                        final_response_text = final_node_output_state.get("response", "Sorry, I couldn't formulate a final answer.")
                else:
                    final_response_text = "An unexpected error occurred, and no final state was determined from the graph."
            
            response_placeholder.markdown(final_response_text)
            st.session_state.messages.append({"role": "assistant", "content": final_response_text})

            with details_expander_placeholder.expander("🔍 Show Processing Details & Agent Steps", expanded=False):
                details = st.session_state.processing_details
                st.markdown("##### Journey of Your Query:")
                st.write("**You Asked:**")
                st.info(details.get("query", "N/A"))
                st.markdown("---")

                router_state_after_node = details.get("router") 
                if router_state_after_node and isinstance(router_state_after_node, dict) :
                    st.subheader("1️⃣ Router Agent Decision")
                    chosen_ds = router_state_after_node.get('data_source', 'N/A')
                    ds_emoji_map = {
                        "sqlite": "🗄️", "mongodb": "🍃", "meilisearch": "🔍",
                        "neo4j": "🕸️", "end": "🏁", "general": "💬"
                    }
                    emoji = ds_emoji_map.get(chosen_ds, "❓")
                    st.success(f"{emoji} Data Source Chosen: **{chosen_ds.upper()}**")
                    if router_state_after_node.get("error"):
                        st.error(f"Router Info/Error: {router_state_after_node['error']}")
                    st.markdown("---")

                qg_state_after_node = details.get("query_generator")
                if qg_state_after_node and isinstance(qg_state_after_node, dict):
                    data_source_for_qg = qg_state_after_node.get("data_source", "unknown_ds") 
                    generated_q_value = qg_state_after_node.get("generated_query", "No query generated or N/A")
                    if data_source_for_qg not in ["end", "general"]: 
                        st.subheader(f"2️⃣ Query Generation Agent ({data_source_for_qg.upper()})")
                        st.write(f"**Generated Query for `{data_source_for_qg}`:**")
                        lang = "sql" 
                        if data_source_for_qg == "mongodb": lang = "json"
                        elif data_source_for_qg == "neo4j": lang = "cypher"
                        elif data_source_for_qg == "meilisearch": lang = "text"
                        if generated_q_value and generated_q_value.strip():
                            st.code(generated_q_value, language=lang, line_numbers=True)
                        else:
                            st.warning("No query was generated by the agent for this step (or router decided to 'end').")
                        st.markdown("---")

                qe_state_after_node = details.get("query_executor")
                if qe_state_after_node and isinstance(qe_state_after_node, dict):
                    data_source_for_qe = qe_state_after_node.get("data_source", "unknown_ds") 
                    retrieved_context_str = qe_state_after_node.get("context", "No context retrieved or N/A")
                    if data_source_for_qe not in ["end", "general"]:
                        st.subheader(f"3️⃣ Query Execution ({data_source_for_qe.upper()})")
                        st.write("**Retrieved Data Context:**")
                        executor_error = qe_state_after_node.get("error")
                        if executor_error and ("Error during query execution" in executor_error or "Connection Error" in executor_error):
                            st.error(executor_error)
                        elif retrieved_context_str == "[]" or \
                             (isinstance(retrieved_context_str, str) and ("No documents found" in retrieved_context_str or "No records found" in retrieved_context_str)):
                            st.warning("No data found matching the query.")
                        else:
                            try:
                                parsed_context = ast.literal_eval(retrieved_context_str)
                                if isinstance(parsed_context, list) and len(parsed_context) == 0:
                                     st.warning("No data found matching the query (parsed as empty list).")
                                else:
                                    st.json(parsed_context) 
                            except (ValueError, SyntaxError, TypeError):
                                st.text(retrieved_context_str) 
                        st.markdown("---")
                
                rg_state_after_node = details.get("response_generator")
                if rg_state_after_node and isinstance(rg_state_after_node, dict):
                    st.subheader("4️⃣ Response Generation Agent State")
                    st.write("This shows the state after the final response was formulated (response text itself is shown above).")
                    rg_internal_details = {k: v for k, v in rg_state_after_node.items() if k != 'response'}
                    if rg_internal_details:
                        st.json(rg_internal_details)
                    else:
                        st.info("No additional metadata from response generator node state.")

        except Exception as e:
            st.error(f"A critical error occurred in the RAG application: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Critical Error: {e}"})
            st.session_state.processing_details["application_error"] = str(e)
            with details_expander_placeholder.expander("🔍 Show Processing Details (Critical Error)", expanded=True):
                st.error(f"Application Critical Error: {str(e)}")
                st.json(st.session_state.processing_details) 

# --- Sidebar ---
st.sidebar.header("درباره این سیستم RAG")
st.sidebar.info(
    "این سیستم Multi-Agent RAG، که با LangChain و LangGraph ساخته شده است، "
    "توانایی پرسش و پاسخ از منابع داده‌ی متنوع با استفاده از Agentهای هوشمند و متخصص را نمایش می‌دهد. "
    "این سیستم می‌تواند با SQLite، MongoDB، MeiliSearch و Neo4j تعامل داشته باشد."
)
st.sidebar.markdown("---")
st.sidebar.subheader("منابع داده و نوع کوئری‌ها:")
st.sidebar.markdown("- **🗄️ SQLite:** کارمندان، دپارتمان‌ها، پروژه‌ها (SQL)")
st.sidebar.markdown("- **🍃 MongoDB:** مقالات پژوهشی (کوئری‌های JSON در MongoDB)")
st.sidebar.markdown("- **🔍 MeiliSearch:** تیکت‌های پشتیبانی (جستجوی متنی)")
st.sidebar.markdown("- **🕸️ Neo4j:** همکاری‌های محققان و پروژه‌ها (کوئری‌های Cypher)")
st.sidebar.markdown("---")
st.sidebar.caption("پیاده‌سازی شده توسط: [نام شما/نام پروژه]") # اینجا را با نام خودتان یا پروژه