"""
Agent Orchestra - Coordinates multiple agents for comprehensive code review.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from app.agents.base import BaseAgent, Finding, CodeFile
from app.agents.security_agent import SecurityAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.style_agent import StyleAgent
from app.agents.logic_agent import LogicAgent
from app.agents.architecture_agent import ArchitectureAgent
from app.core.config import Severity


@dataclass
class ReviewResult:
    """Result of a comprehensive code review."""
    findings: List[Finding] = field(default_factory=list)
    agent_results: Dict[str, List[Finding]] = field(default_factory=dict)
    execution_stats: Dict[str, Any] = field(default_factory=dict)
    total_tokens_used: int = 0
    review_duration: float = 0.0
    files_analyzed: int = 0


@dataclass
class AgentConfig:
    """Configuration for individual agents."""
    enabled: bool = True
    priority: int = 1  # 1 = highest priority
    timeout_seconds: int = 300  # 5 minutes
    max_files_per_agent: int = 50


class AgentOrchestra:
    """Orchestrates multiple agents for comprehensive code review."""
    
    def __init__(self, config: Optional[Dict[str, AgentConfig]] = None):
        """Initialize agent orchestra with optional configuration."""
        self.agents = {
            'security': SecurityAgent(),
            'performance': PerformanceAgent(),
            'style': StyleAgent(),
            'logic': LogicAgent(),
            'architecture': ArchitectureAgent()
        }
        
        # Default configuration
        default_config = {
            agent_name: AgentConfig() for agent_name in self.agents.keys()
        }
        
        self.config = config or default_config
        
        # Filter enabled agents
        self.enabled_agents = {
            name: agent for name, agent in self.agents.items()
            if self.config.get(name, AgentConfig()).enabled
        }
        
        self.executor = ThreadPoolExecutor(max_workers=len(self.enabled_agents))
    
    async def conduct_review(
        self,
        files: List[CodeFile],
        context: Optional[Dict[str, Any]] = None
    ) -> ReviewResult:
        """Conduct comprehensive code review using all enabled agents."""
        start_time = time.time()
        
        # Initialize result
        result = ReviewResult(
            files_analyzed=len(files),
            execution_stats={}
        )
        
        # Filter files by relevance and size
        filtered_files = self._filter_files(files)
        
        # Run agents in parallel with different strategies
        agent_tasks = []
        
        for agent_name, agent in self.enabled_agents.items():
            agent_config = self.config.get(agent_name, AgentConfig())
            
            # Limit files per agent if configured
            agent_files = filtered_files[:agent_config.max_files_per_agent]
            
            # Create async task for each agent
            task = asyncio.create_task(
                self._run_agent_with_timeout(
                    agent,
                    agent_name,
                    agent_files,
                    context,
                    agent_config.timeout_seconds
                )
            )
            agent_tasks.append((agent_name, task))
        
        # Wait for all agents to complete
        agent_results = {}
        total_tokens = 0
        
        for agent_name, task in agent_tasks:
            try:
                findings, tokens, execution_time = await task
                agent_results[agent_name] = findings
                total_tokens += tokens
                
                # Store execution stats
                result.execution_stats[agent_name] = {
                    'findings_count': len(findings),
                    'tokens_used': tokens,
                    'execution_time': execution_time,
                    'files_processed': len(filtered_files)
                }
                
            except asyncio.TimeoutError:
                print(f"Agent {agent_name} timed out")
                agent_results[agent_name] = []
                result.execution_stats[agent_name] = {
                    'error': 'timeout',
                    'findings_count': 0,
                    'tokens_used': 0,
                    'execution_time': self.config.get(agent_name, AgentConfig()).timeout_seconds
                }
            except Exception as e:
                print(f"Agent {agent_name} failed: {e}")
                agent_results[agent_name] = []
                result.execution_stats[agent_name] = {
                    'error': str(e),
                    'findings_count': 0,
                    'tokens_used': 0,
                    'execution_time': 0
                }
        
        # Aggregate and prioritize findings
        all_findings = self._aggregate_findings(agent_results)
        deduplicated_findings = self._deduplicate_findings(all_findings)
        prioritized_findings = self._prioritize_findings(deduplicated_findings)
        
        # Update result
        result.findings = prioritized_findings
        result.agent_results = agent_results
        result.total_tokens_used = total_tokens
        result.review_duration = time.time() - start_time
        
        return result
    
    async def _run_agent_with_timeout(
        self,
        agent: BaseAgent,
        agent_name: str,
        files: List[CodeFile],
        context: Optional[Dict[str, Any]],
        timeout_seconds: int
    ) -> Tuple[List[Finding], int, float]:
        """Run a single agent with timeout protection."""
        start_time = time.time()
        
        try:
            findings, tokens = await asyncio.wait_for(
                agent.analyze(files, context),
                timeout=timeout_seconds
            )
            execution_time = time.time() - start_time
            
            print(f"Agent {agent_name} completed: {len(findings)} findings, {tokens} tokens, {execution_time:.2f}s")
            return findings, tokens, execution_time
            
        except asyncio.TimeoutError:
            execution_time = timeout_seconds
            print(f"Agent {agent_name} timed out after {timeout_seconds}s")
            raise
        except Exception as e:
            execution_time = time.time() - start_time
            print(f"Agent {agent_name} failed after {execution_time:.2f}s: {e}")
            raise
    
    def _filter_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Filter and prioritize files for analysis."""
        # Remove very large files that might cause issues
        max_file_size = 100_000  # 100KB
        filtered = [f for f in files if len(f.content) < max_file_size]
        
        # Prioritize by file type and importance
        priority_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs']
        
        prioritized = []
        
        # Add high-priority files first
        for ext in priority_extensions:
            ext_files = [f for f in filtered if f.path.endswith(ext)]
            prioritized.extend(ext_files)
        
        # Add remaining files
        remaining = [f for f in filtered if f not in prioritized]
        prioritized.extend(remaining)
        
        # Limit total files to prevent overwhelming
        max_total_files = 200
        return prioritized[:max_total_files]
    
    def _aggregate_findings(self, agent_results: Dict[str, List[Finding]]) -> List[Finding]:
        """Aggregate findings from all agents."""
        all_findings = []
        
        for agent_name, findings in agent_results.items():
            for finding in findings:
                # Tag finding with source agent
                finding.metadata = finding.metadata or {}
                finding.metadata['source_agent'] = agent_name
                all_findings.append(finding)
        
        return all_findings
    
    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on file, line, and rule."""
        seen = set()
        deduplicated = []
        
        for finding in findings:
            # Create signature for deduplication
            signature = (
                finding.file_path,
                finding.line_number,
                finding.rule_id,
                finding.title
            )
            
            if signature not in seen:
                seen.add(signature)
                deduplicated.append(finding)
            else:
                # If duplicate, merge metadata if useful
                for existing in deduplicated:
                    if (existing.file_path == finding.file_path and
                        existing.line_number == finding.line_number and
                        existing.rule_id == finding.rule_id):
                        
                        # Add source agent to existing finding
                        if finding.metadata and 'source_agent' in finding.metadata:
                            existing.metadata = existing.metadata or {}
                            source_agents = existing.metadata.get('source_agents', [])
                            if existing.metadata.get('source_agent'):
                                source_agents.append(existing.metadata['source_agent'])
                            source_agents.append(finding.metadata['source_agent'])
                            existing.metadata['source_agents'] = list(set(source_agents))
                            
                            # Increase confidence if multiple agents agree
                            if len(source_agents) > 1:
                                existing.confidence = min(100, existing.confidence.value + 10)
                        break
        
        return deduplicated
    
    def _prioritize_findings(self, findings: List[Finding]) -> List[Finding]:
        """Prioritize findings based on severity, confidence, and other factors."""
        
        def priority_score(finding: Finding) -> int:
            """Calculate priority score for sorting."""
            score = 0
            
            # Severity weight (higher is more important)
            severity_weights = {
                Severity.CRITICAL: 1000,
                Severity.HIGH: 800,
                Severity.MEDIUM: 600,
                Severity.LOW: 400,
                Severity.INFO: 200
            }
            score += severity_weights.get(finding.severity, 200)
            
            # Confidence weight
            score += finding.confidence.value * 2
            
            # Category priority (security issues are highest)
            category_weights = {
                'security': 200,
                'logic': 150,
                'performance': 100,
                'architecture': 80,
                'style': 50
            }
            score += category_weights.get(finding.category, 50)
            
            # Multiple agent agreement bonus
            if finding.metadata and 'source_agents' in finding.metadata:
                agent_count = len(finding.metadata['source_agents'])
                score += agent_count * 50
            
            # File type priority (main source files over tests)
            if 'test' not in finding.file_path.lower():
                score += 100
            
            return score
        
        # Sort by priority score (descending)
        return sorted(findings, key=priority_score, reverse=True)
    
    def get_review_summary(self, result: ReviewResult) -> Dict[str, Any]:
        """Generate summary statistics for the review."""
        findings_by_severity = {}
        findings_by_category = {}
        findings_by_agent = {}
        
        for finding in result.findings:
            # By severity
            severity = finding.severity.name
            findings_by_severity[severity] = findings_by_severity.get(severity, 0) + 1
            
            # By category
            category = finding.category
            findings_by_category[category] = findings_by_category.get(category, 0) + 1
            
            # By agent
            source_agent = finding.metadata.get('source_agent', 'unknown') if finding.metadata else 'unknown'
            findings_by_agent[source_agent] = findings_by_agent.get(source_agent, 0) + 1
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(result.findings)
        
        return {
            'total_findings': len(result.findings),
            'files_analyzed': result.files_analyzed,
            'review_duration': result.review_duration,
            'tokens_used': result.total_tokens_used,
            'findings_by_severity': findings_by_severity,
            'findings_by_category': findings_by_category,
            'findings_by_agent': findings_by_agent,
            'agent_stats': result.execution_stats,
            'risk_score': risk_score,
            'top_issues': [
                {
                    'title': f.title,
                    'file': f.file_path,
                    'line': f.line_number,
                    'severity': f.severity.name,
                    'category': f.category
                }
                for f in result.findings[:10]  # Top 10 issues
            ]
        }
    
    def _calculate_risk_score(self, findings: List[Finding]) -> int:
        """Calculate overall risk score (0-100) based on findings."""
        if not findings:
            return 0
        
        severity_weights = {
            Severity.CRITICAL: 25,
            Severity.HIGH: 15,
            Severity.MEDIUM: 8,
            Severity.LOW: 3,
            Severity.INFO: 1
        }
        
        total_weight = sum(
            severity_weights.get(finding.severity, 1) for finding in findings
        )
        
        # Normalize to 0-100 scale
        max_possible = len(findings) * 25  # If all were critical
        risk_score = min(100, (total_weight / max_possible) * 100) if max_possible > 0 else 0
        
        return int(risk_score)
    
    def close(self):
        """Clean up resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
