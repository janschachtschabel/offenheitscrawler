"""
Help page UI components for the Offenheitscrawler.
"""

import streamlit as st


class HelpPageUI:
    """UI components for the help page."""
    
    def __init__(self):
        """Initialize help page UI."""
        pass
    
    def show_help_page(self) -> None:
        """Display help page."""
        st.title("ℹ️ Hilfe")
        
        # Quick start guide
        self._show_quick_start()
        
        st.divider()
        
        # LLM integration guide
        self._show_llm_guide()
        
        st.divider()
        
        # CSV format guide
        self._show_csv_guide()
        
        st.divider()
        
        # Criteria catalogs
        self._show_criteria_catalogs()
        
        st.divider()
        
        # Technical details
        self._show_technical_details()
        
        st.divider()
        
        # Troubleshooting
        self._show_troubleshooting()
    
    def _show_quick_start(self) -> None:
        """Show quick start guide."""
        st.subheader("🚀 Schnellstart")
        
        st.markdown("""
        ### So verwenden Sie den Offenheitscrawler:
        
        1. **🤖 KI konfigurieren** (erforderlich)
           - Gehen Sie zu **⚙️ Einstellungen**
           - Geben Sie Ihren OpenAI API Key ein
           - Testen Sie die Verbindung
        
        2. **📁 CSV-Datei hochladen**
           - Laden Sie eine CSV-Datei mit Organisationen hoch
           - Format: Organisation;URL (mit oder ohne Header)
           - Wählen Sie aus, welche Organisationen gecrawlt werden sollen
        
        3. **⚙️ Konfiguration anpassen**
           - Wählen Sie den passenden Kriterienkatalog
           - Stellen Sie die Crawling-Strategie ein
           - Passen Sie Verzögerungen an
        
        4. **🚀 Crawling starten**
           - Klicken Sie auf "Crawling starten"
           - Warten Sie auf die Fertigstellung
        
        5. **📊 Ergebnisse analysieren**
           - Betrachten Sie die Statistiken
           - Exportieren Sie die Ergebnisse als CSV oder JSON
        """)
    
    def _show_llm_guide(self) -> None:
        """Show LLM integration guide."""
        st.subheader("🤖 KI-Integration (Mandatory)")
        
        st.markdown("""
        ### Warum ist KI erforderlich?
        
        Der Offenheitscrawler verwendet **Large Language Models** für semantische Inhaltsanalyse:
        
        - **Semantisches Verständnis**: Erkennt Konzepte über einfache Stichwörter hinaus
        - **Kontextverständnis**: Versteht Bedeutung und Zusammenhänge
        - **Höhere Genauigkeit**: Reduziert falsch-positive und falsch-negative Ergebnisse
        - **Mehrsprachigkeit**: Funktioniert mit verschiedenen Sprachen
        
        ### Konfiguration
        
        1. **API Key erhalten**:
           - Registrieren Sie sich bei [OpenAI](https://platform.openai.com/)
           - Erstellen Sie einen API Key
           - Oder verwenden Sie einen kompatiblen Service
        
        2. **In der App konfigurieren**:
           - Gehen Sie zu **⚙️ Einstellungen**
           - Geben Sie den API Key ein (wird sicher gespeichert)
           - Wählen Sie ein Modell (Standard: gpt-4.1-mini)
           - Testen Sie die Verbindung
        
        3. **Umgebungsvariable (optional)**:
           ```bash
           export OPENAI_API_KEY="ihr-api-key"
           export OPENAI_BASE_URL="https://api.openai.com/v1"  # optional
           ```
        
        ### Unterstützte Modelle
        
        | Modell | Beschreibung | Kosten | Empfehlung |
        |--------|-------------|---------|------------|
        | **gpt-4.1-mini** | Optimiert, kostengünstig | Niedrig | ✅ **Standard** |
        | gpt-4o-mini | Kostengünstig | Niedrig | Gut für Tests |
        | gpt-4o | Höchste Qualität | Hoch | Für beste Ergebnisse |
        | gpt-4-turbo | Ausgewogen | Mittel | Gute Balance |
        | gpt-3.5-turbo | Schnell | Niedrig | Für einfache Fälle |
        
        ### Kosten-Optimierung
        
        - **Max Tokens**: Standard 15.000 (anpassbar)
        - **Temperature**: 0.1 (deterministisch)
        - **Batch-Verarbeitung**: Mehrere Kriterien pro Anfrage
        - **Fallback**: Bei niedriger Konfidenz → traditionelle Mustersuche
        """)
    
    def _show_csv_guide(self) -> None:
        """Show CSV format guide."""
        st.subheader("📁 CSV-Format")
        
        st.markdown("""
        ### Flexible CSV-Unterstützung
        
        Der Offenheitscrawler unterstützt CSV-Dateien **mit und ohne Header**:
        
        #### Format 1: Mit Header (empfohlen)
        ```csv
        Organisation;URL
        Universität Hamburg;https://www.uni-hamburg.de
        TU München;https://www.tum.de
        ```
        
        #### Format 2: Ohne Header
        ```csv
        Universität Hamburg;https://www.uni-hamburg.de
        TU München;https://www.tum.de
        ```
        
        ### Wichtige Hinweise
        
        - **Trennzeichen**: Semikolon (;) bevorzugt, Komma (,) auch möglich
        - **Spalten**: Erste Spalte = Organisation, zweite Spalte = URL
        - **Zusätzliche Spalten**: Werden ignoriert (nur erste zwei werden verwendet)
        - **Automatische Erkennung**: Header werden automatisch erkannt
        - **URLs**: Müssen vollständig sein (mit http:// oder https://)
        
        ### Organisationsauswahl
        
        Nach dem Upload können Sie wählen:
        
        - **Alle Organisationen**: Verarbeitet die gesamte CSV-Datei
        - **Bereich (Zeile X-Y)**: z.B. Zeile 5 bis 15 für Tests
        - **Einzelne Organisation**: Wählen Sie eine spezifische Organisation
        
        ### Beispiel-Dateien
        
        Laden Sie Beispiel-CSV-Dateien aus dem Projekt-Repository herunter.
        """)
    
    def _show_criteria_catalogs(self) -> None:
        """Show information about criteria catalogs."""
        st.subheader("📋 Kriterienkataloge")
        
        st.markdown("""
        ### Verfügbare Kataloge
        
        Der Offenheitscrawler enthält spezialisierte Kriterienkataloge für verschiedene Organisationstypen:
        
        #### 🎓 Hochschulen
        - Finanzielle Transparenz (Jahresberichte, Haushalte)
        - Forschungsdaten-Offenheit
        - Lehrmaterial-Zugänglichkeit
        - Governance und Entscheidungsprozesse
        
        #### 🏫 Bildungseinrichtungen
        - Transparenz der Bildungsangebote
        - Zugänglichkeit von Lernmaterialien
        - Offene Kommunikation mit Stakeholdern
        - Partizipationsmöglichkeiten
        
        #### 🎭 Kultureinrichtungen
        - Programmtransparenz
        - Zugänglichkeit und Barrierefreiheit
        - Community-Engagement
        - Digitale Präsenz und Offenheit
        
        #### 🔬 Forschungseinrichtungen
        - Open Science Praktiken
        - Datenveröffentlichung
        - Kollaborationsoffenheit
        - Transparenz der Forschungsagenda
        
        #### 📺 Öffentlich-rechtlicher Rundfunk
        - Programm-Transparenz
        - Finanzielle Offenlegung
        - Bürgerbeteiligung
        - Medienvielfalt und Zugänglichkeit
        
        ### Kriterien-Struktur
        
        Jeder Katalog ist hierarchisch strukturiert:
        
        ```
        Katalog
        ├── Dimensionen (z.B. "Transparenz")
        │   ├── Faktoren (z.B. "Finanzielle Transparenz")
        │   │   ├── Kriterien (z.B. "Jahresbericht verfügbar")
        ```
        
        ### Bewertung
        
        - **Binär**: Kriterium erfüllt (✅) oder nicht erfüllt (❌)
        - **Konfidenz**: 0.0 - 1.0 (Sicherheit der KI-Bewertung)
        - **Begründung**: Textuelle Erklärung der Bewertung
        - **Quelle**: URL der Seite, auf der das Kriterium gefunden wurde
        """)
    
    def _show_technical_details(self) -> None:
        """Show technical details."""
        st.subheader("🔧 Technische Details")
        
        st.markdown("""
        ### Crawling-Strategien
        
        #### 🚀 Schnell (4 Seiten)
        - Startseite + 3 wichtigste Seiten
        - Heuristische Auswahl basierend auf URL-Mustern
        - Schnellste Option für Überblick
        
        #### ⚖️ Standard (5-10 Seiten)
        - KI-basierte Auswahl der relevantesten Seiten
        - Analysiert alle gefundenen Links
        - Wählt die vielversprechendsten für Offenheitskriterien
        
        #### 🔍 Gründlich (bis 15 Seiten)
        - Alle relevanten internen Seiten
        - Umfassendste Analyse
        - Längste Laufzeit
        
        ### Verzögerungsmanagement
        
        #### Intra-Domain-Delay
        - Pause zwischen Seiten **derselben Website**
        - Standard: 2 Sekunden
        - Respektiert Server-Last und robots.txt
        
        #### Inter-Domain-Delay
        - Pause zwischen **verschiedenen Organisationen**
        - Standard: 0.5 Sekunden
        - Minimiert Gesamtlaufzeit
        
        ### Technologie-Stack
        
        - **Web-Crawling**: crawl4ai + aiohttp
        - **KI-Integration**: OpenAI-kompatible APIs
        - **UI**: Streamlit
        - **Datenverarbeitung**: pandas
        - **Visualisierung**: plotly
        - **Logging**: loguru
        - **Konfiguration**: YAML
        
        ### Performance
        
        - **Parallel-Verarbeitung**: Bis zu 3 gleichzeitige Anfragen
        - **Timeout**: 30 Sekunden pro Seite
        - **Retry-Logik**: Automatische Wiederholung bei Fehlern
        - **Caching**: Vermeidet doppelte Anfragen
        """)
    
    def _show_troubleshooting(self) -> None:
        """Show troubleshooting guide."""
        st.subheader("🔧 Problemlösung")
        
        st.markdown("""
        ### Häufige Probleme
        
        #### ❌ "KI-Integration erforderlich"
        **Problem**: OpenAI API Key nicht konfiguriert
        
        **Lösung**:
        1. Gehen Sie zu ⚙️ Einstellungen
        2. Geben Sie einen gültigen API Key ein
        3. Testen Sie die Verbindung
        4. Speichern Sie die Konfiguration
        
        #### ❌ "CSV-Datei kann nicht geladen werden"
        **Problem**: Ungültiges CSV-Format
        
        **Lösung**:
        - Überprüfen Sie das Trennzeichen (Semikolon bevorzugt)
        - Stellen Sie sicher, dass URLs vollständig sind
        - Verwenden Sie UTF-8 Kodierung
        - Mindestens zwei Spalten erforderlich
        
        #### ❌ "Crawling fehlgeschlagen"
        **Problem**: Website nicht erreichbar oder blockiert
        
        **Lösung**:
        - Überprüfen Sie die URL-Korrektheit
        - Prüfen Sie Ihre Internetverbindung
        - Erhöhen Sie das Timeout in den Einstellungen
        - Reduzieren Sie parallele Anfragen
        
        #### ❌ "Niedrige Erfolgsrate"
        **Problem**: Viele Websites blockieren den Crawler
        
        **Lösung**:
        - Erhöhen Sie die Verzögerungen
        - Aktivieren Sie robots.txt-Respekt
        - Verwenden Sie weniger parallele Anfragen
        - Prüfen Sie die User-Agent-Einstellungen
        
        ### Performance-Optimierung
        
        #### Für schnellere Ergebnisse:
        - Verwenden Sie "Schnell"-Strategie
        - Reduzieren Sie Max Tokens (5.000-10.000)
        - Wählen Sie gpt-4o-mini oder gpt-3.5-turbo
        - Begrenzen Sie die Organisationsauswahl
        
        #### Für bessere Qualität:
        - Verwenden Sie "Gründlich"-Strategie
        - Erhöhen Sie Max Tokens (15.000-20.000)
        - Wählen Sie gpt-4o oder gpt-4-turbo
        - Senken Sie den Konfidenz-Schwellenwert
        
        ### Support
        
        Bei weiteren Problemen:
        
        1. **Logs prüfen**: Schauen Sie in die Konsole/Terminal-Ausgabe
        2. **Einstellungen zurücksetzen**: Verwenden Sie "Auf Standardwerte zurücksetzen"
        3. **Browser-Cache leeren**: Aktualisieren Sie die Streamlit-App
        4. **Dokumentation**: Lesen Sie die README-Dateien im Projekt
        
        ### Systemanforderungen
        
        - **Python**: 3.8 oder höher
        - **RAM**: Mindestens 4 GB (8 GB empfohlen)
        - **Internet**: Stabile Verbindung erforderlich
        - **API-Limits**: Beachten Sie OpenAI Rate Limits
        """)
        
        # Contact information
        st.info("""
        💡 **Tipp**: Starten Sie mit einer kleinen Auswahl von Organisationen (5-10), 
        um die Konfiguration zu testen, bevor Sie große Datensätze verarbeiten.
        """)
