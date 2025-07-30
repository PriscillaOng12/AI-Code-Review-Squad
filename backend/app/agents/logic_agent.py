"""
LogicAgent - Finds logical errors, edge cases, and potential bugs.
"""

import re
import ast
from typing import List, Tuple, Dict, Any, Optional
from app.agents.base import BaseAgent, Finding, CodeFile
from app.core.config import Severity, Confidence


class LogicAgent(BaseAgent):
    """Agent specialized in logical correctness and edge case detection."""
    
    def __init__(self):
        super().__init__("logic")
        
        # Logic error patterns
        self.logic_patterns = {
            "null_pointer": [
                r"\.(?:get|access|call)\(\s*\)\s*\.",
                r"\w+\.\w+\s*\(\s*\)\s*\[\s*\]",
                r"if\s+\w+\s*:\s*\n\s*\w+\.\w+\s*=",
            ],
            "off_by_one": [
                r"range\s*\(\s*len\s*\(\s*\w+\s*\)\s*\)",
                r"for\s+\w+\s+in\s+range\s*\(\s*\d+\s*,\s*len\s*\(\s*\w+\s*\)\s*\)",
                r"\[\s*len\s*\(\s*\w+\s*\)\s*\]",
            ],
            "infinite_loops": [
                r"while\s+True\s*:",
                r"while\s+\d+\s*:",
                r"for\s+.*\s+in\s+itertools\.count\(\)",
            ],
            "unreachable_code": [
                r"return\s+.*\n\s*\w+",
                r"break\s*\n\s*\w+",
                r"continue\s*\n\s*\w+",
            ],
            "division_by_zero": [
                r"/\s*0",
                r"//\s*0",
                r"%\s*0",
                r"math\.pow\s*\(\s*\w+\s*,\s*-\d+\s*\)",
            ],
            "resource_leaks": [
                r"open\s*\(\s*.*\)\s*(?!with)",
                r"socket\.\w+\s*\(\s*.*\)\s*(?!with)",
                r"subprocess\.Popen\s*\(\s*.*\)\s*(?!with)",
            ],
        }
    
    def _filter_relevant_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Filter files relevant for logic analysis."""
        relevant_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs',
            '.php', '.rb', '.swift', '.kt', '.scala'
        }
        
        return [
            f for f in files 
            if any(f.path.endswith(ext) for ext in relevant_extensions)
            and not any(skip in f.path.lower() for skip in ['test', 'spec', 'mock'])
        ]
    
    async def _perform_analysis(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """Perform logic analysis on code files."""
        findings = []
        total_tokens = 0
        
        for file in files:
            # Pattern-based logic checking
            pattern_findings = self._detect_logic_patterns(file)
            findings.extend(pattern_findings)
            
            # AST-based analysis for Python files
            if file.path.endswith('.py'):
                ast_findings = self._analyze_python_logic(file)
                findings.extend(ast_findings)
            
            # Control flow analysis
            control_flow_findings = self._analyze_control_flow(file)
            findings.extend(control_flow_findings)
            
            # LLM-based analysis for complex logic issues
            if len(file.content) < 4000:  # Reasonable size for logic analysis
                prompt = self._create_prompt([file], context)
                try:
                    response, tokens = await self._call_llm(prompt)
                    total_tokens += tokens
                    
                    llm_findings = self._parse_llm_response(response, file)
                    findings.extend(llm_findings)
                except Exception as e:
                    print(f"LLM logic analysis failed for {file.path}: {e}")
        
        return findings, total_tokens
    
    def _detect_logic_patterns(self, file: CodeFile) -> List[Finding]:
        """Detect logic issues using regex patterns."""
        findings = []
        
        for issue_type, patterns in self.logic_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, file.content, re.MULTILINE)
                for match in matches:
                    line_num = file.content[:match.start()].count('\n') + 1
                    
                    findings.append(Finding(
                        title=f"Logic Issue: {issue_type.replace('_', ' ').title()}",
                        description=self._get_logic_description(issue_type),
                        severity=self._get_logic_severity(issue_type),
                        confidence=Confidence.HIGH,
                        file_path=file.path,
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(file.content, line_num),
                        suggestion=self._get_logic_suggestion(issue_type),
                        category="logic",
                        rule_id=f"LOGIC_{issue_type.upper()}"
                    ))
        
        return findings
    
    def _analyze_python_logic(self, file: CodeFile) -> List[Finding]:
        """Analyze Python code using AST for logical issues."""
        findings = []
        
        try:
            tree = ast.parse(file.content)
            analyzer = PythonLogicAnalyzer(file)
            analyzer.visit(tree)
            findings.extend(analyzer.findings)
        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception as e:
            print(f"AST logic analysis failed for {file.path}: {e}")
        
        return findings
    
    def _analyze_control_flow(self, file: CodeFile) -> List[Finding]:
        """Analyze control flow for potential issues."""
        findings = []
        lines = file.content.split('\n')
        
        # Check for unreachable code after return statements
        for line_num, line in enumerate(lines, 1):
            if re.search(r'^\s*return\s+', line):
                # Check if there's executable code after return
                for next_line_num in range(line_num + 1, min(line_num + 5, len(lines) + 1)):
                    if next_line_num <= len(lines):
                        next_line = lines[next_line_num - 1]
                        # Skip empty lines and comments
                        if next_line.strip() and not next_line.strip().startswith('#'):
                            # Check if it's not a function/class definition
                            if not re.match(r'^\s*(def|class|if|elif|else|except|finally|with)', next_line):
                                findings.append(Finding(
                                    title="Unreachable Code",
                                    description="Code after return statement may never be executed.",
                                    severity=Severity.MEDIUM,
                                    confidence=Confidence.MEDIUM,
                                    file_path=file.path,
                                    line_number=next_line_num,
                                    code_snippet=next_line.strip(),
                                    suggestion="Remove unreachable code or restructure control flow.",
                                    category="logic",
                                    rule_id="LOGIC_UNREACHABLE"
                                ))
                            break
        
        return findings
    
    def _create_prompt(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> str:
        """Create logic analysis prompt for LLM."""
        file_content = files[0].content if files else ""
        file_path = files[0].path if files else "unknown"
        language = files[0].language if files else "unknown"
        
        prompt = f"""
You are a senior software engineer conducting a thorough logical correctness review.
Analyze the following {language} code for logical errors, edge cases, and potential bugs.

File: {file_path}
Language: {language}

Focus on identifying:
1. Null pointer/undefined reference errors
2. Off-by-one errors in loops and array access
3. Edge cases not handled properly
4. Logic errors in conditional statements
5. Infinite loops or recursion
6. Race conditions and concurrency issues
7. Input validation problems
8. Resource management issues
9. Error handling gaps
10. Boundary condition failures

For each issue found, provide:
- Logic issue type
- Severity level (CRITICAL, HIGH, MEDIUM, LOW)
- Line number where issue occurs
- Potential impact and scenarios where bug occurs
- Recommended fix

Code to analyze:
```{language}
{file_content}
```

Format your response as:
FINDING: [Logic Issue Type]
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
LINE: [Line Number]
IMPACT: [Potential impact and scenarios]
FIX: [How to fix the issue]
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
                    elif key == 'FIX':
                        finding_data['suggestion'] = value
            
            if 'title' in finding_data and 'description' in finding_data:
                findings.append(Finding(
                    title=f"Logic: {finding_data.get('title', 'Logic Issue')}",
                    description=finding_data.get('description', 'Logic issue detected'),
                    severity=getattr(Severity, finding_data.get('severity', 'MEDIUM'), Severity.MEDIUM),
                    confidence=Confidence.HIGH,
                    file_path=file.path,
                    line_number=finding_data.get('line_number', 1),
                    code_snippet=self._get_code_snippet(file.content, finding_data.get('line_number', 1)),
                    suggestion=finding_data.get('suggestion', 'Fix logic issue'),
                    category="logic",
                    rule_id="LOGIC_LLM_DETECTED"
                ))
        
        return findings
    
    def _get_code_snippet(self, content: str, line_number: int) -> str:
        """Extract code snippet around the specified line."""
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""
    
    def _get_logic_description(self, issue_type: str) -> str:
        """Get description for logic issue type."""
        descriptions = {
            "null_pointer": "Potential null pointer or undefined reference that could cause runtime errors.",
            "off_by_one": "Potential off-by-one error in array/list access or loop iteration.",
            "infinite_loops": "Potential infinite loop that could cause application to hang.",
            "unreachable_code": "Code that can never be executed due to control flow.",
            "division_by_zero": "Potential division by zero that could cause runtime exception.",
            "resource_leaks": "Resource not properly closed, which could lead to memory leaks."
        }
        return descriptions.get(issue_type, "Logic issue detected")
    
    def _get_logic_severity(self, issue_type: str) -> Severity:
        """Get severity level for logic issue type."""
        severity_map = {
            "null_pointer": Severity.CRITICAL,
            "off_by_one": Severity.HIGH,
            "infinite_loops": Severity.CRITICAL,
            "unreachable_code": Severity.MEDIUM,
            "division_by_zero": Severity.HIGH,
            "resource_leaks": Severity.HIGH
        }
        return severity_map.get(issue_type, Severity.MEDIUM)
    
    def _get_logic_suggestion(self, issue_type: str) -> str:
        """Get fix suggestion for logic issue type."""
        suggestions = {
            "null_pointer": "Add null checks before accessing objects or use safe navigation operators.",
            "off_by_one": "Review loop bounds and array indices. Consider using range(len(array)) carefully.",
            "infinite_loops": "Add proper exit conditions and ensure loop variables are modified correctly.",
            "unreachable_code": "Remove unreachable code or restructure control flow logic.",
            "division_by_zero": "Add checks to ensure divisor is not zero before division operations.",
            "resource_leaks": "Use context managers (with statements) or try-finally blocks to ensure resource cleanup."
        }
        return suggestions.get(issue_type, "Review and fix logic issue")


class PythonLogicAnalyzer(ast.NodeVisitor):
    """AST visitor for Python-specific logic analysis."""
    
    def __init__(self, file: CodeFile):
        self.file = file
        self.findings = []
        self.variables = set()
        self.function_returns = {}
    
    def visit_Assign(self, node):
        """Track variable assignments."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.add(target.id)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        """Check for undefined variable usage."""
        if isinstance(node.ctx, ast.Load) and node.id not in self.variables:
            # Check if it's a potential undefined variable
            if not node.id in ['True', 'False', 'None'] and not node.id.isupper():
                line_num = node.lineno
                self.findings.append(Finding(
                    title="Potential Undefined Variable",
                    description=f"Variable '{node.id}' used before assignment or may be undefined.",
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    file_path=self.file.path,
                    line_number=line_num,
                    code_snippet=self._get_code_at_line(line_num),
                    suggestion="Ensure variable is defined before use or add proper initialization.",
                    category="logic",
                    rule_id="LOGIC_UNDEFINED_VAR"
                ))
        
        self.generic_visit(node)
    
    def visit_Subscript(self, node):
        """Check for potential index errors."""
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, int):
            # Check for negative indices without length check
            if node.slice.value < 0:
                line_num = node.lineno
                self.findings.append(Finding(
                    title="Negative Index Usage",
                    description="Negative index used without ensuring list is non-empty.",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.MEDIUM,
                    file_path=self.file.path,
                    line_number=line_num,
                    code_snippet=self._get_code_at_line(line_num),
                    suggestion="Ensure list/array is non-empty before using negative indices.",
                    category="logic",
                    rule_id="LOGIC_NEGATIVE_INDEX"
                ))
        
        self.generic_visit(node)
    
    def visit_While(self, node):
        """Check for potential infinite loops."""
        # Simple heuristic: while True without break
        if isinstance(node.test, ast.Constant) and node.test.value is True:
            # Check if there's a break statement in the loop
            has_break = any(isinstance(child, ast.Break) for child in ast.walk(node))
            if not has_break:
                line_num = node.lineno
                self.findings.append(Finding(
                    title="Potential Infinite Loop",
                    description="While True loop without visible break statement.",
                    severity=Severity.HIGH,
                    confidence=Confidence.MEDIUM,
                    file_path=self.file.path,
                    line_number=line_num,
                    code_snippet=self._get_code_at_line(line_num),
                    suggestion="Ensure loop has proper exit conditions to prevent infinite execution.",
                    category="logic",
                    rule_id="LOGIC_INFINITE_WHILE"
                ))
        
        self.generic_visit(node)
    
    def _get_code_at_line(self, line_num: int) -> str:
        """Get code at specific line number."""
        lines = self.file.content.split('\n')
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1].strip()
        return ""
