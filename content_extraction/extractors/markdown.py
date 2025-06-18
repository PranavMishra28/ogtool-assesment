"""
Markdown file extractor module.

This module provides functionality to extract content from markdown files,
either local or remote, and convert them into ContentItem objects.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import requests
from urllib.parse import urlparse

from content_extraction.base import ContentExtractor, ContentItem
from content_extraction.utils import generate_unique_id


class MarkdownExtractor(ContentExtractor):
    """Extractor for markdown files."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the MarkdownExtractor.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.md_config = config.get("extractors", {}).get("markdown", {})
        
        # Default patterns for extracting title from markdown content
        self.title_patterns = self.md_config.get(
            "title_patterns", [
                r'^# (.+)$',  # Match level 1 headers
                r'^(.+)\n=+\s*$',  # Match underlined headers
            ]
        )
        
        self.compiled_title_patterns = [re.compile(pattern, re.MULTILINE) for pattern in self.title_patterns]
        
    def can_handle(self, source: str) -> bool:
        """
        Check if this extractor can handle the given source.
        
        Args:
            source: File path or URL to check
            
        Returns:
            True if this is a markdown file, False otherwise
        """
        # Check for local files with .md extension
        if os.path.isfile(source) and source.lower().endswith('.md'):
            return True
        
        # Check for remote markdown files
        parsed_url = urlparse(source)
        if parsed_url.scheme in ('http', 'https') and parsed_url.path.lower().endswith('.md'):
            return True
            
        return False
    
    def extract(self, source: str) -> List[ContentItem]:
        """
        Extract content from a markdown file.
        
        Args:
            source: File path or URL
            
        Returns:
            List of ContentItem objects (usually just one)
        """
        self.logger.info(f"Extracting content from markdown file: {source}")
        
        try:
            # Load content based on source type
            content = self._load_content(source)
            if not content:
                self.logger.error(f"Failed to load markdown content from {source}")
                return []
            
            # Extract title from content
            title = self._extract_title(content, source)
            
            # Generate ID
            content_id = generate_unique_id(title)
            
            # Create a ContentItem
            return [ContentItem(
                content_id=content_id,
                title=title,
                content=content,
                source_url=source if source.startswith(('http://', 'https://')) else None,
                content_type="documentation",
                metadata={
                    "file_path": source if not source.startswith(('http://', 'https://')) else None,
                    "format": "markdown"
                }
            )]
            
        except Exception as e:
            self.logger.error(f"Error extracting content from markdown file {source}: {e}", exc_info=True)
            return []
    
    def _load_content(self, source: str) -> Optional[str]:
        """
        Load markdown content from file or URL.
        
        Args:
            source: File path or URL
            
        Returns:
            Markdown content or None if loading failed
        """
        try:
            # Load from local file
            if os.path.isfile(source):
                with open(source, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # Load from URL
            if source.startswith(('http://', 'https://')):
                response = requests.get(source)
                response.raise_for_status()
                return response.text
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading markdown content from {source}: {e}")
            return None
    
    def _extract_title(self, content: str, source: str) -> str:
        """
        Extract title from markdown content.
        
        Args:
            content: Markdown content
            source: Source path or URL as fallback
            
        Returns:
            Extracted title or filename as fallback
        """
        # Try to find title using patterns
        for pattern in self.compiled_title_patterns:
            match = pattern.search(content)
            if match:
                return match.group(1).strip()
        
        # Fall back to filename or URL path
        if os.path.isfile(source):
            return Path(source).stem  # Get filename without extension
        
        if source.startswith(('http://', 'https://')):
            parsed_url = urlparse(source)
            path = parsed_url.path.strip('/')
            filename = path.split('/')[-1]  # Get last part of path
            return Path(filename).stem  # Get filename without extension
        
        return "Untitled Markdown Document"
