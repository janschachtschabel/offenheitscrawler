"""
Offenheitscrawler - Streamlit Main Application (Modular Version)

A web crawler application for evaluating organizational openness criteria.
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Import project modules
from src.utils.logger import setup_logger
from src.utils.csv_handler import CSVHandler
from src.config.yaml_loader import YAMLCriteriaLoader
from src.llm.llm_client import LLMClient

# Import UI modules
from src.ui.main_page import MainPageUI
from src.ui.settings_page import SettingsPageUI
from src.ui.statistics_page import StatisticsPageUI
from src.ui.help_page import HelpPageUI

# Configure page
st.set_page_config(
    page_title="Offenheitscrawler",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize logger
logger = setup_logger()


class OffenheitscrawlerApp:
    """Main Streamlit application class."""
    
    def __init__(self):
        """Initialize the application."""
        self.yaml_loader = YAMLCriteriaLoader()
        self.csv_handler = CSVHandler()
        self.logger = logger.bind(name=self.__class__.__name__)
        
        # Initialize UI components
        self.main_page = MainPageUI(self.yaml_loader, self.csv_handler, self.logger)
        self.settings_page = SettingsPageUI(self.logger)
        self.statistics_page = StatisticsPageUI(self.logger)
        self.help_page = HelpPageUI()
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self) -> None:
        """Initialize session state variables."""
        # Core data
        if 'crawling_results' not in st.session_state:
            st.session_state.crawling_results = None
        if 'statistics' not in st.session_state:
            st.session_state.statistics = None
        if 'evaluation_results' not in st.session_state:
            st.session_state.evaluation_results = []
        if 'organizations_df' not in st.session_state:
            st.session_state.organizations_df = pd.DataFrame()
        if 'selected_catalog' not in st.session_state:
            st.session_state.selected_catalog = None
        if 'selected_organizations' not in st.session_state:
            st.session_state.selected_organizations = pd.DataFrame()
        
        # LLM configuration
        if 'llm_client' not in st.session_state:
            # Initialize LLM client from environment or show setup required
            st.session_state.llm_client = LLMClient.create_from_env()
            if st.session_state.llm_client is None:
                st.session_state.llm_setup_required = True
            else:
                st.session_state.llm_setup_required = False
        
        # Settings
        if 'export_settings' not in st.session_state:
            st.session_state.export_settings = {
                'csv_delimiter': ';',
                'date_format': '%Y-%m-%d %H:%M:%S',
                'export_encoding': 'utf-8',
                'include_raw_content': False
            }
        
        if 'advanced_settings' not in st.session_state:
            st.session_state.advanced_settings = {
                'default_timeout': 20,
                'max_concurrent': 3,
                'respect_robots': True,
                'default_confidence': 0.5,
                'enable_pattern_fallback': True,
                'log_level': 'INFO'
            }
    
    def run(self) -> None:
        """Run the main application."""
        # Sidebar navigation
        st.sidebar.title("🕷️ Offenheitscrawler")
        st.sidebar.markdown("---")
        
        # Navigation menu
        page = st.sidebar.selectbox(
            "Navigation",
            ["🏠 Hauptseite", "📊 Statistiken", "⚙️ Einstellungen", "ℹ️ Hilfe"]
        )
        
        # Show current status in sidebar
        self._show_sidebar_status()
        
        # Route to appropriate page
        if page == "🏠 Hauptseite":
            self.main_page.show_main_page()
        elif page == "📊 Statistiken":
            self.statistics_page.show_statistics_page()
        elif page == "⚙️ Einstellungen":
            self.settings_page.show_settings_page()
        elif page == "ℹ️ Hilfe":
            self.help_page.show_help_page()
    
    def _show_sidebar_status(self) -> None:
        """Show current status in sidebar."""
        st.sidebar.markdown("### 📊 Status")
        
        # LLM Status
        if st.session_state.get('llm_setup_required', False):
            st.sidebar.error("🤖 KI nicht konfiguriert")
        else:
            st.sidebar.success("🤖 KI bereit")
        
        # Data Status
        if not st.session_state.organizations_df.empty:
            org_count = len(st.session_state.organizations_df)
            selected_count = len(st.session_state.get('selected_organizations', pd.DataFrame()))
            
            if selected_count > 0:
                st.sidebar.info(f"📁 {selected_count}/{org_count} Org. ausgewählt")
            else:
                st.sidebar.info(f"📁 {org_count} Org. geladen")
        else:
            st.sidebar.warning("📁 Keine Daten geladen")
        
        # Results Status
        if st.session_state.get('crawling_results'):
            results_count = len(st.session_state.crawling_results)
            # Check if results are OrganizationEvaluation objects or dicts
            successful = 0
            for r in st.session_state.crawling_results:
                if hasattr(r, 'success') and r.success:
                    successful += 1
                elif isinstance(r, dict) and r.get('success', False):
                    successful += 1
            st.sidebar.success(f"📊 {successful}/{results_count} erfolgreich")
        else:
            st.sidebar.info("📊 Keine Ergebnisse")


def main():
    """Main function to run the Streamlit app."""
    app = OffenheitscrawlerApp()
    app.run()


if __name__ == "__main__":
    main()
