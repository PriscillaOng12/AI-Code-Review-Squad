"""
PerformanceAgent - Detects performance bottlenecks and optimization opportunities.
"""

import re
import ast
from typing import List, Tuple, Dict, Any, Optional
from app.agents.base import BaseAgent, Finding, CodeFile
from app.core.config import Severity, Confidence


class PerformanceAgent(BaseAgent):
    """Agent specialized in performance analysis and optimization."""
    
    def __init__(self):
        super().__init__("performance")
        
        # Performance anti-patterns
        self.performance_patterns = {
            "nested_loops": [
                r"for\s+.*:\s*\n\s*for\s+.*:",
                r"while\s+.*:\s*\n\s*for\s+.*:",
                r"for\s+.*:\s*\n\s*while\s+.*:",
            ],
            "inefficient_string_concat": [
                r"\w+\s*\+=\s*['\"].*['\"]",
                r"\w+\s*=\s*\w+\s*\+\s*['\"].*['\"]",
            ],
            "memory_leaks": [
                r"(?i)setinterval\s*\(",
                r"(?i)settimeout\s*\(",
                r"addEventListener\s*\(\s*['\"].*['\"],.*\)",
            ],
            "inefficient_database": [
                r"(?i)select\s+\*\s+from",
                r"(?i)\.objects\.all\(\)",
                r"(?i)\.filter\(.*\)\.filter\(",
            ],
            "synchronous_operations": [
                r"(?i)requests\.get\(",
                r"(?i)requests\.post\(",
                r"(?i)urllib\.urlopen\(",
            ],
        }
        
        # Big O complexity patterns
        self.complexity_patterns = {
            "O(n²)": ["nested_loops"],
            "O(n³)": ["triple_nested_loops"],
            "O(2^n)": ["recursive_fibonacci"],
        }
    
    def _filter_relevant_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Filter files relevant for performance analysis."""
        relevant_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs',
            '.php', '.rb', '.swift', '.kt', '.scala', '.sql'
        }
        
        return [
            f for f in files 
            if any(f.path.endswith(ext) for ext in relevant_extensions)
            and not any(skip in f.path.lower() for skip in ['test', 'spec', 'mock'])
        ]
    
    async def _perform_analysis(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """Perform performance analysis on code files."""
        findings = []
        total_tokens = 0
        
        for file in files:
            # Pattern-based analysis
            pattern_findings = self._detect_performance_patterns(file)
            findings.extend(pattern_findings)
            
            # AST-based analysis for Python files
            if file.path.endswith('.py'):
                ast_findings = self._analyze_python_ast(file)
                findings.extend(ast_findings)
            
            # LLM-based analysis for complex patterns
            if len(file.content) < 5000:  # Reasonable size for LLM
                prompt = self._create_prompt([file], context)
                try:
                    response, tokens = await self._call_llm(prompt)
                    total_tokens += tokens
                    
                    llm_findings = self._parse_llm_response(response, file)
                    findings.extend(llm_findings)
                except Exception as e:
                    print(f"LLM analysis failed for {file.path}: {e}")
        
        return findings, total_tokens
    
    def _detect_performance_patterns(self, file: CodeFile) -> List[Finding]:
        """Detect performance issues using regex patterns."""
        findings = []
        lines = file.content.split('\n')
        
        for issue_type, patterns in self.performance_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, file.content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    line_num = file.content[:match.start()].count('\n') + 1
                    
                    findings.append(Finding(
                        title=f"Performance Issue: {issue_type.replace('_', ' ').title()}",
                        description=self._get_performance_description(issue_type),
                        severity=self._get_performance_severity(issue_type),
                        confidence=Confidence.HIGH,
                        file_path=file.path,
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(file.content, line_num),
                        suggestion=self._get_performance_suggestion(issue_type),
                        category="performance",
                        rule_id=f"PERF_{issue_type.upper()}"
                    ))
        
        return findings
    
    def _analyze_python_ast(self, file: CodeFile) -> List[Finding]:
        """Analyze Python code using AST for deeper insights."""
        findings = []
        
        try:
            tree = ast.parse(file.content)
            analyzer = PythonPerformanceAnalyzer(file)
            analyzer.visit(tree)
            findings.extend(analyzer.findings)
        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception as e:
            print(f"AST analysis failed for {file.path}: {e}")
        
        return findings
    
    def _create_prompt(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> str:
        """Create performance analysis prompt for LLM."""
        file_content = files[0].content if files else ""
        file_path = files[0].path if files else "unknown"
        language = files[0].language if files else "unknown"
        
        prompt = f"""
You are a senior performance engineer conducting a thorough performance review of code.
Analyze the following {language} code for performance bottlenecks and optimization opportunities.

File: {file_path}
Language: {language}

Focus on identifying:
1. Algorithm complexity issues (Big O analysis)
2. Memory usage problems and potential leaks
3. Inefficient data structures usage
4. Database query optimization opportunities
5. Caching opportunities
6. Synchronous operations that could be asynchronous
7. Resource-intensive operations
8. Inefficient loops and iterations
9. String concatenation issues
10. Unnecessary computations

For each issue found, provide:
- Performance issue type
- Severity level (CRITICAL, HIGH, MEDIUM, LOW)
- Line number where issue occurs
- Impact on performance
- Recommended optimization

Code to analyze:
```{language}
{file_content}
```

Format your response as:
FINDING: [Performance Issue Type]
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
LINE: [Line Number]
IMPACT: [Performance impact explanation]
OPTIMIZATION: [How to optimize]
---
"""
        return prompt
    
    def _parse_llm_response(self, response: str, file: CodeFile) -> List[Finding]:
        """Parse LLM response into Finding objects."""
        findings = []
        finding_blocks = response.split('---')
        
        for block in finding_blocks:
            if not block.strip():
                continue
            
            finding_data = {}
            lines = block.strip().split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().upper()
                    value = value.strip()
                    
                    if key == 'FINDING':
                        finding_data['title'] = value
                    elif key == 'SEVERITY':
                        finding_data['severity'] = value.upper()
                    elif key == 'LINE':
                        try:
                            finding_data['line_number'] = int(value)
                        except ValueError:
                            finding_data['line_number'] = 1
                    elif key == 'IMPACT':
                        finding_data['description'] = value
                    elif key == 'OPTIMIZATION':
                        finding_data['suggestion'] = value
            
            if 'title' in finding_data and 'description' in finding_data:
                findings.append(Finding(
                    title=f"Performance: {finding_data.get('title', 'Performance Issue')}",
                    description=finding_data.get('description', 'Performance issue detected'),
                    severity=getattr(Severity, finding_data.get('severity', 'MEDIUM'), Severity.MEDIUM),
                    confidence=Confidence.HIGH,
                    file_path=file.path,
                    line_number=finding_data.get('line_number', 1),
                    code_snippet=self._get_code_snippet(file.content, finding_data.get('line_number', 1)),
                    suggestion=finding_data.get('suggestion', 'Optimize for better performance'),
                    category="performance",
                    rule_id="PERF_LLM_DETECTED"
                ))
        
        return findings
    
    def _get_code_snippet(self, content: str, line_number: int) -> str:
        """Extract code snippet around the specified line."""
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""
    
    def _get_performance_description(self, issue_type: str) -> str:
        """Get description for performance issue type."""
        descriptions = {
            "nested_loops": "Nested loops detected, which may result in O(n²) or higher time complexity.",
            "inefficient_string_concat": "Inefficient string concatenation that creates multiple temporary objects.",
            "memory_leaks": "Potential memory leak from event listeners or timers not being cleaned up.",
            "inefficient_database": "Inefficient database query that may cause performance issues.",
            "synchronous_operations": "Synchronous network operation that blocks execution thread."
        }
        return descriptions.get(issue_type, "Performance issue detected")
    
    def _get_performance_severity(self, issue_type: str) -> Severity:
        """Get severity level for performance issue type."""
        severity_map = {
            "nested_loops": Severity.HIGH,
            "inefficient_string_concat": Severity.MEDIUM,
            "memory_leaks": Severity.HIGH,
            "inefficient_database": Severity.HIGH,
            "synchronous_operations": Severity.MEDIUM
        }
        return severity_map.get(issue_type, Severity.MEDIUM)
    
    def _get_performance_suggestion(self, issue_type: str) -> str:
        """Get optimization suggestion for performance issue type."""
        suggestions = {
            "nested_loops": "Consider using more efficient algorithms, data structures, or caching to reduce complexity.",
            "inefficient_string_concat": "Use list comprehension with join() or f-strings for better performance.",
            "memory_leaks": "Ensure event listeners are removed and timers are cleared properly.",
            "inefficient_database": "Use specific field selection, indexing, and query optimization techniques.",
            "synchronous_operations": "Use async/await or threading for non-blocking operations."
        }
        return suggestions.get(issue_type, "Optimize for better performance")


class PythonPerformanceAnalyzer(ast.NodeVisitor):
    """AST visitor for Python-specific performance analysis."""
    
    def __init__(self, file: CodeFile):
        self.file = file
        self.findings = []
        self.loop_depth = 0
        self.function_complexity = {}
    
    def visit_For(self, node):
        """Visit for loops to detect nesting."""
        self.loop_depth += 1
        
        if self.loop_depth >= 2:
            line_num = node.lineno
            self.findings.append(Finding(
                title="High Complexity: Nested Loops",
                description=f"Nested loop detected at depth {self.loop_depth}, potentially O(n^{self.loop_depth}) complexity.",
                severity=Severity.HIGH if self.loop_depth >= 3 else Severity.MEDIUM,
                confidence=Confidence.HIGH,
                file_path=self.file.path,
                line_number=line_num,
                code_snippet=self._get_code_at_line(line_num),
                suggestion="Consider using more efficient algorithms or data structures to reduce complexity.",
                category="performance",
                rule_id="PERF_NESTED_LOOPS"
            ))
        
        self.generic_visit(node)
        self.loop_depth -= 1
    
    def visit_While(self, node):
        """Visit while loops to detect nesting."""
        self.loop_depth += 1
        self.generic_visit(node)
        self.loop_depth -= 1
    
    def visit_ListComp(self, node):
        """Check for complex list comprehensions."""
        # Count generators in list comprehension
        generator_count = len(node.generators)
        
        if generator_count >= 2:
            line_num = node.lineno
            self.findings.append(Finding(
                title="Complex List Comprehension",
                description=f"List comprehension with {generator_count} generators may be hard to read and potentially inefficient.",
                severity=Severity.LOW,
                confidence=Confidence.MEDIUM,
                file_path=self.file.path,
                line_number=line_num,
                code_snippet=self._get_code_at_line(line_num),
                suggestion="Consider breaking down complex list comprehensions into simpler loops for better readability.",
                category="performance",
                rule_id="PERF_COMPLEX_COMPREHENSION"
            ))
        
        self.generic_visit(node)
    
    def _get_code_at_line(self, line_num: int) -> str:
        """Get code at specific line number."""
        lines = self.file.content.split('\n')
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1].strip()
        return ""
