#!/usr/bin/env python3
"""
Test script for ContentIngestionTool.
"""

import unittest
from unittest.mock import patch, MagicMock
from content_ingestion import ContentIngestionTool

class TestContentIngestionTool(unittest.TestCase):
    """Test cases for ContentIngestionTool."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tool = ContentIngestionTool(team_id="test123")
    
    def test_detect_source_type(self):
        """Test the source type detection functionality."""
        self.assertEqual(self.tool.detect_source_type("example.pdf"), "pdf")
        self.assertEqual(self.tool.detect_source_type("https://example.com"), "url")
        self.assertEqual(self.tool.detect_source_type("not_a_url_or_pdf"), "unknown")
    
    @patch('requests.get')
    def test_process_web_page(self, mock_get):
        """Test web page processing."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Article</h1>
                <div class="author">John Doe</div>
                <article>
                    <p>This is a test article content.</p>
                    <p>It has multiple paragraphs.</p>
                </article>
                <div class="ad">This is an ad</div>
            </body>
        </html>
        """
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        # Test processing
        items = self.tool.process_web_page("https://example.com/test")
        
        # Assertions
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Test Article")
        self.assertEqual(items[0]["content_type"], "other")
        self.assertIn("This is a test article content.", items[0]["content"])
        self.assertNotIn("This is an ad", items[0]["content"])
    
    def test_determine_content_type(self):
        """Test content type determination."""
        self.assertEqual(self.tool.determine_content_type("https://example.com/blog/post1"), "blog")
        self.assertEqual(self.tool.determine_content_type("https://example.com/podcast/episode5"), "podcast_transcript")
        self.assertEqual(self.tool.determine_content_type("https://linkedin.com/posts/johndoe"), "linkedin_post")
        self.assertEqual(self.tool.determine_content_type("https://example.com/document.pdf"), "book")
        self.assertEqual(self.tool.determine_content_type("https://example.com"), "other")
    
    def test_html_to_markdown(self):
        """Test HTML to Markdown conversion."""
        html = """
        <h1>Test Heading</h1>
        <p>This is a <strong>paragraph</strong> with <a href="https://example.com">link</a>.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
        """
        
        markdown = self.tool.html_to_markdown(html)
        
        self.assertIn("# Test Heading", markdown)
        self.assertIn("This is a", markdown)
        self.assertIn("[link](https://example.com)", markdown)
        self.assertIn("* Item 1", markdown)
    

if __name__ == "__main__":
    unittest.main()
