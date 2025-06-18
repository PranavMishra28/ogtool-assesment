"""
GitHub extractor module.

This module provides functionality to extract content from GitHub repositories,
including README files, documentation, and relevant markdown files.
"""

import re
import logging
from typing import Dict, List, Any, Optional
import base64
from urllib.parse import urlparse

import requests

from content_extraction.base import ContentExtractor, ContentItem
from content_extraction.utils import generate_unique_id


class GitHubExtractor(ContentExtractor):
    """Extractor for GitHub repository content."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the GitHubExtractor.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__(config)
        self.github_config = config.get("extractors", {}).get("github", {})
        self.access_token = self.github_config.get("access_token", "")
        self.max_files = self.github_config.get("max_files", 50)
        self.file_extensions = self.github_config.get(
            "file_extensions", [".md", ".markdown", ".txt", ".rst"]
        )
        
    def can_handle(self, source: str) -> bool:
        """
        Check if this extractor can handle the given source.
        
        Args:
            source: URL to check
            
        Returns:
            True if this is a GitHub repository URL, False otherwise
        """
        parsed_url = urlparse(source)
        return (
            parsed_url.netloc in ("github.com", "www.github.com") and
            len(parsed_url.path.strip("/").split("/")) >= 2  # At least owner/repo
        )
    
    def extract(self, url: str) -> List[ContentItem]:
        """
        Extract content from a GitHub repository.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            List of ContentItem objects
        """
        self.logger.info(f"Extracting content from GitHub repository: {url}")
        
        try:
            # Extract owner and repo from URL
            path_parts = urlparse(url).path.strip("/").split("/")
            if len(path_parts) < 2:
                self.logger.error(f"Invalid GitHub URL format: {url}")
                return []
            
            owner = path_parts[0]
            repo = path_parts[1]
            
            # Prepare headers for GitHub API
            headers = {
                "Accept": "application/vnd.github.v3+json"
            }
            
            if self.access_token:
                headers["Authorization"] = f"token {self.access_token}"
            
            # First get the README content
            items = self._extract_readme(owner, repo, headers)
            
            # Then get additional documentation files
            items.extend(self._extract_docs(owner, repo, headers))
            
            return items
            
        except Exception as e:
            self.logger.error(f"Error extracting content from GitHub repository {url}: {e}", exc_info=True)
            return []
    
    def _extract_readme(self, owner: str, repo: str, headers: Dict[str, str]) -> List[ContentItem]:
        """Extract README content from a repository."""
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        
        try:
            response = requests.get(readme_url, headers=headers)
            if response.status_code == 404:
                self.logger.warning(f"README not found for {owner}/{repo}")
                return []
            
            response.raise_for_status()
            data = response.json()
            
            content = base64.b64decode(data["content"]).decode("utf-8")
            title = f"{owner}/{repo} - README"
            content_id = generate_unique_id(title)
            
            return [ContentItem(
                content_id=content_id,
                title=title,
                content=content,
                source_url=data["html_url"],
                content_type="documentation",
                author=owner,
                metadata={
                    "repository": f"{owner}/{repo}",
                    "file_path": data["path"],
                    "platform": "GitHub"
                }
            )]
            
        except Exception as e:
            self.logger.error(f"Error extracting README from {owner}/{repo}: {e}")
            return []
    
    def _extract_docs(self, owner: str, repo: str, headers: Dict[str, str]) -> List[ContentItem]:
        """Extract documentation files from a repository."""
        items = []
        
        # Check for common documentation directories
        doc_dirs = ["docs", "documentation", "doc", "wiki"]
        
        for doc_dir in doc_dirs:
            try:
                # Get contents of the directory
                contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{doc_dir}"
                response = requests.get(contents_url, headers=headers)
                
                # Skip if directory doesn't exist
                if response.status_code == 404:
                    continue
                
                response.raise_for_status()
                contents = response.json()
                
                # Process each file in the directory
                file_count = 0
                for item in contents:
                    if item["type"] != "file":
                        continue
                        
                    # Check if file extension matches our criteria
                    if not any(item["name"].endswith(ext) for ext in self.file_extensions):
                        continue
                        
                    # Get the file content
                    file_response = requests.get(item["url"], headers=headers)
                    file_response.raise_for_status()
                    file_data = file_response.json()
                    
                    if file_data.get("encoding") == "base64" and file_data.get("content"):
                        file_content = base64.b64decode(file_data["content"]).decode("utf-8")
                        
                        title = f"{owner}/{repo} - {item['name']}"
                        content_id = generate_unique_id(title)
                        
                        items.append(ContentItem(
                            content_id=content_id,
                            title=title,
                            content=file_content,
                            source_url=file_data["html_url"],
                            content_type="documentation",
                            author=owner,
                            metadata={
                                "repository": f"{owner}/{repo}",
                                "file_path": file_data["path"],
                                "platform": "GitHub"
                            }
                        ))
                        
                        file_count += 1
                        if file_count >= self.max_files:
                            break
            
            except Exception as e:
                self.logger.warning(f"Error extracting docs from {doc_dir} directory: {e}")
        
        return items
