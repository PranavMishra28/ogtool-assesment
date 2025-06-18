"""
Main module for the technical content extraction framework.

This module orchestrates the content extraction process, dynamically discovering
and registering extractors from the content_extraction package for a plugin-based
approach that allows easy extension to new content sources.
"""

import argparse
import json
import logging
import os
import sys
import importlib
import pkgutil
from typing import Dict, List, Any, Optional
from pathlib import Path

from content_extraction.base import ExtractorManager, ContentItem, ContentExtractor, ContentProcessor


class TechContentExtractor:
    """Main class for extracting technical content from various sources."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the extractor.
        
        Args:
            config_path: Path to the configuration file
        """
        self.manager = ExtractorManager(config_path)
        self._register_extractors()
        self._register_processors()
    
    def _register_extractors(self):
        """Dynamically register all available content extractors from the extractors directory."""
        try:
            # Import the extractors package
            from content_extraction import extractors
            
            # Track registered extractors for logging
            registered_count = 0
            
            # Dynamically import all modules in the extractors package
            for _, module_name, _ in pkgutil.iter_modules(extractors.__path__):
                try:
                    # Import the module
                    module = importlib.import_module(f"content_extraction.extractors.{module_name}")
                    
                    # Find all classes in the module that inherit from ContentExtractor
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        
                        # Check if it's a class that inherits from ContentExtractor
                        if (isinstance(attr, type) and 
                            issubclass(attr, ContentExtractor) and 
                            attr is not ContentExtractor):
                            
                            # Create an instance and register it
                            extractor = attr(self.manager.config)
                            self.manager.register_extractor(extractor)
                            registered_count += 1
                            
                except Exception as e:
                    logging.error(f"Error loading extractor module {module_name}: {e}", exc_info=True)
            
            if registered_count == 0:
                logging.warning("No extractors were registered! Check extractors directory.")
            else:
                logging.info(f"Successfully registered {registered_count} extractors")
                
        except ImportError as e:
            logging.error(f"Failed to import extractors package: {e}", exc_info=True)
            # Fall back to manual registration if dynamic loading fails
            logging.info("Falling back to manual extractor registration")
            
            try:
                from content_extraction.extractors.blog import GenericBlogExtractor
                from content_extraction.extractors.pdf import PDFExtractor
                from content_extraction.extractors.substack import SubstackExtractor
                
                self.manager.register_extractor(GenericBlogExtractor(self.manager.config))
                self.manager.register_extractor(PDFExtractor(self.manager.config))
                self.manager.register_extractor(SubstackExtractor(self.manager.config))
            except ImportError as e:
                logging.error(f"Failed to fall back to manual registration: {e}", exc_info=True)
                raise RuntimeError("No extractors could be loaded, extraction not possible")
    
    def _register_processors(self):
        """Register content processors."""
        # This can be expanded similar to extractors when processors are implemented
        pass
        
    def extract_from_source(self, source: str) -> List[ContentItem]:
        """
        Extract content from a specified source.
        
        Args:
            source: Source URL or file path
            
        Returns:
            List of extracted content items
        """
        return self.manager.extract(source)
    
    def save_output(self, output_path: str) -> None:
        """
        Save extracted items to a JSON file.
        
        Args:
            output_path: Path to save the output JSON
        """
        self.manager.save_output(output_path)
    
    @property
    def items(self) -> List[ContentItem]:
        """Get all extracted content items."""
        return self.manager.items


def main():
    """Command line entry point."""
    parser = argparse.ArgumentParser(description="Extract technical content from various sources.")
    parser.add_argument("source", nargs="?", help="URL or file path to extract content from")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--output", "-o", default="extracted_content.json", help="Output JSON file path")
    parser.add_argument("--list-sources", "-l", action="store_true", help="List supported source types")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    # Initialize the extractor
    extractor = TechContentExtractor(args.config)
    
    # List supported sources
    if args.list_sources:
        print("Supported source types:")
        print("- Generic blogs: Any blog website")
        print("- PDF files: Local PDF files or Google Drive links")
        print("- Substack newsletters: Any Substack publication")
        print("- GitHub repositories: GitHub repos with documentation")
        print("- Markdown files: Local or remote markdown files")
        sys.exit(0)
    
    # Interactive mode
    if args.interactive:
        run_interactive_mode(extractor, args.output)
        sys.exit(0)
    
    # Direct source extraction
    if args.source:
        print(f"Extracting content from: {args.source}")
        extractor.extract_from_source(args.source)
        extractor.save_output(args.output)
        print(f"Extracted {len(extractor.items)} items. Output saved to: {args.output}")
    else:
        parser.print_help()


def run_interactive_mode(extractor: TechContentExtractor, default_output: str):
    """
    Run the extractor in interactive mode.
    
    Args:
        extractor: Initialized TechContentExtractor instance
        default_output: Default output file path
    """
    print("\n===== Technical Content Extractor =====\n")
    print("Select a source type to extract from:\n")
    print("1. Blog website")
    print("2. PDF file (local)")
    print("3. Google Drive PDF")
    print("4. GitHub repository")
    print("5. Markdown file")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ")
    
    if choice == "1":
        url = input("\nEnter the blog URL: ")
        output = input(f"\nEnter output file name [{default_output}]: ") or default_output
        print(f"\nExtracting content from: {url}")
        extractor.extract_from_source(url)
        extractor.save_output(output)
        print(f"\nExtracted {len(extractor.items)} items. Output saved to: {output}")
    
    elif choice == "2":
        pdf_path = input("\nEnter the PDF file path: ")
        output = input(f"\nEnter output file name [{default_output}]: ") or default_output
        print(f"\nExtracting content from PDF: {pdf_path}")
        extractor.extract_from_source(pdf_path)
        extractor.save_output(output)
        print(f"\nExtracted {len(extractor.items)} items. Output saved to: {output}")
    
    elif choice == "3":
        gdrive_url = input("\nEnter the Google Drive PDF URL: ")
        output = input(f"\nEnter output file name [{default_output}]: ") or default_output
        print(f"\nExtracting content from Google Drive PDF: {gdrive_url}")
        extractor.extract_from_source(gdrive_url)
        extractor.save_output(output)
        print(f"\nExtracted {len(extractor.items)} items. Output saved to: {output}")
    
    elif choice == "4":
        github_url = input("\nEnter the GitHub repository URL: ")
        output = input(f"\nEnter output file name [{default_output}]: ") or default_output
        print(f"\nExtracting content from GitHub repository: {github_url}")
        extractor.extract_from_source(github_url)
        extractor.save_output(output)
        print(f"\nExtracted {len(extractor.items)} items. Output saved to: {output}")
    
    elif choice == "5":
        markdown_path = input("\nEnter the Markdown file path or URL: ")
        output = input(f"\nEnter output file name [{default_output}]: ") or default_output
        print(f"\nExtracting content from Markdown file: {markdown_path}")
        extractor.extract_from_source(markdown_path)
        extractor.save_output(output)
        print(f"\nExtracted {len(extractor.items)} items. Output saved to: {output}")
    
    elif choice == "6":
        print("\nExiting program...")
        return
    
    else:
        print("\nInvalid choice. Please try again.")
        run_interactive_mode(extractor, default_output)


if __name__ == "__main__":
    main()
