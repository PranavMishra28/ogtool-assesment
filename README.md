# Aline Technical Knowledge Extractor

A robust, production-ready tool for extracting technical content from various sources into a structured knowledge base for Reddit-style auto-comment generation.

## Overview

This tool extracts technical knowledge from:

1. interviewing.io blog posts
2. interviewing.io company guides
3. interviewing.io interview guides
4. nilmamano.com DS&A blog posts
5. Book chapters from PDF files (including Google Drive)
6. Substack newsletters (bonus)
7. Generic blogs (e.g., quill.co/blog for robustness testing)

All content is cleaned, converted to markdown, and structured into a consistent JSON format suitable for importing into a knowledge base.

## Features

- **Multi-Source Support**: Scrapes and processes content from diverse sources
- **Smart Content Cleaning**: Removes ads, navigation bars, footers, and other non-content elements
- **Markdown Conversion**: Converts all content to clean, consistent markdown format
- **Metadata Extraction**: Extracts titles, authors, and content types automatically
- **PDF Processing**: Extracts text from PDFs and identifies chapters
- **Google Drive Integration**: Downloads and processes PDFs from Google Drive links
- **Progress Reporting**: Shows progress bars for multi-item extractions
- **Error Handling**: Robust error handling with detailed logging
- **Flexible Output**: Generates structured JSON in the required format
- **Interactive Scripts**: Includes batch files for easy execution

## Architecture

The project consists of two main Python files:

1. **tech_knowledge_extractor.py**: The main orchestrator that handles specific sources and coordinates the extraction process
2. **content_ingestion.py**: A general-purpose tool for content processing, used by the extractor

Helper scripts:

- **run_extractor.bat**: Windows interactive menu
- **run_extractor.sh**: Linux/macOS interactive menu
- **example_extractor.py**: Example implementation for testing

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

Run the provided script for an interactive menu:

**Windows:**

```bash
run_extractor.bat
```

**macOS/Linux:**

```bash
bash run_extractor.sh
```

### Command Line Usage

**Process all specified sources:**

```bash
python tech_knowledge_extractor.py --all
```

**Process a specific source:**

```bash
python tech_knowledge_extractor.py --source "https://interviewing.io/blog"
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

## Output Format

The tool produces JSON output in the following format:

```json
{
  "team_id": "aline123",
  "items": [
    {
      "title": "<Extracted Title>",
      "content": "<Cleaned markdown content>",
      "content_type": "blog|podcast_transcript|call_transcript|linkedin_post|reddit_comment|book|other",
      "source_url": "<Original URL or source path>",
      "author": "<Author if known>",
      "user_id": ""
    },
    ...
  ]
}
```

## Content Types

The tool automatically detects and assigns the following content types:

- `blog`: Blog posts and articles
- `guide`: Company or interview guides
- `podcast_transcript`: Podcast episode transcripts
- `call_transcript`: Interview or meeting transcripts
- `linkedin_post`: LinkedIn posts
- `reddit_comment`: Reddit comments or posts
- `book`: Book chapters or PDF content
- `other`: Content that doesn't match the above categories

## Command Line Options

- `--source`: URL or file path to process
- `--gdrive`: Google Drive link to a PDF book
- `--all`: Process all specified sources
- `--team_id`: Team ID for the knowledge base (default: 'aline123')
- `--user_id`: User ID (optional)
- `--output`: Output JSON file path (default: 'aline_knowledge.json')

## Source-Specific Examples

### interviewing.io Blog Posts

```bash
python tech_knowledge_extractor.py --source "https://interviewing.io/blog"
```

### interviewing.io Company Guides

```bash
python tech_knowledge_extractor.py --source "https://interviewing.io/topics#companies"
```

### interviewing.io Interview Guides

```bash
python tech_knowledge_extractor.py --source "https://interviewing.io/learn#interview-guides"
```

### nilmamano.com DS&A Blog Posts

```bash
python tech_knowledge_extractor.py --source "https://nilmamano.com/blog/category/dsa"
```

### Substack Newsletter

```bash
python tech_knowledge_extractor.py --source "https://shreycation.substack.com"
```

### Generic Blog (Testing Robustness)

```bash
python tech_knowledge_extractor.py --source "https://quill.co/blog"
```

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
