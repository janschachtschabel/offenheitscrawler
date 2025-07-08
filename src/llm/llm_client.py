"""
LLM Client for OpenAI-compatible APIs.
"""

import os
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
from loguru import logger


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.3
    max_tokens: int = 15000
    timeout: int = 30


class LLMClient:
    """OpenAI-compatible LLM client for enhanced content analysis."""
    
    AVAILABLE_MODELS = [
        "gpt-4.1-mini",
        "gpt-4o-mini",
        "gpt-4o", 
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ]
    
    def __init__(self, config: LLMConfig):
        """
        Initialize LLM client.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout
        )
        self.logger = logger.bind(name=self.__class__.__name__)
    
    async def analyze_content_for_criteria(
        self, 
        content: str, 
        criterion_name: str,
        criterion_description: str,
        patterns: List[str],
        source_url: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze content using LLM to determine if a criterion is fulfilled.
        
        Args:
            content: Web page content to analyze
            criterion_name: Name of the criterion
            criterion_description: Description of what to look for
            patterns: List of patterns/keywords to consider
            source_url: URL of the source page for better context
            
        Returns:
            Dictionary with analysis results
        """
        try:
            prompt = self._create_analysis_prompt(
                content, criterion_name, criterion_description, patterns, source_url
            )
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein Experte für die Bewertung von Organisationsoffenheit. "
                                 "Analysiere Webseiteninhalte und bewerte, ob bestimmte Kriterien erfüllt sind. "
                                 "Antworte immer im JSON-Format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            import json
            analysis = json.loads(result)
            
            self.logger.info(f"LLM analysis completed for criterion: {criterion_name}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed for {criterion_name}: {str(e)}")
            return {
                "fulfilled": False,
                "confidence": 0.0,
                "justification": f"KI-Analyse fehlgeschlagen: {str(e)}",
                "evidence": []
            }
    
    def _create_analysis_prompt(
        self, 
        content: str, 
        criterion_name: str,
        criterion_description: str, 
        patterns: List[str],
        source_url: str = ""
    ) -> str:
        """Create analysis prompt for LLM."""
        
        # Truncate content if too long
        max_content_length = 3000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        url_info = f"\nQUELLE: {source_url}" if source_url else ""
        
        prompt = f"""
Analysiere den folgenden Webseiteninhalt und bewerte, ob das Kriterium "{criterion_name}" erfüllt ist.{url_info}

KRITERIUM:
Name: {criterion_name}
Beschreibung: {criterion_description}
Suchbegriffe: {', '.join(patterns)}

WEBSEITENINHALT:
{content}

AUFGABE:
Bewerte, ob das Kriterium basierend auf dem Webseiteninhalt erfüllt ist. Berücksichtige dabei:
1. Direkte Erwähnungen der Suchbegriffe
2. Inhaltliche Übereinstimmung mit der Kriterienbeschreibung
3. Kontext und Bedeutung der gefundenen Informationen

ANTWORTFORMAT (JSON):
{{
    "fulfilled": true/false,
    "confidence": 0.0-1.0,
    "justification": "Begründung der Bewertung",
    "evidence": ["Liste der gefundenen Belege"],
    "found_patterns": ["Liste der gefundenen Suchbegriffe"]
}}

Antworte nur mit dem JSON-Objekt, ohne zusätzlichen Text.
"""
        return prompt
    
    async def enhance_pattern_matching(
        self,
        content: str,
        patterns: List[str],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Use LLM to enhance pattern matching beyond simple keyword search.
        
        Args:
            content: Content to analyze
            patterns: Patterns to look for
            context: Additional context for analysis
            
        Returns:
            Enhanced matching results
        """
        try:
            prompt = f"""
Analysiere den folgenden Text und finde semantische Übereinstimmungen mit den gegebenen Mustern.

MUSTER: {', '.join(patterns)}
KONTEXT: {context}

TEXT:
{content[:2000]}...

Finde nicht nur exakte Übereinstimmungen, sondern auch:
- Synonyme und verwandte Begriffe
- Konzeptuelle Übereinstimmungen
- Implizite Hinweise

Antwortformat (JSON):
{{
    "matches_found": true/false,
    "confidence": 0.0-1.0,
    "found_concepts": ["Liste der gefundenen Konzepte"],
    "semantic_matches": ["Semantische Übereinstimmungen"],
    "explanation": "Erklärung der Analyse"
}}
"""
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein Experte für semantische Textanalyse. "
                                 "Analysiere Texte auf konzeptuelle und semantische Übereinstimmungen."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            self.logger.error(f"Enhanced pattern matching failed: {str(e)}")
            return {
                "matches_found": False,
                "confidence": 0.0,
                "found_concepts": [],
                "semantic_matches": [],
                "explanation": f"Analysis failed: {str(e)}"
            }
    
    async def select_best_subpages(
        self,
        organization_name: str,
        base_url: str,
        subpages: List[Dict[str, str]],
        criteria_names: List[str],
        max_pages: int
    ) -> List[str]:
        """
        Use LLM to intelligently select the best subpages for criteria evaluation.
        
        Args:
            organization_name: Name of the organization
            base_url: Base URL of the organization
            subpages: List of subpages with 'url' and 'title' keys
            criteria_names: List of criteria names to evaluate
            max_pages: Maximum number of pages to select
            
        Returns:
            List of selected URLs
        """
        try:
            # Prepare subpages info for prompt
            subpages_info = "\n".join([
                f"- {page.get('title', 'Unbekannter Titel')}: {page['url']}"
                for page in subpages[:50]  # Limit to first 50 to avoid token limits
            ])
            
            criteria_list = "\n".join([f"- {criterion}" for criterion in criteria_names])
            
            prompt = f"""
Wähle die {max_pages} besten Unterseiten für die Bewertung von Offenheitskriterien aus.

ORGANISATION: {organization_name}
HAUPTSEITE: {base_url}

KRITERIEN ZU BEWERTEN:
{criteria_list}

VERFÜGBARE UNTERSEITEN:
{subpages_info}

AUFGABE:
Wähle die {max_pages} Unterseiten aus, die am wahrscheinlichsten relevante Informationen für die Bewertung der Offenheitskriterien enthalten. Berücksichtige dabei:

1. **Relevanz für Offenheitskriterien**: Seiten wie "Über uns", "Transparenz", "Publikationen", "Open Data", "Forschung", "Projekte"
2. **Informationsgehalt**: Seiten mit substantiellem Inhalt vs. reine Navigationseiten
3. **Organisationsstruktur**: Seiten über Governance, Führung, Strategie
4. **Zugänglichkeit**: Seiten über Barrierefreiheit, Kontakt, Services
5. **Diversität**: Verschiedene Bereiche der Organisation abdecken

ANTWORTFORMAT (JSON):
{{
    "selected_urls": ["url1", "url2", "url3", ...],
    "reasoning": "Begründung für die Auswahl",
    "relevance_scores": {{
        "url1": 0.9,
        "url2": 0.8,
        ...
    }}
}}

Wähle genau {max_pages} URLs aus und sortiere sie nach Relevanz (höchste zuerst).
"""
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein Experte für Organisationsanalyse und Offenheitsbewertung. "
                                 "Wähle intelligent die relevantesten Webseiten für die Bewertung von Offenheitskriterien aus."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent selection
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            selected_urls = result.get("selected_urls", [])
            
            self.logger.info(
                f"LLM selected {len(selected_urls)} subpages for {organization_name}: "
                f"{result.get('reasoning', 'No reasoning provided')}"
            )
            
            return selected_urls[:max_pages]  # Ensure we don't exceed the limit
            
        except Exception as e:
            self.logger.error(f"LLM subpage selection failed for {organization_name}: {str(e)}")
            # Fallback: return first N URLs
            return [page['url'] for page in subpages[:max_pages]]
    
    async def summarize_organization_analysis(
        self,
        organization_name: str,
        evaluation_results: Dict[str, Any]
    ) -> str:
        """
        Generate a summary of the organization analysis using LLM.
        
        Args:
            organization_name: Name of the organization
            evaluation_results: Results from criteria evaluation
            
        Returns:
            Summary text
        """
        try:
            prompt = f"""
Erstelle eine Zusammenfassung der Offenheitsanalyse für die Organisation "{organization_name}".

ANALYSEERGEBNISSE:
{str(evaluation_results)}

Erstelle eine prägnante, verständliche Zusammenfassung, die:
1. Die wichtigsten Stärken hervorhebt
2. Verbesserungspotentiale aufzeigt
3. Eine Gesamteinschätzung gibt
4. Konkrete Empfehlungen enthält

Die Zusammenfassung sollte 200-300 Wörter umfassen und für Entscheidungsträger verständlich sein.
"""
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Du bist ein Experte für Organisationsanalyse und erstellst "
                                 "prägnante, actionable Zusammenfassungen für Führungskräfte."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {str(e)}")
            return f"Zusammenfassung konnte nicht erstellt werden: {str(e)}"
    
    @classmethod
    def create_from_env(cls, model: str = "gpt-4.1-mini") -> Optional['LLMClient']:
        """
        Create LLM client from environment variables.
        
        Args:
            model: Model to use
            
        Returns:
            LLM client or None if API key not found
        """
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return None
        
        config = LLMConfig(
            api_key=api_key,
            model=model,
            base_url=os.getenv('OPENAI_BASE_URL', "https://api.openai.com/v1")
        )
        
        return cls(config)
    
    async def test_connection(self) -> bool:
        """
        Test the LLM connection.
        
        Returns:
            True if connection successful
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "user",
                        "content": "Test connection. Respond with 'OK'."
                    }
                ],
                max_tokens=10
            )
            
            return "OK" in response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
