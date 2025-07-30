"""
GitHub integration service for repository operations.
"""

import base64
import aiohttp
from typing import List, Dict, Any, Optional
from urllib.parse import quote


class GitHubService:
    """Service for GitHub API operations."""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {access_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def get_repository_files(
        self,
        repo_full_name: str,
        branch: str = "main",
        files: Optional[List[str]] = None,
        max_files: int = 100
    ) -> List[Dict[str, Any]]:
        """Get repository files with content."""
        
        async with aiohttp.ClientSession() as session:
            if files:
                # Get specific files
                file_contents = []
                for file_path in files[:max_files]:
                    try:
                        content = await self._get_file_content(session, repo_full_name, file_path, branch)
                        if content:
                            file_contents.append(content)
                    except Exception as e:
                        print(f"Failed to get file {file_path}: {e}")
                        continue
                return file_contents
            else:
                # Get all files from repository
                return await self._get_all_files(session, repo_full_name, branch, max_files)
    
    async def _get_file_content(
        self,
        session: aiohttp.ClientSession,
        repo_full_name: str,
        file_path: str,
        branch: str
    ) -> Optional[Dict[str, Any]]:
        """Get content of a specific file."""
        
        url = f"{self.base_url}/repos/{repo_full_name}/contents/{quote(file_path)}"
        params = {"ref": branch}
        
        async with session.get(url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get("type") == "file" and "content" in data:
                    # Decode base64 content
                    try:
                        content = base64.b64decode(data["content"]).decode("utf-8")
                        return {
                            "path": file_path,
                            "content": content,
                            "size": data.get("size", 0),
                            "language": self._detect_language(file_path),
                            "sha": data.get("sha")
                        }
                    except UnicodeDecodeError:
                        # Skip binary files
                        return None
            
            return None
    
    async def _get_all_files(
        self,
        session: aiohttp.ClientSession,
        repo_full_name: str,
        branch: str,
        max_files: int
    ) -> List[Dict[str, Any]]:
        """Get all files from repository recursively."""
        
        # Get repository tree
        tree_files = await self._get_repository_tree(session, repo_full_name, branch)
        
        # Filter and limit files
        relevant_files = self._filter_relevant_files(tree_files)[:max_files]
        
        # Get file contents
        file_contents = []
        for file_info in relevant_files:
            try:
                content = await self._get_file_content(
                    session, repo_full_name, file_info["path"], branch
                )
                if content:
                    file_contents.append(content)
            except Exception as e:
                print(f"Failed to get file {file_info['path']}: {e}")
                continue
        
        return file_contents
    
    async def _get_repository_tree(
        self,
        session: aiohttp.ClientSession,
        repo_full_name: str,
        branch: str
    ) -> List[Dict[str, str]]:
        """Get repository file tree."""
        
        url = f"{self.base_url}/repos/{repo_full_name}/git/trees/{branch}"
        params = {"recursive": "1"}
        
        async with session.get(url, headers=self.headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return [
                    {"path": item["path"], "type": item["type"]}
                    for item in data.get("tree", [])
                    if item["type"] == "blob"  # Only files, not directories
                ]
            else:
                return []
    
    def _filter_relevant_files(self, tree_files: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Filter files relevant for code review."""
        
        # Relevant file extensions
        relevant_extensions = {
            '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala',
            '.html', '.css', '.scss', '.less', '.vue', '.svelte'
        }
        
        # Files/directories to skip
        skip_patterns = [
            'node_modules/', '.git/', '__pycache__/', '.pytest_cache/',
            'venv/', 'env/', '.env/', 'dist/', 'build/', 'target/',
            '.idea/', '.vscode/', 'coverage/', '.coverage',
            'package-lock.json', 'yarn.lock', 'Pipfile.lock'
        ]
        
        filtered_files = []
        
        for file_info in tree_files:
            file_path = file_info["path"]
            
            # Skip if matches skip patterns
            if any(pattern in file_path for pattern in skip_patterns):
                continue
            
            # Include if has relevant extension
            if any(file_path.endswith(ext) for ext in relevant_extensions):
                filtered_files.append(file_info)
        
        return filtered_files
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.less': 'less',
            '.vue': 'vue',
            '.svelte': 'svelte'
        }
        
        for ext, lang in extension_map.items():
            if file_path.endswith(ext):
                return lang
        
        return 'unknown'
    
    async def get_repository_info(self, repo_full_name: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        
        url = f"{self.base_url}/repos/{repo_full_name}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                return None
    
    async def get_user_repositories(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get user's repositories."""
        
        url = f"{self.base_url}/user/repos"
        params = {
            "sort": "updated",
            "per_page": min(limit, 100),
            "type": "all"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return []
    
    async def create_webhook(
        self,
        repo_full_name: str,
        webhook_url: str,
        events: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create webhook for repository events."""
        
        if events is None:
            events = ["push", "pull_request"]
        
        url = f"{self.base_url}/repos/{repo_full_name}/hooks"
        
        payload = {
            "name": "web",
            "active": True,
            "events": events,
            "config": {
                "url": webhook_url,
                "content_type": "json"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=payload) as response:
                if response.status == 201:
                    return await response.json()
                return None
