"""
Base agent class for all code review agents.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

import openai
from anthropic import Anthropic

from app.core.config import settings, AGENT_CONFIGS, Severity, Confidence


@dataclass
class Finding:
    """Represents a single finding from an agent."""
    title: str
    description: str
    severity: Severity
    confidence: Confidence
    file_path: str
    line_number: Optional[int] = None
    line_end: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    category: Optional[str] = None
    rule_id: Optional[str] = None


@dataclass
class AgentResult:
    """Result from an agent analysis."""
    agent_type: str
    findings: List[Finding]
    summary: str
    confidence: Confidence
    severity: Severity
    execution_time_ms: int
    tokens_used: int
    cost_cents: int
    status: str = "completed"
    error_message: Optional[str] = None


@dataclass
class CodeFile:
    """Represents a code file to be analyzed."""
    path: str
    content: str
    language: str
    size: int
    hash: str


class BaseAgent(ABC):
    """Base class for all code review agents."""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.config = AGENT_CONFIGS.get(agent_type, {})
        
        # Initialize LLM clients
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.openai_api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        
        if settings.anthropic_api_key:
            self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
    
    async def analyze_code(self, files: List[CodeFile], context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """
        Analyze code files and return findings.
        
        Args:
            files: List of code files to analyze
            context: Additional context like PR info, repository info, etc.
            
        Returns:
            AgentResult with findings and metadata
        """
        start_time = time.time()
        
        try:
            # Pre-analysis filtering
            relevant_files = self._filter_relevant_files(files)
            
            if not relevant_files:
                return AgentResult(
                    agent_type=self.agent_type,
                    findings=[],
                    summary="No relevant files found for analysis.",
                    confidence=Confidence.HIGH,
                    severity=Severity.INFO,
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    tokens_used=0,
                    cost_cents=0
                )
            
            # Perform analysis
            findings, tokens_used = await self._perform_analysis(relevant_files, context)
            
            # Calculate metrics
            execution_time_ms = int((time.time() - start_time) * 1000)
            cost_cents = self._calculate_cost(tokens_used)
            overall_confidence, overall_severity = self._calculate_overall_metrics(findings)
            summary = self._generate_summary(findings)
            
            return AgentResult(
                agent_type=self.agent_type,
                findings=findings,
                summary=summary,
                confidence=overall_confidence,
                severity=overall_severity,
                execution_time_ms=execution_time_ms,
                tokens_used=tokens_used,
                cost_cents=cost_cents
            )
            
        except Exception as e:
            return AgentResult(
                agent_type=self.agent_type,
                findings=[],
                summary=f"Analysis failed: {str(e)}",
                confidence=Confidence.LOW,
                severity=Severity.INFO,
                execution_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=0,
                cost_cents=0,
                status="failed",
                error_message=str(e)
            )
    
    def _filter_relevant_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Filter files relevant to this agent's analysis."""
        # Default implementation - can be overridden by specific agents
        return [f for f in files if self._is_file_relevant(f)]
    
    def _is_file_relevant(self, file: CodeFile) -> bool:
        """Check if a file is relevant for this agent's analysis."""
        # Base implementation - analyze most code files
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php', '.rb'}
        return any(file.path.endswith(ext) for ext in code_extensions)
    
    @abstractmethod
    async def _perform_analysis(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """
        Perform the actual analysis. Must be implemented by subclasses.
        
        Returns:
            Tuple of (findings, tokens_used)
        """
        pass
    
    @abstractmethod
    def _create_prompt(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> str:
        """Create the prompt for LLM analysis."""
        pass
    
    def _calculate_cost(self, tokens_used: int) -> int:
        """Calculate cost in cents based on tokens used."""
        # GPT-4 pricing: ~$0.03 per 1K tokens (input) + $0.06 per 1K tokens (output)
        # Simplified calculation assuming 50/50 input/output
        cost_per_1k_tokens = 0.045  # Average of input/output costs
        return int((tokens_used / 1000) * cost_per_1k_tokens * 100)
    
    def _calculate_overall_metrics(self, findings: List[Finding]) -> Tuple[Confidence, Severity]:
        """Calculate overall confidence and severity from findings."""
        if not findings:
            return Confidence.HIGH, Severity.INFO
        
        # Calculate severity based on highest severity finding
        severity_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
        max_severity = Severity.INFO
        
        for finding in findings:
            for severity in severity_order:
                if finding.severity == severity:
                    max_severity = severity
                    break
            if max_severity != Severity.INFO:
                break
        
        # Calculate confidence based on average confidence
        confidence_scores = {
            Confidence.VERY_HIGH: 95,
            Confidence.HIGH: 80,
            Confidence.MEDIUM: 60,
            Confidence.LOW: 40,
            Confidence.VERY_LOW: 20
        }
        
        avg_confidence = sum(confidence_scores[f.confidence] for f in findings) / len(findings)
        
        if avg_confidence >= 90:
            overall_confidence = Confidence.VERY_HIGH
        elif avg_confidence >= 70:
            overall_confidence = Confidence.HIGH
        elif avg_confidence >= 50:
            overall_confidence = Confidence.MEDIUM
        elif avg_confidence >= 30:
            overall_confidence = Confidence.LOW
        else:
            overall_confidence = Confidence.VERY_LOW
        
        return overall_confidence, max_severity
    
    def _generate_summary(self, findings: List[Finding]) -> str:
        """Generate a summary of findings."""
        if not findings:
            return f"{self.agent_type.title()} analysis completed with no issues found."
        
        # Count by severity
        severity_counts = {}
        for finding in findings:
            severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1
        
        summary_parts = [f"Found {len(findings)} issue(s):"]
        for severity in [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                summary_parts.append(f"{count} {severity}")
        
        return " ".join(summary_parts)
    
    async def _call_llm(self, prompt: str, model: Optional[str] = None) -> Tuple[str, int]:
        """
        Call the configured LLM with the given prompt.
        
        Returns:
            Tuple of (response_text, tokens_used)
        """
        model = model or self.config.get("model", "gpt-4")
        temperature = self.config.get("temperature", 0.1)
        max_tokens = self.config.get("max_tokens", 2000)
        
        if model.startswith("gpt") and self.openai_client:
            response = await self.openai_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            tokens_used = response.usage.total_tokens if response.usage else 0
            return response.choices[0].message.content, tokens_used
        
        elif model.startswith("claude") and self.anthropic_client:
            # Note: Anthropic client might need different handling for async
            response = await asyncio.to_thread(
                self.anthropic_client.messages.create,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            tokens_used = response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
            return response.content[0].text, tokens_used
        
        else:
            raise ValueError(f"Unsupported model: {model} or missing API key")
    
    def _parse_llm_response(self, response: str) -> List[Finding]:
        """
        Parse LLM response into Finding objects.
        This is a base implementation that should be overridden by specific agents.
        """
        # Simple parsing - look for structured responses
        findings = []
        
        # This is a placeholder implementation
        # Real agents should implement sophisticated parsing based on their prompt format
        
        return findings
