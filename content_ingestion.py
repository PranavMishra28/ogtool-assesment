import argparse
import json
import os
import re
from typing import Dict, List, Optional, Union
import uuid
import sys

import requests
from bs4 import BeautifulSoup
import markdown
import PyPDF2
from urllib.parse import urlparse, urljoin
try:
    import gdown
except ImportError:
    print("gdown package not found. Installing gdown...")
    os.system(f"{sys.executable} -m pip install gdown")
    import gdown


class ContentIngestionTool:
    """Tool for ingesting technical content from various sources into a structured format."""

    def __init__(self, team_id: str, user_id: str = ""):
        """
        Initialize the ContentIngestionTool.
        
        Args:
            team_id: The team identifier for the knowledge base.
            user_id: Optional user identifier.
        """
        self.team_id = team_id
        self.user_id = user_id
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.items = []
        
    def detect_source_type(self, source: str) -> str:
        """
        Detect the type of source based on the input.
        
        Args:
            source: Source URL or file path.
            
        Returns:
            A string indicating the source type: 'url', 'pdf', or 'unknown'.
        """
        if source.lower().endswith('.pdf'):
            return 'pdf'
        elif re.match(r'^https?://', source):
            return 'url'
        else:
            return 'unknown'
            
    def clean_html_content(self, html_content: str) -> str:
        """
        Clean HTML content by removing ads, navigation, footers, etc.
        
        Args:
            html_content: Raw HTML content.
            
        Returns:
            Cleaned HTML content.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove common ad elements, navigation, etc.
        for selector in [
            'nav', 'header', 'footer', 'aside', '.sidebar', '.ad', '.advertisement',
            '.nav', '.navbar', '.menu', '.navigation', '.footer', '.header',
            '.cookie-notice', '.subscription', '.cta', '.ad-container', 
            '.popup', '.modal', '.newsletter', '#comments', '.comments',
            '.social-share', '.related-posts', '.author-bio'
        ]:
            for element in soup.select(selector):
                element.decompose()
          # Find the main content (heuristic approach)
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|article|post|entry'))
        
        if main_content:
            return str(main_content)
        return str(soup.body) if soup.body else str(soup)
    
    def html_to_markdown(self, html_content: str) -> str:
        """
        Convert HTML content to Markdown.
        
        Args:
            html_content: HTML content to convert.
            
        Returns:
            Markdown formatted content.
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Process headings - with error handling
            for i in range(6, 0, -1):
                for heading in soup.find_all(f'h{i}'):
                    try:
                        heading_text = heading.get_text().strip()
                        heading.string = f"{'#' * i} {heading_text}\n\n"
                        heading.unwrap()
                    except Exception as e:
                        # If unwrapping fails, replace the element with text
                        heading_text = heading.get_text().strip()
                        heading.replace_with(f"{'#' * i} {heading_text}\n\n")
            
            # Process links with error handling
            for a in soup.find_all('a'):
                try:
                    href = a.get('href', '')
                    text = a.get_text().strip()
                    a.replace_with(f"[{text}]({href})")
                except Exception as e:
                    # Skip problematic links
                    pass
            
            # Process images
            for img in soup.find_all('img'):
                try:
                    src = img.get('src', '')
                    alt = img.get('alt', '')
                    img.replace_with(f"![{alt}]({src})")
                except Exception as e:
                    pass
            
            # Process lists
            for ul in soup.find_all('ul'):
                try:
                    for li in ul.find_all('li'):
                        li_text = li.get_text().strip()
                        li.string = f"* {li_text}\n"
                        li.unwrap()
                    ul.unwrap()
                except Exception as e:
                    pass
            
            for ol in soup.find_all('ol'):
                try:
                    for i, li in enumerate(ol.find_all('li'), 1):
                        li_text = li.get_text().strip()
                        li.string = f"{i}. {li_text}\n"
                        li.unwrap()
                    ol.unwrap()
                except Exception as e:
                    pass
            
            # Process code blocks
            for pre in soup.find_all('pre'):
                try:
                    code_text = pre.get_text()
                    language = ""
                    if pre.find('code', class_=True):
                        class_name = pre.find('code').get('class', [""])[0]
                        if "language-" in class_name:
                            language = class_name.replace("language-", "")
                    pre.replace_with(f"```{language}\n{code_text}\n```\n\n")
                except Exception as e:
                    pass
            
            # Process inline code
            for code in soup.find_all('code'):
                try:
                    if code.parent.name != 'pre':
                        code_text = code.get_text()
                        code.replace_with(f"`{code_text}`")
                except Exception as e:
                    pass
            
            # Process blockquotes
            for blockquote in soup.find_all('blockquote'):
                try:
                    lines = blockquote.get_text().strip().split('\n')
                    quoted_lines = [f"> {line}" for line in lines]
                    blockquote.replace_with('\n'.join(quoted_lines) + '\n\n')
                except Exception as e:
                    pass
            
            # Process tables
            for table in soup.find_all('table'):
                try:
                    markdown_table = []
                    
                    # Process table headers
                    headers = []
                    if table.find('thead'):
                        for th in table.find('thead').find_all('th'):
                            headers.append(th.get_text().strip())
                    elif table.find('tr'):
                        for th in table.find('tr').find_all(['th', 'td']):
                            headers.append(th.get_text().strip())
                    
                    if headers:
                        markdown_table.append('| ' + ' | '.join(headers) + ' |')
                        markdown_table.append('| ' + ' | '.join(['---' for _ in headers]) + ' |')
                    
                    # Process table rows
                    rows = table.find_all('tr')
                    start_idx = 1 if headers and not table.find('thead') else 0
                    
                    for row in rows[start_idx:]:
                        cells = []
                        for cell in row.find_all(['td', 'th']):
                            cells.append(cell.get_text().strip())
                        if cells:
                            markdown_table.append('| ' + ' | '.join(cells) + ' |')
                    
                    table.replace_with('\n'.join(markdown_table) + '\n\n')
                except Exception as e:
                    pass
            
            # Clean up the text
            text = soup.get_text()
            
            # Remove excessive newlines
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            return text.strip()
        except Exception as e:
            # Fallback for any errors
            if html_content:
                # Try to extract plain text as a fallback
                try:
                    soup = BeautifulSoup(html_content, 'html.parser')
                    text = soup.get_text(separator='\n\n')
                    return text.strip()
                except:
                    return html_content
            return ""

    def extract_title_from_html(self, html_content: str) -> str:
        """
        Extract the title from HTML content.
        
        Args:
            html_content: HTML content to extract title from.
            
        Returns:
            Extracted title.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Try to find title in various elements
        title_element = (
            soup.find('h1') or 
            soup.find('title') or 
            soup.find('meta', property='og:title') or
            soup.find('meta', attrs={'name': 'title'})
        )
        
        if title_element:
            if title_element.name == 'meta':
                return title_element.get('content', '').strip()
            else:
                return title_element.get_text().strip()
        
        return "Untitled Content"

    def extract_author_from_html(self, html_content: str) -> str:
        """
        Extract the author from HTML content.
        
        Args:
            html_content: HTML content to extract author from.
            
        Returns:
            Extracted author or empty string if not found.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for author in meta tags
        author_meta = (
            soup.find('meta', property='author') or
            soup.find('meta', property='og:author') or
            soup.find('meta', attrs={'name': 'author'})
        )
        
        if author_meta and author_meta.get('content'):
            return author_meta.get('content').strip()
        
        # Look for author in common elements
        author_element = (
            soup.find('a', rel='author') or
            soup.find(class_=re.compile(r'author')) or
            soup.find(attrs={'itemprop': 'author'})
        )
        
        if author_element:
            return author_element.get_text().strip()
        
        return ""
        
    def determine_content_type(self, url: str, html_content: str = None) -> str:
        """
        Determine the content type based on URL and content.
        
        Args:
            url: Source URL.
            html_content: HTML content for additional context.
            
        Returns:
            Content type string.
        """
        # Check URL patterns
        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
        
        if 'blog' in url or '/post/' in url or '/posts/' in url or '/article/' in url:
            return 'blog'
        elif 'podcast' in url or '/episodes/' in url:
            return 'podcast_transcript'
        elif 'linkedin.com/posts' in url:
            return 'linkedin_post'
        elif 'reddit.com' in url:
            return 'reddit_comment'
        elif '.pdf' in url:
            return 'book'
        elif 'substack.com' in url:
            return 'blog'
        elif html_content:
            # Try to determine from content if URL wasn't conclusive
            soup = BeautifulSoup(html_content, 'html.parser')
            if soup.find(text=re.compile(r'podcast|episode|transcript')):
                return 'podcast_transcript'
            elif soup.find(text=re.compile(r'chapter|book')):
                return 'book'
            elif soup.find(text=re.compile(r'call|meeting|interview')):
                return 'call_transcript'
        
        return 'other'
        
    def process_web_page(self, url: str) -> List[Dict]:
        """
        Process a single web page.
        
        Args:
            url: The URL of the web page to process.
            
        Returns:
            List of processed content items.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            html_content = response.text
            
            try:
                cleaned_html = self.clean_html_content(html_content)
                markdown_content = self.html_to_markdown(cleaned_html)
            except Exception as parse_error:
                # Fallback method for pages with problematic HTML
                print(f"Error parsing HTML structure for {url}: {parse_error}")
                print("Using fallback extraction method...")
                
                # Create a new BeautifulSoup object with a more lenient parser
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract main text content directly
                text_content = soup.get_text(separator='\n\n')
                
                # Basic markdown formatting
                markdown_content = text_content.strip()
                
                # Remove excessive whitespace
                markdown_content = re.sub(r'\n{3,}', '\n\n', markdown_content)
            
            title = self.extract_title_from_html(html_content)
            author = self.extract_author_from_html(html_content)
            content_type = self.determine_content_type(url, html_content)
            
            item = {
                "title": title,
                "content": markdown_content,
                "content_type": content_type,
                "source_url": url,
                "author": author,
                "user_id": self.user_id
            }
            
            return [item]
            
        except requests.RequestException as e:
            print(f"Error processing {url}: {e}")
            return []

    def extract_links_from_list_page(self, url: str) -> List[str]:
        """
        Extract individual article links from a list-style page.
        
        Args:
            url: The URL of the list page.
            
        Returns:
            List of extracted article URLs.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
            
            links = []
            
            # Handle interviewing.io specifically
            if 'interviewing.io' in url:
                # For blog posts
                if '/blog' in url:
                    article_links = soup.select('.post-title a, .post a, article a, .blog-post a')
                # For company guides
                elif '/topics#companies' in url:
                    article_links = soup.select('.company-card a, .topics-card a')
                # For interview guides
                elif '/learn' in url:
                    article_links = soup.select('.guide-card a, .card a')
                else:
                    article_links = soup.select('a[href*="article"], a[href*="post"], a[href*="blog"], a[href*="guide"]')
            # Handle nilmamano.com specifically
            elif 'nilmamano.com' in url:
                article_links = soup.select('article a, .post a, .entry a, .blog-entry a')
            # Handle quill.co specifically
            elif 'quill.co/blog' in url:
                article_links = soup.select('.post-card a, .blog-post a, article a')
            # Generic approach for other sites
            else:
                article_links = (
                    soup.select('a[href*="article"]') or
                    soup.select('a[href*="post"]') or
                    soup.select('a[href*="blog"]') or
                    soup.select('.article-title a') or
                    soup.select('.post-title a') or
                    soup.select('article a') or
                    soup.select('.card a, .guide a')  # Common for guide/card based layouts
                )
            
            seen_urls = set()
            for link in article_links:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    if not href.startswith(('http://', 'https://')):
                        href = urljoin(base_url, href)
                    
                    # Skip duplicates and non-article links
                    if href not in seen_urls and not re.search(r'(#comment|/tag/|/category/|/author/|/page/|/feed/)', href):
                        links.append(href)
                        seen_urls.add(href)
            
            return links
            
        except requests.RequestException as e:
            print(f"Error extracting links from {url}: {e}")
            return []

    def process_substack(self, url: str) -> List[Dict]:
        """
        Process a Substack newsletter.
        
        Args:
            url: The base URL of the Substack newsletter.
            
        Returns:
            List of processed content items.
        """
        # Remove trailing slashes and add '/archive' if not present
        base_url = url.rstrip('/')
        if not base_url.endswith('/archive'):
            archive_url = f"{base_url}/archive"
        else:
            archive_url = base_url
        
        try:
            # Get the archive page to extract post links
            response = requests.get(archive_url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract the main author/owner of the Substack
            main_author = ""
            author_elem = soup.select_one('.header-metadata .name, .pencraft-byline')
            if author_elem:
                main_author = author_elem.get_text().strip()
            
            # Find all post links
            post_items = []
            post_links = soup.select('.post-preview a.post-title')
            
            for link in post_links:
                href = link.get('href')
                if href and not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                
                # Process each post
                post_items.extend(self.process_web_page(href))
            
            # Filter posts by the main author if available
            if main_author:
                post_items = [post for post in post_items if not post["author"] or post["author"] == main_author]
            
            return post_items
            
        except requests.RequestException as e:
            print(f"Error processing Substack {url}: {e}")
            return []

    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Process a PDF file, extracting contents by chapter if possible.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            List of processed content items.
        """
        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            return []
        
        try:
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Extract text from all pages
                full_text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    full_text += page.extract_text() + "\n\n"
                
                # Try to identify chapters
                chapter_pattern = re.compile(r'(?:Chapter|CHAPTER)\s+(\d+|[IVX]+)[:\s]+(.+?)(?=(?:Chapter|CHAPTER)\s+\d+|$)', re.DOTALL)
                chapters = chapter_pattern.findall(full_text)
                
                items = []
                
                if chapters:
                    # Process each chapter as a separate item
                    for chapter_num, chapter_content in chapters:
                        chapter_title = f"Chapter {chapter_num}"
                        
                        # Try to extract title from the first few lines
                        title_match = re.search(r'(.+?)(?:\n\n|\r\n\r\n)', chapter_content)
                        if title_match:
                            potential_title = title_match.group(1).strip()
                            if len(potential_title) < 100:  # Reasonable title length
                                chapter_title = f"Chapter {chapter_num}: {potential_title}"
                        
                        # Clean and format the content
                        clean_content = self.clean_pdf_content(chapter_content)
                        
                        items.append({
                            "title": chapter_title,
                            "content": clean_content,
                            "content_type": "book",
                            "source_url": os.path.basename(pdf_path),
                            "author": "",
                            "user_id": self.user_id
                        })
                else:
                    # If no chapters found, process as a single item
                    title = os.path.splitext(os.path.basename(pdf_path))[0]
                    clean_content = self.clean_pdf_content(full_text)
                    
                    items.append({
                        "title": title,
                        "content": clean_content,
                        "content_type": "book",
                        "source_url": os.path.basename(pdf_path),
                        "author": "",
                        "user_id": self.user_id
                    })
                
                return items
                
        except Exception as e:
            print(f"Error processing PDF {pdf_path}: {e}")
            return []

    def clean_pdf_content(self, text: str) -> str:
        """
        Clean and format PDF content.
        
        Args:
            text: Raw text extracted from PDF.
            
        Returns:
            Cleaned and formatted markdown content.
        """
        # Remove page numbers
        text = re.sub(r'\n\s*\d+\s*\n', '\n\n', text)
        
        # Fix common PDF extraction issues
        text = re.sub(r'([a-z])\n([a-z])', r'\1 \2', text)  # Join broken words
        
        # Convert headings
        lines = text.split('\n')
        markdown_lines = []
        
        for line in lines:
            # Check if line looks like a heading (short, ends with no punctuation)
            if len(line.strip()) < 80 and re.match(r'^[A-Z][\w\s\-]+$', line.strip()):
                markdown_lines.append(f"## {line.strip()}\n")
            else:
                markdown_lines.append(line)
        
        text = '\n'.join(markdown_lines)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def process_source(self, source: str) -> None:
        """
        Process a source (URL or file) and extract content.
        
        Args:
            source: Source URL or file path.
        """
        source_type = self.detect_source_type(source)
        
        if source_type == 'pdf':
            items = self.process_pdf(source)
            self.items.extend(items)
            
        elif source_type == 'url':
            # Check if it's a Substack
            if 'substack.com' in source.lower():
                items = self.process_substack(source)
                self.items.extend(items)
            else:
                # Check if it's a list page or individual article
                response = requests.get(source, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                  # Heuristic to determine if it's a list page
                article_count = len(soup.find_all(['article', '.post', '.entry']))
                link_count = len(soup.find_all('a', href=re.compile(r'/(article|post|blog)/')))
                if article_count > 3 or link_count > 10:
                    # Process as a list page
                    article_links = self.extract_links_from_list_page(source)
                    for link in article_links:
                        items = self.process_web_page(link)
                        self.items.extend(items)
                else:
                    # Process as an individual page
                    items = self.process_web_page(source)
                    self.items.extend(items)
        else:
            print(f"Unknown source type: {source}")
            
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
        
    def download_from_google_drive(self, file_id: str, destination: str) -> str:
        """
        Download a file from Google Drive using gdown library.
        
        Args:
            file_id: The ID of the file in Google Drive.
            destination: The local path to save the file to.
            
        Returns:
            The local path where the file was saved.
        """
        # Ensure gdown is installed
        try:
            import gdown
        except ImportError:
            print("gdown package not found. Installing gdown...")
            import subprocess
            subprocess.check_call(['pip', 'install', 'gdown'])
            import gdown
        
        try:
            print(f"Downloading file from Google Drive with ID: {file_id}")
            
            # Construct the Google Drive URL
            url = f"https://drive.google.com/uc?id={file_id}"
            
            # Use gdown to download the file - this handles large files and authentication
            output = gdown.download(url, destination, quiet=False)
            
            # Check if download was successful
            if output is None or not os.path.exists(destination) or os.path.getsize(destination) == 0:
                print("Download failed. Trying alternative method...")
                
                # Try with the full sharing URL
                sharing_url = f"https://drive.google.com/file/d/{file_id}/view"
                output = gdown.download(sharing_url, destination, fuzzy=True, quiet=False)
                
                # If still failed, print detailed instructions
                if output is None or not os.path.exists(destination) or os.path.getsize(destination) == 0:
                    print("\n===== GOOGLE DRIVE DOWNLOAD FAILED =====")
                    print("The file could not be downloaded due to Google Drive restrictions.")
                    print("\nTo fix this issue:")
                    print("1. Open the Google Drive link in your browser")
                    print(f"   https://drive.google.com/file/d/{file_id}/view")
                    print("2. Click the 'Share' button in the top-right corner")
                    print("3. Click 'Change to anyone with the link'")
                    print("4. Make sure 'Viewer' permission is selected")
                    print("5. Click 'Copy link'")
                    print("6. Click 'Done'")
                    print("7. Try running this tool again with the copied link")
                    print("\nAlternatively:")
                    print("1. Download the PDF manually from Google Drive")
                    print("2. Save it to your computer")
                    print("3. Use the --source parameter with the local file path instead")
                    print("   python tech_knowledge_extractor.py --source /path/to/your/file.pdf\n")
            
            # Validate file size
            if os.path.exists(destination) and os.path.getsize(destination) < 1000:  # Less than 1KB is suspicious
                print(f"Warning: Downloaded file is suspiciously small ({os.path.getsize(destination)} bytes).")
                print("This usually means the download failed or requires authentication.")
                print("Make sure the file is shared with 'Anyone with the link' on Google Drive.")
            
            return destination
        
        except Exception as e:
            print(f"Error downloading file from Google Drive: {e}")
            if not os.path.exists(destination):
                # Create an empty file to prevent further errors
                with open(destination, 'w') as f:
                    pass
            return destination


def main():
    parser = argparse.ArgumentParser(description='Technical Content Ingestion Tool')
    parser.add_argument('--source', type=str, required=True, help='Source URL or file path')
    parser.add_argument('--team_id', type=str, default='aline123', help='Team ID for the knowledge base')
    parser.add_argument('--user_id', type=str, default='', help='User ID (optional)')
    parser.add_argument('--output', type=str, default='output.json', help='Output JSON file path')
    
    args = parser.parse_args()
    
    tool = ContentIngestionTool(args.team_id, args.user_id)
    tool.process_source(args.source)
    
    output = tool.generate_output()
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Processing complete. Output saved to {args.output}")
    print(f"Processed {len(output['items'])} items.")


if __name__ == "__main__":
    main()
