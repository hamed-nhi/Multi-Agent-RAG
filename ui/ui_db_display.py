# ui/ui_db_display.py
import streamlit as st
import pandas as pd # For displaying dataframes from SQLite

# We need to access our database tools
import sys
import os

# Add the project root to the Python path to allow imports from 'tools'
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.db_tools import get_sqlite_connection, get_schema_sqlite, run_sqlite_query
# We will import tools for other databases later as we implement their display functions
# from tools.db_tools import get_mongodb_client, run_mongodb_query, get_meilisearch_client, run_meilisearch_query, get_neo4j_driver, run_neo4j_query


# --- SQLite Display Functions ---

def display_sqlite_for_normal_user():
    """
    Displays a user-friendly, textual description of the SQLite database content.
    """
    st.markdown("""
        این پایگاه داده شامل اطلاعات مربوط به یک شرکت فرضی است. شما می‌توانید سوالاتی در مورد موارد زیر بپرسید:

        * **کارمندان (Employees):**
            * نام، نقش شغلی (مانند 'Data Scientist', 'Project Manager').
            * دپارتمانی که در آن کار می‌کنند (مانند 'Engineering', 'Data Science').
            * *مثال سوال:* `Which employees work in the Engineering department?`

        * **دپارتمان‌ها (Departments):**
            * نام دپارتمان‌های مختلف شرکت.
            * *مثال سوال:* `List all departments.` (البته Agent شما هنوز برای این سوال مستقیم آماده نشده، اما داده‌ها موجود است)

        * **پروژه‌ها (Projects):**
            * نام پروژه‌ها.
            * وضعیت فعلی آن‌ها (مانند 'active', 'completed', 'paused', 'planning').
            * کارمندی که مسئول آن پروژه است.
            * *مثال سوال:* `What is the status of the "Multi-Agent RAG System" project?` یا `Who is working on the "Customer Churn Prediction" project?`

        این داده‌ها به شما کمک می‌کنند تا سوالات دقیق‌تری از سیستم بپرسید.
    """)

def display_sqlite_for_pro_user():
    """
    Displays the schema and sample data from SQLite tables for professional users.
    """
    st.subheader("SQLite Database Schema:")
    try:
        schema = get_schema_sqlite.invoke({}) # Call our existing tool
        st.text(schema)
    except Exception as e:
        st.error(f"Could not retrieve SQLite schema: {e}")

    st.subheader("Sample Data from Tables (First 5 Rows):")
    
    conn = None
    try:
        conn = get_sqlite_connection()
        
        tables_to_show = ["departments", "employees", "projects"]
        for table_name in tables_to_show:
            st.markdown(f"**Table: `{table_name}`**")
            try:
                # Using pandas to read and display table data for better formatting
                df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5;", conn)
                if not df.empty:
                    st.dataframe(df, hide_index=True)
                else:
                    st.warning(f"Table '{table_name}' is empty or could not be read.")
            except Exception as e:
                st.error(f"Error reading table '{table_name}': {e}")
        
    except Exception as e:
        st.error(f"Could not connect to SQLite or fetch data: {e}")
    finally:
        if conn:
            conn.close()

# --- Placeholder functions for other databases (to be implemented later) ---

def display_mongodb_for_normal_user():
    st.info("TODO: Implement user-friendly description for MongoDB data.")

def display_mongodb_for_pro_user():
    st.info("TODO: Implement schema and sample document display for MongoDB.")

def display_meilisearch_for_normal_user():
    st.info("TODO: Implement user-friendly description for MeiliSearch data (support tickets).")

def display_meilisearch_for_pro_user():
    st.info("TODO: Implement searchable fields and sample ticket display for MeiliSearch.")

def display_neo4j_for_normal_user():
    st.info("TODO: Implement user-friendly description for Neo4j graph data (research network).")

def display_neo4j_for_pro_user():
    st.info("TODO: Implement node labels, relationship types, and sample Cypher query results for Neo4j.")