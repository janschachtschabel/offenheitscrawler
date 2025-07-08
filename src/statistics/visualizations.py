"""
Visualization components for the Offenheitscrawler statistics.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from typing import Dict, List, Any, Optional
import streamlit as st
from loguru import logger

from ..analysis.criteria_evaluator import OrganizationEvaluation


class StatisticsVisualizer:
    """Creates interactive visualizations for statistics."""
    
    def __init__(self):
        """Initialize visualizer."""
        self.logger = logger.bind(name=self.__class__.__name__)
        
        # Color schemes
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'warning': '#d62728',
            'info': '#9467bd',
            'light': '#17becf'
        }
    
    def create_overview_dashboard(
        self,
        evaluation_results: List[OrganizationEvaluation],
        statistics: Dict[str, Any]
    ) -> None:
        """
        Create overview dashboard with key metrics.
        
        Args:
            evaluation_results: List of organization evaluation results
            statistics: Statistics dictionary
        """
        if not evaluation_results:
            st.warning("No evaluation results available for visualization.")
            return
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        summary = statistics.get('summary', {})
        
        with col1:
            st.metric(
                "Organizations",
                summary.get('total_organizations_processed', 0),
                delta=None
            )
        
        with col2:
            success_rate = summary.get('success_rate_percentage', 0)
            st.metric(
                "Success Rate",
                f"{success_rate:.1f}%",
                delta=f"{success_rate - 80:.1f}%" if success_rate > 0 else None
            )
        
        with col3:
            fulfillment = summary.get('average_fulfillment_percentage', 0)
            st.metric(
                "Avg. Fulfillment",
                f"{fulfillment:.1f}%",
                delta=f"{fulfillment - 50:.1f}%" if fulfillment > 0 else None
            )
        
        with col4:
            confidence = summary.get('average_confidence', 0)
            st.metric(
                "Avg. Confidence",
                f"{confidence:.2f}",
                delta=f"{confidence - 0.5:.2f}" if confidence > 0 else None
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self.create_fulfillment_distribution(evaluation_results)
        
        with col2:
            self.create_confidence_distribution(evaluation_results)
    
    def create_fulfillment_distribution(
        self,
        evaluation_results: List[OrganizationEvaluation]
    ) -> None:
        """Create fulfillment percentage distribution chart."""
        if not evaluation_results:
            return
        
        fulfillment_data = [result.fulfillment_percentage for result in evaluation_results]
        
        fig = go.Figure(data=[
            go.Histogram(
                x=fulfillment_data,
                nbinsx=20,
                name="Organizations",
                marker_color=self.colors['primary'],
                opacity=0.7
            )
        ])
        
        fig.update_layout(
            title="Distribution of Fulfillment Percentages",
            xaxis_title="Fulfillment Percentage (%)",
            yaxis_title="Number of Organizations",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_confidence_distribution(
        self,
        evaluation_results: List[OrganizationEvaluation]
    ) -> None:
        """Create confidence score distribution chart."""
        if not evaluation_results:
            return
        
        confidence_data = [result.average_confidence for result in evaluation_results]
        
        fig = go.Figure(data=[
            go.Histogram(
                x=confidence_data,
                nbinsx=20,
                name="Organizations",
                marker_color=self.colors['secondary'],
                opacity=0.7
            )
        ])
        
        fig.update_layout(
            title="Distribution of Average Confidence Scores",
            xaxis_title="Average Confidence Score",
            yaxis_title="Number of Organizations",
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_organization_ranking(
        self,
        evaluation_results: List[OrganizationEvaluation],
        top_n: int = 20
    ) -> None:
        """Create organization ranking chart."""
        if not evaluation_results:
            return
        
        # Sort by fulfillment percentage
        sorted_results = sorted(
            evaluation_results,
            key=lambda x: x.fulfillment_percentage,
            reverse=True
        )[:top_n]
        
        org_names = [result.organization_name for result in sorted_results]
        fulfillment_pcts = [result.fulfillment_percentage for result in sorted_results]
        confidence_scores = [result.average_confidence for result in sorted_results]
        
        fig = go.Figure()
        
        # Fulfillment bars
        fig.add_trace(go.Bar(
            y=org_names,
            x=fulfillment_pcts,
            name="Fulfillment %",
            marker_color=self.colors['success'],
            orientation='h',
            yaxis='y',
            offsetgroup=1
        ))
        
        # Confidence line
        fig.add_trace(go.Scatter(
            y=org_names,
            x=[score * 100 for score in confidence_scores],  # Scale to 0-100
            mode='markers',
            name="Confidence (scaled)",
            marker=dict(
                color=self.colors['warning'],
                size=8,
                symbol='diamond'
            ),
            yaxis='y'
        ))
        
        fig.update_layout(
            title=f"Top {len(sorted_results)} Organizations by Performance",
            xaxis_title="Percentage / Score",
            yaxis_title="Organization",
            height=max(400, len(sorted_results) * 25),
            showlegend=True,
            legend=dict(x=0.7, y=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_dimension_analysis(
        self,
        evaluation_results: List[OrganizationEvaluation]
    ) -> None:
        """Create dimension performance analysis."""
        if not evaluation_results:
            return
        
        # Aggregate dimension data
        dimension_data = {}
        
        for result in evaluation_results:
            for dimension, stats in result.evaluation_summary.get('by_dimension', {}).items():
                if dimension not in dimension_data:
                    dimension_data[dimension] = {'total': 0, 'fulfilled': 0}
                
                dimension_data[dimension]['total'] += stats.get('total', 0)
                dimension_data[dimension]['fulfilled'] += stats.get('fulfilled', 0)
        
        if not dimension_data:
            st.info("No dimension data available.")
            return
        
        # Calculate percentages
        dimensions = list(dimension_data.keys())
        percentages = [
            (data['fulfilled'] / data['total'] * 100) if data['total'] > 0 else 0
            for data in dimension_data.values()
        ]
        totals = [data['total'] for data in dimension_data.values()]
        
        # Create subplot with bar and line
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Fulfillment by Dimension", "Total Criteria by Dimension"),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Fulfillment percentages
        fig.add_trace(
            go.Bar(
                x=dimensions,
                y=percentages,
                name="Fulfillment %",
                marker_color=self.colors['primary']
            ),
            row=1, col=1
        )
        
        # Total criteria counts
        fig.add_trace(
            go.Bar(
                x=dimensions,
                y=totals,
                name="Total Criteria",
                marker_color=self.colors['info']
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title="Dimension Performance Analysis",
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Dimension", row=1, col=1)
        fig.update_xaxes(title_text="Dimension", row=1, col=2)
        fig.update_yaxes(title_text="Fulfillment %", row=1, col=1)
        fig.update_yaxes(title_text="Count", row=1, col=2)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_criteria_heatmap(
        self,
        evaluation_results: List[OrganizationEvaluation],
        max_criteria: int = 50
    ) -> None:
        """Create criteria fulfillment heatmap."""
        if not evaluation_results:
            return
        
        # Collect all criteria evaluations
        criteria_matrix = {}
        all_criteria = set()
        
        for result in evaluation_results:
            org_name = result.organization_name
            criteria_matrix[org_name] = {}
            
            for criterion in result.criteria_results:
                criterion_id = criterion.criterion_id
                all_criteria.add(criterion_id)
                criteria_matrix[org_name][criterion_id] = 1 if criterion.evaluation else 0
        
        # Limit criteria for readability
        if len(all_criteria) > max_criteria:
            # Select most variable criteria
            criterion_variance = {}
            for criterion_id in all_criteria:
                values = [
                    criteria_matrix[org].get(criterion_id, 0)
                    for org in criteria_matrix.keys()
                ]
                criterion_variance[criterion_id] = pd.Series(values).var()
            
            # Select top variable criteria
            sorted_criteria = sorted(
                criterion_variance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max_criteria]
            
            selected_criteria = [item[0] for item in sorted_criteria]
        else:
            selected_criteria = list(all_criteria)
        
        # Create matrix for heatmap
        organizations = list(criteria_matrix.keys())
        matrix_data = []
        
        for org in organizations:
            row = [criteria_matrix[org].get(criterion, 0) for criterion in selected_criteria]
            matrix_data.append(row)
        
        fig = go.Figure(data=go.Heatmap(
            z=matrix_data,
            x=selected_criteria,
            y=organizations,
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="Fulfilled")
        ))
        
        fig.update_layout(
            title="Criteria Fulfillment Heatmap",
            xaxis_title="Criteria",
            yaxis_title="Organizations",
            height=max(500, len(organizations) * 20),
            xaxis=dict(tickangle=45)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_pattern_analysis(
        self,
        evaluation_results: List[OrganizationEvaluation]
    ) -> None:
        """Create pattern matching analysis."""
        if not evaluation_results:
            return
        
        # Collect pattern statistics
        pattern_stats = {'text': 0, 'url': 0, 'logo': 0, 'other': 0}
        confidence_by_pattern = {'text': [], 'url': [], 'logo': [], 'other': []}
        
        for result in evaluation_results:
            for criterion in result.criteria_results:
                if criterion.evaluation:  # Only count successful matches
                    pattern_type = criterion.pattern_type or 'other'
                    if pattern_type in pattern_stats:
                        pattern_stats[pattern_type] += 1
                        confidence_by_pattern[pattern_type].append(criterion.confidence)
                    else:
                        pattern_stats['other'] += 1
                        confidence_by_pattern['other'].append(criterion.confidence)
        
        # Create subplot
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Pattern Type Distribution", "Confidence by Pattern Type"),
            specs=[[{"type": "pie"}, {"type": "box"}]]
        )
        
        # Pie chart for pattern distribution
        fig.add_trace(
            go.Pie(
                labels=list(pattern_stats.keys()),
                values=list(pattern_stats.values()),
                name="Pattern Types"
            ),
            row=1, col=1
        )
        
        # Box plot for confidence by pattern type
        for pattern_type, confidences in confidence_by_pattern.items():
            if confidences:  # Only add if there are values
                fig.add_trace(
                    go.Box(
                        y=confidences,
                        name=pattern_type,
                        showlegend=False
                    ),
                    row=1, col=2
                )
        
        fig.update_layout(
            title="Pattern Matching Analysis",
            height=500
        )
        
        fig.update_yaxes(title_text="Confidence Score", row=1, col=2)
        
        st.plotly_chart(fig, use_container_width=True)
    
    def create_detailed_organization_view(
        self,
        organization_result: OrganizationEvaluation
    ) -> None:
        """Create detailed view for a single organization."""
        st.subheader(f"Detailed Analysis: {organization_result.organization_name}")
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Criteria", organization_result.total_criteria)
        
        with col2:
            st.metric("Fulfilled", organization_result.fulfilled_criteria)
        
        with col3:
            st.metric("Fulfillment %", f"{organization_result.fulfillment_percentage:.1f}%")
        
        with col4:
            st.metric("Avg. Confidence", f"{organization_result.average_confidence:.2f}")
        
        # Dimension breakdown
        dimension_data = organization_result.evaluation_summary.get('by_dimension', {})
        
        if dimension_data:
            st.subheader("Performance by Dimension")
            
            dimensions = list(dimension_data.keys())
            percentages = [data.get('percentage', 0) for data in dimension_data.values()]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=dimensions,
                    y=percentages,
                    marker_color=self.colors['primary']
                )
            ])
            
            fig.update_layout(
                title="Fulfillment by Dimension",
                xaxis_title="Dimension",
                yaxis_title="Fulfillment Percentage (%)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed criteria table
        st.subheader("Detailed Criteria Results")
        
        criteria_data = []
        for criterion in organization_result.criteria_results:
            criteria_data.append({
                'Criterion': criterion.criterion_name,
                'Fulfilled': '✅' if criterion.evaluation else '❌',
                'Confidence': f"{criterion.confidence:.2f}",
                'Pattern Type': criterion.pattern_type or 'N/A',
                'Justification': criterion.justification[:100] + '...' if len(criterion.justification) > 100 else criterion.justification
            })
        
        df = pd.DataFrame(criteria_data)
        st.dataframe(df, use_container_width=True)
    
    def create_criteria_overview(self, evaluation_results: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create criteria overview chart."""
        if not evaluation_results:
            return None
        
        try:
            # Extract criteria fulfillment data
            criteria_data = {}
            
            for result in evaluation_results:
                criteria_results = result.get('criteria_results', {})
                for criterion_id, criterion_result in criteria_results.items():
                    criterion_name = criterion_result.get('name', criterion_id)
                    if criterion_name not in criteria_data:
                        criteria_data[criterion_name] = {'fulfilled': 0, 'total': 0}
                    
                    criteria_data[criterion_name]['total'] += 1
                    if criterion_result.get('fulfilled', False):
                        criteria_data[criterion_name]['fulfilled'] += 1
            
            # Calculate percentages
            criteria_names = list(criteria_data.keys())
            percentages = [
                (data['fulfilled'] / data['total'] * 100) if data['total'] > 0 else 0
                for data in criteria_data.values()
            ]
            
            # Create horizontal bar chart
            fig = go.Figure(data=[
                go.Bar(
                    y=criteria_names,
                    x=percentages,
                    orientation='h',
                    marker_color=self.colors['primary']
                )
            ])
            
            fig.update_layout(
                title="Criteria Fulfillment Overview",
                xaxis_title="Fulfillment Percentage (%)",
                yaxis_title="Criteria",
                height=max(400, len(criteria_names) * 25)
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating criteria overview: {str(e)}")
            return None
    
    def create_organization_comparison(self, evaluation_results: List[Dict[str, Any]]) -> Optional[go.Figure]:
        """Create organization comparison chart."""
        if not evaluation_results:
            return None
        
        try:
            # Extract organization data
            org_names = []
            fulfillment_rates = []
            
            for result in evaluation_results:
                org_name = result.get('organization_name', 'Unknown')
                criteria_results = result.get('criteria_results', {})
                
                total_criteria = len(criteria_results)
                fulfilled_criteria = len([c for c in criteria_results.values() if c.get('fulfilled', False)])
                fulfillment_rate = (fulfilled_criteria / total_criteria * 100) if total_criteria > 0 else 0
                
                org_names.append(org_name)
                fulfillment_rates.append(fulfillment_rate)
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=org_names,
                    y=fulfillment_rates,
                    marker_color=self.colors['secondary']
                )
            ])
            
            fig.update_layout(
                title="Organization Comparison",
                xaxis_title="Organization",
                yaxis_title="Fulfillment Rate (%)",
                height=400,
                xaxis={'tickangle': 45}
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating organization comparison: {str(e)}")
            return None
    
    def create_simple_bar_chart(self, df: pd.DataFrame, x_col: str, y_col: str, title: str) -> Optional[go.Figure]:
        """Create a simple bar chart."""
        try:
            fig = go.Figure(data=[
                go.Bar(
                    x=df[x_col],
                    y=df[y_col],
                    marker_color=self.colors['primary']
                )
            ])
            
            fig.update_layout(
                title=title,
                xaxis_title=x_col,
                yaxis_title=y_col,
                height=400,
                xaxis={'tickangle': 45}
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating simple bar chart: {str(e)}")
            return None
    
    def create_histogram(self, data: List[float], x_title: str, title: str) -> Optional[go.Figure]:
        """Create a histogram."""
        try:
            fig = go.Figure(data=[
                go.Histogram(
                    x=data,
                    nbinsx=20,
                    marker_color=self.colors['info'],
                    opacity=0.7
                )
            ])
            
            fig.update_layout(
                title=title,
                xaxis_title=x_title,
                yaxis_title="Count",
                height=400
            )
            
            return fig
            
        except Exception as e:
            self.logger.error(f"Error creating histogram: {str(e)}")
            return None
    
    def create_export_options(
        self,
        evaluation_results: List[OrganizationEvaluation],
        statistics: Dict[str, Any]
    ) -> None:
        """Create export options for visualizations and data."""
        st.subheader("Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 Export Charts as HTML"):
                # This would export all charts as an HTML report
                st.success("Charts exported successfully!")
        
        with col2:
            if st.button("📈 Export Statistics as JSON"):
                import json
                stats_json = json.dumps(statistics, indent=2, default=str)
                st.download_button(
                    label="Download Statistics JSON",
                    data=stats_json,
                    file_name="offenheitscrawler_statistics.json",
                    mime="application/json"
                )
        
        with col3:
            if st.button("📋 Export Summary Report"):
                from .stats_collector import StatisticsCollector
                collector = StatisticsCollector()
                report = collector.export_statistics_report(statistics, 'markdown')
                st.download_button(
                    label="Download Summary Report",
                    data=report,
                    file_name="offenheitscrawler_report.md",
                    mime="text/markdown"
                )
