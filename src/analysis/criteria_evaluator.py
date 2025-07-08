"""
Criteria evaluation engine for the Offenheitscrawler.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from loguru import logger

from ..crawler.web_crawler import OrganizationCrawlResult, CrawlResult
from ..llm.llm_client import LLMClient


@dataclass
class CriterionEvaluation:
    """Result of evaluating a single criterion."""
    criterion_id: str
    criterion_name: str
    evaluation: bool  # True if criterion is fulfilled
    confidence: float  # Confidence score (0.0 to 1.0)
    justification: str  # Explanation of the evaluation
    source_url: str  # URL where evidence was found
    evidence_text: str  # Specific text that matched
    pattern_type: str  # Type of pattern that matched (text, url, logo)


@dataclass
class OrganizationEvaluation:
    """Result of evaluating all criteria for an organization."""
    organization_name: str
    base_url: str
    criteria_results: List[CriterionEvaluation]
    total_criteria: int
    fulfilled_criteria: int
    fulfillment_percentage: float
    average_confidence: float
    evaluation_summary: Dict[str, Any]


class CriteriaEvaluator:
    """Evaluates organizations against criteria catalogs."""
    
    def __init__(
        self,
        criteria_catalog: Dict[str, Any],
        confidence_threshold: float = 0.5,
        case_sensitive: bool = False,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize criteria evaluator.
        
        Args:
            criteria_catalog: YAML criteria catalog
            confidence_threshold: Minimum confidence for positive evaluation
            case_sensitive: Whether pattern matching is case sensitive
            llm_client: Optional LLM client for enhanced analysis
        """
        self.criteria_catalog = criteria_catalog
        self.confidence_threshold = confidence_threshold
        self.case_sensitive = case_sensitive
        self.llm_client = llm_client
        
        self.logger = logger.bind(name=self.__class__.__name__)
        
        # Extract all criteria from catalog
        self.criteria = self._extract_criteria()
        
        self.logger.info(f"Initialized evaluator with {len(self.criteria)} criteria")
    
    def evaluate_organization(
        self, 
        organization_name: str, 
        crawl_result: OrganizationCrawlResult
    ) -> OrganizationEvaluation:
        """
        Evaluate an organization against all criteria.
        
        Args:
            organization_name: Name of the organization
            crawl_result: Result from crawling the organization
        
        Returns:
            Organization evaluation result
        """
        self.logger.info(f"Evaluating {organization_name} against {len(self.criteria)} criteria")
        
        criteria_results = []
        
        for criterion in self.criteria:
            evaluation = self._evaluate_criterion(criterion, crawl_result)
            criteria_results.append(evaluation)
        
        # Calculate summary statistics
        fulfilled_criteria = sum(1 for result in criteria_results if result.evaluation)
        total_criteria = len(criteria_results)
        fulfillment_percentage = (fulfilled_criteria / total_criteria * 100) if total_criteria > 0 else 0
        
        # Calculate average confidence
        confidences = [result.confidence for result in criteria_results]
        average_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Create evaluation summary
        evaluation_summary = self._create_evaluation_summary(criteria_results)
        
        result = OrganizationEvaluation(
            organization_name=organization_name,
            base_url=crawl_result.base_url,
            criteria_results=criteria_results,
            total_criteria=total_criteria,
            fulfilled_criteria=fulfilled_criteria,
            fulfillment_percentage=fulfillment_percentage,
            average_confidence=average_confidence,
            evaluation_summary=evaluation_summary
        )
        
        self.logger.info(
            f"Evaluation complete for {organization_name}: "
            f"{fulfilled_criteria}/{total_criteria} criteria fulfilled "
            f"({fulfillment_percentage:.1f}%)"
        )
        
        return result
    
    def _extract_criteria(self) -> List[Dict[str, Any]]:
        """Extract all criteria from the catalog with context."""
        criteria = []
        
        for dim_name, dimension in self.criteria_catalog.get('dimensions', {}).items():
            for factor_name, factor in dimension.get('factors', {}).items():
                for criterion_id, criterion in factor.get('criteria', {}).items():
                    criterion_with_context = {
                        'id': criterion_id,
                        'dimension': dim_name,
                        'factor': factor_name,
                        'name': criterion['name'],
                        'description': criterion['description'],
                        'type': criterion['type'],
                        'patterns': criterion.get('patterns', {}),
                        'weight': criterion.get('weight', 1.0),
                        'confidence_threshold': criterion.get('confidence_threshold', self.confidence_threshold)
                    }
                    criteria.append(criterion_with_context)
        
        return criteria
    
    def _evaluate_criterion(
        self, 
        criterion: Dict[str, Any], 
        crawl_result: OrganizationCrawlResult
    ) -> CriterionEvaluation:
        """
        Evaluate a single criterion against crawl results.
        
        Args:
            criterion: Criterion definition
            crawl_result: Organization crawl result
        
        Returns:
            Criterion evaluation result
        """
        best_match = None
        best_confidence = 0.0
        
        # Check each successfully crawled page
        for page in crawl_result.pages:
            if not page.success:
                continue
            
            # Primary LLM evaluation if available
            if self.llm_client:
                llm_result = self._evaluate_with_llm(criterion, page)
                if llm_result and llm_result[1] > best_confidence:
                    best_match = llm_result
                    best_confidence = llm_result[1]
            
            # Fallback to traditional pattern matching if LLM didn't find strong evidence
            if best_confidence < 0.3:
                for pattern_type, patterns in criterion.get('patterns', {}).items():
                    if not patterns:
                        continue
                    
                    match_result = self._evaluate_patterns(
                        patterns, pattern_type, page, criterion
                    )
                    
                    if match_result and match_result[1] > best_confidence:
                        best_match = match_result
                        best_confidence = match_result[1]
        
        # Determine evaluation result
        if best_match and best_confidence >= criterion['confidence_threshold']:
            evaluation = True
            justification = f"Nachweis gefunden über {best_match[2]} Muster: {best_match[3]}"
            source_url = best_match[4]
            evidence_text = best_match[3]
            pattern_type = best_match[2]
        else:
            evaluation = False
            justification = "Keine ausreichenden Belege gefunden"
            source_url = crawl_result.base_url
            evidence_text = ""
            pattern_type = ""
        
        return CriterionEvaluation(
            criterion_id=criterion['id'],
            criterion_name=criterion['name'],
            evaluation=evaluation,
            confidence=best_confidence,
            justification=justification,
            source_url=source_url,
            evidence_text=evidence_text,
            pattern_type=pattern_type
        )
    
    def _evaluate_patterns(
        self, 
        patterns: List[str], 
        pattern_type: str, 
        page: CrawlResult, 
        criterion: Dict[str, Any]
    ) -> Optional[Tuple[bool, float, str, str, str]]:
        """
        Evaluate patterns against a page.
        
        Args:
            patterns: List of patterns to match
            pattern_type: Type of pattern (text, url, logo)
            page: Page crawl result
            criterion: Criterion definition
        
        Returns:
            Tuple of (match_found, confidence, pattern_type, evidence, source_url) or None
        """
        if pattern_type == 'text':
            return self._evaluate_text_patterns(patterns, page, criterion)
        elif pattern_type == 'url':
            return self._evaluate_url_patterns(patterns, page, criterion)
        elif pattern_type == 'logo':
            return self._evaluate_logo_patterns(patterns, page, criterion)
        else:
            self.logger.warning(f"Unknown pattern type: {pattern_type}")
            return None
    
    def _evaluate_text_patterns(
        self, 
        patterns: List[str], 
        page: CrawlResult, 
        criterion: Dict[str, Any]
    ) -> Optional[Tuple[bool, float, str, str, str]]:
        """Evaluate text patterns against page content."""
        if not page.content:
            return None
        
        content = page.content if self.case_sensitive else page.content.lower()
        matches = []
        
        for pattern in patterns:
            search_pattern = pattern if self.case_sensitive else pattern.lower()
            
            # Simple substring search
            if search_pattern in content:
                # Find the context around the match
                start_idx = content.find(search_pattern)
                context_start = max(0, start_idx - 50)
                context_end = min(len(content), start_idx + len(search_pattern) + 50)
                context = content[context_start:context_end].strip()
                
                matches.append((pattern, context))
        
        if matches:
            # Calculate confidence based on number of matches and pattern specificity
            confidence = min(0.9, 0.3 + (len(matches) * 0.2))
            
            # Use the first match for evidence
            evidence = f"'{matches[0][0]}' gefunden im Kontext: {matches[0][1]}"
            
            return (True, confidence, 'textmuster', evidence, page.url)
        
        return None
    
    def _evaluate_url_patterns(
        self, 
        patterns: List[str], 
        page: CrawlResult, 
        criterion: Dict[str, Any]
    ) -> Optional[Tuple[bool, float, str, str, str]]:
        """Evaluate URL patterns against page URL and links."""
        # Check page URL itself
        page_url = page.url if self.case_sensitive else page.url.lower()
        
        for pattern in patterns:
            search_pattern = pattern if self.case_sensitive else pattern.lower()
            
            if search_pattern in page_url:
                confidence = 0.8  # High confidence for URL matches
                evidence = f"URL contains '{pattern}': {page.url}"
                return (True, confidence, 'url', evidence, page.url)
        
        # Check links on the page
        for link in page.links:
            link_lower = link if self.case_sensitive else link.lower()
            
            for pattern in patterns:
                search_pattern = pattern if self.case_sensitive else pattern.lower()
                
                if search_pattern in link_lower:
                    confidence = 0.7  # Slightly lower confidence for linked URLs
                    evidence = f"Link enthält '{pattern}': {link}"
                    return (True, confidence, 'url-muster', evidence, page.url)
        
        return None
    
    def _evaluate_logo_patterns(
        self, 
        patterns: List[str], 
        page: CrawlResult, 
        criterion: Dict[str, Any]
    ) -> Optional[Tuple[bool, float, str, str, str]]:
        """Evaluate logo patterns (simplified - looks for image alt text and filenames)."""
        if not page.content:
            return None
        
        content = page.content if self.case_sensitive else page.content.lower()
        
        # Look for image-related patterns in alt text, filenames, etc.
        for pattern in patterns:
            search_pattern = pattern if self.case_sensitive else pattern.lower()
            
            # Simple pattern matching for logo-related content
            logo_indicators = [
                f"alt=\"{search_pattern}\"",
                f"alt='{search_pattern}'",
                f"{search_pattern}.png",
                f"{search_pattern}.jpg",
                f"{search_pattern}.svg",
                f"logo/{search_pattern}",
                f"images/{search_pattern}"
            ]
            
            for indicator in logo_indicators:
                if indicator in content:
                    confidence = 0.6  # Moderate confidence for logo matches
                    evidence = f"Logo-Muster '{pattern}' gefunden: {indicator}"
                    return (True, confidence, 'logo-muster', evidence, page.url)
        
        return None
    
    def _evaluate_with_llm(
        self, 
        criterion: Dict[str, Any], 
        page: CrawlResult
    ) -> Optional[Tuple[bool, float, str, str, str]]:
        """
        Evaluate criterion using LLM for enhanced semantic analysis.
        
        Args:
            criterion: Criterion definition
            page: Crawl result for a single page
            
        Returns:
            Tuple of (found, confidence, pattern_type, evidence, url) or None
        """
        try:
            # Extract patterns for LLM context
            all_patterns = []
            for pattern_type, patterns in criterion.get('patterns', {}).items():
                all_patterns.extend(patterns)
            
            if not all_patterns:
                return None
            
            # Run LLM analysis asynchronously
            import asyncio
            
            # Create event loop if none exists
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run LLM analysis
            analysis = loop.run_until_complete(
                self.llm_client.analyze_content_for_criteria(
                    content=page.content,
                    criterion_name=criterion['name'],
                    criterion_description=criterion.get('description', ''),
                    patterns=all_patterns,
                    source_url=page.url
                )
            )
            
            if analysis and analysis.get('fulfilled', False):
                confidence = float(analysis.get('confidence', 0.0))
                justification = analysis.get('justification', 'KI-Analyse fand Belege')
                evidence = '; '.join(analysis.get('evidence', []))
                
                self.logger.info(
                    f"LLM enhanced evaluation for {criterion['name']}: "
                    f"confidence={confidence:.2f}"
                )
                
                return (True, confidence, 'ki-analyse', evidence or justification, page.url)
            
            return None
            
        except Exception as e:
            self.logger.error(f"LLM evaluation failed for {criterion['name']}: {str(e)}")
            return None
    
    def _create_evaluation_summary(
        self, 
        criteria_results: List[CriterionEvaluation]
    ) -> Dict[str, Any]:
        """Create a summary of the evaluation results."""
        summary = {
            'by_dimension': {},
            'by_confidence': {
                'high': 0,  # > 0.8
                'medium': 0,  # 0.5 - 0.8
                'low': 0  # < 0.5
            },
            'by_pattern_type': {},
            'fulfilled_by_type': {
                'operational': 0,
                'strategic': 0
            },
            'total_by_type': {
                'operational': 0,
                'strategic': 0
            }
        }
        
        # Group by dimension
        for result in criteria_results:
            # Find the criterion definition to get dimension info
            criterion = next((c for c in self.criteria if c['id'] == result.criterion_id), None)
            
            if criterion:
                dimension = criterion['dimension']
                criterion_type = criterion['type']
                
                # By dimension
                if dimension not in summary['by_dimension']:
                    summary['by_dimension'][dimension] = {'total': 0, 'fulfilled': 0}
                
                summary['by_dimension'][dimension]['total'] += 1
                if result.evaluation:
                    summary['by_dimension'][dimension]['fulfilled'] += 1
                
                # By type
                summary['total_by_type'][criterion_type] += 1
                if result.evaluation:
                    summary['fulfilled_by_type'][criterion_type] += 1
            
            # By confidence
            if result.confidence > 0.8:
                summary['by_confidence']['high'] += 1
            elif result.confidence >= 0.5:
                summary['by_confidence']['medium'] += 1
            else:
                summary['by_confidence']['low'] += 1
            
            # By pattern type
            if result.pattern_type:
                if result.pattern_type not in summary['by_pattern_type']:
                    summary['by_pattern_type'][result.pattern_type] = 0
                summary['by_pattern_type'][result.pattern_type] += 1
        
        # Calculate percentages for dimensions
        for dimension_data in summary['by_dimension'].values():
            if dimension_data['total'] > 0:
                dimension_data['percentage'] = (
                    dimension_data['fulfilled'] / dimension_data['total'] * 100
                )
            else:
                dimension_data['percentage'] = 0
        
        return summary
