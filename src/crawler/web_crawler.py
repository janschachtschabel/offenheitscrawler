"""
Web crawler implementation using crawl4ai for the Offenheitscrawler.
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
import re
from loguru import logger

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    logger.warning("crawl4ai not available, falling back to basic crawler")

from bs4 import BeautifulSoup
import requests


@dataclass
class CrawlResult:
    """Result of crawling a single page."""
    url: str
    title: str
    content: str
    links: List[str]
    success: bool
    error_message: Optional[str] = None
    crawl_time: Optional[datetime] = None


@dataclass
class OrganizationCrawlResult:
    """Result of crawling an entire organization."""
    organization_name: str
    base_url: str
    pages: List[CrawlResult]
    total_pages: int
    successful_pages: int
    crawl_duration: timedelta
    errors: List[str]


class WebCrawler:
    """Web crawler for organization websites."""
    
    def __init__(
        self,
        max_pages_per_site: int = 10,
        delay_between_requests: float = 1.0,
        timeout: int = 30,
        max_concurrent: int = 3,
        respect_robots_txt: bool = True,
        crawling_strategy: str = "intelligent",
        intra_domain_delay: float = 1.0,
        inter_domain_delay: float = 2.0
    ):
        """
        Initialize web crawler.
        
        Args:
            max_pages_per_site: Maximum pages to crawl per organization
            delay_between_requests: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_concurrent: Maximum concurrent requests
            respect_robots_txt: Whether to respect robots.txt
        """
        self.max_pages_per_site = max_pages_per_site
        self.delay_between_requests = delay_between_requests
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.respect_robots_txt = respect_robots_txt
        self.crawling_strategy = crawling_strategy
        self.intra_domain_delay = intra_domain_delay
        self.inter_domain_delay = inter_domain_delay
        
        self.logger = logger.bind(name=self.__class__.__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # User agent for polite crawling
        self.user_agent = (
            "Offenheitscrawler/1.0 (Research Tool; "
            "https://github.com/offenheitscrawler) "
            "Mozilla/5.0 (compatible)"
        )
    
    async def crawl_organization(
        self, 
        organization_name: str, 
        base_url: str,
        llm_client=None,
        criteria_names: List[str] = None,
        status_callback=None
    ) -> OrganizationCrawlResult:
        """
        Crawl an organization's website using different strategies.
        
        Args:
            organization_name: Name of the organization
            base_url: Base URL of the organization's website
            llm_client: Optional LLM client for intelligent page selection
            criteria_names: List of criteria names for intelligent selection
            status_callback: Optional callback function for status updates
        
        Returns:
            Organization crawl result
        """
        start_time = datetime.now()
        self.logger.info(f"Starting crawl for {organization_name}: {base_url} (Strategy: {self.crawling_strategy})")
        
        def update_status(message: str):
            """Update status via callback if provided."""
            if status_callback:
                status_callback(message)
            self.logger.info(message)
        
        try:
            # Initialize session
            await self._init_session()
            
            update_status(f"🔍 Lade Hauptseite: {base_url}")
            
            # Get initial page and extract links
            main_page = await self._crawl_page(base_url)
            
            if not main_page.success:
                return OrganizationCrawlResult(
                    organization_name=organization_name,
                    base_url=base_url,
                    pages=[main_page],
                    total_pages=1,
                    successful_pages=0,
                    crawl_duration=datetime.now() - start_time,
                    errors=[f"Failed to crawl main page: {main_page.error_message}"]
                )
            
            # Handle different crawling strategies
            if self.crawling_strategy == "homepage_only":
                update_status("📄 Nur Hauptseite wird analysiert")
                urls_to_crawl = [base_url]
                
            elif self.crawling_strategy == "all_pages":
                update_status("🔍 Suche alle verfügbaren Unterseiten...")
                internal_links = self._extract_internal_links(base_url, main_page.links)
                urls_to_crawl = [base_url] + internal_links
                update_status(f"📊 {len(internal_links)} Unterseiten gefunden, alle werden gecrawlt")
                
            elif self.crawling_strategy == "intelligent" and llm_client and criteria_names:
                update_status("🤖 KI analysiert verfügbare Unterseiten...")
                internal_links = self._extract_internal_links(base_url, main_page.links)
                
                if len(internal_links) == 0:
                    update_status("📄 Keine Unterseiten gefunden, nur Hauptseite wird analysiert")
                    urls_to_crawl = [base_url]
                else:
                    # Prepare subpages info for LLM
                    subpages_info = []
                    for link in internal_links[:50]:  # Limit for performance
                        # Try to get title from the link or use URL path
                        title = self._extract_title_from_url(link)
                        subpages_info.append({"url": link, "title": title})
                    
                    update_status(f"🤖 KI wählt die besten {self.max_pages_per_site - 1} von {len(internal_links)} Unterseiten aus...")
                    
                    try:
                        selected_urls = await llm_client.select_best_subpages(
                            organization_name=organization_name,
                            base_url=base_url,
                            subpages=subpages_info,
                            criteria_names=criteria_names,
                            max_pages=self.max_pages_per_site - 1  # -1 for main page
                        )
                        urls_to_crawl = [base_url] + selected_urls
                        update_status(f"✅ KI hat {len(selected_urls)} relevante Unterseiten ausgewählt")
                    except Exception as e:
                        self.logger.warning(f"LLM selection failed, falling back to first {self.max_pages_per_site - 1} pages: {str(e)}")
                        urls_to_crawl = [base_url] + internal_links[:self.max_pages_per_site - 1]
                        update_status(f"⚠️ KI-Auswahl fehlgeschlagen, verwende erste {len(urls_to_crawl) - 1} Unterseiten")
            else:
                # Default: limited pages
                update_status("🔍 Suche Unterseiten...")
                internal_links = self._extract_internal_links(base_url, main_page.links)
                urls_to_crawl = [base_url] + internal_links[:self.max_pages_per_site - 1]
                update_status(f"📊 {len(urls_to_crawl) - 1} Unterseiten werden gecrawlt")
            
            # Crawl all selected pages
            pages = [main_page]
            errors = []
            
            total_pages = len(urls_to_crawl)
            update_status(f"🕷️ Starte Crawling von {total_pages} Seiten...")
            
            # Crawl additional pages with rate limiting
            for idx, url in enumerate(urls_to_crawl[1:], 1):  # Skip main page (already crawled)
                update_status(f"🔍 Crawle Seite {idx + 1}/{total_pages}: {self._get_page_name(url)}")
                
                await asyncio.sleep(self.intra_domain_delay)
                
                page_result = await self._crawl_page(url)
                pages.append(page_result)
                
                if page_result.success:
                    update_status(f"✅ Erfolgreich: {self._get_page_name(url)}")
                else:
                    update_status(f"❌ Fehler: {self._get_page_name(url)} - {page_result.error_message}")
                    if page_result.error_message:
                        errors.append(f"{url}: {page_result.error_message}")
            
            successful_pages = sum(1 for page in pages if page.success)
            
            result = OrganizationCrawlResult(
                organization_name=organization_name,
                base_url=base_url,
                pages=pages,
                total_pages=len(pages),
                successful_pages=successful_pages,
                crawl_duration=datetime.now() - start_time,
                errors=errors
            )
            
            update_status(
                f"🎉 Crawling abgeschlossen: {successful_pages}/{len(pages)} Seiten erfolgreich "
                f"(Dauer: {result.crawl_duration.total_seconds():.1f}s)"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error crawling {organization_name}: {str(e)}")
            return OrganizationCrawlResult(
                organization_name=organization_name,
                base_url=base_url,
                pages=[],
                total_pages=0,
                successful_pages=0,
                crawl_duration=datetime.now() - start_time,
                errors=[f"Crawling failed: {str(e)}"]
            )
        
        finally:
            await self._close_session()
    
    async def _init_session(self) -> None:
        """Initialize HTTP session."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=self.max_concurrent)
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
    
    async def _close_session(self) -> None:
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def _crawl_page(self, url: str) -> CrawlResult:
        """
        Crawl a single page.
        
        Args:
            url: URL to crawl
        
        Returns:
            Crawl result for the page
        """
        crawl_time = datetime.now()
        
        try:
            # Use crawl4ai if available, otherwise fallback to basic crawler
            if CRAWL4AI_AVAILABLE:
                return await self._crawl_with_crawl4ai(url, crawl_time)
            else:
                return await self._crawl_with_aiohttp(url, crawl_time)
                
        except Exception as e:
            self.logger.error(f"Error crawling {url}: {str(e)}")
            return CrawlResult(
                url=url,
                title="",
                content="",
                links=[],
                success=False,
                error_message=str(e),
                crawl_time=crawl_time
            )
    
    async def _crawl_with_crawl4ai(self, url: str, crawl_time: datetime) -> CrawlResult:
        """Crawl page using crawl4ai."""
        try:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(url=url)
                
                if result.success:
                    # Extract links from the HTML
                    soup = BeautifulSoup(result.html, 'html.parser')
                    links = [a.get('href') for a in soup.find_all('a', href=True)]
                    links = [link for link in links if link]  # Remove empty links
                    
                    return CrawlResult(
                        url=url,
                        title=result.metadata.get('title', '') if result.metadata else '',
                        content=result.cleaned_html or result.markdown or '',
                        links=links,
                        success=True,
                        crawl_time=crawl_time
                    )
                else:
                    return CrawlResult(
                        url=url,
                        title="",
                        content="",
                        links=[],
                        success=False,
                        error_message="crawl4ai failed to crawl page",
                        crawl_time=crawl_time
                    )
                    
        except Exception as e:
            # Fallback to basic crawler
            return await self._crawl_with_aiohttp(url, crawl_time)
    
    async def _crawl_with_aiohttp(self, url: str, crawl_time: datetime) -> CrawlResult:
        """Crawl page using aiohttp and BeautifulSoup."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_tag = soup.find('title')
                    title = title_tag.get_text().strip() if title_tag else ''
                    
                    # Extract text content
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    content = soup.get_text()
                    # Clean up whitespace
                    content = re.sub(r'\s+', ' ', content).strip()
                    
                    # Extract links
                    links = [a.get('href') for a in soup.find_all('a', href=True)]
                    links = [link for link in links if link]  # Remove empty links
                    
                    return CrawlResult(
                        url=url,
                        title=title,
                        content=content,
                        links=links,
                        success=True,
                        crawl_time=crawl_time
                    )
                else:
                    return CrawlResult(
                        url=url,
                        title="",
                        content="",
                        links=[],
                        success=False,
                        error_message=f"HTTP {response.status}",
                        crawl_time=crawl_time
                    )
                    
        except Exception as e:
            return CrawlResult(
                url=url,
                title="",
                content="",
                links=[],
                success=False,
                error_message=str(e),
                crawl_time=crawl_time
            )
    
    def _extract_internal_links(self, base_url: str, links: List[str]) -> List[str]:
        """
        Extract internal links from a list of links.
        
        Args:
            base_url: Base URL of the website
            links: List of all links found on the page
        
        Returns:
            List of internal links
        """
        base_domain = urlparse(base_url).netloc
        internal_links = set()
        
        for link in links:
            try:
                # Convert relative URLs to absolute
                absolute_url = urljoin(base_url, link)
                parsed_url = urlparse(absolute_url)
                
                # Check if it's an internal link
                if (parsed_url.netloc == base_domain and 
                    parsed_url.scheme in ['http', 'https']):
                    
                    # Clean URL (remove fragments and query params for deduplication)
                    clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                    
                    # Avoid common non-content URLs
                    if not self._is_excluded_url(clean_url):
                        internal_links.add(clean_url)
                        
            except Exception:
                continue  # Skip malformed URLs
        
        # Remove the base URL itself
        internal_links.discard(base_url)
        
        return list(internal_links)
    
    def _is_excluded_url(self, url: str) -> bool:
        """
        Check if URL should be excluded from crawling.
        
        Args:
            url: URL to check
        
        Returns:
            True if URL should be excluded
        """
        excluded_patterns = [
            r'\.pdf$', r'\.doc$', r'\.docx$', r'\.xls$', r'\.xlsx$',
            r'\.zip$', r'\.rar$', r'\.tar$', r'\.gz$',
            r'\.jpg$', r'\.jpeg$', r'\.png$', r'\.gif$', r'\.svg$',
            r'\.mp3$', r'\.mp4$', r'\.avi$', r'\.mov$',
            r'/login', r'/admin', r'/wp-admin', r'/user',
            r'mailto:', r'tel:', r'javascript:', r'#',
            r'/feed', r'/rss', r'\.xml$'
        ]
        
        url_lower = url.lower()
        
        for pattern in excluded_patterns:
            if re.search(pattern, url_lower):
                return True
        
        return False
    
    async def check_robots_txt(self, base_url: str) -> Dict[str, Any]:
        """
        Check robots.txt for crawling permissions.
        
        Args:
            base_url: Base URL of the website
        
        Returns:
            Dictionary with robots.txt information
        """
        robots_url = urljoin(base_url, '/robots.txt')
        
        try:
            await self._init_session()
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    robots_content = await response.text()
                    return {
                        'exists': True,
                        'content': robots_content,
                        'crawl_delay': self._extract_crawl_delay(robots_content)
                    }
                else:
                    return {'exists': False, 'content': '', 'crawl_delay': None}
                    
        except Exception as e:
            self.logger.warning(f"Could not check robots.txt for {base_url}: {str(e)}")
            return {'exists': False, 'content': '', 'crawl_delay': None}
    
    def _extract_crawl_delay(self, robots_content: str) -> Optional[float]:
        """Extract crawl delay from robots.txt content."""
        try:
            for line in robots_content.split('\n'):
                line = line.strip().lower()
                if line.startswith('crawl-delay:'):
                    delay_str = line.split(':', 1)[1].strip()
                    return float(delay_str)
        except Exception:
            pass
        
        return None
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a meaningful title from URL path."""
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if not path:
                return "Startseite"
            
            # Split path and get last meaningful part
            parts = [part for part in path.split('/') if part]
            if parts:
                title = parts[-1]
                # Clean up common file extensions and URL patterns
                title = re.sub(r'\.(html?|php|asp|jsp)$', '', title, flags=re.IGNORECASE)
                title = title.replace('-', ' ').replace('_', ' ')
                return title.title()
            
            return "Unbekannte Seite"
        except Exception:
            return "Unbekannte Seite"
    
    def _get_page_name(self, url: str) -> str:
        """Get a short, readable name for a page URL."""
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if not path:
                return "Startseite"
            
            # Get last part of path
            parts = [part for part in path.split('/') if part]
            if parts:
                name = parts[-1]
                # Clean up and truncate
                name = re.sub(r'\.(html?|php|asp|jsp)$', '', name, flags=re.IGNORECASE)
                name = name.replace('-', ' ').replace('_', ' ')
                # Truncate if too long
                if len(name) > 30:
                    name = name[:27] + "..."
                return name.title()
            
            return "Unbekannte Seite"
        except Exception:
            return "Unbekannte Seite"
