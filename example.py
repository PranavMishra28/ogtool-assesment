#!/usr/bin/env python3
"""
Example script demonstrating the plugin-based content extraction framework.
"""

import argparse
import sys
import json
import logging

from tech_content_extractor import TechContentExtractor


def show_available_extractors(extractor):
    """Show all available content extractors."""
    extractors = extractor.manager.extractors
    
    print("\n=== Available Content Extractors ===\n")
    for idx, ext in enumerate(extractors, 1):
        print(f"{idx}. {ext.__class__.__name__}")
        print(f"   - Description: {ext.__class__.__doc__.strip().split('.')[0]}")
    print("\n")


def interactive_extraction():
    """Run an interactive extraction session."""
    extractor = TechContentExtractor()
    
    print("\n=== Content Extraction Framework ===")
    print("This tool extracts content from various sources into a structured format.")
    
    # Display available extractors
    show_available_extractors(extractor)
    
    # Prompt for source
    print("Enter a source URL or file path to extract content from:")
    source = input("> ").strip()
    
    if not source:
        print("No source provided. Exiting.")
        return
    
    # Check if any extractor can handle this source
    can_handle = False
    for ext in extractor.manager.extractors:
        if ext.can_handle(source):
            can_handle = True
            print(f"Using {ext.__class__.__name__} to extract content from {source}")
            break
    
    if not can_handle:
        print(f"No suitable extractor found for {source}")
        print("Available extractors are configured to handle:")
        for ext in extractor.manager.extractors:
            # Just a simple description of what each extractor can handle
            if "GitHub" in ext.__class__.__name__:
                print("- GitHub repositories (github.com/owner/repo)")
            elif "PDF" in ext.__class__.__name__:
                print("- PDF files (local or Google Drive URLs)")
            elif "Substack" in ext.__class__.__name__:
                print("- Substack newsletters")
            elif "Blog" in ext.__class__.__name__:
                print("- Generic blog websites")
        return
    
    # Extract content
    print(f"\nExtracting content from {source}...")
    items = extractor.extract_from_source(source)
    
    if not items:
        print("No content was extracted.")
        return
    
    print(f"\nSuccessfully extracted {len(items)} content items.")
    
    # Ask where to save
    print("\nWhere would you like to save the extracted content?")
    print("Enter output file path (default: extracted_content.json):")
    output_path = input("> ").strip() or "extracted_content.json"
    
    # Save the output
    extractor.save_output(output_path)
    print(f"\nExtracted content saved to {output_path}")
    
    # Show a sample of the extracted content
    if len(items) > 0:
        print("\nSample of extracted content:")
        sample = items[0].to_dict()
        print(f"Title: {sample['title']}")
        content_preview = sample['content'][:150] + '...' if len(sample['content']) > 150 else sample['content']
        print(f"Content preview: {content_preview}")
        print(f"Content type: {sample['content_type']}")
        print(f"Source URL: {sample['source_url']}")


def example_blog_processing():
    """Process a sample blog post using the new framework."""
    extractor = TechContentExtractor()
    items = extractor.extract_from_source("https://blog.interviewing.io/how-to-become-a-data-scientist/")
    
    if not items:
        print("No content was extracted.")
        return
    
    print(f"Processed {len(items)} blog items.")
    extractor.save_output('blog_example_output.json')
    print("Blog processing complete. Output saved to blog_example_output.json")


def example_github_processing():
    """Process a sample GitHub repository using the new framework."""
    extractor = TechContentExtractor()
    items = extractor.extract_from_source("https://github.com/microsoft/TypeScript")
    
    if not items:
        print("No content was extracted.")
        return
    
    print(f"Processed {len(items)} GitHub items.")
    extractor.save_output('github_example_output.json')
    print("GitHub processing complete. Output saved to github_example_output.json")


def example_substack_processing():
    """Process a sample Substack newsletter using the new framework."""
    extractor = TechContentExtractor()
    items = extractor.extract_from_source("https://lethain.com/")
    
    if not items:
        print("No content was extracted.")
        return
    
    print(f"Processed {len(items)} Substack items.")
    extractor.save_output('substack_example_output.json')
    print("Substack processing complete. Output saved to substack_example_output.json")


def main():
    """Main entry point for the example script."""
    parser = argparse.ArgumentParser(
        description="Example script for the content extraction framework."
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode."
    )
    
    parser.add_argument(
        "--blog",
        action="store_true",
        help="Run the blog processing example."
    )
    
    parser.add_argument(
        "--github",
        action="store_true",
        help="Run the GitHub processing example."
    )
    
    parser.add_argument(
        "--substack",
        action="store_true",
        help="Run the Substack processing example."
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_extraction()
    elif args.blog:
        example_blog_processing()
    elif args.github:
        example_github_processing()
    elif args.substack:
        example_substack_processing()
    else:
        print("Running the blog processing example by default:")
        example_blog_processing()


if __name__ == "__main__":
    print("Running content extraction examples...")
    main()
    print("Examples complete!")
