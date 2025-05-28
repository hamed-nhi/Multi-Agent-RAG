# ui/ui_components.py
import streamlit as st
# در ui_components.py
import ui_db_display # اگر ui_db_display را به عنوان یک ماژول کامل پاس می‌دهید
# from . import ui_db_display # Assuming it's in the same folder

def display_sidebar():
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
    st.sidebar.caption("پیاده‌سازی شده توسط: [HMDAI]")

def display_example_questions():
    st.subheader("Or try one of these example questions:")
    cols_sg = st.columns(4)
    # ... (کد مربوط به تعریف لیست‌های نمونه سوالات) ...
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
            if st.button(q_text, key=f"sqlite_ex_{q_idx}_btn_comp"): # Changed key
                st.session_state.user_query_input_main = q_text

    with cols_sg[1]:
        st.markdown("##### 🍃 MongoDB Examples")
        for q_idx, q_text in enumerate(mongodb_examples):
            if st.button(q_text, key=f"mongodb_ex_{q_idx}_btn_comp"): # Changed key
                st.session_state.user_query_input_main = q_text
    
    with cols_sg[2]:
        st.markdown("##### 🔍 MeiliSearch Examples")
        for q_idx, q_text in enumerate(meilisearch_examples):
            if st.button(q_text, key=f"meilisearch_ex_{q_idx}_btn_comp"): # Changed key
                st.session_state.user_query_input_main = q_text
            
    with cols_sg[3]:
        st.markdown("##### 🕸️ Neo4j Examples")
        for q_idx, q_text in enumerate(neo4j_examples):
            if st.button(q_text, key=f"neo4j_ex_{q_idx}_btn_comp"): # Changed key
                st.session_state.user_query_input_main = q_text


def display_browse_database_contents(ui_db_display_module): # Pass the module as an argument
    with st.expander("📖 Browse Database Contents (See what you can ask about!)", expanded=False):
        st.write("Select your preferred view:")
        
        current_view_type_index = 0 
        if st.session_state.user_type_for_db_view == "کاربر حرفه‌ای (ساختار و داده خام)":
            current_view_type_index = 1

        user_type_selection = st.radio(
            "Choose view type:",
            ("کاربر عادی (توضیحات متنی)", "کاربر حرفه‌ای (ساختار و داده خام)"),
            index=current_view_type_index,
            key="db_view_type_radio_comp", # Changed key
            horizontal=True,
        )
        st.session_state.user_type_for_db_view = user_type_selection

        tab_sqlite, tab_mongodb, tab_meilisearch, tab_neo4j = st.tabs(["🗄️ SQLite", "🍃 MongoDB", "🔍 MeiliSearch", "🕸️ Neo4j"])

        with tab_sqlite:
            st.header("SQLite Data (Employees, Projects, Departments)")
            if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
                ui_db_display_module.display_sqlite_for_normal_user()
            else: 
                ui_db_display_module.display_sqlite_for_pro_user()
        # ... (Implement similarly for other tabs, calling respective functions from ui_db_display_module)
        with tab_mongodb:
            st.header("MongoDB Data (Research Papers)")
            if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
                ui_db_display_module.display_mongodb_for_normal_user()
            else: # کاربر حرفه‌ای
                ui_db_display_module.display_mongodb_for_pro_user()

        with tab_meilisearch:
            st.header("MeiliSearch Data (Support Tickets)")
            if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
                ui_db_display_module.display_meilisearch_for_normal_user()
            else: # کاربر حرفه‌ای
                ui_db_display_module.display_meilisearch_for_pro_user()

        with tab_neo4j:
            st.header("Neo4j Data (Research Network)")
            if st.session_state.user_type_for_db_view == "کاربر عادی (توضیحات متنی)":
                ui_db_display_module.display_neo4j_for_normal_user()
            else: # کاربر حرفه‌ای
                ui_db_display_module.display_neo4j_for_pro_user()


def display_processing_journey(processing_details_dict):
    # This function will contain the logic to display the expander
    # with router, query_generator, query_executor, and response_generator details
    # For brevity, I'm not re-pasting the entire expander code here,
    # but you would move the expander logic from app_ui.py into this function.
    # It will take 'processing_details_dict' (which is st.session_state.processing_details) as input.
    
    details = processing_details_dict
    st.markdown("##### Journey of Your Query:")
    # ... (کد کامل بخش st.expander که قبلاً داشتیم اینجا می‌آید و از details استفاده می‌کند) ...
    # Example snippet:
    st.write("**You Asked:**")
    st.info(details.get("query", "N/A"))
    st.markdown("---")

    router_state_after_node = details.get("router") 
    if router_state_after_node and isinstance(router_state_after_node, dict) :
        st.subheader("1️⃣ Router Agent Decision")
        # ... (rest of router display logic) ...
        st.markdown("---")

    qg_state_after_node = details.get("query_generator")
    if qg_state_after_node and isinstance(qg_state_after_node, dict):
        # ... (rest of query_generator display logic) ...
        st.markdown("---")

    qe_state_after_node = details.get("query_executor")
    if qe_state_after_node and isinstance(qe_state_after_node, dict):
        # ... (rest of query_executor display logic) ...
        st.markdown("---")
    
    rg_state_after_node = details.get("response_generator")
    if rg_state_after_node and isinstance(rg_state_after_node, dict):
        # ... (rest of response_generator display logic) ...
        pass # No final markdown needed if this is the last section in expander