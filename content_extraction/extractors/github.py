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
            True if this is a GitHub repository URL, False otherwise        """
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
                self.logger.error("GitHub URL should be in format: https://github.com/username/repository")
                if len(path_parts) == 1:
                    self.logger.info(f"Detected user profile URL. You may want to specify a specific repository.")
                    # Try to suggest repositories for this user
                    self._suggest_repositories(path_parts[0])
                return []
            
            owner = path_parts[0]
            repo = path_parts[1]
            
            # Prepare headers for GitHub API
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Content-Extractor/1.0"
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
            response = requests.get(readme_url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                self.logger.warning(f"No README found for {owner}/{repo}")
                return []
            
            response.raise_for_status()
            readme_data = response.json()
            
            # Decode base64 content
            content = base64.b64decode(readme_data['content']).decode('utf-8')
            
            # Extract title from the content or use default
            title = self._extract_title_from_content(content) or f"{repo} README"
            
            # Create content item
            content_item = ContentItem(
                content_id=generate_unique_id(f"{owner}/{repo}/README"),
                title=title,
                content=content,
                source_url=f"https://github.com/{owner}/{repo}",
                content_type="documentation",
                metadata={
                    "github_owner": owner,
                    "github_repo": repo,
                    "file_type": "README",
                    "file_name": readme_data.get('name', 'README')
                }
            )
            
            return [content_item]
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching README for {owner}/{repo}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error processing README for {owner}/{repo}: {e}", exc_info=True)
            return []
    
    def _extract_docs(self, owner: str, repo: str, headers: Dict[str, str]) -> List[ContentItem]:
        """Extract documentation files from a repository."""
        items = []
        
        # Check for common documentation directories
        doc_dirs = ["docs", "documentation", "doc"]
        
        for doc_dir in doc_dirs:
            try:
                # Get contents of the directory
                contents_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{doc_dir}"
                response = requests.get(contents_url, headers=headers, timeout=30)
                
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
                        
                    # Respect max files limit
                    if file_count >= self.max_files:
                        break
                        
                    # Get the file content
                    file_response = requests.get(item["url"], headers=headers, timeout=30)
                    file_response.raise_for_status()
                    file_data = file_response.json()
                    
                    if file_data.get("encoding") == "base64" and file_data.get("content"):
                        try:
                            file_content = base64.b64decode(file_data["content"]).decode("utf-8")
                            
                            title = self._extract_title_from_content(file_content) or f"{repo} - {item['name']}"
                            content_id = generate_unique_id(f"{owner}/{repo}/{item['name']}")
                            
                            items.append(ContentItem(
                                content_id=content_id,
                                title=title,
                                content=file_content,
                                source_url=file_data["html_url"],
                                content_type="documentation",
                                metadata={
                                    "github_owner": owner,
                                    "github_repo": repo,
                                    "file_path": file_data["path"],
                                    "file_name": item["name"]
                                }
                            ))
                            
                            file_count += 1
                            
                        except UnicodeDecodeError:
                            self.logger.warning(f"Could not decode file {item['name']} in {owner}/{repo}")
                            continue
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error fetching docs from {doc_dir} in {owner}/{repo}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Error processing docs from {doc_dir} in {owner}/{repo}: {e}", exc_info=True)
                continue
        
        return items
    
    def _suggest_repositories(self, username: str):
        """Suggest repositories for a given username."""
        try:
            api_url = f"https://api.github.com/users/{username}/repos"
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "Content-Extractor/1.0"
            }
            
            if self.access_token:
                headers["Authorization"] = f"token {self.access_token}"
            
            response = requests.get(api_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                repos = response.json()
                if repos:
                    self.logger.info(f"Found {len(repos)} repositories for user '{username}':")
                    for i, repo in enumerate(repos[:5]):  # Show first 5 repos
                        self.logger.info(f"  - {repo['html_url']} ({repo['description'] or 'No description'})")
                    if len(repos) > 5:
                        self.logger.info(f"  ... and {len(repos) - 5} more repositories")
                else:
                    self.logger.info(f"No public repositories found for user '{username}'")
            else:
                self.logger.warning(f"Could not fetch repositories for user '{username}' (status: {response.status_code})")
                
        except Exception as e:
            self.logger.error(f"Error fetching repositories for user '{username}': {e}")
    
    def _extract_title_from_content(self, content: str) -> Optional[str]:
        """Extract title from markdown content."""
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            elif line and not line.startswith('#') and len(line) < 100:
                # First non-header line might be the title
                return line
        
        return None
