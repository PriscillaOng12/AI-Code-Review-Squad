"""
Database models for the AI Code Review Squad.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base
from app.core.config import ReviewStatus, Severity, Confidence


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=True)
    github_username = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repositories = relationship("Repository", back_populates="owner")
    reviews = relationship("CodeReview", back_populates="created_by")


class Repository(Base):
    """Repository model for GitHub repositories."""
    __tablename__ = "repositories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, unique=True, index=True)  # owner/repo
    github_id = Column(Integer, nullable=False, unique=True, index=True)
    clone_url = Column(String(500), nullable=False)
    webhook_secret = Column(String(255), nullable=True)
    default_branch = Column(String(100), default="main")
    language = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Configuration
    auto_review_enabled = Column(Boolean, default=True)
    review_on_pr = Column(Boolean, default=True)
    review_on_push = Column(Boolean, default=False)
    
    # Owner
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="repositories")
    reviews = relationship("CodeReview", back_populates="repository")


class CodeReview(Base):
    """Code review model for tracking review sessions."""
    __tablename__ = "code_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # GitHub information
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=False)
    commit_hash = Column(String(40), nullable=False, index=True)
    pr_number = Column(Integer, nullable=True, index=True)
    branch = Column(String(255), nullable=True)
    
    # Review metadata
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, index=True)
    trigger_event = Column(String(50), nullable=True)  # webhook, manual, scheduled
    
    # Timing information
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Summary statistics
    total_files = Column(Integer, default=0)
    analyzed_files = Column(Integer, default=0)
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    
    # Overall assessment
    overall_score = Column(Float, nullable=True)  # 0-100 quality score
    recommendation = Column(Text, nullable=True)
    
    # Foreign keys
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    repository = relationship("Repository", back_populates="reviews")
    created_by = relationship("User", back_populates="reviews")
    agent_responses = relationship("AgentResponse", back_populates="review", cascade="all, delete-orphan")
    file_analyses = relationship("FileAnalysis", back_populates="review", cascade="all, delete-orphan")


class AgentResponse(Base):
    """Agent response model for individual agent analysis results."""
    __tablename__ = "agent_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Review association
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # Agent information
    agent_type = Column(String(50), nullable=False, index=True)  # security, performance, style, logic, architecture
    agent_version = Column(String(20), nullable=True)
    
    # Analysis results
    findings = Column(JSON, nullable=True)  # Structured findings data
    summary = Column(Text, nullable=True)
    confidence = Column(Enum(Confidence), nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    
    # Metrics
    execution_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_cents = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(20), default="completed")  # completed, failed, timeout
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    review = relationship("CodeReview", back_populates="agent_responses")


class FileAnalysis(Base):
    """File-level analysis results."""
    __tablename__ = "file_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Review association
    review_id = Column(UUID(as_uuid=True), ForeignKey("code_reviews.id"), nullable=False)
    
    # File information
    file_path = Column(String(1000), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 of content
    file_size = Column(Integer, nullable=True)
    language = Column(String(50), nullable=True)
    
    # Analysis results per agent
    security_findings = Column(JSON, nullable=True)
    performance_findings = Column(JSON, nullable=True)
    style_findings = Column(JSON, nullable=True)
    logic_findings = Column(JSON, nullable=True)
    architecture_findings = Column(JSON, nullable=True)
    
    # File-level metrics
    complexity_score = Column(Float, nullable=True)
    maintainability_score = Column(Float, nullable=True)
    test_coverage = Column(Float, nullable=True)
    
    # Status
    analysis_status = Column(String(20), default="pending")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    review = relationship("CodeReview", back_populates="file_analyses")


class ReviewMetrics(Base):
    """Aggregated metrics for reviews and repositories."""
    __tablename__ = "review_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    date = Column(DateTime, nullable=False, index=True)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), nullable=True)
    
    # Metrics
    total_reviews = Column(Integer, default=0)
    avg_review_time_minutes = Column(Float, nullable=True)
    avg_quality_score = Column(Float, nullable=True)
    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    false_positive_rate = Column(Float, nullable=True)
    
    # Agent performance
    agent_reliability = Column(JSON, nullable=True)  # Per-agent success rates
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentConfig(Base):
    """Configuration for AI agents."""
    __tablename__ = "agent_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Agent identification
    agent_type = Column(String(50), nullable=False, unique=True, index=True)
    
    # Configuration
    enabled = Column(Boolean, default=True)
    model = Column(String(100), nullable=False)
    temperature = Column(Float, default=0.1)
    max_tokens = Column(Integer, default=2000)
    timeout_seconds = Column(Integer, default=120)
    priority = Column(Integer, default=1)
    
    # Custom prompts and rules
    system_prompt = Column(Text, nullable=True)
    custom_rules = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
