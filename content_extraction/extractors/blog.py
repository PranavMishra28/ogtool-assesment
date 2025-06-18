"""
Generic blog extractor module.

This module provides functionality to extract content from generic blog sites.
"""

import re
import time
import random
import logging
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from content_extraction.base import ContentExtractor, ContentItem
from content_extraction.utils import (
    fetch_url, extract_links_from_page, extract_main_content,
    extract_title, extract_author, extract_date_published,
    html_to_markdown_text, generate_unique_id
)


class GenericBlogExtractor(ContentExtractor):
    """Extractor for generic blog content."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GenericBlogExtractor.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.article_selectors = config.get("extractors", {}).get("generic_blog", {}).get(
            "article_selectors", ["article", ".post", ".entry", ".blog-post"]
        )
        self.link_patterns = config.get("extractors", {}).get("generic_blog", {}).get(
            "list_page_link_patterns", ["/(article|post|blog)/", "/\\d{4}/\\d{2}/"]
        )
        self.delay_range = config.get("sources", {}).get("blog", {}).get(
            "delay_between_requests", [1, 3]
        )
    
    def can_handle(self, source: str) -> bool:
        """
        Check if this extractor can handle the given source.
        
        Args:
            source: URL to check
            
        Returns:
            True if this extractor can handle the source, False otherwise
        """
        return source.startswith(("http://", "https://")) and not any([
            "substack.com" in source.lower(),
            "drive.google.com" in source.lower(),
            source.lower().endswith(".pdf")
        ])
    
    def extract(self, url: str) -> List[ContentItem]:
        """
        Extract content from a generic blog.
        
        Args:
            url: Blog URL
            
        Returns:
            List of ContentItem objects
        """
        self.logger.info(f"Extracting content from generic blog: {url}")
        
        try:
            # Fetch the page content
            html_content = fetch_url(url)
            if not html_content:
                self.logger.error(f"Failed to fetch URL: {url}")
                return []
            
            # Determine if it's a list page or an individual article
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Heuristic to determine if it's a list page
            article_count = len(soup.select(','.join(self.article_selectors)))
            link_count = 0
            
            for pattern in self.link_patterns:
                compiled_pattern = re.compile(pattern)
                links = soup.find_all('a', href=compiled_pattern)
                link_count += len(links)
            
            if article_count > 3 or link_count > 10:
                # Process as a list page
                extracted_items = self._process_list_page(url, html_content)
                self.logger.info(f"Processed {len(extracted_items)} articles from list page")
                return extracted_items
            else:
                # Process as an individual page
                extracted_items = self._process_individual_page(url, html_content)
                self.logger.info(f"Processed individual page with {len(extracted_items)} items")
                return extracted_items
                
        except Exception as e:
            self.logger.error(f"Error processing generic blog {url}: {e}", exc_info=True)
            return []
    
    def _process_list_page(self, url: str, html_content: str) -> List[ContentItem]:
        """
        Process a blog list page.
        
        Args:
            url: List page URL
            html_content: HTML content
            
        Returns:
            List of ContentItem objects
        """
        # Extract links to individual articles
        links = extract_links_from_page(html_content, url, self.link_patterns)
        total_links = len(links)
        self.logger.info(f"Found {total_links} articles on list page")
        
        extracted_items = []
        
        # Process each article link with progress indicator
        for link in tqdm(links, desc="Processing articles", unit="article"):
            try:
                items = self._process_individual_page(link)
                extracted_items.extend(items)
                
                # Add a small delay to avoid overloading the server
                time.sleep(random.uniform(self.delay_range[0], self.delay_range[1]))
            except Exception as e:
                self.logger.error(f"Error processing article {link}: {e}")
        
        return extracted_items
    
    def _process_individual_page(self, url: str, html_content: Optional[str] = None) -> List[ContentItem]:
        """
        Process an individual blog page.
        
        Args:
            url: URL of the page
            html_content: HTML content if already fetched, otherwise None
            
        Returns:
            List with a single ContentItem
        """
        try:
            # Fetch content if not provided
            if not html_content:
                html_content = fetch_url(url)
                if not html_content:
                    self.logger.error(f"Failed to fetch URL: {url}")
                    return []
            
            # Extract article title
            title = extract_title(html_content)
            if not title:
                self.logger.warning(f"Could not extract title from {url}")
                title = "Untitled Article"
            
            # Extract main content
            main_content_html = extract_main_content(html_content, self.article_selectors)
            if not main_content_html or len(main_content_html) < 100:  # Sanity check
                self.logger.warning(f"Extracted content from {url} is too short or empty")
                # Try using body as fallback
                soup = BeautifulSoup(html_content, 'html.parser')
                body = soup.find('body')
                if body:
                    main_content_html = str(body)
                else:
                    self.logger.error(f"Could not extract meaningful content from {url}")
                    return []
            
            # Convert to markdown
            markdown_content = html_to_markdown_text(main_content_html)
            if not markdown_content or len(markdown_content) < 100:
                self.logger.error(f"Markdown conversion failed or content too short for {url}")
                return []
            
            # Extract metadata
            author = extract_author(html_content)
            date_published = extract_date_published(html_content)
            
            # Create content item
            content_item = ContentItem(
                content_id=generate_unique_id(),
                title=title,
                content=markdown_content,
                source_url=url,
                content_type="article",
                author=author,
                date_published=date_published
            )
            
            return [content_item]
            
        except Exception as e:
            self.logger.error(f"Error processing page {url}: {e}", exc_info=True)
            return []
