"""
Review service for managing code review operations.
"""

from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.code_review import CodeReview
from app.models.agent_response import AgentResponse
from app.agents.orchestra import ReviewResult
from app.agents.base import Finding


class ReviewService:
    """Service for code review operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def save_review_results(self, review_id: int, result: ReviewResult) -> None:
        """Save review results to database."""
        
        # Save individual findings as agent responses
        for finding in result.findings:
            agent_response = AgentResponse(
                review_id=review_id,
                agent_name=finding.metadata.get('source_agent', 'unknown') if finding.metadata else 'unknown',
                title=finding.title,
                description=finding.description,
                severity=finding.severity,
                confidence=finding.confidence.value,
                file_path=finding.file_path,
                line_number=finding.line_number,
                code_snippet=finding.code_snippet,
                suggestion=finding.suggestion,
                category=finding.category,
                rule_id=finding.rule_id,
                metadata=finding.metadata or {}
            )
            self.db.add(agent_response)
        
        self.db.commit()
    
    def get_review_statistics(self, review_id: int) -> Dict[str, Any]:
        """Get statistics for a specific review."""
        
        findings = self.db.query(AgentResponse).filter(
            AgentResponse.review_id == review_id
        ).all()
        
        if not findings:
            return {
                'total_findings': 0,
                'by_severity': {},
                'by_category': {},
                'by_agent': {}
            }
        
        # Count by severity
        severity_counts = {}
        for finding in findings:
            severity = finding.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by category
        category_counts = {}
        for finding in findings:
            category = finding.category
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Count by agent
        agent_counts = {}
        for finding in findings:
            agent = finding.agent_name
            agent_counts[agent] = agent_counts.get(agent, 0) + 1
        
        return {
            'total_findings': len(findings),
            'by_severity': severity_counts,
            'by_category': category_counts,
            'by_agent': agent_counts
        }
    
    def get_findings_by_file(self, review_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get findings grouped by file."""
        
        findings = self.db.query(AgentResponse).filter(
            AgentResponse.review_id == review_id
        ).order_by(AgentResponse.file_path, AgentResponse.line_number).all()
        
        findings_by_file = {}
        
        for finding in findings:
            file_path = finding.file_path
            if file_path not in findings_by_file:
                findings_by_file[file_path] = []
            
            findings_by_file[file_path].append({
                'id': finding.id,
                'title': finding.title,
                'description': finding.description,
                'severity': finding.severity.value,
                'confidence': finding.confidence,
                'line_number': finding.line_number,
                'code_snippet': finding.code_snippet,
                'suggestion': finding.suggestion,
                'category': finding.category,
                'rule_id': finding.rule_id,
                'agent_name': finding.agent_name
            })
        
        return findings_by_file
    
    def get_top_issues(self, review_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top issues from a review ordered by severity and confidence."""
        
        findings = self.db.query(AgentResponse).filter(
            AgentResponse.review_id == review_id
        ).order_by(
            AgentResponse.severity.desc(),
            AgentResponse.confidence.desc()
        ).limit(limit).all()
        
        return [
            {
                'id': finding.id,
                'title': finding.title,
                'description': finding.description,
                'severity': finding.severity.value,
                'confidence': finding.confidence,
                'file_path': finding.file_path,
                'line_number': finding.line_number,
                'category': finding.category,
                'agent_name': finding.agent_name
            }
            for finding in findings
        ]
