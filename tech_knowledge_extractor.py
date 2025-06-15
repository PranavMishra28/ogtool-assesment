#!/usr/bin/env python3
"""
Specialized content scraper for Aline's technical knowledge.

This script extracts content from:
1. interviewing.io blog posts
2. interviewing.io company guides
3. interviewing.io interview guides
4. nilmamano.com DS&A blog posts
5. Book chapters (PDF)
6. Supports Substack (bonus)
"""

import argparse
import json
import os
import re
import sys
import tempfile
from typing import Dict, List, Optional, Union
import time
import random
from tqdm import tqdm
import logging
import requests
from bs4 import BeautifulSoup

from content_ingestion import ContentIngestionTool

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extraction.log"),
        logging.StreamHandler()
    ]
)

class TechKnowledgeExtractor:
    """Tool for extracting technical knowledge from various sources into knowledgebase format."""
    
    def __init__(self, team_id: str = "aline123", user_id: str = ""):
        """Initialize the extractor."""
        self.team_id = team_id
        self.user_id = user_id
        self.content_tool = ContentIngestionTool(team_id, user_id)
        self.items = []
    
    def process_interviewing_io_blog(self):
        """Process all blog posts from interviewing.io."""
        logging.info("Processing interviewing.io blog posts...")
        url = "https://interviewing.io/blog"
        
        # Get all blog post links
        try:
            links = self.content_tool.extract_links_from_list_page(url)
            total_links = len(links)
            logging.info(f"Found {total_links} blog posts.")
            
            # Process each link with a progress bar
            for link in tqdm(links, desc="Processing blog posts", unit="post"):
                try:
                    items = self.content_tool.process_web_page(link)
                    self.items.extend(items)
                    
                    # Add a small delay to avoid overwhelming the server
                    time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logging.error(f"Error processing blog post {link}: {e}")
        except Exception as e:
            logging.error(f"Error extracting links from {url}: {e}")
    
    def process_interviewing_io_company_guides(self):
        """Process all company guides from interviewing.io."""
        logging.info("Processing interviewing.io company guides...")
        url = "https://interviewing.io/topics#companies"
        
        # Get all company guide links
        try:
            links = self.content_tool.extract_links_from_list_page(url)
            total_links = len(links)
            logging.info(f"Found {total_links} company guides.")
            
            # Process each link with a progress bar
            for link in tqdm(links, desc="Processing company guides", unit="guide"):
                try:
                    items = self.content_tool.process_web_page(link)
                    
                    # Set the content type specifically to guide
                    for item in items:
                        item["content_type"] = "guide"
                    
                    self.items.extend(items)
                    
                    # Add a small delay to avoid overwhelming the server
                    time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logging.error(f"Error processing company guide {link}: {e}")
        except Exception as e:
            logging.error(f"Error extracting links from {url}: {e}")
    
    def process_interviewing_io_interview_guides(self):
        """Process all interview guides from interviewing.io."""
        logging.info("Processing interviewing.io interview guides...")
        url = "https://interviewing.io/learn#interview-guides"
        
        # Get all interview guide links
        try:
            links = self.content_tool.extract_links_from_list_page(url)
            total_links = len(links)
            logging.info(f"Found {total_links} interview guides.")
            
            # Process each link with a progress bar
            for link in tqdm(links, desc="Processing interview guides", unit="guide"):
                try:
                    items = self.content_tool.process_web_page(link)
                    
                    # Set the content type specifically to guide
                    for item in items:
                        item["content_type"] = "guide"
                    
                    self.items.extend(items)
                    
                    # Add a small delay to avoid overwhelming the server
                    time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logging.error(f"Error processing interview guide {link}: {e}")
        except Exception as e:
            logging.error(f"Error extracting links from {url}: {e}")
    
    def process_nilmamano_dsa_posts(self):
        """Process all DS&A blog posts from nilmamano.com."""
        logging.info("Processing nilmamano.com DS&A blog posts...")
        url = "https://nilmamano.com/blog/category/dsa"
        
        # Get all DSA blog post links
        try:
            links = self.content_tool.extract_links_from_list_page(url)
            total_links = len(links)
            logging.info(f"Found {total_links} DS&A blog posts.")
            
            # Process each link with a progress bar
            for link in tqdm(links, desc="Processing DS&A blog posts", unit="post"):
                try:
                    items = self.content_tool.process_web_page(link)
                    self.items.extend(items)
                    
                    # Add a small delay to avoid overwhelming the server
                    time.sleep(random.uniform(1, 3))
                except Exception as e:
                    logging.error(f"Error processing DS&A blog post {link}: {e}")
        except Exception as e:
            logging.error(f"Error extracting links from {url}: {e}")
    
    def process_book_chapters_from_gdrive(self, gdrive_link: str):
        """
        Process book chapters from a Google Drive PDF link.
        
        Args:
            gdrive_link: Google Drive link to the PDF file.
        """
        logging.info("Processing book chapters from Google Drive link...")
        
        # Extract the file ID from the Google Drive link
        file_id_match = re.search(r'[-\w]{25,}', gdrive_link)
        
        if not file_id_match:
            logging.error("Invalid Google Drive link. Could not extract file ID.")
            return
        
        file_id = file_id_match.group(0)
        
        try:
            # Create a temporary directory for the PDF
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_path = os.path.join(temp_dir, "book.pdf")
                
                # Download the PDF from Google Drive
                logging.info(f"Downloading PDF from Google Drive (ID: {file_id})...")
                self.content_tool.download_from_google_drive(file_id, pdf_path)
                
                # Process the PDF
                logging.info("Processing PDF content...")
                items = self.content_tool.process_pdf(pdf_path)
                
                # If it's specified to process only the first 8 chapters
                # We'll check the titles and only include those that match
                first_8_chapters = []
                chapter_pattern = re.compile(r'Chapter (\d+)', re.IGNORECASE)
                
                for item in items:
                    match = chapter_pattern.search(item["title"])
                    if match:
                        chapter_num = int(match.group(1))
                        if chapter_num <= 8:
                            first_8_chapters.append(item)
                
                logging.info(f"Extracted {len(first_8_chapters)} chapters from the PDF.")
                self.items.extend(first_8_chapters)
        except Exception as e:
            logging.error(f"Error processing PDF from Google Drive: {e}")
    
    def process_substack(self, url: str):
        """
        Process a Substack newsletter.
        
        Args:
            url: URL of the Substack.
        """
        logging.info(f"Processing Substack: {url}")
        try:
            items = self.content_tool.process_substack(url)
            self.items.extend(items)
            logging.info(f"Processed {len(items)} Substack posts.")
        except Exception as e:
            logging.error(f"Error processing Substack {url}: {e}")
    
    def process_generic_blog(self, url: str):
        """
        Process a generic blog that wasn't specifically handled.
        
        Args:
            url: URL of the blog.
        """
        logging.info(f"Processing generic blog: {url}")
        
        try:
            # Try to detect if it's a list page or an individual article
            response = requests.get(url, headers=self.content_tool.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Heuristic to determine if it's a list page
            article_count = len(soup.find_all(['article', '.post', '.entry']))
            link_count = len(soup.find_all('a', href=re.compile(r'/(article|post|blog)/')))
            
            if article_count > 3 or link_count > 10:
                # Process as a list page
                links = self.content_tool.extract_links_from_list_page(url)
                total_links = len(links)
                logging.info(f"Found {total_links} articles.")
                
                # Process each link with a progress bar
                for link in tqdm(links, desc="Processing articles", unit="article"):
                    try:
                        items = self.content_tool.process_web_page(link)
                        self.items.extend(items)
                        
                        # Add a small delay to avoid overwhelming the server
                        time.sleep(random.uniform(1, 3))
                    except Exception as e:
                        logging.error(f"Error processing article {link}: {e}")
            else:
                # Process as an individual page
                items = self.content_tool.process_web_page(url)
                self.items.extend(items)
                logging.info(f"Processed individual page with {len(items)} items.")
        except Exception as e:
            logging.error(f"Error processing generic blog {url}: {e}")
    
    def process_pdf_file(self, pdf_path: str):
        """
        Process a PDF file.
        
        Args:
            pdf_path: Path to the PDF file.
        """
        logging.info(f"Processing PDF file: {pdf_path}")
        try:
            items = self.content_tool.process_pdf(pdf_path)
            self.items.extend(items)
            logging.info(f"Processed PDF with {len(items)} items/chapters.")
        except Exception as e:
            logging.error(f"Error processing PDF file {pdf_path}: {e}")
    
    def generate_output(self) -> Dict:
        """
        Generate the final output in the required JSON format.
        
        Returns:
            A dictionary with the required output structure.
        """
        return {
            "team_id": self.team_id,
            "items": self.items
        }
    
    def save_output(self, output_path: str):
        """
        Save the output to a JSON file.
        
        Args:
            output_path: Path to save the JSON output to.
        """
        output = self.generate_output()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Output saved to {output_path}")
            logging.info(f"Processed {len(output['items'])} items in total.")
        except Exception as e:
            logging.error(f"Error saving output to {output_path}: {e}")
    
    def process_all_sources(self, gdrive_link: str = None, output_path: str = "aline_knowledge.json"):
        """
        Process all the specified sources and save the output.
        
        Args:
            gdrive_link: Google Drive link to the PDF file.
            output_path: Path to save the JSON output to.
        """
        try:
            self.process_interviewing_io_blog()
            self.process_interviewing_io_company_guides()
            self.process_interviewing_io_interview_guides()
            self.process_nilmamano_dsa_posts()
            
            # Process book chapters if link is provided
            if gdrive_link:
                self.process_book_chapters_from_gdrive(gdrive_link)
            
            self.save_output(output_path)
            
        except Exception as e:
            logging.error(f"Error processing sources: {e}")
            # Save whatever we've processed so far
            self.save_output(output_path)


def main():
    parser = argparse.ArgumentParser(description='Technical Knowledge Extraction Tool')
    parser.add_argument('--source', type=str, help='Source URL or file path')
    parser.add_argument('--gdrive', type=str, help='Google Drive link for the PDF book')
    parser.add_argument('--all', action='store_true', help='Process all specified sources')
    parser.add_argument('--team_id', type=str, default='aline123', help='Team ID')
    parser.add_argument('--user_id', type=str, default='', help='User ID (optional)')
    parser.add_argument('--output', type=str, default='aline_knowledge.json', help='Output JSON file path')
    
    args = parser.parse_args()
    
    extractor = TechKnowledgeExtractor(args.team_id, args.user_id)
    
    if args.all:
        # Process all sources
        extractor.process_all_sources(args.gdrive, args.output)
    elif args.source:
        # Process a single source
        source_type = extractor.content_tool.detect_source_type(args.source)
        
        if source_type == 'pdf':
            extractor.process_pdf_file(args.source)
        elif source_type == 'url':
            # Detect what type of URL it is
            if 'interviewing.io/blog' in args.source:
                extractor.process_interviewing_io_blog()
            elif 'interviewing.io/topics#companies' in args.source:
                extractor.process_interviewing_io_company_guides()
            elif 'interviewing.io/learn' in args.source:
                extractor.process_interviewing_io_interview_guides()
            elif 'nilmamano.com/blog/category/dsa' in args.source:
                extractor.process_nilmamano_dsa_posts()
            elif 'substack.com' in args.source:
                extractor.process_substack(args.source)
            else:
                extractor.process_generic_blog(args.source)
        else:
            logging.error(f"Unknown source type: {args.source}")
        
        extractor.save_output(args.output)
    else:
        logging.error("Please specify a source with --source or use --all to process all sources.")
        parser.print_help()


if __name__ == "__main__":
    main()
