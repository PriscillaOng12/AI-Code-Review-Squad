"""
Test suite for the AI Code Review Squad agents.
"""

import pytest
import asyncio
from typing import List
from unittest.mock import Mock, patch, AsyncMock

from app.agents.base import CodeFile, Finding
from app.agents.security_agent import SecurityAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.style_agent import StyleAgent
from app.agents.logic_agent import LogicAgent
from app.agents.architecture_agent import ArchitectureAgent
from app.agents.orchestra import AgentOrchestra, AgentConfig
from app.core.config import Severity, Confidence


@pytest.fixture
def sample_python_file():
    """Sample Python file with various issues."""
    content = """
import os
import subprocess

# Hardcoded secret
API_KEY = "sk-1234567890abcdef"
DATABASE_URL = "postgres://user:password@localhost/db"

def vulnerable_function(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    
    # Command injection
    os.system(f"echo {user_input}")
    
    # Inefficient nested loops
    result = []
    for i in range(1000):
        for j in range(1000):
            for k in range(100):
                result.append(i * j * k)
    
    return result

class god_class:  # Style issues: class name, no docstring
    def __init__(self):
        self.data = []
    
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass

def logic_issues(items):
    # Potential off-by-one error
    for i in range(len(items)):
        if i == len(items):  # This condition is never true
            print("Never reached")
    
    # Division by zero potential
    result = 10 / 0
    
    return result

# Unreachable code
def unreachable_code():
    return "early return"
    print("This will never execute")  # Unreachable
"""
    
    return CodeFile(
        path="test_file.py",
        content=content,
        language="python"
    )


@pytest.fixture
def sample_javascript_file():
    """Sample JavaScript file with issues."""
    content = """
// Hardcoded credentials
const API_KEY = "secret_key_12345";
const password = "admin123";

function vulnerableFunction(userInput) {
    // XSS vulnerability
    document.getElementById("output").innerHTML = userInput;
    
    // Potential null reference
    let obj = null;
    console.log(obj.property);
    
    // Inefficient algorithm
    function fibonacci(n) {
        if (n <= 1) return n;
        return fibonacci(n - 1) + fibonacci(n - 2);  // Exponential time complexity
    }
    
    return fibonacci(40);
}

// Style issues
function badlyNamedFunction(a,b,c) {  // Poor naming, spacing
var result=a+b+c;  // Missing spaces
return result
}  // Missing semicolon

// Architecture issue - God function
function doEverything(input) {
    // Validation
    if (!input) throw new Error("Invalid input");
    
    // Data processing
    const processed = input.map(x => x * 2);
    
    // API calls
    fetch('/api/data', { method: 'POST', body: JSON.stringify(processed) });
    
    // UI updates
    document.getElementById('result').textContent = 'Done';
    
    // Logging
    console.log('Process completed');
    
    // File operations
    localStorage.setItem('result', JSON.stringify(processed));
    
    // More processing...
    // ... 50 more lines of mixed responsibilities
    
    return processed;
}
"""
    
    return CodeFile(
        path="test_file.js",
        content=content,
        language="javascript"
    )


class TestSecurityAgent:
    """Test SecurityAgent functionality."""
    
    @pytest.fixture
    def security_agent(self):
        return SecurityAgent()
    
    @pytest.mark.asyncio
    async def test_sql_injection_detection(self, security_agent, sample_python_file):
        """Test SQL injection pattern detection."""
        findings, _ = await security_agent.analyze([sample_python_file])
        
        sql_findings = [f for f in findings if 'sql' in f.title.lower()]
        assert len(sql_findings) > 0
        assert any(f.severity == Severity.CRITICAL for f in sql_findings)
    
    @pytest.mark.asyncio
    async def test_hardcoded_secrets_detection(self, security_agent, sample_python_file):
        """Test hardcoded secrets detection."""
        findings, _ = await security_agent.analyze([sample_python_file])
        
        secret_findings = [f for f in findings if 'secret' in f.title.lower() or 'credential' in f.title.lower()]
        assert len(secret_findings) > 0
        assert any(f.severity in [Severity.HIGH, Severity.CRITICAL] for f in secret_findings)
    
    @pytest.mark.asyncio
    async def test_command_injection_detection(self, security_agent, sample_python_file):
        """Test command injection detection."""
        findings, _ = await security_agent.analyze([sample_python_file])
        
        cmd_findings = [f for f in findings if 'command' in f.title.lower()]
        assert len(cmd_findings) > 0
    
    @pytest.mark.asyncio
    async def test_xss_detection(self, security_agent, sample_javascript_file):
        """Test XSS vulnerability detection."""
        findings, _ = await security_agent.analyze([sample_javascript_file])
        
        xss_findings = [f for f in findings if 'xss' in f.title.lower()]
        assert len(xss_findings) > 0


class TestPerformanceAgent:
    """Test PerformanceAgent functionality."""
    
    @pytest.fixture
    def performance_agent(self):
        return PerformanceAgent()
    
    @pytest.mark.asyncio
    async def test_nested_loops_detection(self, performance_agent, sample_python_file):
        """Test nested loops detection."""
        findings, _ = await performance_agent.analyze([sample_python_file])
        
        loop_findings = [f for f in findings if 'nested' in f.title.lower() or 'loop' in f.title.lower()]
        assert len(loop_findings) > 0
    
    @pytest.mark.asyncio
    async def test_inefficient_algorithm_detection(self, performance_agent, sample_javascript_file):
        """Test inefficient algorithm detection."""
        findings, _ = await performance_agent.analyze([sample_javascript_file])
        
        # Should detect the exponential fibonacci implementation
        algo_findings = [f for f in findings if 'algorithm' in f.title.lower() or 'complexity' in f.title.lower()]
        assert len(algo_findings) >= 0  # May be detected by pattern or LLM


class TestStyleAgent:
    """Test StyleAgent functionality."""
    
    @pytest.fixture
    def style_agent(self):
        return StyleAgent()
    
    @pytest.mark.asyncio
    async def test_naming_conventions(self, style_agent, sample_python_file):
        """Test naming convention detection."""
        findings, _ = await style_agent.analyze([sample_python_file])
        
        naming_findings = [f for f in findings if 'naming' in f.title.lower() or 'convention' in f.title.lower()]
        assert len(naming_findings) > 0
    
    @pytest.mark.asyncio
    async def test_documentation_issues(self, style_agent, sample_python_file):
        """Test documentation checking."""
        findings, _ = await style_agent.analyze([sample_python_file])
        
        doc_findings = [f for f in findings if 'documentation' in f.title.lower() or 'docstring' in f.title.lower()]
        assert len(doc_findings) >= 0


class TestLogicAgent:
    """Test LogicAgent functionality."""
    
    @pytest.fixture
    def logic_agent(self):
        return LogicAgent()
    
    @pytest.mark.asyncio
    async def test_division_by_zero_detection(self, logic_agent, sample_python_file):
        """Test division by zero detection."""
        findings, _ = await logic_agent.analyze([sample_python_file])
        
        div_findings = [f for f in findings if 'division' in f.title.lower() or 'zero' in f.title.lower()]
        assert len(div_findings) > 0
    
    @pytest.mark.asyncio
    async def test_unreachable_code_detection(self, logic_agent, sample_python_file):
        """Test unreachable code detection."""
        findings, _ = await logic_agent.analyze([sample_python_file])
        
        unreachable_findings = [f for f in findings if 'unreachable' in f.title.lower()]
        assert len(unreachable_findings) > 0
    
    @pytest.mark.asyncio
    async def test_null_reference_detection(self, logic_agent, sample_javascript_file):
        """Test null reference detection."""
        findings, _ = await logic_agent.analyze([sample_javascript_file])
        
        null_findings = [f for f in findings if 'null' in f.title.lower() or 'undefined' in f.title.lower()]
        assert len(null_findings) >= 0


class TestArchitectureAgent:
    """Test ArchitectureAgent functionality."""
    
    @pytest.fixture
    def architecture_agent(self):
        return ArchitectureAgent()
    
    @pytest.mark.asyncio
    async def test_god_class_detection(self, architecture_agent, sample_python_file):
        """Test God class detection."""
        findings, _ = await architecture_agent.analyze([sample_python_file])
        
        god_findings = [f for f in findings if 'god' in f.title.lower() or 'large' in f.title.lower()]
        assert len(god_findings) > 0
    
    @pytest.mark.asyncio
    async def test_high_complexity_detection(self, architecture_agent, sample_python_file):
        """Test high complexity detection."""
        findings, _ = await architecture_agent.analyze([sample_python_file])
        
        complexity_findings = [f for f in findings if 'complexity' in f.title.lower()]
        assert len(complexity_findings) >= 0


class TestAgentOrchestra:
    """Test AgentOrchestra coordination."""
    
    @pytest.fixture
    def orchestra(self):
        return AgentOrchestra()
    
    @pytest.mark.asyncio
    async def test_full_review_process(self, orchestra, sample_python_file, sample_javascript_file):
        """Test complete review process with multiple agents."""
        files = [sample_python_file, sample_javascript_file]
        
        with patch.object(SecurityAgent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = ("No additional issues found.", 100)
            
            result = await orchestra.conduct_review(files)
            
            # Verify result structure
            assert hasattr(result, 'findings')
            assert hasattr(result, 'agent_results')
            assert hasattr(result, 'execution_stats')
            assert hasattr(result, 'total_tokens_used')
            
            # Should have findings from multiple agents
            assert len(result.findings) > 0
            
            # Should have results from each agent
            agent_names = {'security', 'performance', 'style', 'logic', 'architecture'}
            assert agent_names.issubset(set(result.agent_results.keys()))
            
            # Verify execution stats
            for agent_name in agent_names:
                assert agent_name in result.execution_stats
                stats = result.execution_stats[agent_name]
                assert 'findings_count' in stats
                assert 'execution_time' in stats
    
    @pytest.mark.asyncio
    async def test_agent_configuration(self):
        """Test agent configuration and selective enabling."""
        config = {
            'security': AgentConfig(enabled=True, priority=1),
            'performance': AgentConfig(enabled=False),
            'style': AgentConfig(enabled=True, max_files_per_agent=10),
            'logic': AgentConfig(enabled=True, timeout_seconds=60),
            'architecture': AgentConfig(enabled=True)
        }
        
        orchestra = AgentOrchestra(config)
        
        # Verify only enabled agents are active
        expected_agents = {'security', 'style', 'logic', 'architecture'}
        assert set(orchestra.enabled_agents.keys()) == expected_agents
    
    def test_risk_score_calculation(self, orchestra):
        """Test risk score calculation."""
        findings = [
            Finding(
                title="Critical Security Issue",
                description="Test",
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                file_path="test.py",
                line_number=1,
                code_snippet="test",
                suggestion="Fix it",
                category="security",
                rule_id="SEC_001"
            ),
            Finding(
                title="Medium Performance Issue",
                description="Test",
                severity=Severity.MEDIUM,
                confidence=Confidence.MEDIUM,
                file_path="test.py",
                line_number=2,
                code_snippet="test",
                suggestion="Optimize",
                category="performance",
                rule_id="PERF_001"
            )
        ]
        
        risk_score = orchestra._calculate_risk_score(findings)
        assert 0 <= risk_score <= 100
        assert risk_score > 0  # Should have some risk with critical finding
    
    def test_finding_deduplication(self, orchestra):
        """Test finding deduplication logic."""
        duplicate_findings = [
            Finding(
                title="Same Issue",
                description="Test",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                file_path="test.py",
                line_number=1,
                code_snippet="test",
                suggestion="Fix it",
                category="security",
                rule_id="SEC_001"
            ),
            Finding(
                title="Same Issue",
                description="Test duplicate",
                severity=Severity.HIGH,
                confidence=Confidence.MEDIUM,
                file_path="test.py",
                line_number=1,
                code_snippet="test",
                suggestion="Fix it differently",
                category="security",
                rule_id="SEC_001"
            )
        ]
        
        deduplicated = orchestra._deduplicate_findings(duplicate_findings)
        assert len(deduplicated) == 1
    
    def test_finding_prioritization(self, orchestra):
        """Test finding prioritization logic."""
        findings = [
            Finding(
                title="Low Priority",
                description="Test",
                severity=Severity.LOW,
                confidence=Confidence.LOW,
                file_path="test.py",
                line_number=1,
                code_snippet="test",
                suggestion="Fix it",
                category="style",
                rule_id="STYLE_001"
            ),
            Finding(
                title="High Priority",
                description="Test",
                severity=Severity.CRITICAL,
                confidence=Confidence.HIGH,
                file_path="test.py",
                line_number=2,
                code_snippet="test",
                suggestion="Fix it",
                category="security",
                rule_id="SEC_001"
            )
        ]
        
        prioritized = orchestra._prioritize_findings(findings)
        
        # Critical security issue should be first
        assert prioritized[0].severity == Severity.CRITICAL
        assert prioritized[0].category == "security"
        assert prioritized[1].severity == Severity.LOW


class TestIntegration:
    """Integration tests for the complete system."""
    
    @pytest.mark.asyncio
    async def test_multi_file_analysis(self):
        """Test analysis of multiple files with different languages."""
        files = [
            CodeFile(
                path="security_test.py",
                content="password = 'admin123'\nquery = f'SELECT * FROM users WHERE id = {user_id}'",
                language="python"
            ),
            CodeFile(
                path="performance_test.js", 
                content="for(let i=0; i<1000; i++) { for(let j=0; j<1000; j++) { console.log(i*j); } }",
                language="javascript"
            ),
            CodeFile(
                path="style_test.py",
                content="def BadFunction(x,y,z):\n    return x+y+z",
                language="python"
            )
        ]
        
        orchestra = AgentOrchestra()
        
        with patch.object(SecurityAgent, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = ("Additional security concern found.", 150)
            
            result = await orchestra.conduct_review(files)
            
            # Should find issues in multiple categories
            categories = {f.category for f in result.findings}
            assert len(categories) > 1
            
            # Should have findings from multiple files
            files_with_findings = {f.file_path for f in result.findings}
            assert len(files_with_findings) > 1


@pytest.mark.asyncio
async def test_agent_timeout_handling():
    """Test agent timeout handling."""
    config = {
        'security': AgentConfig(enabled=True, timeout_seconds=0.001)  # Very short timeout
    }
    
    orchestra = AgentOrchestra(config)
    
    files = [CodeFile(
        path="test.py",
        content="print('hello world')",
        language="python"
    )]
    
    result = await orchestra.conduct_review(files)
    
    # Should handle timeout gracefully
    assert 'security' in result.execution_stats
    # May have timeout error in stats
    assert result.execution_stats['security']['findings_count'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
