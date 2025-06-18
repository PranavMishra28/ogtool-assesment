"""
Substack extractor module.

This module provides functionality to extract content from Substack newsletters.
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


class SubstackExtractor(ContentExtractor):
    """Extractor for Substack newsletters."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SubstackExtractor.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.delay_range = config.get("sources", {}).get("blog", {}).get(
            "delay_between_requests", [1, 3]
        )
    
    def can_handle(self, source: str) -> bool:
        """
        Check if this extractor can handle the given source.
        
        Args:
            source: URL to check
            
        Returns:
            True if this is a Substack URL, False otherwise
        """
        return "substack.com" in source.lower()
    
    def extract(self, url: str) -> List[ContentItem]:
        """
        Extract content from a Substack newsletter.
        
        Args:
            url: Substack URL
            
        Returns:
            List of ContentItem objects
        """
        self.logger.info(f"Extracting content from Substack: {url}")
        
        try:
            # Fetch the main page
            html_content = fetch_url(url)
            if not html_content:
                self.logger.error(f"Failed to fetch Substack URL: {url}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find main author (for filtering)
            main_author = self._find_main_author(soup)
            self.logger.info(f"Main author identified as: {main_author or 'Unknown'}")
            
            # Find archive link
            archive_link = None
            for a in soup.find_all('a', href=True):
                if '/archive' in a['href']:
                    archive_link = a['href']
                    if not archive_link.startswith('http'):
                        # Ensure absolute URL
                        if archive_link.startswith('/'):
                            archive_link = f"{url.rstrip('/')}{archive_link}"
                        else:
                            archive_link = f"{url.rstrip('/')}/{archive_link}"
                    break
            
            if not archive_link:
                self.logger.warning("Could not find archive link, using main page for post extraction")
                archive_link = url
            
            # Extract post links from archive
            post_links = self._extract_post_links(archive_link)
            if not post_links:
                self.logger.error(f"No post links found on Substack archive: {archive_link}")
                return []
            
            # Process each post
            extracted_items = []
            for link in tqdm(post_links, desc="Processing Substack posts", unit="post"):
                try:
                    items = self._process_post(link)
                    if items and main_author:
                        # Filter posts by main author if available
                        items = [item for item in items 
                                if not item.author or item.author == main_author]
                    
                    extracted_items.extend(items)
                    
                    # Add a small delay
                    time.sleep(random.uniform(self.delay_range[0], self.delay_range[1]))
                except Exception as e:
                    self.logger.error(f"Error processing Substack post {link}: {e}")
            
            self.logger.info(f"Processed {len(extracted_items)} Substack posts")
            return extracted_items
            
        except Exception as e:
            self.logger.error(f"Error processing Substack {url}: {e}", exc_info=True)
            return []
    
    def _find_main_author(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Find the main author of the Substack.
        
        Args:
            soup: BeautifulSoup object of the main page
            
        Returns:
            Author name or None if not found
        """
        # Look for author in header
        for selector in ['.header-author', '.author-name', '.site-author', 'h1.author']:
            author_elem = soup.select_one(selector)
            if author_elem:
                return author_elem.get_text(strip=True)
        
        # Look in meta tags
        for meta in soup.find_all('meta', {'name': 'author'}):
            return meta.get('content')
        
        for meta in soup.find_all('meta', {'property': 'og:site_name'}):
            return meta.get('content')
        
        return None
    
    def _extract_post_links(self, archive_url: str) -> List[str]:
        """
        Extract post links from Substack archive page.
        
        Args:
            archive_url: URL of the archive page
            
        Returns:
            List of post URLs
        """
        html_content = fetch_url(archive_url)
        if not html_content:
            self.logger.error(f"Failed to fetch archive URL: {archive_url}")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all post links
        post_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Check if it's a post link (typically has /p/ in the URL)
            if '/p/' in href:
                # Ensure absolute URL
                if not href.startswith('http'):
                    base_url = '/'.join(archive_url.split('/')[:3])  # Get domain
                    if href.startswith('/'):
                        href = f"{base_url}{href}"
                    else:
                        href = f"{base_url}/{href}"
                post_links.append(href)
        
        # Remove duplicates while preserving order
        unique_links = []
        for link in post_links:
            if link not in unique_links:
                unique_links.append(link)
        
        return unique_links
    
    def _process_post(self, url: str) -> List[ContentItem]:
        """
        Process an individual Substack post.
        
        Args:
            url: URL of the post
            
        Returns:
            List with a single ContentItem
        """
        try:
            html_content = fetch_url(url)
            if not html_content:
                self.logger.error(f"Failed to fetch post URL: {url}")
                return []
            
            # Extract post title
            title = extract_title(html_content)
            if not title:
                self.logger.warning(f"Could not extract title from {url}")
                title = "Untitled Post"
            
            # Extract main content - Substack has specific content classes
            main_content_html = extract_main_content(html_content, [
                '.single-post', '.post-content', '.substack-post', 
                'article', '.post'
            ])
            
            if not main_content_html or len(main_content_html) < 100:
                self.logger.warning(f"Extracted content from {url} is too short or empty")
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
                content_type="newsletter",
                author=author,
                date_published=date_published
            )
            
            return [content_item]
            
        except Exception as e:
            self.logger.error(f"Error processing Substack post {url}: {e}", exc_info=True)
            return []
