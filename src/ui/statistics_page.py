"""
Statistics page UI components for the Offenheitscrawler.
"""

import streamlit as st
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from src.statistics.visualizations import StatisticsVisualizer


class StatisticsPageUI:
    """UI components for the statistics page."""
    
    def __init__(self, logger):
        """Initialize statistics page UI."""
        self.logger = logger
        self.visualizer = StatisticsVisualizer()
    
    def show_statistics_page(self) -> None:
        """Display statistics and analysis page."""
        st.title("📊 Statistiken & Analyse")
        
        # Check if we have results
        if not st.session_state.get('crawling_results'):
            st.info("ℹ️ Keine Crawling-Ergebnisse verfügbar. Führen Sie zuerst einen Crawling-Prozess durch.")
            return
        
        results = st.session_state.crawling_results
        
        # Overview metrics
        self._show_overview_metrics(results)
        
        st.divider()
        
        # Detailed statistics
        if st.session_state.get('evaluation_results'):
            self._show_detailed_statistics()
        else:
            self._show_simple_statistics(results)
        
        st.divider()
        
        # Visualizations section
        self._show_visualizations_section()
        
        st.divider()
        
        # Export section
        self._show_export_section(results)
    
    def _show_overview_metrics(self, results: List[Dict[str, Any]]) -> None:
        """Show overview metrics."""
        st.subheader("📈 Übersicht")
        
        # Calculate basic metrics
        total_orgs = len(results)
        
        # Count successful organizations (handle both dict and object types)
        successful_orgs = 0
        for r in results:
            if hasattr(r, 'success') and r.success:
                successful_orgs += 1
            elif isinstance(r, dict) and r.get('success', False):
                successful_orgs += 1
            elif hasattr(r, 'criteria_results'):  # OrganizationEvaluation objects are successful
                successful_orgs += 1
        
        failed_orgs = total_orgs - successful_orgs
        success_rate = (successful_orgs / total_orgs * 100) if total_orgs > 0 else 0
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Organisationen gesamt",
                total_orgs,
                help="Gesamtanzahl der verarbeiteten Organisationen"
            )
        
        with col2:
            st.metric(
                "Erfolgreich",
                successful_orgs,
                help="Anzahl erfolgreich gecrawlter Organisationen"
            )
        
        with col3:
            st.metric(
                "Fehlgeschlagen",
                failed_orgs,
                delta=f"-{failed_orgs}" if failed_orgs > 0 else None,
                delta_color="inverse",
                help="Anzahl fehlgeschlagener Crawling-Versuche"
            )
        
        with col4:
            st.metric(
                "Erfolgsrate",
                f"{success_rate:.1f}%",
                help="Prozentsatz erfolgreich gecrawlter Organisationen"
            )
        
        # Show failed organizations if any
        if failed_orgs > 0:
            with st.expander(f"❌ Fehlgeschlagene Organisationen ({failed_orgs})"):
                failed_results = []
                for r in results:
                    # Check if organization failed (handle both dict and object types)
                    is_failed = False
                    if hasattr(r, 'success') and not r.success:
                        is_failed = True
                    elif isinstance(r, dict) and not r.get('success', False):
                        is_failed = True
                    elif not hasattr(r, 'criteria_results'):  # OrganizationEvaluation objects without results are failed
                        is_failed = True
                    
                    if is_failed:
                        failed_results.append(r)
                
                for result in failed_results:
                    # Get organization name and error (handle both dict and object types)
                    if hasattr(result, 'organization_name'):
                        org_name = result.organization_name
                    elif isinstance(result, dict):
                        org_name = result.get('organization_name', 'Unbekannt')
                    else:
                        org_name = 'Unbekannt'
                    
                    if hasattr(result, 'error'):
                        error_msg = result.error
                    elif isinstance(result, dict):
                        error_msg = result.get('error', 'Unbekannter Fehler')
                    else:
                        error_msg = 'Unbekannter Fehler'
                    
                    st.error(f"**{org_name}**: {error_msg}")
    
    def _show_detailed_statistics(self) -> None:
        """Show detailed statistics when evaluation results are available."""
        st.subheader("📊 Detaillierte Auswertung")
        
        evaluation_results = st.session_state.evaluation_results
        catalog_name = st.session_state.get('selected_catalog', 'Unbekannt')
        
        st.info(f"📋 Verwendeter Kriterienkatalog: **{catalog_name}**")
        
        # Create visualizations
        try:
            # Criteria fulfillment overview
            fig_overview = self.visualizer.create_criteria_overview(evaluation_results)
            if fig_overview:
                st.plotly_chart(fig_overview, use_container_width=True)
            
            # Organization comparison
            fig_comparison = self.visualizer.create_organization_comparison(evaluation_results)
            if fig_comparison:
                st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Dimension analysis
            fig_dimensions = self.visualizer.create_dimension_analysis(evaluation_results)
            if fig_dimensions:
                st.plotly_chart(fig_dimensions, use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Fehler beim Erstellen der Visualisierungen: {str(e)}")
            self.logger.error(f"Visualization error: {str(e)}")
        
        # Detailed results table
        self._show_detailed_results_table(evaluation_results)
    
    def _show_simple_statistics(self, results: List[Dict[str, Any]]) -> None:
        """Show simple statistics when detailed evaluation results are not available."""
        st.subheader("📊 Einfache Statistiken")
        
        # Extract basic crawling statistics
        crawling_stats = []
        
        for result in results:
            if result.get('success', False):
                org_name = result.get('organization_name', 'Unbekannt')
                pages_crawled = len(result.get('pages', []))
                successful_pages = len([p for p in result.get('pages', []) if p.get('success', False)])
                
                crawling_stats.append({
                    'Organisation': org_name,
                    'Seiten gecrawlt': pages_crawled,
                    'Erfolgreich': successful_pages,
                    'Erfolgsrate': f"{(successful_pages/pages_crawled*100):.1f}%" if pages_crawled > 0 else "0%"
                })
        
        if crawling_stats:
            df_stats = pd.DataFrame(crawling_stats)
            st.dataframe(df_stats, use_container_width=True)
            
            # Simple charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Pages per organization
                fig_pages = self.visualizer.create_simple_bar_chart(
                    df_stats, 'Organisation', 'Seiten gecrawlt',
                    'Anzahl gecrawlter Seiten pro Organisation'
                )
                if fig_pages:
                    st.plotly_chart(fig_pages, use_container_width=True)
            
            with col2:
                # Success rate distribution
                success_rates = [float(rate.replace('%', '')) for rate in df_stats['Erfolgsrate']]
                fig_success = self.visualizer.create_histogram(
                    success_rates, 'Erfolgsrate (%)', 'Verteilung der Erfolgsraten'
                )
                if fig_success:
                    st.plotly_chart(fig_success, use_container_width=True)
        else:
            st.warning("⚠️ Keine auswertbaren Crawling-Daten verfügbar.")
    
    def _show_detailed_results_table(self, evaluation_results: List[Dict[str, Any]]) -> None:
        """Show detailed results in a table format."""
        st.subheader("📋 Detaillierte Ergebnisse")
        
        # Prepare data for table
        table_data = []
        
        for result in evaluation_results:
            # Handle both dict and OrganizationEvaluation objects
            if hasattr(result, 'organization_name'):
                # OrganizationEvaluation object
                org_name = result.organization_name
                org_url = result.base_url  # Correct attribute name
                total_criteria = result.total_criteria
                fulfilled_criteria = result.fulfilled_criteria
                fulfillment_rate = result.fulfillment_percentage
                avg_confidence = result.average_confidence
            else:
                # Dictionary object
                org_name = result.get('organization_name', 'Unbekannt')
                org_url = result.get('organization_url', 'Unbekannt')
                total_criteria = result.get('total_criteria', 0)
                fulfilled_criteria = result.get('fulfilled_criteria', 0)
                fulfillment_rate = result.get('fulfillment_rate', 0.0)
                avg_confidence = result.get('average_confidence', 0.0)
            
            # Get additional info based on object type
            if hasattr(result, 'organization_name'):
                # OrganizationEvaluation object
                base_url = org_url  # Already extracted above
                pages_crawled = 0  # Not available in OrganizationEvaluation
            else:
                # Dictionary object
                base_url = result.get('base_url', '')
                pages_crawled = len(result.get('pages', []))
            
            table_data.append({
                'Organisation': org_name,
                'Kriterien gesamt': total_criteria,
                'Erfüllt': fulfilled_criteria,
                'Erfüllungsgrad': f"{fulfillment_rate:.1f}%",
                'URL': base_url,
                'Seiten gecrawlt': pages_crawled
            })
        
        if table_data:
            df_results = pd.DataFrame(table_data)
            st.dataframe(df_results, use_container_width=True)
            
            # Expandable detailed view for each organization
            st.subheader("🔍 Detailansicht pro Organisation")
            
            for result in evaluation_results:
                # Handle both dict and OrganizationEvaluation objects
                if hasattr(result, 'organization_name'):
                    org_name = result.organization_name
                else:
                    org_name = result.get('organization_name', 'Unbekannt')
                
                with st.expander(f"📊 {org_name}"):
                    self._show_organization_details(result)
    
    def _show_organization_details(self, result) -> None:
        """Show detailed information for a single organization."""
        # Handle both dict and OrganizationEvaluation objects
        if hasattr(result, 'organization_name'):
            # OrganizationEvaluation object
            org_name = result.organization_name
            base_url = result.base_url
            criteria_results = result.criteria_results  # List of CriterionEvaluation objects
            pages_crawled = 0  # Not available in OrganizationEvaluation
        else:
            # Dictionary object
            org_name = result.get('organization_name', 'Unbekannt')
            base_url = result.get('base_url', '')
            criteria_results = result.get('criteria_results', {})
            pages_crawled = len(result.get('pages', []))
        
        # Basic info
        st.write(f"**URL:** {base_url}")
        st.write(f"**Seiten gecrawlt:** {pages_crawled}")
        
        # Criteria breakdown
        if criteria_results:
            criteria_df = []
            
            if hasattr(result, 'organization_name'):
                # OrganizationEvaluation - criteria_results is a list of CriterionEvaluation objects
                for criterion_eval in criteria_results:
                    criteria_df.append({
                        'Kriterium': criterion_eval.criterion_name,
                        'Erfüllt': '✅' if criterion_eval.evaluation else '❌',
                        'Konfidenz': f"{criterion_eval.confidence:.2f}",
                        'Quelle': criterion_eval.source_url if hasattr(criterion_eval, 'source_url') else 'Unbekannt',
                        'Begründung': (criterion_eval.justification[:100] + '...' 
                                     if len(criterion_eval.justification) > 100 
                                     else criterion_eval.justification)
                    })
            else:
                # Dictionary - criteria_results is a dict
                for criterion_id, criterion_result in criteria_results.items():
                    criteria_df.append({
                        'Kriterium': criterion_result.get('name', criterion_id),
                        'Erfüllt': '✅' if criterion_result.get('fulfilled', False) else '❌',
                        'Konfidenz': f"{criterion_result.get('confidence', 0):.2f}",
                        'Quelle': criterion_result.get('source', 'Unbekannt'),
                        'Begründung': (criterion_result.get('justification', '')[:100] + '...' 
                                     if len(criterion_result.get('justification', '')) > 100 
                                     else criterion_result.get('justification', ''))
                    })
            
            if criteria_df:
                df_criteria = pd.DataFrame(criteria_df)
                st.dataframe(df_criteria, use_container_width=True)
        else:
            st.warning("⚠️ Keine Kriterienauswertung verfügbar.")
    
    def _show_visualizations_section(self) -> None:
        """Show saved visualizations from recent crawling runs."""
        st.subheader("📊 Visualisierungen")
        
        import os
        from pathlib import Path
        
        # Check for visualizations directory
        viz_dir = Path("output/visualizations")
        
        if not viz_dir.exists():
            st.info("📊 Keine Visualisierungen verfügbar. Führen Sie einen Crawling-Prozess durch, um automatisch Grafiken zu generieren.")
            return
        
        # Get all PNG files in visualizations directory
        viz_files = list(viz_dir.glob("*.png"))
        
        if not viz_files:
            st.info("📊 Keine Visualisierungen gefunden. Führen Sie einen Crawling-Prozess durch, um automatisch Grafiken zu generieren.")
            return
        
        # Sort files by modification time (newest first)
        viz_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Group files by catalog and timestamp
        file_groups = {}
        for file in viz_files:
            # Extract catalog and timestamp from filename
            # Format: type_catalog_timestamp.png
            parts = file.stem.split('_')
            if len(parts) >= 3:
                catalog = parts[-2]  # Second to last part is catalog
                timestamp = parts[-1]  # Last part is timestamp
                key = f"{catalog}_{timestamp}"
                
                if key not in file_groups:
                    file_groups[key] = []
                file_groups[key].append(file)
        
        if not file_groups:
            st.info("📊 Keine gültigen Visualisierungen gefunden.")
            return
        
        # Display file groups
        st.write(f"📁 **{len(file_groups)} Visualisierungs-Sets gefunden**")
        
        # Create tabs for different visualization sets
        if len(file_groups) == 1:
            # Single set - show directly
            key, files = next(iter(file_groups.items()))
            catalog, timestamp = key.split('_', 1)
            
            st.write(f"📊 **Katalog:** {catalog.title()} | **Erstellt:** {timestamp}")
            self._display_visualization_set(files)
        else:
            # Multiple sets - use tabs
            tab_names = []
            tab_files = []
            
            for key, files in file_groups.items():
                catalog, timestamp = key.split('_', 1)
                tab_names.append(f"{catalog.title()} ({timestamp})")
                tab_files.append(files)
            
            tabs = st.tabs(tab_names)
            
            for tab, files in zip(tabs, tab_files):
                with tab:
                    self._display_visualization_set(files)
    
    def _display_visualization_set(self, files: List[Path]) -> None:
        """Display a set of visualization files."""
        # Sort files by type for consistent display order
        file_order = {
            'organisationen_uebersicht': 1,
            'kriterien_performance': 2,
            'zusammenfassung_statistik': 3
        }
        
        def get_file_priority(file_path):
            for key, priority in file_order.items():
                if key in file_path.stem:
                    return priority
            return 999
        
        files.sort(key=get_file_priority)
        
        for file in files:
            # Extract visualization type from filename
            if 'organisationen_uebersicht' in file.stem:
                st.subheader("🏢 Organisationen-Übersicht")
                st.write("Erfüllungsgrad und Verteilung nach Organisationen")
            elif 'kriterien_performance' in file.stem:
                st.subheader("🎯 Kriterien-Performance")
                st.write("Erfüllungsrate und Konfidenz nach Kriterien")
            elif 'zusammenfassung_statistik' in file.stem:
                st.subheader("📊 Zusammenfassende Statistiken")
                st.write("Top/Bottom Kriterien und Gesamtverteilungen")
            
            # Display the image
            try:
                st.image(str(file), use_container_width=True)
                
                # Add download button
                with open(file, 'rb') as f:
                    st.download_button(
                        label=f"💾 {file.name} herunterladen",
                        data=f.read(),
                        file_name=file.name,
                        mime="image/png",
                        key=f"download_{file.stem}"
                    )
                    
            except Exception as e:
                st.error(f"❌ Fehler beim Laden der Visualisierung {file.name}: {str(e)}")
            
            st.divider()
    
    def _show_export_section(self, results: List[Dict[str, Any]]) -> None:
        """Show export options."""
        st.subheader("💾 Export")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Generate detailed CSV report
            if st.button("📊 Detaillierten CSV-Bericht generieren", use_container_width=True):
                self._generate_detailed_report(results)
        
        with col2:
            # Generate statistics summary
            if st.button("📈 Statistik-Zusammenfassung (JSON)", use_container_width=True):
                self._generate_statistics_summary(results)
    
    def _generate_detailed_report(self, results: List[Dict[str, Any]]) -> None:
        """Generate detailed CSV report."""
        try:
            # Get export settings
            export_settings = st.session_state.get('export_settings', {})
            delimiter = export_settings.get('csv_delimiter', ';')
            date_format = export_settings.get('date_format', '%Y-%m-%d %H:%M:%S')
            encoding = export_settings.get('export_encoding', 'utf-8')
            
            # Prepare detailed data
            detailed_data = []
            
            for result in results:
                # Get organization details (handle both dict and object types)
                if hasattr(result, 'organization_name'):
                    org_name = result.organization_name
                elif isinstance(result, dict):
                    org_name = result.get('organization_name', 'Unbekannt')
                else:
                    org_name = 'Unbekannt'
                
                if hasattr(result, 'base_url'):
                    base_url = result.base_url
                elif isinstance(result, dict):
                    base_url = result.get('base_url', '')
                else:
                    base_url = ''
                
                # Check success status
                success = False
                if hasattr(result, 'success') and result.success:
                    success = True
                elif isinstance(result, dict) and result.get('success', False):
                    success = True
                elif hasattr(result, 'criteria_results'):
                    success = True
                
                # Handle criteria results for both dict and OrganizationEvaluation objects
                if hasattr(result, 'criteria_results') and result.criteria_results:
                    # OrganizationEvaluation object
                    for criterion_result in result.criteria_results:
                        detailed_data.append({
                            'Organisation': org_name,
                            'URL': base_url,
                            'Kriterium_ID': criterion_result.criterion_id,
                            'Kriterium_Name': criterion_result.criterion_name,
                            'Erfüllt': 'Ja' if criterion_result.evaluation else 'Nein',
                            'Konfidenz': criterion_result.confidence,
                            'Quelle': criterion_result.source_url or '',
                            'Begründung': criterion_result.justification or '',
                            'Timestamp': datetime.now().strftime(date_format)
                        })
                elif isinstance(result, dict) and success and 'criteria_results' in result:
                    # Dictionary result
                    for criterion_id, criterion_result in result['criteria_results'].items():
                        detailed_data.append({
                            'Organisation': org_name,
                            'URL': base_url,
                            'Kriterium_ID': criterion_id,
                            'Kriterium_Name': criterion_result.get('name', ''),
                            'Erfüllt': 'Ja' if criterion_result.get('fulfilled', False) else 'Nein',
                            'Konfidenz': criterion_result.get('confidence', 0),
                            'Quelle': criterion_result.get('source', ''),
                            'Begründung': criterion_result.get('justification', ''),
                            'Timestamp': datetime.now().strftime(date_format)
                        })
                else:
                    # Basic result for failed crawls
                    if hasattr(result, 'error'):
                        error_msg = result.error
                    elif isinstance(result, dict):
                        error_msg = result.get('error', 'Crawling fehlgeschlagen')
                    else:
                        error_msg = 'Crawling fehlgeschlagen'
                    
                    detailed_data.append({
                        'Organisation': org_name,
                        'URL': base_url,
                        'Kriterium_ID': '',
                        'Kriterium_Name': '',
                        'Erfüllt': 'Nein',
                        'Konfidenz': 0,
                        'Quelle': '',
                        'Begründung': error_msg,
                        'Timestamp': datetime.now().strftime(date_format)
                    })
            
            if detailed_data:
                df_detailed = pd.DataFrame(detailed_data)
                csv_data = df_detailed.to_csv(sep=delimiter, index=False, encoding=encoding)
                
                st.download_button(
                    label="📥 CSV-Bericht herunterladen",
                    data=csv_data,
                    file_name=f"offenheitscrawler_detailbericht_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                st.success("✅ Detaillierter CSV-Bericht erstellt!")
            else:
                st.warning("⚠️ Keine Daten für den Export verfügbar.")
                
        except Exception as e:
            st.error(f"❌ Fehler beim Erstellen des CSV-Berichts: {str(e)}")
            self.logger.error(f"CSV export error: {str(e)}")
    
    def _generate_statistics_summary(self, results: List[Dict[str, Any]]) -> None:
        """Generate statistics summary as JSON."""
        try:
            # Calculate summary statistics
            total_orgs = len(results)
            
            # Count successful organizations (handle both dict and object types)
            successful_orgs = 0
            for r in results:
                if hasattr(r, 'success') and r.success:
                    successful_orgs += 1
                elif isinstance(r, dict) and r.get('success', False):
                    successful_orgs += 1
                elif hasattr(r, 'criteria_results'):  # OrganizationEvaluation objects are successful
                    successful_orgs += 1
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_organizations': total_orgs,
                'successful_crawls': successful_orgs,
                'success_rate': (successful_orgs / total_orgs * 100) if total_orgs > 0 else 0,
                'catalog_used': st.session_state.get('selected_catalog', 'Unbekannt'),
                'organizations': []
            }
            
            # Add organization details
            for result in results:
                # Get organization details (handle both dict and object types)
                if hasattr(result, 'organization_name'):
                    org_name = result.organization_name
                elif isinstance(result, dict):
                    org_name = result.get('organization_name', 'Unbekannt')
                else:
                    org_name = 'Unbekannt'
                
                if hasattr(result, 'base_url'):
                    base_url = result.base_url
                elif isinstance(result, dict):
                    base_url = result.get('base_url', '')
                else:
                    base_url = ''
                
                # Check success status
                is_success = False
                if hasattr(result, 'success') and result.success:
                    is_success = True
                elif isinstance(result, dict) and result.get('success', False):
                    is_success = True
                elif hasattr(result, 'criteria_results'):
                    is_success = True
                
                # Get pages count
                pages_count = 0
                if hasattr(result, 'pages'):
                    pages_count = len(result.pages) if result.pages else 0
                elif isinstance(result, dict) and 'pages' in result:
                    pages_count = len(result['pages']) if result['pages'] else 0
                
                org_summary = {
                    'name': org_name,
                    'url': base_url,
                    'success': is_success,
                    'pages_crawled': pages_count,
                }
                
                # Add criteria details if available
                if hasattr(result, 'criteria_results') and result.criteria_results:
                    criteria_results = result.criteria_results
                    total_criteria = len(criteria_results)
                    fulfilled_criteria = sum(1 for c in criteria_results if c.evaluation)
                    
                    org_summary.update({
                        'total_criteria': total_criteria,
                        'fulfilled_criteria': fulfilled_criteria,
                        'fulfillment_rate': (fulfilled_criteria / total_criteria * 100) if total_criteria > 0 else 0
                    })
                elif isinstance(result, dict) and result.get('success', False) and 'criteria_results' in result:
                    criteria_results = result['criteria_results']
                    total_criteria = len(criteria_results)
                    fulfilled_criteria = len([c for c in criteria_results.values() if c.get('fulfilled', False)])
                    
                    org_summary.update({
                        'total_criteria': total_criteria,
                        'fulfilled_criteria': fulfilled_criteria,
                        'fulfillment_rate': (fulfilled_criteria / total_criteria * 100) if total_criteria > 0 else 0
                    })
                
                summary['organizations'].append(org_summary)
            
            # Create JSON download
            json_data = json.dumps(summary, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="📥 JSON-Zusammenfassung herunterladen",
                data=json_data,
                file_name=f"offenheitscrawler_statistiken_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
            
            st.success("✅ Statistik-Zusammenfassung erstellt!")
            
        except Exception as e:
            st.error(f"❌ Fehler beim Erstellen der Statistik-Zusammenfassung: {str(e)}")
            self.logger.error(f"Statistics summary error: {str(e)}")
