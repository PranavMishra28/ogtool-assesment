"""
Utility functions for content extraction and processing.
"""

import os
import re
import tempfile
import uuid
import json
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
import html2text
import markdown

# Configure logger
logger = logging.getLogger("ContentUtils")

# Set up HTML to Markdown converter
html_to_markdown = html2text.HTML2Text()
html_to_markdown.ignore_links = False
html_to_markdown.ignore_images = False
html_to_markdown.ignore_tables = False
html_to_markdown.body_width = 0  # No line wrapping


def get_user_agent() -> str:
    """Get a user-agent string for HTTP requests."""
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


def get_headers() -> Dict[str, str]:
    """Get HTTP headers for requests."""
    return {
        "User-Agent": get_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def fetch_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Fetch the content of a URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        HTML content as string, or None if the request failed
    """
    try:
        response = requests.get(url, headers=get_headers(), timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        return None


def extract_links_from_page(html: str, base_url: str, link_patterns: Optional[List[str]] = None) -> List[str]:
    """
    Extract links from an HTML page that match the given patterns.
    
    Args:
        html: HTML content
        base_url: Base URL for resolving relative links
        link_patterns: List of regex patterns to match against href attributes
        
    Returns:
        List of absolute URLs
    """
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    
    # Compile patterns if provided
    compiled_patterns = None
    if link_patterns:
        compiled_patterns = [re.compile(pattern) for pattern in link_patterns]
    
    # Find all links
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(base_url, href)
        
        # Skip URLs that point to different domains
        if urlparse(absolute_url).netloc != urlparse(base_url).netloc:
            continue
        
        # Check if the URL matches any pattern
        if compiled_patterns:
            if any(pattern.search(href) for pattern in compiled_patterns):
                links.append(absolute_url)
        else:
            links.append(absolute_url)
    
    # Remove duplicates while preserving order
    unique_links = []
    for link in links:
        if link not in unique_links:
            unique_links.append(link)
    
    return unique_links


def clean_html(html: str, selectors_to_remove: Optional[List[str]] = None) -> str:
    """
    Clean HTML by removing unwanted elements.
    
    Args:
        html: HTML content to clean
        selectors_to_remove: CSS selectors for elements to remove
        
    Returns:
        Cleaned HTML
    """
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Default elements to remove
    default_selectors = [
        'header', 'footer', 'nav', 
        '.sidebar', '.navigation', '.menu', '.ads', '.advertisement',
        '.cookie-banner', '.social-media', '.comments', 
        'script', 'style', 'noscript', 'iframe',
        '[class*="cookie"]', '[class*="banner"]', '[id*="banner"]',
        '[class*="popup"]', '[id*="popup"]', '[class*="modal"]', '[id*="modal"]'
    ]
    
    # Combine default and custom selectors
    if selectors_to_remove:
        default_selectors.extend(selectors_to_remove)
    
    # Remove unwanted elements
    for selector in default_selectors:
        for element in soup.select(selector):
            element.decompose()
    
    return str(soup)


def html_to_markdown_text(html: str) -> str:
    """
    Convert HTML to Markdown.
    
    Args:
        html: HTML content
        
    Returns:
        Markdown text
    """
    if not html:
        return ""
    
    # Clean the HTML first
    clean_content = clean_html(html)
    
    # Convert to markdown
    md_content = html_to_markdown.handle(clean_content)
    
    # Clean up markdown
    # Remove excessive newlines
    md_content = re.sub(r'\n{3,}', '\n\n', md_content)
    
    return md_content


def extract_main_content(html: str, content_selectors: Optional[List[str]] = None) -> str:
    """
    Extract the main content from an HTML page.
    
    Args:
        html: HTML content
        content_selectors: CSS selectors to try for finding main content
        
    Returns:
        HTML string containing the main content
    """
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Default content selectors (in order of preference)
    default_selectors = [
        'article', 
        '.post-content', '.entry-content', '.article-content', 
        '.content', '.main-content', '.post', '.entry', 
        'main', '#content', '#main', '#main-content'
    ]
    
    # Combine default and custom selectors
    selectors = content_selectors if content_selectors else default_selectors
    
    # Try each selector in order
    for selector in selectors:
        main_content = soup.select(selector)
        if main_content:
            # If multiple elements match, combine them
            if len(main_content) > 1:
                wrapper = soup.new_tag('div')
                for element in main_content:
                    wrapper.append(element)
                return str(wrapper)
            return str(main_content[0])
    
    # Fallback to body if no selectors matched
    body = soup.find('body')
    if body:
        # Clean the body
        cleaned_body = clean_html(str(body))
        return cleaned_body
    
    # Last resort: return the original HTML
    return html


def extract_title(html: str) -> str:
    """
    Extract the title from an HTML page.
    
    Args:
        html: HTML content
        
    Returns:
        Title string
    """
    if not html:
        return ""
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to get title from article header first
    for selector in ['.post-title', '.entry-title', '.article-title', 'h1.title', 'h1']:
        title_elem = soup.select_one(selector)
        if title_elem:
            return title_elem.get_text(strip=True)
    
    # Fall back to document title
    if soup.title:
        # Clean up title (remove site name, etc.)
        title = soup.title.string
        title = re.sub(r'\s*[|\-–—]\s*.*$', '', title)  # Remove text after separator
        return title.strip()
    
    return "Untitled"


def extract_author(html: str) -> Optional[str]:
    """
    Extract the author from an HTML page.
    
    Args:
        html: HTML content
        
    Returns:
        Author string or None if not found
    """
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try different selectors commonly used for authors
    for selector in [
        '.author', '.byline', '.post-author', '.entry-author', 
        '[rel="author"]', '[itemprop="author"]', '.meta-author'
    ]:
        author_elem = soup.select_one(selector)
        if author_elem:
            return author_elem.get_text(strip=True)
    
    # Look for structured data
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                # Check for author in JSON-LD
                author = data.get('author', {})
                if author:
                    if isinstance(author, dict):
                        return author.get('name')
                    elif isinstance(author, str):
                        return author
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return None


def extract_date_published(html: str) -> Optional[str]:
    """
    Extract the publication date from an HTML page.
    
    Args:
        html: HTML content
        
    Returns:
        Date string or None if not found
    """
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find date in meta tags
    for meta in soup.find_all('meta'):
        property = meta.get('property', '')
        name = meta.get('name', '')
        if 'publish' in property or 'publish' in name or 'date' in property or 'date' in name:
            content = meta.get('content')
            if content:
                return content
    
    # Try common date selectors
    for selector in [
        '.date', '.published', '.post-date', '.entry-date', 
        '[itemprop="datePublished"]', '.meta-date', '.time'
    ]:
        date_elem = soup.select_one(selector)
        if date_elem:
            return date_elem.get_text(strip=True)
    
    # Try structured data
    for script in soup.find_all('script', {'type': 'application/ld+json'}):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                date = data.get('datePublished')
                if date:
                    return date
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return None


def generate_unique_id(text: str) -> str:
    """
    Generate a unique ID based on text content.
    
    Args:
        text: Text to base the ID on
        
    Returns:
        Unique ID string
    """
    # Create a UUID based on the text
    unique_id = str(uuid.uuid5(uuid.NAMESPACE_URL, text))
    return unique_id
