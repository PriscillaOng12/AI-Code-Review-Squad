"""
Core application configuration and settings.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "AI Code Review Squad"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-change-in-production"
    
    # Database
    database_url: str = "postgresql://aiuser:aipassword@localhost:5432/aicodereview"
    redis_url: str = "redis://localhost:6379"
    
    # API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # GitHub Configuration
    github_app_id: Optional[str] = None
    github_private_key: Optional[str] = None
    github_webhook_secret: Optional[str] = None
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    rate_limit_burst: int = 20
    
    # Agent Configuration
    max_concurrent_reviews: int = 10
    review_timeout_minutes: int = 15
    agent_timeout_seconds: int = 120
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_enabled: bool = True
    
    # Email (optional)
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    
    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    @validator('allowed_hosts', pre=True)
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',')]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Agent configurations
AGENT_CONFIGS = {
    "security": {
        "enabled": True,
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000,
        "timeout": 120,
        "priority": 1,
        "description": "Identifies security vulnerabilities and threats"
    },
    "performance": {
        "enabled": True,
        "model": "gpt-4",
        "temperature": 0.2,
        "max_tokens": 2000,
        "timeout": 120,
        "priority": 2,
        "description": "Analyzes performance bottlenecks and optimization opportunities"
    },
    "style": {
        "enabled": True,
        "model": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_tokens": 1500,
        "timeout": 90,
        "priority": 3,
        "description": "Enforces coding standards and style guidelines"
    },
    "logic": {
        "enabled": True,
        "model": "gpt-4",
        "temperature": 0.1,
        "max_tokens": 2000,
        "timeout": 120,
        "priority": 1,
        "description": "Detects logical errors and edge cases"
    },
    "architecture": {
        "enabled": True,
        "model": "gpt-4",
        "temperature": 0.2,
        "max_tokens": 2500,
        "timeout": 150,
        "priority": 2,
        "description": "Reviews code architecture and design patterns"
    }
}

# Supported file extensions for code analysis
SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.jsx': 'javascript',
    '.tsx': 'typescript',
    '.java': 'java',
    '.cpp': 'cpp',
    '.c': 'c',
    '.cs': 'csharp',
    '.go': 'go',
    '.rs': 'rust',
    '.php': 'php',
    '.rb': 'ruby',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.sql': 'sql',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.json': 'json',
    '.xml': 'xml',
    '.html': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.less': 'less'
}

# Review status constants
class ReviewStatus:
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

# Agent response severity levels
class Severity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

# Confidence levels for agent responses
class Confidence:
    VERY_HIGH = "very_high"  # 90-100%
    HIGH = "high"           # 70-89%
    MEDIUM = "medium"       # 50-69%
    LOW = "low"            # 30-49%
    VERY_LOW = "very_low"  # 0-29%
