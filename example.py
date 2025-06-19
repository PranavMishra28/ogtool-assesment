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
    
    while True:
        print("\n" + "="*60)
        print("SELECT AN ACTION:")
        print("="*60)
        print("1. 🌐 Extract from Blog/Website")
        print("2. 📁 Extract from GitHub Repository") 
        print("3. 📄 Extract from PDF File (local)")
        print("4. ☁️  Extract from Google Drive PDF")
        print("5. 📝 Extract from Markdown File")
        print("6. 📧 Extract from Substack Newsletter")
        print("7. ℹ️  Show Available Extractors")
        print("8. ❌ Exit")
        print("="*60)
        
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            print("\n--- Blog/Website Extraction ---")
            url = input("Enter the blog/website URL: ").strip()
            if url:
                print(f"\nExtracting content from: {url}")
                output = input("Enter output file name (default: blog_content.json): ").strip() or "blog_content.json"
                _extract_and_save(extractor, url, output)
        
        elif choice == "2":
            print("\n--- GitHub Repository Extraction ---")
            repo_url = input("Enter the GitHub repository URL (e.g., https://github.com/owner/repo): ").strip()
            if repo_url:
                print(f"\nExtracting content from: {repo_url}")
                output = input("Enter output file name (default: github_content.json): ").strip() or "github_content.json"
                _extract_and_save(extractor, repo_url, output)
        
        elif choice == "3":
            print("\n--- Local PDF File Extraction ---")
            pdf_path = input("Enter the PDF file path: ").strip()
            if pdf_path:
                print(f"\nExtracting content from: {pdf_path}")
                output = input("Enter output file name (default: pdf_content.json): ").strip() or "pdf_content.json"
                _extract_and_save(extractor, pdf_path, output)
        
        elif choice == "4":
            print("\n--- Google Drive PDF Extraction ---")
            print("Note: Make sure the PDF is shared publicly or with 'Anyone with the link'")
            gdrive_url = input("Enter the Google Drive PDF URL: ").strip()
            if gdrive_url:
                print(f"\nExtracting content from: {gdrive_url}")
                output = input("Enter output file name (default: gdrive_pdf_content.json): ").strip() or "gdrive_pdf_content.json"
                _extract_and_save(extractor, gdrive_url, output)
        
        elif choice == "5":
            print("\n--- Markdown File Extraction ---")
            md_path = input("Enter the markdown file path or URL: ").strip()
            if md_path:
                print(f"\nExtracting content from: {md_path}")
                output = input("Enter output file name (default: markdown_content.json): ").strip() or "markdown_content.json"
                _extract_and_save(extractor, md_path, output)
        
        elif choice == "6":
            print("\n--- Substack Newsletter Extraction ---")
            substack_url = input("Enter the Substack newsletter URL: ").strip()
            if substack_url:
                print(f"\nExtracting content from: {substack_url}")
                output = input("Enter output file name (default: substack_content.json): ").strip() or "substack_content.json"
                _extract_and_save(extractor, substack_url, output)
        
        elif choice == "7":
            print("\n--- Available Content Extractors ---")
            show_available_extractors(extractor)
        
        elif choice == "8":
            print("\nThank you for using the Content Extraction Framework!")
            break
        
        else:
            print("\n❌ Invalid choice. Please select a number between 1-8.")
        
        # Ask if user wants to continue
        if choice in ["1", "2", "3", "4", "5", "6"]:
            continue_choice = input("\nWould you like to extract from another source? (y/n): ").strip().lower()
            if continue_choice not in ["y", "yes"]:
                print("\nThank you for using the Content Extraction Framework!")
                break


def _extract_and_save(extractor, source, output_file):
    """Helper function to extract content and save to file."""
    try:
        # Clear previous items
        extractor.manager.items = []
        
        # Extract content
        items = extractor.extract_from_source(source)
        
        if items:
            extractor.save_output(output_file)
            print(f"\n✅ Success! Extracted {len(items)} items.")
            print(f"📁 Output saved to: {output_file}")
            
            # Show a preview of the first item
            if len(items) > 0:
                sample = items[0]
                print(f"\n📄 Preview of extracted content:")
                print(f"   Title: {sample.title}")
                print(f"   Type: {sample.content_type}")
                print(f"   Content length: {len(sample.content)} characters")
                if sample.author:
                    print(f"   Author: {sample.author}")
                content_preview = sample.content[:200] + "..." if len(sample.content) > 200 else sample.content
                print(f"   Content preview: {content_preview}")
        else:
            print(f"\n⚠️  No content was extracted from {source}")
            print("This might happen if:")
            print("- The URL is not accessible")
            print("- The content format is not supported")
            print("- There was a network error")
            
            # Provide specific guidance for GitHub URLs
            if "github.com" in source and source.count("/") == 3:
                print("\n💡 GitHub URL tip:")
                print("   Make sure to use the full repository URL format:")
                print("   https://github.com/username/repository")
                print("   For example: https://github.com/microsoft/vscode")
            
    except Exception as e:
        print(f"\n❌ Error extracting content: {e}")
        print("Please check the source URL/path and try again.")


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
