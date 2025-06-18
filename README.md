# Technical Content Extractor

A robust, production-ready, and extensible tool for extracting technical content from various sources into a structured knowledge base. The system uses a plugin-based architecture that allows easy addition of new content sources without modifying the core code.

## Overview

This tool extracts technical knowledge from many different sources through a configurable plugin system:

1. Generic blogs and technical articles
2. Book chapters from PDF files (including Google Drive)
3. Substack newsletters
4. GitHub repositories (documentation, README files)
5. Other sources via custom extractors

All content is cleaned, converted to markdown, and structured into a consistent JSON format suitable for importing into a knowledge base or further processing.

## Features

- **Plugin-Based Architecture**: Easily extend the system with new content source extractors
- **Configuration-Driven**: Configure extractors and behavior through a simple JSON config file
- **Multi-Source Support**: Scrapes and processes content from diverse sources
- **Smart Content Cleaning**: Removes ads, navigation bars, footers, and other non-content elements
- **Markdown Conversion**: Converts all content to clean, consistent markdown format
- **Metadata Extraction**: Extracts titles, authors, and content types automatically
- **PDF Processing**: Extracts text from PDFs and identifies chapters
- **Google Drive Integration**: Downloads and processes PDFs from Google Drive links
- **Progress Reporting**: Shows progress bars for multi-item extractions
- **Error Handling**: Robust error handling with detailed logging
- **Flexible Output**: Generates structured JSON in the required format
- **Interactive Scripts**: Includes example scripts for easy testing and demonstration

## Architecture

The project follows a modular, plugin-based architecture:

1. **tech_content_extractor.py**: The main orchestrator that dynamically discovers and loads extractors
2. **content_extraction/base.py**: Core abstractions and interfaces for the extraction system
3. **content_extraction/extractors/**: Directory containing individual extractor plugins
4. **config.json**: Configuration file for customizing extractor behavior

Helper scripts:

- **example.py**: Example script demonstrating how to use the framework
- **run_extractor.bat/sh**: Interactive menu scripts for easy usage

## Installation

### Prerequisites

- Python 3.6 or later
- Internet connection

### Setup

1. **Create a virtual environment (recommended)**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Interactive Mode

Run the example script in interactive mode:

```bash
python example.py --interactive
```

### Command Line Usage

**Process a specific source:**

```bash
python tech_content_extractor.py "https://example.com/blog/article"
```

**Process a source with custom output location:**

```bash
python tech_content_extractor.py "https://github.com/username/repo" --output "github_content.json"
```

### Example Script

Try the included examples:

```bash
# Run the blog example
python example.py --blog

# Run the GitHub example
python example.py --github

# Run the Substack example
python example.py --substack
```

**Process all sources plus a book from Google Drive:**

```bash
python tech_knowledge_extractor.py --all --gdrive "https://drive.google.com/file/d/YOUR_FILE_ID/view"
```

**Process a local PDF file:**

```bash
python tech_knowledge_extractor.py --source "path/to/book.pdf"
```

### Using the Base Content Ingestion Tool

For more flexibility with any source:

```bash
python content_ingestion.py --source <SOURCE_URL_OR_PATH> [--team_id TEAM_ID] [--user_id USER_ID] [--output OUTPUT_FILE]
```

## Extending with Custom Extractors

The plugin architecture makes it easy to add new content source extractors:

1. Create a new file in `content_extraction/extractors/` (e.g., `my_source.py`)
2. Implement a class that inherits from `ContentExtractor`
3. Implement the required methods: `can_handle` and `extract`
4. Update the configuration in `config.json` with source-specific settings

Example structure for a custom extractor:

```python
from content_extraction.base import ContentExtractor, ContentItem

class MyCustomExtractor(ContentExtractor):
    """Extractor for my custom content source."""

    def __init__(self, config):
        super().__init__(config)
        # Get custom configuration settings
        self.my_setting = config.get("extractors", {}).get("my_source", {}).get("my_setting", "default")

    def can_handle(self, source: str) -> bool:
        # Determine if this extractor can handle the source
        return "mysite.com" in source.lower()

    def extract(self, source: str) -> List[ContentItem]:
        # Extract content from the source
        # Return a list of ContentItem objects
        # ...
```

## Output Format

The tool produces JSON output in the following format:

```json
[
  {
    "id": "<Unique identifier>",
    "title": "<Extracted Title>",
    "content": "<Cleaned markdown content>",
    "source_url": "<Original URL or source path>",
    "content_type": "article|documentation|guide|book_chapter|other",
    "author": "<Author if known>",
    "date_published": "<Publication date if available>",
    "tags": ["<tag1>", "<tag2>"],
    "metadata": {
      "<key>": "<value>",
      ...
    }
  },
  ...
]
```

## Content Types

The system automatically detects and assigns appropriate content types:

- `article`: Blog posts, technical articles
- `documentation`: Documentation pages, GitHub READMEs
- `guide`: How-to guides, tutorials
- `book_chapter`: Book chapters or PDF content sections
- `other`: Content that doesn't match the above categories

## Configuration Options

The `config.json` file allows you to customize extractor behavior:

```json
{
  "output_directory": "./output",
  "log_level": "INFO",
  "user_agent": "Mozilla/5.0...",
  "sources": {
    "blog": {
      "enabled": true,
      "delay_between_requests": [1, 3]
    },
    "pdf": {
      "enabled": true,
      "max_chapters": 0
    },
    "github": {
      "enabled": true,
      "max_files_per_repo": 50
    }
  },
  "extractors": {
    "generic_blog": {
      "article_selectors": ["article", ".post", ".entry", ".blog-post"],
      "list_page_link_patterns": ["/(article|post|blog)/", "/\\d{4}/\\d{2}/"]
    },
    "pdf": {
      "chapter_patterns": [
        "(?:Chapter|CHAPTER)\\s+(\\d+|[IVX]+)[:\\s]+(.+?)(?=(?:Chapter|CHAPTER)\\s+\\d+|$)"
      ]
    },
    "github": {
      "access_token": "",
      "max_files": 50,
      "file_extensions": [".md", ".markdown", ".txt", ".rst"]
    }
  }
}
```

## Command Line Options

### tech_content_extractor.py

- Source URL or file path (positional argument): The source to process
- `--config`: Path to configuration file (default: 'config.json')
- `--output`: Output JSON file path (default: 'extracted_content.json')
- `--list-sources`: List supported source types
- `--interactive`: Run in interactive mode

### example.py

- `--interactive`: Run in interactive mode
- `--blog`: Run the blog processing example
- `--github`: Run the GitHub processing example
- `--substack`: Run the Substack processing example

### interviewing.io Interview Guides

```bash
python tech_knowledge_extractor.py --source "https://interviewing.io/learn#interview-guides"
```

The tool will extract all interview guides by:

1. Finding all interview guide links on the learn page
2. Following each link to extract the full content of each guide
3. Setting the content_type to "guide" for appropriate categorization

### nilmamano.com DS&A Blog Posts

```bash
python tech_knowledge_extractor.py --source "https://nilmamano.com/blog/category/dsa"
```

The tool will extract all DS&A blog posts by:

1. Finding all article links on the category page
2. Following each link to extract the full content
3. Processing any pagination to ensure all posts are captured

### PDF Book from Google Drive

```bash
python tech_knowledge_extractor.py --gdrive "https://drive.google.com/file/d/YOUR_FILE_ID/view" --output "book_content.json"
```

For a Google Drive folder with multiple PDFs:

```bash
python tech_knowledge_extractor.py --gdrive "https://drive.google.com/drive/folders/YOUR_FOLDER_ID" --output "books_content.json"
```

#### Important: Google Drive Permissions

For the tool to successfully download files from Google Drive:

1. Make sure the PDF file is shared with the correct permissions:

   - Open the file in Google Drive
   - Click "Share" button in the top-right corner
   - Click "Change to anyone with the link"
   - Make sure "Viewer" permission is selected
   - Click "Copy link"
   - Click "Done"
   - Use the copied link with the `--gdrive` parameter

2. If you encounter "Cannot retrieve the public link of the file" error:

   - The file might have restricted access
   - Try downloading the file manually from Google Drive
   - Save it to your computer
   - Use the `--source` parameter with the local file path instead:
     ```bash
     python tech_knowledge_extractor.py --source "/path/to/your/file.pdf" --output "book_content.json"
     ```

3. For large files or files with frequent access:

   - Google Drive may temporarily restrict automated downloads
   - Consider using a direct download link or local file
   - Set sharing to "Anyone with the link" can view
   - Copy the link

4. The tool now uses the `gdown` library for more reliable downloads from Google Drive.
   If it's not installed, the tool will attempt to automatically install it.

#### What the Tool Does

1. Extract the file ID from the Google Drive URL
2. Download the PDF file(s) using the gdown library
3. Process the PDF content, identifying and extracting chapters
4. For books, process only the first 8 chapters as specified

You can specify the output file path using the `--output` parameter. If not specified, the default output file will be `aline_knowledge.json`.

### Substack Newsletter

```bash
python tech_knowledge_extractor.py --source "https://shreycation.substack.com"
```

The tool will:

1. Access the Substack archive page to find all posts
2. Extract and process each individual post
3. Filter content by the main author if specified

### Generic Blog (Testing Robustness)

```bash
python tech_knowledge_extractor.py --source "https://quill.co/blog"
```

The tool demonstrates robustness by:

1. Automatically detecting the blog structure
2. Extracting links to individual articles
3. Processing each article while handling different HTML structures

## Troubleshooting

### Common Issues

1. **Missing Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Failed to Access Website**

   - Check your internet connection
   - Verify the URL is correct
   - Try again later (website might be temporarily blocking automated requests)

3. **PDF Processing Problems**

   - Ensure the PDF is not password-protected
   - Verify the PDF contains text (not just scanned images)
   - For Google Drive PDFs, check file permissions and link validity

4. **Error Logs**
   - Check `extraction.log` for detailed error messages

## Running Tests

Basic tests for the content ingestion functionality:

```bash
python test_content_ingestion.py
```

Example extractor script (runs extraction for selected sources):

```bash
python example_extractor.py
```

## Handling Complex Link Structures

The extractor is designed to handle complex link structures that may be encountered:

### Link Redirects

The tool follows HTTP redirects to ensure it reaches the final content page, even when the initial URL points to an intermediate page.

### Nested Content

For pages that require multiple clicks to reach the actual content (like clicking on a blog card to reach the full article), the tool:

1. First identifies all links on the list/category page
2. Then processes each link individually to extract the full content

### Pagination

For blogs with multiple pages, the tool can detect and follow pagination links to ensure all content is captured.

### Non-Standard Layouts

The tool uses multiple selectors and fallback strategies to handle various page layouts:

- Common article selectors: `.post`, `article`, `.entry`, etc.
- Site-specific selectors for known sites
- Generic fallback for unknown structures

## Important Notes on URL Processing

When using the tool, always provide the exact URL as shown in the examples above. Using abbreviated source names like `interviewing_blog` instead of the full URL will cause errors.
