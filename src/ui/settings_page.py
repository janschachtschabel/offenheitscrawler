"""
Settings page UI components for the Offenheitscrawler.
"""

import streamlit as st
import os
from src.llm.llm_client import LLMClient, LLMConfig


class SettingsPageUI:
    """UI components for the settings page."""
    
    def __init__(self, logger):
        """Initialize settings page UI."""
        self.logger = logger
    
    def show_settings_page(self) -> None:
        """Display settings page."""
        st.title("⚙️ Einstellungen")
        
        # LLM Configuration Section
        self._show_llm_configuration()
        
        st.divider()
        
        # Export Settings Section
        self._show_export_settings()
        
        st.divider()
        
        # Advanced Settings Section
        self._show_advanced_settings()
    
    def _show_llm_configuration(self) -> None:
        """Display LLM configuration section."""
        st.subheader("🤖 KI-Integration (Erforderlich)")
        
        # Current status
        if st.session_state.get('llm_client') and not st.session_state.get('llm_setup_required', False):
            st.success("✅ KI-Integration ist konfiguriert und einsatzbereit!")
        else:
            st.warning("⚠️ KI-Integration ist noch nicht konfiguriert. Dies ist für die Kriterienauswertung erforderlich.")
        
        # API Key input
        current_key = os.getenv('OPENAI_API_KEY', '')
        api_key = st.text_input(
            "OpenAI API Key",
            value=current_key if current_key else "",
            type="password",
            help="Ihr OpenAI API Key. Kann auch über die Umgebungsvariable OPENAI_API_KEY gesetzt werden."
        )
        
        # Base URL (optional)
        base_url = st.text_input(
            "API Base URL (optional)",
            value=os.getenv('OPENAI_BASE_URL', ''),
            help="Nur ändern wenn Sie einen anderen OpenAI-kompatiblen Service verwenden"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Model selection
            model = st.selectbox(
                "Modell",
                ["gpt-4.1-mini", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
                index=0,
                help="KI-Modell für die Inhaltsanalyse. gpt-4.1-mini ist optimiert und kostengünstig."
            )
            
            # Temperature
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.1,
                step=0.1,
                help="Kreativität des Modells (0.0 = deterministisch, 1.0 = kreativ)"
            )
        
        with col2:
            # Max tokens
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=1000,
                max_value=50000,
                value=15000,
                step=1000,
                help="Maximale Anzahl Tokens pro Anfrage"
            )
            
            # Test connection button
            if st.button("🔍 Verbindung testen"):
                if api_key:
                    self._test_llm_connection(api_key, base_url, model, temperature, max_tokens)
                else:
                    st.error("❌ Bitte geben Sie einen API Key ein.")
        
        # Save configuration
        if st.button("💾 Konfiguration speichern", type="primary"):
            if api_key:
                config = LLMConfig(
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                st.session_state.llm_client = LLMClient(config)
                st.session_state.llm_setup_required = False
                st.success("✅ LLM-Konfiguration gespeichert!")
            else:
                st.warning("⚠️ Bitte geben Sie einen API Key ein.")
    
    def _test_llm_connection(self, api_key: str, base_url: str, model: str, temperature: float, max_tokens: int) -> None:
        """Test LLM connection."""
        try:
            with st.spinner("🔍 Teste Verbindung..."):
                config = LLMConfig(
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                test_client = LLMClient(config)
                
                # Simple test query
                response = test_client.analyze_content(
                    "Test", 
                    "Antworte nur mit 'OK' wenn du diese Nachricht verstehst."
                )
                
                if response and "OK" in response.get('analysis', ''):
                    st.success("✅ Verbindung erfolgreich! KI-Integration funktioniert.")
                else:
                    st.warning("⚠️ Verbindung hergestellt, aber unerwartete Antwort erhalten.")
                    
        except Exception as e:
            st.error(f"❌ Verbindungstest fehlgeschlagen: {str(e)}")
            self.logger.error(f"LLM connection test failed: {str(e)}")
    
    def _show_export_settings(self) -> None:
        """Display export settings section."""
        st.subheader("📤 Export-Einstellungen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV delimiter
            csv_delimiter = st.selectbox(
                "CSV-Trennzeichen",
                [";", ",", "\t"],
                index=0,
                help="Trennzeichen für CSV-Export"
            )
            
            # Include raw content
            include_raw_content = st.checkbox(
                "Rohe Inhalte in Export einbeziehen",
                value=False,
                help="Fügt die gecrawlten Rohinhalte zum CSV-Export hinzu (macht Datei größer)"
            )
        
        with col2:
            # Date format
            date_format = st.text_input(
                "Datumsformat",
                value="%Y-%m-%d %H:%M:%S",
                help="Format für Zeitstempel im Export"
            )
            
            # Export encoding
            export_encoding = st.selectbox(
                "Zeichenkodierung",
                ["utf-8", "utf-8-sig", "iso-8859-1"],
                index=0,
                help="Zeichenkodierung für exportierte Dateien"
            )
        
        # Save export settings
        if st.button("💾 Export-Einstellungen speichern"):
            st.session_state.export_settings = {
                'csv_delimiter': csv_delimiter,
                'date_format': date_format,
                'export_encoding': export_encoding,
                'include_raw_content': include_raw_content
            }
            st.success("✅ Export-Einstellungen gespeichert!")
    
    def _show_advanced_settings(self) -> None:
        """Display advanced settings section."""
        st.subheader("🔧 Erweiterte Einstellungen")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🕷️ Crawler-Einstellungen")
            
            # Default timeout
            default_timeout = st.number_input(
                "Standard-Timeout (Sekunden)",
                min_value=10,
                max_value=120,
                value=30,
                help="Standard-Timeout für HTTP-Anfragen"
            )
            
            # Max concurrent requests
            max_concurrent = st.number_input(
                "Max. parallele Anfragen",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximale Anzahl gleichzeitiger HTTP-Anfragen"
            )
            
            # Respect robots.txt
            respect_robots = st.checkbox(
                "robots.txt respektieren",
                value=True,
                help="Berücksichtigt robots.txt-Anweisungen der Websites"
            )
        
        with col2:
            st.subheader("📊 Analyse-Einstellungen")
            
            # Default confidence threshold
            default_confidence = st.slider(
                "Standard-Konfidenz-Schwellenwert",
                min_value=0.1,
                max_value=1.0,
                value=0.3,
                step=0.1,
                help="Standard-Schwellenwert für KI-Konfidenz"
            )
            
            # Enable pattern fallback
            enable_pattern_fallback = st.checkbox(
                "Muster-Fallback aktivieren",
                value=True,
                help="Verwendet traditionelle Mustersuche als Fallback bei niedriger KI-Konfidenz"
            )
            
            # Log level
            log_level = st.selectbox(
                "Log-Level",
                ["DEBUG", "INFO", "WARNING", "ERROR"],
                index=1,
                help="Detailgrad der Protokollierung"
            )
        
        # Save advanced settings
        if st.button("💾 Erweiterte Einstellungen speichern"):
            st.session_state.advanced_settings = {
                'default_timeout': default_timeout,
                'max_concurrent': max_concurrent,
                'respect_robots': respect_robots,
                'default_confidence': default_confidence,
                'enable_pattern_fallback': enable_pattern_fallback,
                'log_level': log_level
            }
            st.success("✅ Erweiterte Einstellungen gespeichert!")
        
        # Reset to defaults
        if st.button("🔄 Auf Standardwerte zurücksetzen"):
            # Clear all settings from session state
            keys_to_clear = ['export_settings', 'advanced_settings']
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.success("✅ Einstellungen auf Standardwerte zurückgesetzt!")
            st.rerun()
