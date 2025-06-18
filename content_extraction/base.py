"""
Base classes for the content extraction framework.

This module provides the abstract base classes and interfaces for the content extraction 
system, ensuring all content sources implement a consistent API.
"""

import abc
from typing import Dict, List, Any, Optional
import json
import os
import logging
from pathlib import Path


class ContentItem:
    """Represents a single piece of extracted content with metadata."""
    
    def __init__(
        self,
        content_id: str,
        title: str,
        content: str,
        source_url: Optional[str] = None,
        content_type: str = "article",
        author: Optional[str] = None,
        date_published: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ContentItem.
        
        Args:
            content_id: Unique identifier for this content
            title: Title of the content
            content: The main content in markdown format
            source_url: Original URL where the content was extracted from
            content_type: Type of content (article, chapter, post, etc.)
            author: Author of the content
            date_published: Publication date
            tags: List of tags/categories
            metadata: Additional metadata as key-value pairs
        """
        self.content_id = content_id
        self.title = title
        self.content = content
        self.source_url = source_url
        self.content_type = content_type
        self.author = author
        self.date_published = date_published
        self.tags = tags or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ContentItem to a dictionary.
        
        Returns:
            Dictionary representation of the ContentItem.
        """
        return {
            "id": self.content_id,
            "title": self.title,
            "content": self.content,
            "source_url": self.source_url,
            "content_type": self.content_type,
            "author": self.author,
            "date_published": self.date_published,
            "tags": self.tags,
            "metadata": self.metadata
        }


class ContentExtractor(abc.ABC):
    """Abstract base class for content extractors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ContentExtractor.
        
        Args:
            config: Configuration dictionary for the extractor
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abc.abstractmethod
    def extract(self, source: str) -> List[ContentItem]:
        """
        Extract content items from the source.
        
        Args:
            source: URL, file path, or other identifier for the content source
            
        Returns:
            List of ContentItem objects
        """
        pass
    
    @abc.abstractmethod
    def can_handle(self, source: str) -> bool:
        """
        Check if this extractor can handle the given source.
        
        Args:
            source: URL, file path, or other identifier to check
            
        Returns:
            True if this extractor can handle the source, False otherwise
        """
        pass


class ContentProcessor:
    """Base class for processing extracted content."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the ContentProcessor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def clean_content(self, content: str) -> str:
        """
        Clean the content by removing unwanted elements.
        
        Args:
            content: Raw content string
            
        Returns:
            Cleaned content string
        """
        # Basic cleaning (override in subclasses for specific cleaning)
        return content
    
    def convert_to_markdown(self, content: str) -> str:
        """
        Convert HTML content to markdown.
        
        Args:
            content: HTML content
            
        Returns:
            Markdown content
        """
        # Basic conversion (override in subclasses for specific conversion)
        return content


class ExtractorManager:
    """Manager class for content extractors."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the ExtractorManager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config = self._load_config(config_path)
        self.extractors: List[ContentExtractor] = []
        self.logger = self._setup_logger()
        self.items: List[ContentItem] = []
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from a JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading configuration: {e}")
            return {}
    
    def _setup_logger(self) -> logging.Logger:
        """
        Set up logging.
        
        Returns:
            Configured logger
        """
        log_level = getattr(logging, self.config.get("log_level", "INFO"))
        logger = logging.getLogger("ExtractorManager")
        logger.setLevel(log_level)
        
        # Create handlers
        file_handler = logging.FileHandler("extraction.log")
        console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def register_extractor(self, extractor: ContentExtractor) -> None:
        """
        Register a content extractor.
        
        Args:
            extractor: ContentExtractor instance to register
        """
        self.extractors.append(extractor)
        self.logger.info(f"Registered extractor: {extractor.__class__.__name__}")
    
    def extract(self, source: str) -> List[ContentItem]:
        """
        Extract content from a source using the appropriate extractor.
        
        Args:
            source: URL, file path, or other identifier for the content source
            
        Returns:
            List of ContentItem objects
        """
        for extractor in self.extractors:
            if extractor.can_handle(source):
                self.logger.info(f"Using {extractor.__class__.__name__} for {source}")
                items = extractor.extract(source)
                self.items.extend(items)
                return items
        
        self.logger.warning(f"No suitable extractor found for {source}")
        return []
    
    def save_output(self, output_path: str) -> None:
        """
        Save extracted items to a JSON file.
        
        Args:
            output_path: Path to save the output JSON
        """
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Convert items to dictionaries
        items_dict = [item.to_dict() for item in self.items]
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(items_dict, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"Saved {len(items_dict)} items to {output_path}")
