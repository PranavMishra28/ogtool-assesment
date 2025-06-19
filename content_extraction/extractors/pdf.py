"""
PDF extractor module.

This module provides functionality to extract content from PDF files.
"""

import os
import re
import logging
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

import PyPDF2
import gdown

from content_extraction.base import ContentExtractor, ContentItem


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
                r"(?:Chapter|CHAPTER)\s+(\d+|[IVX]+)[:\s]+(.+?)(?=(?:Chapter|CHAPTER)\s+\d+|$)"
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
            # Create a temporary file
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"gdrive_pdf_{uuid.uuid4().hex[:8]}.pdf")
            
            # Use gdown to download the file
            gdown.download(url, output_path, quiet=False)
            
            # Verify the file was downloaded and is a PDF
            if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                self.logger.error("Failed to download file from Google Drive")
                return None
                
            # Check if the file is actually a PDF
            if not self._is_valid_pdf(output_path):
                self.logger.error("Downloaded file is not a valid PDF")
                os.remove(output_path)  # Clean up the invalid file
                return None
                
            self.logger.info(f"Successfully downloaded PDF to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Error downloading from Google Drive: {e}", exc_info=True)
            return None
    
    def _is_valid_pdf(self, filepath: str) -> bool:
        """
        Check if a file is a valid PDF.
        
        Args:
            filepath: Path to the file to check
            
        Returns:
            True if the file is a valid PDF, False otherwise
        """
        try:
            with open(filepath, 'rb') as f:
                PyPDF2.PdfReader(f)
            return True
        except:
            return False
    
    def _extract_from_pdf(self, pdf_path: str, source_url: Optional[str] = None) -> List[ContentItem]:
        """
        Extract content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            source_url: Original source URL if available
            
        Returns:
            List of ContentItem objects
        """
        self.logger.info(f"Extracting content from PDF: {pdf_path}")
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Get basic info
                num_pages = len(pdf_reader.pages)
                self.logger.info(f"PDF has {num_pages} pages")
                
                # Extract text from all pages
                full_text = ""
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text() + "\n\n"
                
                # Try to extract a title from the PDF
                title = self._extract_pdf_title(pdf_reader) or os.path.basename(pdf_path)
                
                # Try to identify chapters/sections
                chapters = self._identify_chapters(full_text)
                
                items = []
                
                if chapters:
                    self.logger.info(f"Identified {len(chapters)} chapters/sections")
                    
                    # Process each chapter as a separate ContentItem
                    for idx, (chapter_title, chapter_content) in enumerate(chapters):
                        # Generate a unique ID
                        content_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_url or pdf_path}#{idx}"))
                        
                        # Create content item
                        item = ContentItem(
                            content_id=content_id,
                            title=f"{title} - {chapter_title}",
                            content=chapter_content.strip(),
                            source_url=source_url,
                            content_type="book_chapter",
                            metadata={
                                "pdf_path": pdf_path if not source_url else None,
                                "chapter_index": idx,
                                "total_chapters": len(chapters),
                                "parent_document": title
                            }
                        )
                        items.append(item)
                        
                        # Respect max_chapters limit if set
                        if self.max_chapters > 0 and len(items) >= self.max_chapters:
                            break
                else:
                    # If no chapters identified, treat the whole document as one item
                    self.logger.info("No chapters identified, treating the whole document as one item")
                    
                    content_id = str(uuid.uuid5(uuid.NAMESPACE_URL, source_url or pdf_path))
                    
                    item = ContentItem(
                        content_id=content_id,
                        title=title,
                        content=full_text.strip(),
                        source_url=source_url,
                        content_type="book_chapter",
                        metadata={
                            "pdf_path": pdf_path if not source_url else None,
                            "page_count": num_pages
                        }
                    )
                    items.append(item)
                
                return items
                
        except Exception as e:
            self.logger.error(f"Error processing PDF {pdf_path}: {e}", exc_info=True)
            return []
    
    def _extract_pdf_title(self, pdf_reader: PyPDF2.PdfReader) -> Optional[str]:
        """Extract title from PDF metadata if available."""
        try:
            if pdf_reader.metadata and pdf_reader.metadata.title:
                return pdf_reader.metadata.title
                
            # Try to extract from first page text
            if len(pdf_reader.pages) > 0:
                first_page_text = pdf_reader.pages[0].extract_text()
                lines = first_page_text.split('\n')
                # Heuristic: first non-empty line might be the title
                for line in lines:
                    if line.strip() and len(line.strip()) < 100:  # Reasonable title length
                        return line.strip()
        except:
            pass
            
        return None
    
    def _identify_chapters(self, text: str) -> List[tuple]:
        """
        Identify chapters or sections in the text.
        
        Args:
            text: Full text of the PDF
            
        Returns:
            List of (chapter_title, chapter_content) tuples
        """
        chapters = []
        
        for pattern in self.compiled_patterns:
            matches = list(pattern.finditer(text))
            
            if matches:
                # Extract chapters based on the matches
                for i, match in enumerate(matches):
                    chapter_num = match.group(1)
                    chapter_title = match.group(2).strip()
                    
                    # Chapter content goes from current match to next match or end
                    start_pos = match.start()
                    end_pos = matches[i+1].start() if i < len(matches)-1 else len(text)
                    
                    # Skip the chapter heading itself
                    content_start = match.end()
                    
                    chapter_content = text[content_start:end_pos].strip()
                    chapters.append((f"Chapter {chapter_num}: {chapter_title}", chapter_content))
                
                # If we found chapters with this pattern, no need to try others
                break
        
        return chapters
