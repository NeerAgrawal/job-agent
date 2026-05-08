import streamlit as st
import sys
import os
from pathlib import Path

# Add app root to Python path
app_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(app_root))

from app.core.config import settings
from app.core.logging import setup_logging


def setup_page_config():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def render_sidebar():
    """Render sidebar navigation."""
    with st.sidebar:
        st.title(f"🤖 {settings.app_name}")
        st.markdown(f"Version: {settings.app_version}")
        
        st.markdown("---")
        
        # Navigation
        st.subheader("Navigation")
        page = st.selectbox(
            "Choose a page",
            ["Dashboard", "Jobs", "Applications", "Settings"],
            index=0
        )
        
        st.markdown("---")
        
        # Status
        st.subheader("System Status")
        st.success("🟢 API Connected")
        st.info("🔄 Scheduler Active")
        
        return page


def render_dashboard():
    """Render dashboard page."""
    st.markdown("## 📊 Dashboard")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Jobs", "0", "0 today")
    
    with col2:
        st.metric("Applications", "0", "0 today")
    
    with col3:
        st.metric("Interviews", "0", "0 today")
    
    with col4:
        st.metric("Success Rate", "0%", "0%")
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("Recent Activity")
    st.info("No recent activity. Job fetching will begin once configured.")
    
    # Quick Actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Fetch Jobs", type="primary"):
            st.success("Job fetching initiated (placeholder)")
    
    with col2:
        if st.button("📊 Generate Report"):
            st.info("Report generation (placeholder)")
    
    with col3:
        if st.button("⚙️ Settings"):
            st.info("Settings page (placeholder)")


def render_jobs():
    """Render jobs page."""
    st.markdown("## 💼 Jobs")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.selectbox("Source", ["All", "LinkedIn", "Indeed", "Glassdoor"])
    
    with col2:
        st.selectbox("Status", ["All", "New", "Applied", "Interviewing"])
    
    with col3:
        st.date_input("Date Range")
    
    # Jobs table
    st.info("No jobs found. Start fetching jobs to see results here.")


def render_applications():
    """Render applications page."""
    st.markdown("## 📝 Applications")
    
    st.info("No applications yet. Apply to jobs to track them here.")


def render_settings():
    """Render settings page."""
    st.markdown("## ⚙️ Settings")
    
    st.subheader("API Configuration")
    st.text_input("OpenAI API Key", type="password", placeholder="Enter your OpenAI API key")
    st.text_input("Telegram Bot Token", type="password", placeholder="Enter Telegram bot token")
    
    st.subheader("Job Fetching")
    st.number_input("Fetch Interval (hours)", min_value=1, max_value=24, value=6)
    st.number_input("Max Jobs per Run", min_value=1, max_value=100, value=50)
    
    if st.button("Save Settings", type="primary"):
        st.success("Settings saved (placeholder)")


def main():
    """Main Streamlit application."""
    setup_page_config()
    setup_logging()
    
    page = render_sidebar()
    
    # Render selected page
    if page == "Dashboard":
        render_dashboard()
    elif page == "Jobs":
        render_jobs()
    elif page == "Applications":
        render_applications()
    elif page == "Settings":
        render_settings()


if __name__ == "__main__":
    main()
