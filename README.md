# Technical Content Ingestion Tool

This tool extracts clean, high-quality, structured knowledge from diverse online sources (blogs, guides, PDFs, etc.) into a reusable JSON format for a knowledgebase that supports Reddit-style auto-comment generation.

## Features

- Scrapes and parses technical blog posts, interview guides, and book chapters
- Supports multiple input sources: blog URLs, list pages, PDFs, and Substack newsletters
- Cleans content by removing ads, navigation bars, and unrelated footers
- Outputs structured JSON with metadata tagging
- Converts content to clean markdown format

## Installation

1. Clone this repository or download the files
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the tool from the command line with the following options:

```bash
python content_ingestion.py --source <SOURCE_URL_OR_PATH> [--team_id TEAM_ID] [--user_id USER_ID] [--output OUTPUT_FILE]
```

### Parameters:

- `--source`: Source URL or file path (required)
- `--team_id`: Team ID for the knowledge base (default: 'aline123')
- `--user_id`: User ID (optional)
- `--output`: Output JSON file path (default: 'output.json')

### Examples:

Process a blog post:

```bash
python content_ingestion.py --source https://interviewing.io/blog/why-you-bombed-your-last-interview --output blog_output.json
```

Process a PDF file:

```bash
python content_ingestion.py --source "path/to/Beyond Cracking the Coding Interview - Ch 1-8.pdf" --output book_output.json
```

Process a Substack newsletter:

```bash
python content_ingestion.py --source https://shreycation.substack.com --output newsletter_output.json
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
- `podcast_transcript`: Podcast episode transcripts
- `call_transcript`: Interview or meeting transcripts
- `linkedin_post`: LinkedIn posts
- `reddit_comment`: Reddit comments or posts
- `book`: Book chapters or PDF content
- `other`: Content that doesn't match the above categories
