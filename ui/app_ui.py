# ui/app_ui.py
import sys
import os
import streamlit as st

import ui_components 
import ui_components
# import ast # ast might be needed in ui_components or ui_db_display now

# --- Add the project root to the Python path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from graph.builder import app as rag_app
from ui import ui_db_display # For database content display functions
from ui import ui_components   # Our new module for UI components

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
    st.session_state.user_type_for_db_view = "کاربر عادی (توضیحات متنی)"
if "user_query_input_main" not in st.session_state: # For handling button clicks
    st.session_state.user_query_input_main = None


# --- Main UI Layout ---
ui_components.display_sidebar() # Display the sidebar

st.title("Multi-Agent RAG System Explorer 🚀")
st.caption("Ask questions and see how the agents collaborate across diverse data sources!")

st.markdown("---")
ui_components.display_example_questions() # Display example question buttons
st.markdown("---")

ui_components.display_browse_database_contents(ui_db_display) # Display database browser section
st.markdown("---")

# --- Chat History and Input ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Determine query source (button click or direct chat input)
query_from_button = st.session_state.get("user_query_input_main")
user_query_from_chat_input = st.chat_input("Ask your question here...", key="chat_input_field_main")

user_query_to_process = None
if query_from_button:
    user_query_to_process = query_from_button
    st.session_state.user_query_input_main = None # Clear after use
elif user_query_from_chat_input:
    user_query_to_process = user_query_from_chat_input

if user_query_to_process:
    st.session_state.messages.append({"role": "user", "content": user_query_to_process})
    with st.chat_message("user"):
        st.markdown(user_query_to_process)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        details_expander_placeholder = st.empty() # For the expander itself
        st.session_state.processing_details = {"query": user_query_to_process} # Reset for new query
        
        final_response_text = "Sorry, an issue occurred." # Default

        try:
            with st.spinner("🧠 The RAG agents are thinking... Please wait."):
                 # Initialize all expected keys in GraphState for the initial input
                inputs = {
                    "query": user_query_to_process, # یا هر نامی که برای سوال کاربر دارید
                    "data_source": None,
                    "generated_query": None,
                    "context": None,
                    "response": None,
                    "error": None,
                    "original_user_query": user_query_to_process, # یا هر نامی که برای سوال کاربر دارید
                    "initial_generated_query": None,
                    "last_failed_query": None,
                    "needs_query_refinement": False, # Default to False
                    "refinement_attempt_count": 0   # Default to 0
                }
                final_node_output_state = None
                
                # فراخوانی stream
                
                
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

            # Display processing details using the component function
            with details_expander_placeholder.expander("🔍 Show Processing Details & Agent Steps", expanded=False):
                ui_components.display_processing_journey(st.session_state.processing_details)

        except Exception as e:
            st.error(f"A critical error occurred in the RAG application: {e}")
            st.session_state.messages.append({"role": "assistant", "content": f"Critical Error: {e}"})
            st.session_state.processing_details["application_error"] = str(e)
            with details_expander_placeholder.expander("🔍 Show Processing Details (Critical Error)", expanded=True):
                st.error(f"Application Critical Error: {str(e)}")
                st.json(st.session_state.processing_details)