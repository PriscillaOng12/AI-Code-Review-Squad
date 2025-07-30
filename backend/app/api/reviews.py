"""
Code Review API endpoints.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid

from app.core.database import get_db
from app.models.code_review import CodeReview, ReviewStatus
from app.models.repository import Repository
from app.models.agent_response import AgentResponse
from app.agents.orchestra import AgentOrchestra, AgentConfig
from app.agents.base import CodeFile
from app.services.github_service import GitHubService
from app.services.review_service import ReviewService
from app.core.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/reviews", tags=["reviews"])


class CreateReviewRequest(BaseModel):
    """Request model for creating a code review."""
    repository_id: int
    branch: str = "main"
    commit_sha: Optional[str] = None
    files: Optional[List[str]] = None  # Specific files to review
    agents_config: Optional[Dict[str, Dict[str, Any]]] = None
    context: Optional[Dict[str, Any]] = None


class ReviewResponse(BaseModel):
    """Response model for code review."""
    id: int
    repository_id: int
    status: str
    branch: str
    commit_sha: Optional[str]
    created_at: str
    completed_at: Optional[str]
    summary: Optional[Dict[str, Any]]
    findings_count: int


class FindingResponse(BaseModel):
    """Response model for individual finding."""
    id: int
    title: str
    description: str
    severity: str
    confidence: int
    file_path: str
    line_number: int
    code_snippet: str
    suggestion: str
    category: str
    rule_id: str
    agent_name: str


@router.post("/", response_model=ReviewResponse)
async def create_review(
    request: CreateReviewRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new code review."""
    
    # Verify repository exists and user has access
    repository = db.query(Repository).filter(
        Repository.id == request.repository_id,
        Repository.user_id == current_user.id
    ).first()
    
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Create review record
    review = CodeReview(
        repository_id=request.repository_id,
        branch=request.branch,
        commit_sha=request.commit_sha,
        status=ReviewStatus.PENDING
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # Start review in background
    background_tasks.add_task(
        run_code_review,
        review.id,
        request.files,
        request.agents_config,
        request.context
    )
    
    return ReviewResponse(
        id=review.id,
        repository_id=review.repository_id,
        status=review.status.value,
        branch=review.branch,
        commit_sha=review.commit_sha,
        created_at=review.created_at.isoformat(),
        completed_at=None,
        summary=None,
        findings_count=0
    )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get code review by ID."""
    
    review = db.query(CodeReview).join(Repository).filter(
        CodeReview.id == review_id,
        Repository.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Count findings
    findings_count = db.query(AgentResponse).filter(
        AgentResponse.review_id == review_id
    ).count()
    
    return ReviewResponse(
        id=review.id,
        repository_id=review.repository_id,
        status=review.status.value,
        branch=review.branch,
        commit_sha=review.commit_sha,
        created_at=review.created_at.isoformat(),
        completed_at=review.completed_at.isoformat() if review.completed_at else None,
        summary=review.summary,
        findings_count=findings_count
    )


@router.get("/{review_id}/findings", response_model=List[FindingResponse])
async def get_review_findings(
    review_id: int,
    severity: Optional[str] = Query(None, description="Filter by severity"),
    category: Optional[str] = Query(None, description="Filter by category"),
    agent: Optional[str] = Query(None, description="Filter by agent"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get findings for a code review."""
    
    # Verify access
    review = db.query(CodeReview).join(Repository).filter(
        CodeReview.id == review_id,
        Repository.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Build query
    query = db.query(AgentResponse).filter(AgentResponse.review_id == review_id)
    
    if severity:
        query = query.filter(AgentResponse.severity == severity)
    if category:
        query = query.filter(AgentResponse.category == category)
    if agent:
        query = query.filter(AgentResponse.agent_name == agent)
    
    # Apply pagination and ordering
    findings = query.order_by(
        AgentResponse.severity.desc(),
        AgentResponse.confidence.desc()
    ).offset(offset).limit(limit).all()
    
    return [
        FindingResponse(
            id=finding.id,
            title=finding.title,
            description=finding.description,
            severity=finding.severity.value,
            confidence=finding.confidence,
            file_path=finding.file_path,
            line_number=finding.line_number,
            code_snippet=finding.code_snippet,
            suggestion=finding.suggestion,
            category=finding.category,
            rule_id=finding.rule_id,
            agent_name=finding.agent_name
        )
        for finding in findings
    ]


@router.get("/", response_model=List[ReviewResponse])
async def list_reviews(
    repository_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List code reviews for the current user."""
    
    query = db.query(CodeReview).join(Repository).filter(
        Repository.user_id == current_user.id
    )
    
    if repository_id:
        query = query.filter(CodeReview.repository_id == repository_id)
    if status:
        query = query.filter(CodeReview.status == status)
    
    reviews = query.order_by(CodeReview.created_at.desc()).offset(offset).limit(limit).all()
    
    response = []
    for review in reviews:
        findings_count = db.query(AgentResponse).filter(
            AgentResponse.review_id == review.id
        ).count()
        
        response.append(ReviewResponse(
            id=review.id,
            repository_id=review.repository_id,
            status=review.status.value,
            branch=review.branch,
            commit_sha=review.commit_sha,
            created_at=review.created_at.isoformat(),
            completed_at=review.completed_at.isoformat() if review.completed_at else None,
            summary=review.summary,
            findings_count=findings_count
        ))
    
    return response


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a code review."""
    
    review = db.query(CodeReview).join(Repository).filter(
        CodeReview.id == review_id,
        Repository.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Delete related findings first
    db.query(AgentResponse).filter(AgentResponse.review_id == review_id).delete()
    
    # Delete review
    db.delete(review)
    db.commit()
    
    return {"message": "Review deleted successfully"}


async def run_code_review(
    review_id: int,
    files: Optional[List[str]] = None,
    agents_config: Optional[Dict[str, Dict[str, Any]]] = None,
    context: Optional[Dict[str, Any]] = None
):
    """Run code review in background task."""
    
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        # Get review and repository
        review = db.query(CodeReview).filter(CodeReview.id == review_id).first()
        if not review:
            return
        
        repository = db.query(Repository).filter(Repository.id == review.repository_id).first()
        if not repository:
            return
        
        # Update status to running
        review.status = ReviewStatus.RUNNING
        db.commit()
        
        # Configure agents
        orchestra_config = {}
        if agents_config:
            for agent_name, config in agents_config.items():
                orchestra_config[agent_name] = AgentConfig(**config)
        
        # Initialize services
        github_service = GitHubService(repository.github_token)
        review_service = ReviewService(db)
        orchestra = AgentOrchestra(orchestra_config)
        
        try:
            # Get repository files
            repo_files = await github_service.get_repository_files(
                repository.full_name,
                branch=review.branch,
                files=files
            )
            
            # Convert to CodeFile objects
            code_files = [
                CodeFile(
                    path=file_data['path'],
                    content=file_data['content'],
                    language=file_data.get('language', 'unknown')
                )
                for file_data in repo_files
            ]
            
            # Run review
            result = await orchestra.conduct_review(code_files, context)
            
            # Save results
            await review_service.save_review_results(review_id, result)
            
            # Update review status
            review.status = ReviewStatus.COMPLETED
            review.summary = orchestra.get_review_summary(result)
            
        except Exception as e:
            print(f"Review failed: {e}")
            review.status = ReviewStatus.FAILED
            review.summary = {"error": str(e)}
        
        finally:
            review.completed_at = db.now()
            db.commit()
            orchestra.close()
    
    finally:
        db.close()
