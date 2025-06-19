"""
Generic blog extractor module.

This module provides functionality to extract content from generic blog sites.
"""

import re
import time
import random
import logging
import uuid
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
import html2text
from tqdm import tqdm

from content_extraction.base import ContentExtractor, ContentItem


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
        self.delay_between_requests = config.get("sources", {}).get("blog", {}).get(
            "delay_between_requests", [1, 3]
        )
        
        # Set up HTML to markdown converter
        self.markdown_converter = html2text.HTML2Text()
        self.markdown_converter.ignore_links = False
        self.markdown_converter.ignore_images = False
        self.markdown_converter.ignore_emphasis = False
        self.markdown_converter.ignore_tables = False
        self.markdown_converter.body_width = 0  # No line wrapping
        
        # Define headers for requests
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
    
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
            "github.com" in source.lower(),
            source.lower().endswith(".pdf"),
            source.lower().endswith(".md")
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
            html_content = self._fetch_url(url)
            if not html_content:
                self.logger.error(f"Failed to fetch URL: {url}")
                return []
            
            # Process the page
            items = self._process_page(url, html_content)
            self.logger.info(f"Extracted {len(items)} item(s) from {url}")
            return items
                
        except Exception as e:
            self.logger.error(f"Error processing generic blog {url}: {e}", exc_info=True)
            return []
    
    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch content from a URL with error handling."""
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch URL {url}: {e}", exc_info=True)
            return None
    
    def _process_page(self, url: str, html_content: str) -> List[ContentItem]:
        """Process a blog page and extract content."""
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            if not title:
                title = "Untitled Article"
            
            # Extract main content
            main_content_html = self._extract_main_content(soup)
            
            # Convert to markdown
            markdown_content = self._html_to_markdown(main_content_html)
            
            # Extract metadata
            author = self._extract_author(soup)
            date_published = self._extract_date_published(soup)
            
            # Generate unique ID
            content_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url + title))
            
            # Create content item
            content_item = ContentItem(
                content_id=content_id,
                title=title,
                content=markdown_content,
                source_url=url,
                content_type="article",
                author=author,
                date_published=date_published,
                metadata={
                    "extracted_from": "generic_blog",
                    "extraction_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
            return [content_item]
            
        except Exception as e:
            self.logger.error(f"Error processing blog page {url}: {e}", exc_info=True)
            return []
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from a BeautifulSoup object."""
        # Try the title tag first
        title_tag = soup.title
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            # Clean up title (remove site name, etc.)
            title = re.sub(r'\s*[|–-].*$', '', title)
            return title
        
        # Try h1 tags
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        # Try article header
        header = soup.find('header')
        if header:
            h_tag = header.find(['h1', 'h2'])
            if h_tag:
                return h_tag.get_text(strip=True)
        
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content from a BeautifulSoup object."""
        # Remove unwanted elements
        for selector in ['script', 'style', 'nav', 'header', 'footer', '.ads', 
                        '.sidebar', '.comments', '.navbar', '.menu', '.navigation']:
            for element in soup.select(selector):
                element.decompose()
        
        # Try to find the main content using common selectors
        main_content = None
        
        # Try common content selectors
        for selector in self.article_selectors + ['main', '.content', '.post-content', '.entry-content']:
            content = soup.select_one(selector)
            if content:
                # Check if the content has enough text
                text = content.get_text(strip=True)
                if len(text) > 200:  # Reasonable minimum for an article
                    main_content = content
                    break
        
        # If no suitable content found, try to find the largest text block
        if not main_content:
            max_text_length = 0
            for tag in soup.find_all(['div', 'section', 'article']):
                text = tag.get_text(strip=True)
                if len(text) > max_text_length:
                    max_text_length = len(text)
                    main_content = tag
        
        # If all else fails, use the body
        if not main_content or len(main_content.get_text(strip=True)) < 200:
            main_content = soup.body or soup
        
        return str(main_content)
    
    def _html_to_markdown(self, html_content: str) -> str:
        """Convert HTML to markdown text."""
        markdown_text = self.markdown_converter.handle(html_content)
        
        # Clean up the markdown
        markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)  # Replace excessive newlines
        
        return markdown_text
    
    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author information from a BeautifulSoup object."""
        # Try common author selectors
        for selector in [
            '[rel="author"]', '.author', '.byline', '[itemprop="author"]', 
            '.post-author', '.entry-author', '.author-name', '.writer'
        ]:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text(strip=True)
        
        # Try meta tags
        meta_author = soup.find('meta', {'name': 'author'}) or soup.find('meta', {'property': 'author'})
        if meta_author and meta_author.get('content'):
            return meta_author['content']
        
        return None
    
    def _extract_date_published(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date from a BeautifulSoup object."""
        # Try time tag
        time_tag = soup.find('time')
        if time_tag:
            if time_tag.has_attr('datetime'):
                return time_tag['datetime']
            return time_tag.get_text(strip=True)
        
        # Try common date selectors
        for selector in [
            '[itemprop="datePublished"]', '.published', '.post-date', 
            '.entry-date', '.date', '.timestamp', '.post-timestamp'
        ]:
            date_elem = soup.select_one(selector)
            if date_elem:
                if date_elem.has_attr('datetime'):
                    return date_elem['datetime']
                return date_elem.get_text(strip=True)
        
        # Try meta tags
        for prop in ['article:published_time', 'published_time', 'publication_date']:
            meta_date = soup.find('meta', {'property': prop})
            if meta_date and meta_date.get('content'):
                return meta_date['content']
        
        return None
