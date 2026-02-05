"""
Cassandra GUI Client - Streamlit Entry Point

A web-based graphical client for Apache Cassandra with full schema-driven CRUD support.
"""

import streamlit as st
from src.app import CassandraGUIApp

def main():
    """Initialize and run the Streamlit application."""
    st.set_page_config(
        page_title="Cassandra GUI Client",
        page_icon="🗄️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    app = CassandraGUIApp()
    app.run()

if __name__ == "__main__":
    main()
