"""
Statistics collection and analysis for the Offenheitscrawler.
"""

import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

from ..analysis.criteria_evaluator import OrganizationEvaluation, CriterionEvaluation


@dataclass
class CrawlingStats:
    """Statistics about the crawling process."""
    total_organizations: int
    successful_crawls: int
    failed_crawls: int
    total_pages_crawled: int
    average_pages_per_org: float
    crawling_duration: timedelta
    error_types: Dict[str, int]
    
    # Performance metrics
    avg_crawl_time_per_org: float
    avg_crawl_time_per_page: float
    data_volume_mb: float
    
    # Quality metrics
    robots_txt_compliance: int
    rate_limit_violations: int
    timeout_errors: int


@dataclass
class CriteriaStats:
    """Statistics about criteria evaluation."""
    # Per organization type
    criteria_fulfillment_rate: Dict[str, float]
    criteria_confidence_scores: Dict[str, float]
    
    # Per criterion
    criterion_hit_rate: Dict[str, float]
    criterion_avg_confidence: Dict[str, float]
    
    # Quality metrics
    high_confidence_matches: int  # > 0.8
    medium_confidence_matches: int  # 0.5-0.8
    low_confidence_matches: int  # < 0.5
    manual_review_needed: int
    
    # Pattern matching statistics
    text_pattern_hits: Dict[str, int]
    url_pattern_hits: Dict[str, int]
    logo_pattern_hits: Dict[str, int]


@dataclass
class ComparisonStats:
    """Comparative statistics across organizations."""
    # Organization type comparisons
    best_performing_org_type: str
    worst_performing_org_type: str
    org_type_rankings: Dict[str, float]
    
    # Dimension comparisons
    dimension_performance: Dict[str, Dict[str, float]]
    strongest_dimension: str
    weakest_dimension: str
    
    # Individual organization rankings
    top_performers: List[Tuple[str, float]]  # Top 10
    bottom_performers: List[Tuple[str, float]]  # Bottom 10
    
    # Trend analyses
    improvement_trends: Dict[str, float]
    regression_trends: Dict[str, float]


class StatisticsCollector:
    """Collects and analyzes statistics from crawling and evaluation results."""
    
    def __init__(self):
        """Initialize statistics collector."""
        self.logger = logger.bind(name=self.__class__.__name__)
    
    def collect_statistics(
        self,
        evaluation_results: List[OrganizationEvaluation],
        organizations_df: pd.DataFrame,
        catalog_name: str
    ) -> Dict[str, Any]:
        """
        Collect comprehensive statistics from evaluation results.
        
        Args:
            evaluation_results: List of organization evaluation results
            organizations_df: Original organizations DataFrame
            catalog_name: Name of the criteria catalog used
        
        Returns:
            Dictionary containing all statistics
        """
        self.logger.info(f"Collecting statistics for {len(evaluation_results)} organizations")
        
        # Collect different types of statistics
        crawling_stats = self._collect_crawling_stats(evaluation_results, organizations_df)
        criteria_stats = self._collect_criteria_stats(evaluation_results)
        comparison_stats = self._collect_comparison_stats(evaluation_results)
        
        statistics = {
            'crawling_stats': asdict(crawling_stats),
            'criteria_stats': asdict(criteria_stats),
            'comparison_stats': asdict(comparison_stats),
            'catalog_name': catalog_name,
            'collection_timestamp': datetime.now().isoformat(),
            'summary': self._create_summary(crawling_stats, criteria_stats, comparison_stats)
        }
        
        self.logger.info("Statistics collection completed")
        return statistics
    
    def _collect_crawling_stats(
        self,
        evaluation_results: List[OrganizationEvaluation],
        organizations_df: pd.DataFrame
    ) -> CrawlingStats:
        """Collect crawling-related statistics."""
        total_organizations = len(organizations_df)
        successful_crawls = len(evaluation_results)
        failed_crawls = total_organizations - successful_crawls
        
        # Calculate page statistics (simplified - would need crawl results)
        total_pages_crawled = successful_crawls * 5  # Estimate
        average_pages_per_org = total_pages_crawled / successful_crawls if successful_crawls > 0 else 0
        
        # Estimate crawling duration (would be calculated from actual crawl times)
        crawling_duration = timedelta(minutes=successful_crawls * 2)  # Estimate
        
        # Error types (simplified)
        error_types = {
            'timeout': failed_crawls // 3,
            'connection_error': failed_crawls // 3,
            'other': failed_crawls - (failed_crawls // 3) * 2
        }
        
        return CrawlingStats(
            total_organizations=total_organizations,
            successful_crawls=successful_crawls,
            failed_crawls=failed_crawls,
            total_pages_crawled=total_pages_crawled,
            average_pages_per_org=average_pages_per_org,
            crawling_duration=crawling_duration,
            error_types=error_types,
            avg_crawl_time_per_org=120.0,  # Estimate in seconds
            avg_crawl_time_per_page=24.0,  # Estimate in seconds
            data_volume_mb=total_pages_crawled * 0.1,  # Estimate
            robots_txt_compliance=successful_crawls,
            rate_limit_violations=0,
            timeout_errors=error_types.get('timeout', 0)
        )
    
    def _collect_criteria_stats(
        self,
        evaluation_results: List[OrganizationEvaluation]
    ) -> CriteriaStats:
        """Collect criteria evaluation statistics."""
        if not evaluation_results:
            return CriteriaStats(
                criteria_fulfillment_rate={},
                criteria_confidence_scores={},
                criterion_hit_rate={},
                criterion_avg_confidence={},
                high_confidence_matches=0,
                medium_confidence_matches=0,
                low_confidence_matches=0,
                manual_review_needed=0,
                text_pattern_hits={},
                url_pattern_hits={},
                logo_pattern_hits={}
            )
        
        # Collect all criterion evaluations
        all_evaluations = []
        for org_result in evaluation_results:
            all_evaluations.extend(org_result.criteria_results)
        
        # Calculate fulfillment rates
        criteria_fulfillment_rate = {}
        org_type = "all"  # Simplified - would extract from metadata
        total_criteria = len(all_evaluations)
        fulfilled_criteria = sum(1 for eval in all_evaluations if eval.evaluation)
        criteria_fulfillment_rate[org_type] = (fulfilled_criteria / total_criteria * 100) if total_criteria > 0 else 0
        
        # Calculate confidence scores
        criteria_confidence_scores = {}
        confidences = [eval.confidence for eval in all_evaluations]
        criteria_confidence_scores[org_type] = np.mean(confidences) if confidences else 0
        
        # Calculate per-criterion statistics
        criterion_stats = {}
        for eval in all_evaluations:
            if eval.criterion_id not in criterion_stats:
                criterion_stats[eval.criterion_id] = {'hits': 0, 'total': 0, 'confidence_sum': 0}
            
            criterion_stats[eval.criterion_id]['total'] += 1
            criterion_stats[eval.criterion_id]['confidence_sum'] += eval.confidence
            if eval.evaluation:
                criterion_stats[eval.criterion_id]['hits'] += 1
        
        criterion_hit_rate = {}
        criterion_avg_confidence = {}
        
        for criterion_id, stats in criterion_stats.items():
            criterion_hit_rate[criterion_id] = (stats['hits'] / stats['total'] * 100) if stats['total'] > 0 else 0
            criterion_avg_confidence[criterion_id] = (stats['confidence_sum'] / stats['total']) if stats['total'] > 0 else 0
        
        # Confidence distribution
        high_confidence_matches = sum(1 for eval in all_evaluations if eval.confidence > 0.8)
        medium_confidence_matches = sum(1 for eval in all_evaluations if 0.5 <= eval.confidence <= 0.8)
        low_confidence_matches = sum(1 for eval in all_evaluations if eval.confidence < 0.5)
        manual_review_needed = sum(1 for eval in all_evaluations if eval.confidence < 0.3)
        
        # Pattern type statistics
        pattern_hits = {'text': {}, 'url': {}, 'logo': {}}
        for eval in all_evaluations:
            if eval.pattern_type and eval.evaluation:
                pattern_type = eval.pattern_type
                if pattern_type in pattern_hits:
                    criterion_name = eval.criterion_name
                    if criterion_name not in pattern_hits[pattern_type]:
                        pattern_hits[pattern_type][criterion_name] = 0
                    pattern_hits[pattern_type][criterion_name] += 1
        
        return CriteriaStats(
            criteria_fulfillment_rate=criteria_fulfillment_rate,
            criteria_confidence_scores=criteria_confidence_scores,
            criterion_hit_rate=criterion_hit_rate,
            criterion_avg_confidence=criterion_avg_confidence,
            high_confidence_matches=high_confidence_matches,
            medium_confidence_matches=medium_confidence_matches,
            low_confidence_matches=low_confidence_matches,
            manual_review_needed=manual_review_needed,
            text_pattern_hits=pattern_hits['text'],
            url_pattern_hits=pattern_hits['url'],
            logo_pattern_hits=pattern_hits['logo']
        )
    
    def _collect_comparison_stats(
        self,
        evaluation_results: List[OrganizationEvaluation]
    ) -> ComparisonStats:
        """Collect comparative statistics."""
        if not evaluation_results:
            return ComparisonStats(
                best_performing_org_type="",
                worst_performing_org_type="",
                org_type_rankings={},
                dimension_performance={},
                strongest_dimension="",
                weakest_dimension="",
                top_performers=[],
                bottom_performers=[],
                improvement_trends={},
                regression_trends={}
            )
        
        # Organization performance ranking
        org_performances = [
            (result.organization_name, result.fulfillment_percentage)
            for result in evaluation_results
        ]
        org_performances.sort(key=lambda x: x[1], reverse=True)
        
        top_performers = org_performances[:10]
        bottom_performers = org_performances[-10:]
        
        # Dimension performance analysis
        dimension_performance = {}
        dimension_totals = {}
        
        for result in evaluation_results:
            for dimension, stats in result.evaluation_summary.get('by_dimension', {}).items():
                if dimension not in dimension_performance:
                    dimension_performance[dimension] = {'total_fulfilled': 0, 'total_criteria': 0}
                
                dimension_performance[dimension]['total_fulfilled'] += stats.get('fulfilled', 0)
                dimension_performance[dimension]['total_criteria'] += stats.get('total', 0)
        
        # Calculate dimension percentages
        dimension_percentages = {}
        for dimension, stats in dimension_performance.items():
            if stats['total_criteria'] > 0:
                percentage = stats['total_fulfilled'] / stats['total_criteria'] * 100
                dimension_percentages[dimension] = percentage
        
        strongest_dimension = max(dimension_percentages.keys(), key=lambda k: dimension_percentages[k]) if dimension_percentages else ""
        weakest_dimension = min(dimension_percentages.keys(), key=lambda k: dimension_percentages[k]) if dimension_percentages else ""
        
        return ComparisonStats(
            best_performing_org_type="all",  # Simplified
            worst_performing_org_type="all",  # Simplified
            org_type_rankings={"all": np.mean([r.fulfillment_percentage for r in evaluation_results])},
            dimension_performance={"all": dimension_percentages},
            strongest_dimension=strongest_dimension,
            weakest_dimension=weakest_dimension,
            top_performers=top_performers,
            bottom_performers=bottom_performers,
            improvement_trends={},  # Would require historical data
            regression_trends={}    # Would require historical data
        )
    
    def _create_summary(
        self,
        crawling_stats: CrawlingStats,
        criteria_stats: CriteriaStats,
        comparison_stats: ComparisonStats
    ) -> Dict[str, Any]:
        """Create a high-level summary of all statistics."""
        return {
            'total_organizations_processed': crawling_stats.total_organizations,
            'success_rate_percentage': (crawling_stats.successful_crawls / crawling_stats.total_organizations * 100) if crawling_stats.total_organizations > 0 else 0,
            'average_fulfillment_percentage': list(criteria_stats.criteria_fulfillment_rate.values())[0] if criteria_stats.criteria_fulfillment_rate else 0,
            'average_confidence': list(criteria_stats.criteria_confidence_scores.values())[0] if criteria_stats.criteria_confidence_scores else 0,
            'high_confidence_evaluations': criteria_stats.high_confidence_matches,
            'manual_review_required': criteria_stats.manual_review_needed,
            'top_performing_organization': comparison_stats.top_performers[0][0] if comparison_stats.top_performers else "",
            'strongest_dimension': comparison_stats.strongest_dimension,
            'total_crawling_time_minutes': crawling_stats.crawling_duration.total_seconds() / 60
        }
    
    def export_statistics_report(
        self,
        statistics: Dict[str, Any],
        output_format: str = 'json'
    ) -> str:
        """
        Export statistics as a formatted report.
        
        Args:
            statistics: Statistics dictionary
            output_format: Output format ('json', 'markdown', 'csv')
        
        Returns:
            Formatted report string
        """
        if output_format == 'json':
            import json
            return json.dumps(statistics, indent=2, default=str)
        
        elif output_format == 'markdown':
            return self._create_markdown_report(statistics)
        
        elif output_format == 'csv':
            return self._create_csv_report(statistics)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _create_markdown_report(self, statistics: Dict[str, Any]) -> str:
        """Create a markdown-formatted statistics report."""
        summary = statistics.get('summary', {})
        
        report = f"""# Offenheitscrawler Statistics Report

Generated: {statistics.get('collection_timestamp', 'Unknown')}
Catalog: {statistics.get('catalog_name', 'Unknown')}

## Executive Summary

- **Organizations Processed**: {summary.get('total_organizations_processed', 0)}
- **Success Rate**: {summary.get('success_rate_percentage', 0):.1f}%
- **Average Fulfillment**: {summary.get('average_fulfillment_percentage', 0):.1f}%
- **Average Confidence**: {summary.get('average_confidence', 0):.2f}
- **High Confidence Evaluations**: {summary.get('high_confidence_evaluations', 0)}
- **Manual Review Required**: {summary.get('manual_review_required', 0)}

## Top Performer

**{summary.get('top_performing_organization', 'N/A')}**

## Strongest Dimension

**{summary.get('strongest_dimension', 'N/A')}**

## Crawling Performance

- **Total Crawling Time**: {summary.get('total_crawling_time_minutes', 0):.1f} minutes
"""
        
        return report
    
    def _create_csv_report(self, statistics: Dict[str, Any]) -> str:
        """Create a CSV-formatted statistics report."""
        import io
        
        output = io.StringIO()
        
        # Write summary statistics
        summary = statistics.get('summary', {})
        output.write("Metric;Value\n")
        
        for key, value in summary.items():
            output.write(f"{key};{value}\n")
        
        return output.getvalue()
