"""
Main page UI components for the Offenheitscrawler.
"""

import streamlit as st
import pandas as pd
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.crawler.web_crawler import WebCrawler
from src.analysis.criteria_evaluator import CriteriaEvaluator
from src.statistics.stats_collector import StatisticsCollector


class MainPageUI:
    """UI components for the main crawling page."""
    
    def __init__(self, yaml_loader, csv_handler, logger):
        """Initialize main page UI."""
        self.yaml_loader = yaml_loader
        self.csv_handler = csv_handler
        self.logger = logger
    
    def show_main_page(self) -> None:
        """Display main crawling page."""
        st.title("🕷️ Offenheitscrawler")
        st.markdown("Automatisierte Bewertung von Organisationsoffenheit")
        
        # LLM Setup Warning
        if st.session_state.get('llm_setup_required', False):
            st.error(
                "🤖 **KI-Integration erforderlich**: Für die Kriterienauswertung wird ein OpenAI API Key benötigt. "
                "Bitte gehen Sie zu ⚙️ **Einstellungen** und konfigurieren Sie die KI-Anbindung."
            )
            if st.button("🔧 Zu den Einstellungen"):
                st.rerun()
            st.divider()
        
        # File upload section
        self._show_file_upload_section()
        
        # Configuration section (only if file is uploaded)
        if not st.session_state.organizations_df.empty:
            self._show_configuration_section()
    
    def _show_file_upload_section(self) -> None:
        """Display file upload section."""
        st.subheader("📁 Organisationen hochladen")
        
        uploaded_file = st.file_uploader(
            "CSV-Datei mit Organisationen hochladen",
            type=['csv'],
            help="Die CSV-Datei sollte die Spalten 'Organisation' und 'URL' enthalten (Semikolon-getrennt)."
        )
        
        if uploaded_file is not None:
            try:
                # Load organizations
                organizations_df = self.csv_handler.load_organizations(uploaded_file)
                st.session_state.organizations_df = organizations_df
                
                st.success(f"✅ {len(organizations_df)} Organisationen erfolgreich geladen!")
                
                # Show preview
                st.subheader("📋 Vorschau der geladenen Organisationen")
                st.dataframe(organizations_df.head(10), use_container_width=True)
                
                if len(organizations_df) > 10:
                    st.info(f"Zeige die ersten 10 von {len(organizations_df)} Organisationen.")
                
                # Organization selection
                self._show_organization_selection(organizations_df)
                
            except Exception as e:
                st.error(f"❌ Fehler beim Laden der CSV-Datei: {str(e)}")
                self.logger.error(f"CSV loading error: {str(e)}")
    
    def _show_organization_selection(self, organizations_df: pd.DataFrame) -> None:
        """Display organization selection options."""
        st.subheader("🎯 Organisationsauswahl")
        
        selection_mode = st.radio(
            "Welche Organisationen sollen gecrawlt werden?",
            ["Alle Organisationen", "Bereich auswählen (Zeile X bis Y)", "Einzelne Organisation"],
            help="Wählen Sie aus, welche Organisationen aus der CSV-Datei verarbeitet werden sollen."
        )
        
        if selection_mode == "Alle Organisationen":
            st.session_state.selected_organizations = organizations_df
            st.info(f"📊 Alle {len(organizations_df)} Organisationen ausgewählt")
            
        elif selection_mode == "Bereich auswählen (Zeile X bis Y)":
            col1, col2 = st.columns(2)
            
            with col1:
                start_row = st.number_input(
                    "Von Zeile",
                    min_value=1,
                    max_value=len(organizations_df),
                    value=1,
                    help="Startzeile (1-basiert)"
                )
            
            with col2:
                end_row = st.number_input(
                    "Bis Zeile",
                    min_value=start_row,
                    max_value=len(organizations_df),
                    value=max(start_row, min(10, len(organizations_df))),
                    help="Endzeile (1-basiert, inklusive)"
                )
            
            # Convert to 0-based indexing for pandas
            selected_df = organizations_df.iloc[start_row-1:end_row]
            st.session_state.selected_organizations = selected_df
            
            st.info(f"📊 {len(selected_df)} Organisationen ausgewählt (Zeile {start_row} bis {end_row})")
            
            # Show preview of selection
            if len(selected_df) > 0:
                st.dataframe(selected_df, use_container_width=True)
        
        elif selection_mode == "Einzelne Organisation":
            selected_org = st.selectbox(
                "Organisation auswählen",
                organizations_df['Organisation'].tolist(),
                help="Wählen Sie eine einzelne Organisation aus"
            )
            
            if selected_org:
                selected_df = organizations_df[organizations_df['Organisation'] == selected_org]
                st.session_state.selected_organizations = selected_df
                st.info(f"📊 1 Organisation ausgewählt: {selected_org}")
                st.dataframe(selected_df, use_container_width=True)
    
    def _show_configuration_section(self) -> None:
        """Display crawling configuration section."""
        st.subheader("⚙️ Crawling-Konfiguration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Catalog selection
            available_catalogs = self.yaml_loader.get_available_catalogs()
            
            if not available_catalogs:
                st.error("❌ Keine Kriterienkataloge gefunden!")
                return
            
            # Find index of 'hochschulen' catalog for default selection
            default_index = 0
            for i, catalog in enumerate(available_catalogs):
                if 'hochschulen' in catalog.lower():
                    default_index = i
                    break
            
            selected_catalog = st.selectbox(
                "Kriterienkatalog",
                available_catalogs,
                index=default_index,
                help="Wählen Sie den passenden Kriterienkatalog für Ihre Organisationen"
            )
            
            # Subpage selection strategy
            st.subheader("📄 Unterseiten-Auswahl")
            
            subpage_strategy = st.selectbox(
                "Welche Unterseiten sollen einbezogen werden?",
                ["Intelligente Auswahl (KI wählt beste Seiten)", 
                 "Begrenzte Anzahl", 
                 "Alle Unterseiten", 
                 "Nur Startseite"],
                index=0,
                help="Bestimmt, welche Unterseiten für die Kriterienbewertung verwendet werden"
            )
            
            # Configure max pages based on strategy
            if subpage_strategy == "Nur Startseite":
                max_pages = 1
                crawling_strategy = "homepage_only"
                st.info("📄 Nur die Startseite wird analysiert")
                
            elif subpage_strategy == "Alle Unterseiten":
                max_pages = 500  # Higher limit for comprehensive crawling
                crawling_strategy = "all_pages"
                st.warning("⚠️ Alle gefundenen Unterseiten werden gecrawlt (kann lange dauern)")
                
            elif subpage_strategy == "Begrenzte Anzahl":
                max_pages = st.number_input(
                    "Anzahl Unterseiten (1-200)",
                    min_value=1,
                    max_value=200,
                    value=20,
                    help="Anzahl der Unterseiten, die zusätzlich zur Startseite gecrawlt werden"
                )
                crawling_strategy = "limited"
                st.info(f"📄 Startseite + {max_pages - 1} Unterseiten werden analysiert")
                
            else:  # Intelligente Auswahl
                max_pages = st.number_input(
                    "Anzahl der besten Seiten (1-200)",
                    min_value=1,
                    max_value=200,
                    value=20,
                    help="KI wählt die relevantesten Seiten für die Kriterienbewertung aus"
                )
                crawling_strategy = "intelligent"
                if st.session_state.get('llm_setup_required', False):
                    st.error("🤖 KI-Integration erforderlich für intelligente Auswahl!")
                else:
                    st.success(f"🤖 KI wählt die {max_pages} relevantesten Seiten aus")
        
        with col2:
            # Delay configuration
            st.subheader("⏱️ Verzögerungseinstellungen")
            
            intra_domain_delay = st.slider(
                "Verzögerung innerhalb einer Domain (Sekunden)",
                min_value=0.5,
                max_value=5.0,
                value=1.0,
                step=0.5,
                help="Pause zwischen Seiten derselben Website"
            )
            
            inter_domain_delay = st.slider(
                "Verzögerung zwischen Organisationen (Sekunden)",
                min_value=0.0,
                max_value=3.0,
                value=0.0,
                step=0.1,
                help="Pause beim Wechsel zwischen verschiedenen Organisationen"
            )
            
            # Confidence threshold
            confidence_threshold = st.slider(
                "KI-Konfidenz-Schwellenwert",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="Mindest-Konfidenz für KI-Bewertungen (niedrigere Werte → Fallback auf Muster)"
            )
        
        # Start crawling button
        if st.button("🚀 Crawling starten", type="primary", use_container_width=True):
            # Check if LLM is configured
            if st.session_state.get('llm_setup_required', False):
                st.error("❌ KI-Integration ist erforderlich! Bitte konfigurieren Sie die KI-Anbindung in den Einstellungen.")
                return
            
            # Get selected organizations
            selected_orgs = st.session_state.get('selected_organizations', st.session_state.organizations_df)
            
            if selected_orgs.empty:
                st.error("❌ Keine Organisationen ausgewählt!")
                return
            
            # Run crawling process
            with st.spinner("🕷️ Crawling läuft..."):
                asyncio.run(self._run_crawling_process(
                    selected_orgs,
                    selected_catalog,
                    max_pages,
                    intra_domain_delay,
                    inter_domain_delay,
                    confidence_threshold,
                    crawling_strategy
                ))
    
    async def _run_crawling_process(
        self, 
        organizations_df: pd.DataFrame, 
        catalog_name: str,
        max_pages: int,
        intra_domain_delay: float,
        inter_domain_delay: float,
        confidence_threshold: float,
        crawling_strategy: str
    ) -> None:
        """Run the crawling and evaluation process."""
        try:
            # Load criteria catalog
            catalog = self.yaml_loader.load_catalog(catalog_name)
            criteria_names = list(catalog.get('criteria', {}).keys())
            
            # Initialize crawler with new delay settings
            crawler = WebCrawler(
                max_pages_per_site=max_pages,
                intra_domain_delay=intra_domain_delay,
                inter_domain_delay=inter_domain_delay,
                crawling_strategy=crawling_strategy
            )
            
            # Initialize evaluator
            evaluator = CriteriaEvaluator(
                catalog, 
                llm_client=st.session_state.llm_client,
                confidence_threshold=confidence_threshold
            )
            
            # Initialize statistics collector
            stats_collector = StatisticsCollector()
            
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            detailed_status = st.empty()
            
            total_orgs = len(organizations_df)
            
            # Status callback for detailed updates
            def update_detailed_status(message: str):
                detailed_status.text(message)
            
            for idx, (_, org) in enumerate(organizations_df.iterrows()):
                org_name = org['Organisation']
                org_url = org['URL']
                
                status_text.text(f"🏢 Organisation {idx + 1}/{total_orgs}: {org_name}")
                detailed_status.text(f"🔍 Starte Crawling von {org_url}...")
                
                try:
                    # Crawl organization with status updates
                    crawl_result = await crawler.crawl_organization(
                        org_name, 
                        org_url,
                        llm_client=st.session_state.llm_client,
                        criteria_names=criteria_names,
                        status_callback=update_detailed_status
                    )
                    
                    detailed_status.text(f"📊 Bewerte {len(crawl_result.pages)} Seiten gegen {len(criteria_names)} Kriterien...")
                    
                    # Evaluate criteria
                    evaluation_result = evaluator.evaluate_organization(org_name, crawl_result)
                    
                    results.append(evaluation_result)
                    
                    detailed_status.text(f"✅ {org_name} erfolgreich abgeschlossen ({crawl_result.successful_pages}/{crawl_result.total_pages} Seiten)")
                    
                except Exception as e:
                    self.logger.error(f"Error processing {org_name}: {str(e)}")
                    detailed_status.text(f"❌ Fehler bei {org_name}: {str(e)}")
                    results.append({
                        'organization_name': org_name,
                        'base_url': org_url,
                        'error': str(e),
                        'success': False
                    })
                
                # Update progress
                progress_bar.progress((idx + 1) / total_orgs)
                
                # Small delay between organizations
                if idx < total_orgs - 1:  # Don't delay after last organization
                    await asyncio.sleep(inter_domain_delay)
            
            # Filter successful evaluations for statistics
            successful_results = [r for r in results if not isinstance(r, dict) or r.get('success', True)]
            
            # Collect comprehensive statistics
            statistics = stats_collector.collect_statistics(
                successful_results, 
                organizations_df, 
                catalog_name
            )
            
            # Store results in session state
            st.session_state.crawling_results = results
            st.session_state.statistics = statistics
            st.session_state.evaluation_results = results
            st.session_state.selected_catalog = catalog_name
            
            # Calculate final statistics
            successful_orgs = len(successful_results)
            total_criteria_evaluated = sum([
                getattr(r, 'total_criteria', 0) if hasattr(r, 'total_criteria') else 0 
                for r in successful_results
            ])
            avg_fulfillment = sum([
                getattr(r, 'fulfillment_percentage', 0) if hasattr(r, 'fulfillment_percentage') else 0 
                for r in successful_results
            ]) / len(successful_results) if successful_results else 0
            
            status_text.text("🎉 Alle Organisationen erfolgreich verarbeitet!")
            detailed_status.text(f"📊 Insgesamt {total_criteria_evaluated} Kriterien für {successful_orgs} Organisationen bewertet")
            
            st.success(
                f"✅ **Crawling abgeschlossen!**\n\n"
                f"📈 **Ergebnisse:** {successful_orgs}/{total_orgs} Organisationen erfolgreich\n"
                f"📊 **Kriterien:** {total_criteria_evaluated} Kriterien insgesamt bewertet\n"
                f"💯 **Durchschnittliche Erfüllung:** {avg_fulfillment:.1f}%\n"
                f"🎯 **Strategie:** {crawling_strategy.replace('_', ' ').title()}\n"
                f"📋 **Katalog:** {catalog_name}"
            )
            
            # Automatically save results to CSV
            self._save_results_to_csv(successful_results, catalog_name, crawling_strategy)
            
            # Show results preview
            self._display_results_preview()
            
        except Exception as e:
            st.error(f"❌ Fehler beim Crawling: {str(e)}")
            self.logger.error(f"Crawling process error: {str(e)}")
    
    def _display_results_preview(self) -> None:
        """Display a preview of crawling results."""
        if st.session_state.crawling_results:
            st.subheader("📊 Ergebnisse (Vorschau)")
            
            # Quick stats
            results = st.session_state.crawling_results
            successful = 0
            for r in results:
                if hasattr(r, 'success') and r.success:
                    successful += 1
                elif isinstance(r, dict) and r.get('success', False):
                    successful += 1
            total = len(results)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Organisationen", total)
            with col2:
                st.metric("Erfolgreich", successful)
            with col3:
                st.metric("Erfolgsrate", f"{(successful/total*100):.1f}%")
            
            st.info("📊 Vollständige Ergebnisse und Statistiken finden Sie auf der **Statistiken**-Seite.")
    
    def _save_results_to_csv(self, results: List, catalog_name: str, strategy: str) -> None:
        """Save evaluation results to CSV files automatically."""
        import pandas as pd
        from datetime import datetime
        import os
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Prepare detailed results data
            detailed_data = []
            
            for org_result in results:
                if hasattr(org_result, 'criteria_results'):
                    org_name = org_result.organization_name
                    base_url = org_result.base_url
                    
                    for criterion in org_result.criteria_results:
                        detailed_data.append({
                            'Organisation': org_name,
                            'Basis_URL': base_url,
                            'Kriterium_ID': criterion.criterion_id,
                            'Kriterium_Name': criterion.criterion_name,
                            'Erfüllt': 'Ja' if criterion.evaluation else 'Nein',
                            'Konfidenz': f"{criterion.confidence:.2f}",
                            'Begründung': criterion.justification,
                            'Quelle_URL': criterion.source_url,
                            'Beweis_Text': criterion.evidence_text[:200] + '...' if len(criterion.evidence_text) > 200 else criterion.evidence_text,
                            'Muster_Typ': criterion.pattern_type
                        })
            
            # Save detailed results
            if detailed_data:
                detailed_df = pd.DataFrame(detailed_data)
                detailed_filename = f"{output_dir}/bewertung_details_{catalog_name}_{timestamp}.csv"
                detailed_df.to_csv(detailed_filename, sep=';', index=False, encoding='utf-8-sig')
                st.success(f"📄 Detaillierte Bewertung gespeichert: `{detailed_filename}`")
            
            # Prepare summary statistics data
            summary_data = []
            
            for org_result in results:
                if hasattr(org_result, 'criteria_results'):
                    summary_data.append({
                        'Organisation': org_result.organization_name,
                        'Basis_URL': org_result.base_url,
                        'Gesamt_Kriterien': org_result.total_criteria,
                        'Erfüllte_Kriterien': org_result.fulfilled_criteria,
                        'Erfüllungsgrad_Prozent': f"{org_result.fulfillment_percentage:.1f}%",
                        'Durchschnittliche_Konfidenz': f"{org_result.average_confidence:.2f}",
                        'Katalog': catalog_name,
                        'Strategie': strategy,
                        'Bewertungsdatum': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # Save summary statistics
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_filename = f"{output_dir}/statistik_zusammenfassung_{catalog_name}_{timestamp}.csv"
                summary_df.to_csv(summary_filename, sep=';', index=False, encoding='utf-8-sig')
                st.success(f"📊 Statistik-Zusammenfassung gespeichert: `{summary_filename}`")
            
            # Prepare criteria-based statistics
            criteria_stats = []
            
            if detailed_data:
                criteria_df = pd.DataFrame(detailed_data)
                
                # Group by criteria and calculate statistics
                for criterion_id in criteria_df['Kriterium_ID'].unique():
                    criterion_data = criteria_df[criteria_df['Kriterium_ID'] == criterion_id]
                    
                    total_orgs = len(criterion_data)
                    fulfilled_count = len(criterion_data[criterion_data['Erfüllt'] == 'Ja'])
                    avg_confidence = criterion_data['Konfidenz'].astype(float).mean()
                    
                    criteria_stats.append({
                        'Kriterium_ID': criterion_id,
                        'Kriterium_Name': criterion_data['Kriterium_Name'].iloc[0],
                        'Anzahl_Organisationen': total_orgs,
                        'Erfüllte_Organisationen': fulfilled_count,
                        'Nicht_Erfüllte_Organisationen': total_orgs - fulfilled_count,
                        'Erfüllungsrate_Prozent': f"{(fulfilled_count / total_orgs * 100):.1f}%",
                        'Durchschnittliche_Konfidenz': f"{avg_confidence:.2f}",
                        'Katalog': catalog_name,
                        'Bewertungsdatum': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            # Save criteria statistics
            if criteria_stats:
                criteria_df = pd.DataFrame(criteria_stats)
                criteria_filename = f"{output_dir}/kriterien_statistik_{catalog_name}_{timestamp}.csv"
                criteria_df.to_csv(criteria_filename, sep=';', index=False, encoding='utf-8-sig')
                st.success(f"📈 Kriterien-Statistik gespeichert: `{criteria_filename}`")
            
            # Generate and save visualizations
            self._generate_visualizations(detailed_data, summary_data, criteria_stats, catalog_name, timestamp, output_dir)
            
            # Show file info
            st.info(
                f"💾 **Automatisch gespeichert:**\n\n"
                f"📄 **Detaillierte Bewertung:** {len(detailed_data)} Kriterien-Bewertungen\n"
                f"📊 **Statistik-Zusammenfassung:** {len(summary_data)} Organisationen\n"
                f"📈 **Kriterien-Statistik:** {len(criteria_stats)} Kriterien\n\n"
                f"📁 **Speicherort:** `{output_dir}/`"
            )
            
        except Exception as e:
            st.error(f"❌ Fehler beim Speichern der CSV-Dateien: {str(e)}")
            self.logger.error(f"CSV save error: {str(e)}")
    
    def _generate_visualizations(self, detailed_data: List, summary_data: List, criteria_stats: List, 
                           catalog_name: str, timestamp: str, output_dir: str) -> None:
        """Generate visualizations for the evaluation results."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            import pandas as pd
            import numpy as np
            import os
            
            # Set style for better looking plots
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Create visualizations directory
            viz_dir = f"{output_dir}/visualizations"
            os.makedirs(viz_dir, exist_ok=True)
            
            # 1. Organization fulfillment overview
            if summary_data:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                
                summary_df = pd.DataFrame(summary_data)
                
                # Handle different column name formats and extract numeric fulfillment percentage
                try:
                    if 'Erfüllungsgrad_Prozent' in summary_df.columns:
                        # Convert percentage strings to numeric values
                        summary_df['Erfüllungsgrad_Numeric'] = pd.to_numeric(
                            summary_df['Erfüllungsgrad_Prozent'].astype(str).str.replace('%', ''), 
                            errors='coerce'
                        )
                    elif 'fulfillment_rate' in summary_df.columns:
                        summary_df['Erfüllungsgrad_Numeric'] = pd.to_numeric(summary_df['fulfillment_rate'], errors='coerce')
                    else:
                        # Fallback: try to find any column with percentage values
                        pct_cols = [col for col in summary_df.columns if 'prozent' in col.lower() or 'rate' in col.lower()]
                        if pct_cols:
                            summary_df['Erfüllungsgrad_Numeric'] = pd.to_numeric(
                                summary_df[pct_cols[0]].astype(str).str.replace('%', ''), 
                                errors='coerce'
                            )
                        else:
                            st.warning("Keine Erfüllungsgrad-Spalte gefunden für Visualisierung")
                            return
                    
                    # Check if we have valid numeric data
                    if summary_df['Erfüllungsgrad_Numeric'].isna().all():
                        st.warning("Keine gültigen numerischen Werte für Erfüllungsgrad gefunden")
                        return
                        
                except Exception as e:
                    st.warning(f"Fehler beim Konvertieren der Erfüllungsgrad-Daten: {str(e)}")
                    return
                    
                # Bar chart of fulfillment rates
                ax1.bar(range(len(summary_df)), summary_df['Erfüllungsgrad_Numeric'], 
                       color='steelblue', alpha=0.7)
                ax1.set_xlabel('Organisationen')
                ax1.set_ylabel('Erfüllungsgrad (%)')
                ax1.set_title(f'Erfüllungsgrad nach Organisation\n({catalog_name.title()})')
                ax1.set_xticks(range(len(summary_df)))
                # Handle different organization column names
                org_col = 'Organisation' if 'Organisation' in summary_df.columns else 'organization_name'
                if org_col in summary_df.columns:
                    ax1.set_xticklabels([org[:20] + '...' if len(org) > 20 else org 
                                       for org in summary_df[org_col]], 
                                      rotation=45, ha='right')
                else:
                    ax1.set_xticklabels([f'Org {i+1}' for i in range(len(summary_df))], 
                                      rotation=45, ha='right')
                
                # Histogram of fulfillment distribution
                ax2.hist(summary_df['Erfüllungsgrad_Numeric'], bins=10, 
                        color='lightcoral', alpha=0.7, edgecolor='black')
                ax2.set_xlabel('Erfüllungsgrad (%)')
                ax2.set_ylabel('Anzahl Organisationen')
                ax2.set_title('Verteilung der Erfüllungsgrade')
                
                plt.tight_layout()
                plt.savefig(f"{viz_dir}/organisationen_uebersicht_{catalog_name}_{timestamp}.png", 
                           dpi=300, bbox_inches='tight')
                plt.close()
                
            # 2. Criteria performance overview
            if criteria_stats:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
                
                criteria_df = pd.DataFrame(criteria_stats)
                
                # Handle different column name formats for fulfillment rate
                if 'Erfüllungsrate_Prozent' in criteria_df.columns:
                    criteria_df['Erfüllungsrate_Numeric'] = criteria_df['Erfüllungsrate_Prozent'].astype(str).str.replace('%', '').astype(float)
                elif 'fulfillment_rate' in criteria_df.columns:
                    criteria_df['Erfüllungsrate_Numeric'] = criteria_df['fulfillment_rate']
                else:
                    # Fallback: try to find any column with rate values
                    rate_cols = [col for col in criteria_df.columns if 'rate' in col.lower() or 'prozent' in col.lower()]
                    if rate_cols:
                        criteria_df['Erfüllungsrate_Numeric'] = criteria_df[rate_cols[0]].astype(str).str.replace('%', '').astype(float)
                    else:
                        st.warning("Keine Erfüllungsrate-Spalte gefunden für Kriterien-Visualisierung")
                        return
                
                # Sort by fulfillment rate for better visualization
                criteria_df_sorted = criteria_df.sort_values('Erfüllungsrate_Numeric', ascending=True)
                
                # Horizontal bar chart of criteria fulfillment
                y_pos = np.arange(len(criteria_df_sorted))
                bars = ax1.barh(y_pos, criteria_df_sorted['Erfüllungsrate_Numeric'], 
                               color='mediumseagreen', alpha=0.7)
                
                # Add value labels on bars
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    ax1.text(width + 1, bar.get_y() + bar.get_height()/2, 
                            f'{width:.1f}%', ha='left', va='center', fontsize=8)
                
                ax1.set_yticks(y_pos)
                # Handle different criterion name column formats
                name_col = 'Kriterium_Name' if 'Kriterium_Name' in criteria_df_sorted.columns else 'criterion_name'
                if name_col in criteria_df_sorted.columns:
                    ax1.set_yticklabels([name[:30] + '...' if len(name) > 30 else name 
                                       for name in criteria_df_sorted[name_col]], fontsize=8)
                else:
                    ax1.set_yticklabels([f'Kriterium {i+1}' for i in range(len(criteria_df_sorted))], fontsize=8)
                ax1.set_xlabel('Erfüllungsrate (%)')
                ax1.set_title(f'Erfüllungsrate nach Kriterium\n({catalog_name.title()})')
                ax1.set_xlim(0, 105)
                
                # Confidence vs fulfillment scatter plot
                # Handle different confidence column formats
                conf_col = 'Durchschnittliche_Konfidenz' if 'Durchschnittliche_Konfidenz' in criteria_df.columns else 'average_confidence'
                if conf_col in criteria_df.columns:
                    criteria_df['Konfidenz_Numeric'] = criteria_df[conf_col].astype(float)
                else:
                    # Fallback: use zeros if no confidence data available
                    criteria_df['Konfidenz_Numeric'] = 0.0
                scatter = ax2.scatter(criteria_df['Konfidenz_Numeric'], 
                                    criteria_df['Erfüllungsrate_Numeric'],
                                    alpha=0.6, s=60, c='darkorange')
                
                ax2.set_xlabel('Durchschnittliche Konfidenz')
                ax2.set_ylabel('Erfüllungsrate (%)')
                ax2.set_title('Konfidenz vs. Erfüllungsrate')
                ax2.grid(True, alpha=0.3)
                
                plt.tight_layout()
                plt.savefig(f"{viz_dir}/kriterien_performance_{catalog_name}_{timestamp}.png", 
                           dpi=300, bbox_inches='tight')
                plt.close()
                
            # 3. Summary statistics visualization
            if summary_data and criteria_stats:
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
                
                summary_df = pd.DataFrame(summary_data)
                criteria_df = pd.DataFrame(criteria_stats)
                
                # Handle different column name formats and extract numeric fulfillment percentage
                try:
                    if 'Erfüllungsgrad_Prozent' in summary_df.columns:
                        # Convert percentage strings to numeric values
                        summary_df['Erfüllungsgrad_Numeric'] = pd.to_numeric(
                            summary_df['Erfüllungsgrad_Prozent'].astype(str).str.replace('%', ''), 
                            errors='coerce'
                        )
                    elif 'fulfillment_rate' in summary_df.columns:
                        summary_df['Erfüllungsgrad_Numeric'] = pd.to_numeric(summary_df['fulfillment_rate'], errors='coerce')
                    else:
                        # Fallback: try to find any column with percentage values
                        pct_cols = [col for col in summary_df.columns if 'prozent' in col.lower() or 'rate' in col.lower()]
                        if pct_cols:
                            summary_df['Erfüllungsgrad_Numeric'] = pd.to_numeric(
                                summary_df[pct_cols[0]].astype(str).str.replace('%', ''), 
                                errors='coerce'
                            )
                        else:
                            st.warning("Keine Erfüllungsgrad-Spalte gefunden für zusammenfassende Visualisierung")
                            return
                    
                    # Check if we have valid numeric data
                    if summary_df['Erfüllungsgrad_Numeric'].isna().all():
                        st.warning("Keine gültigen numerischen Werte für zusammenfassende Erfüllungsgrad-Visualisierung gefunden")
                        return
                        
                except Exception as e:
                    st.warning(f"Fehler beim Konvertieren der Erfüllungsgrad-Daten für zusammenfassende Visualisierung: {str(e)}")
                    return
                
                # Handle criteria_df column processing for Erfüllungsrate_Numeric
                try:
                    if 'Erfüllungsrate_Prozent' in criteria_df.columns:
                        # Convert percentage strings to numeric values
                        criteria_df['Erfüllungsrate_Numeric'] = pd.to_numeric(
                            criteria_df['Erfüllungsrate_Prozent'].astype(str).str.replace('%', ''), 
                            errors='coerce'
                        )
                    elif 'fulfillment_rate' in criteria_df.columns:
                        criteria_df['Erfüllungsrate_Numeric'] = pd.to_numeric(criteria_df['fulfillment_rate'], errors='coerce')
                    elif 'Erfüllungsrate' in criteria_df.columns:
                        criteria_df['Erfüllungsrate_Numeric'] = pd.to_numeric(
                            criteria_df['Erfüllungsrate'].astype(str).str.replace('%', ''), 
                            errors='coerce'
                        )
                    else:
                        # Fallback: try to find any column with rate values
                        rate_cols = [col for col in criteria_df.columns if 'rate' in col.lower() or 'prozent' in col.lower()]
                        if rate_cols:
                            criteria_df['Erfüllungsrate_Numeric'] = pd.to_numeric(
                                criteria_df[rate_cols[0]].astype(str).str.replace('%', ''), 
                                errors='coerce'
                            )
                        else:
                            st.warning("Keine Erfüllungsrate-Spalte gefunden für Kriterien-Visualisierung")
                            return
                    
                    # Check if we have valid numeric data for criteria
                    if criteria_df['Erfüllungsrate_Numeric'].isna().all():
                        st.warning("Keine gültigen numerischen Werte für Kriterien-Erfüllungsrate-Visualisierung gefunden")
                        return
                        
                except Exception as e:
                    st.warning(f"Fehler beim Konvertieren der Kriterien-Erfüllungsrate-Daten: {str(e)}")
                    return
                
                # Pie chart of overall fulfillment distribution
                fulfillment_ranges = ['0-25%', '26-50%', '51-75%', '76-100%']
                fulfillment_counts = [0, 0, 0, 0]
                
                for rate in summary_df['Erfüllungsgrad_Numeric']:
                    if rate <= 25:
                        fulfillment_counts[0] += 1
                    elif rate <= 50:
                        fulfillment_counts[1] += 1
                    elif rate <= 75:
                        fulfillment_counts[2] += 1
                    else:
                        fulfillment_counts[3] += 1
                
                colors = ['#ff9999', '#ffcc99', '#99ccff', '#99ff99']
                ax1.pie(fulfillment_counts, labels=fulfillment_ranges, autopct='%1.1f%%',
                       colors=colors, startangle=90)
                ax1.set_title('Verteilung der Erfüllungsgrade\n(Organisationen)')
                
                # Box plot of confidence values
                confidence_data = [float(conf) for conf in summary_df['Durchschnittliche_Konfidenz']]
                ax2.boxplot(confidence_data, patch_artist=True, 
                           boxprops=dict(facecolor='lightblue', alpha=0.7))
                ax2.set_ylabel('Konfidenz')
                ax2.set_title('Verteilung der Konfidenzwerte\n(Organisationen)')
                ax2.set_xticklabels(['Alle Organisationen'])
                
                # Top 10 best performing criteria
                top_criteria = criteria_df.nlargest(10, 'Erfüllungsrate_Numeric')
                ax3.barh(range(len(top_criteria)), top_criteria['Erfüllungsrate_Numeric'],
                        color='forestgreen', alpha=0.7)
                ax3.set_yticks(range(len(top_criteria)))
                ax3.set_yticklabels([name[:25] + '...' if len(name) > 25 else name 
                                   for name in top_criteria['Kriterium_Name']], fontsize=8)
                ax3.set_xlabel('Erfüllungsrate (%)')
                ax3.set_title('Top 10 Kriterien\n(Höchste Erfüllungsrate)')
                
                # Bottom 10 performing criteria
                bottom_criteria = criteria_df.nsmallest(10, 'Erfüllungsrate_Numeric')
                ax4.barh(range(len(bottom_criteria)), bottom_criteria['Erfüllungsrate_Numeric'],
                        color='crimson', alpha=0.7)
                ax4.set_yticks(range(len(bottom_criteria)))
                ax4.set_yticklabels([name[:25] + '...' if len(name) > 25 else name 
                                   for name in bottom_criteria['Kriterium_Name']], fontsize=8)
                ax4.set_xlabel('Erfüllungsrate (%)')
                ax4.set_title('Bottom 10 Kriterien\n(Niedrigste Erfüllungsrate)')
                
                plt.tight_layout()
                plt.savefig(f"{viz_dir}/zusammenfassung_statistik_{catalog_name}_{timestamp}.png", 
                           dpi=300, bbox_inches='tight')
                plt.close()
                
            st.success(f"📊 Visualisierungen gespeichert in: `{viz_dir}/`")
            
        except ImportError:
            st.warning("⚠️ Matplotlib/Seaborn nicht verfügbar. Visualisierungen werden übersprungen.")
            self.logger.warning("Visualization libraries not available")
        except Exception as e:
            st.warning(f"⚠️ Fehler beim Erstellen der Visualisierungen: {str(e)}")
            self.logger.error(f"Visualization error: {str(e)}")
