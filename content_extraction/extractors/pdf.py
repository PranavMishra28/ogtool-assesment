"""
PDF extractor module.

This module provides functionality to extract content from PDF files.
"""

import os
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import PyPDF2
import gdown

from content_extraction.base import ContentExtractor, ContentItem
from content_extraction.utils import generate_unique_id


class PDFExtractor(ContentExtractor):
    """Extractor for PDF content."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the PDFExtractor.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.chapter_patterns = config.get("extractors", {}).get("pdf", {}).get(
            "chapter_patterns", [
                "(?:Chapter|CHAPTER)\\s+(\\d+|[IVX]+)[:\\s]+(.+?)(?=(?:Chapter|CHAPTER)\\s+\\d+|$)"
            ]
        )
        self.max_chapters = config.get("sources", {}).get("pdf", {}).get("max_chapters", 0)
        self.compiled_patterns = [re.compile(pattern, re.DOTALL) for pattern in self.chapter_patterns]
    
    def can_handle(self, source: str) -> bool:
        """
        Check if this extractor can handle the given source.
        
        Args:
            source: File path or URL to check
            
        Returns:
            True if this is a PDF file or Google Drive PDF link, False otherwise
        """
        if source.lower().endswith('.pdf'):
            return True
        if "drive.google.com" in source.lower():
            return True
        return False
    
    def extract(self, source: str) -> List[ContentItem]:
        """
        Extract content from a PDF file.
        
        Args:
            source: PDF file path or Google Drive URL
            
        Returns:
            List of ContentItem objects, one per chapter/section
        """
        # Check if it's a Google Drive link
        if "drive.google.com" in source.lower():
            pdf_path = self._download_from_google_drive(source)
            if not pdf_path:
                return []
        else:
            pdf_path = source
        
        # Verify PDF exists
        if not os.path.exists(pdf_path):
            self.logger.error(f"PDF file not found: {pdf_path}")
            return []
        
        try:
            return self._extract_from_pdf(pdf_path, source)
        except Exception as e:
            self.logger.error(f"Error extracting content from PDF {pdf_path}: {e}", exc_info=True)
            return []
    
    def _download_from_google_drive(self, url: str) -> Optional[str]:
        """
        Download a PDF from Google Drive.
        
        Args:
            url: Google Drive URL
            
        Returns:
            Local file path to downloaded PDF, or None if download failed
        """
        self.logger.info(f"Downloading PDF from Google Drive: {url}")
        
        try:
            # Extract file ID from URL
            file_id = None
            
            # Format: https://drive.google.com/file/d/FILE_ID/view
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
            # Format: https://drive.google.com/open?id=FILE_ID
            elif 'open?id=' in url:
                file_id = url.split('open?id=')[1].split('&')[0]
            
            if not file_id:
                self.logger.error(f"Could not extract file ID from Google Drive URL: {url}")
                return None
            
            # Create temporary file
            temp_dir = Path(os.path.expanduser("~")) / ".temp_pdf_downloads"
            temp_dir.mkdir(exist_ok=True)
            
            pdf_path = os.path.join(temp_dir, f"{file_id}.pdf")
            
            # Download using gdown
            self.logger.info(f"Downloading file ID {file_id} to {pdf_path}")
            try:
                output = gdown.download(id=file_id, output=pdf_path, quiet=False)
                if output is None:
                    self.logger.error(f"Failed to download file. Make sure the file exists and is shared with 'Anyone with the link'")
                    return None
            except Exception as e:
                self.logger.error(f"Error downloading file from Google Drive: {e}", exc_info=True)
                return None
            
            # Check if file was downloaded successfully
            if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
                self.logger.error("PDF download failed. The file is empty or not accessible.")
                return None
            
            self.logger.info(f"Successfully downloaded PDF to {pdf_path}")
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"Error downloading from Google Drive: {e}", exc_info=True)
            return None
    
    def _extract_from_pdf(self, pdf_path: str, source_url: Optional[str] = None) -> List[ContentItem]:
        """
        Extract content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            source_url: Original source URL (optional)
            
        Returns:
            List of ContentItem objects, one per chapter/section
        """
        self.logger.info(f"Extracting content from PDF: {pdf_path}")
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                full_text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text() + "\n\n"
                
                # Extract document info for metadata
                title = os.path.basename(pdf_path)
                if pdf_reader.metadata and pdf_reader.metadata.title:
                    title = pdf_reader.metadata.title
                
                author = None
                if pdf_reader.metadata and pdf_reader.metadata.author:
                    author = pdf_reader.metadata.author
                
                # Try to identify chapters
                chapters = []
                for pattern in self.compiled_patterns:
                    matches = pattern.findall(full_text)
                    if matches:
                        for chapter_num, chapter_content in matches:
                            chapter_title = f"Chapter {chapter_num}"
                            
                            # Try to extract title from the first few lines
                            title_match = re.search(r'(.+?)(?:\n\n|\r\n\r\n)', chapter_content)
                            if title_match:
                                potential_title = title_match.group(1).strip()
                                if len(potential_title) <= 100:  # Reasonable title length
                                    chapter_title = f"Chapter {chapter_num}: {potential_title}"
                            
                            chapters.append({
                                "number": chapter_num,
                                "title": chapter_title,
                                "content": chapter_content.strip()
                            })
                        
                        # If we found chapters with this pattern, no need to try others
                        break
                
                items = []
                
                # If chapters were found, process each one
                if chapters:
                    # Limit chapters if configured
                    if self.max_chapters > 0:
                        chapters = chapters[:self.max_chapters]
                    
                    for chapter in chapters:
                        content_item = ContentItem(
                            content_id=generate_unique_id(),
                            title=chapter["title"],
                            content=chapter["content"],
                            source_url=source_url,
                            content_type="book_chapter",
                            author=author,
                            metadata={
                                "chapter_number": chapter["number"],
                                "pdf_filename": os.path.basename(pdf_path)
                            }
                        )
                        items.append(content_item)
                else:
                    # No chapters found, treat the whole document as a single item
                    content_item = ContentItem(
                        content_id=generate_unique_id(),
                        title=title,
                        content=full_text.strip(),
                        source_url=source_url,
                        content_type="document",
                        author=author,
                        metadata={
                            "pdf_filename": os.path.basename(pdf_path)
                        }
                    )
                    items.append(content_item)
                
                self.logger.info(f"Extracted {len(items)} items from PDF")
                return items
                
        except Exception as e:
            self.logger.error(f"Error extracting from PDF {pdf_path}: {e}", exc_info=True)
            return []
