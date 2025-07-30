"""
StyleAgent - Enforces coding standards, naming conventions, and documentation.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from app.agents.base import BaseAgent, Finding, CodeFile
from app.core.config import Severity, Confidence


class StyleAgent(BaseAgent):
    """Agent specialized in code style and formatting standards."""
    
    def __init__(self):
        super().__init__("style")
        
        # Style patterns by language
        self.style_patterns = {
            "python": {
                "snake_case": r"^[a-z_][a-z0-9_]*$",
                "class_case": r"^[A-Z][a-zA-Z0-9]*$",
                "constant_case": r"^[A-Z][A-Z0-9_]*$",
                "line_length": 88,  # Black formatter standard
            },
            "javascript": {
                "camel_case": r"^[a-z][a-zA-Z0-9]*$",
                "class_case": r"^[A-Z][a-zA-Z0-9]*$",
                "constant_case": r"^[A-Z][A-Z0-9_]*$",
                "line_length": 80,
            },
            "java": {
                "camel_case": r"^[a-z][a-zA-Z0-9]*$",
                "class_case": r"^[A-Z][a-zA-Z0-9]*$",
                "constant_case": r"^[A-Z][A-Z0-9_]*$",
                "line_length": 120,
            }
        }
        
        # Common style issues
        self.common_issues = {
            "trailing_whitespace": r"\s+$",
            "mixed_tabs_spaces": r"^\t+ +|\s*\t+\s*",
            "multiple_blank_lines": r"\n\s*\n\s*\n",
            "missing_docstring": r"^(def|class|async def)\s+\w+.*:\s*\n(?!\s*['\"])",
            "long_lines": None,  # Handled separately per language
            "inconsistent_quotes": None,  # Handled separately
        }
    
    def _filter_relevant_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Filter files relevant for style analysis."""
        relevant_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', 
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.scala'
        }
        
        return [
            f for f in files 
            if any(f.path.endswith(ext) for ext in relevant_extensions)
            and not any(skip in f.path.lower() for skip in ['generated', 'build', 'dist'])
        ]
    
    async def _perform_analysis(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """Perform style analysis on code files."""
        findings = []
        total_tokens = 0
        
        for file in files:
            # Pattern-based style checking
            pattern_findings = self._check_style_patterns(file)
            findings.extend(pattern_findings)
            
            # Language-specific checks
            language_findings = self._check_language_specific_style(file)
            findings.extend(language_findings)
            
            # Documentation checks
            doc_findings = self._check_documentation(file)
            findings.extend(doc_findings)
            
            # LLM-based analysis for complex style issues
            if len(file.content) < 3000:  # Reasonable size for style analysis
                prompt = self._create_prompt([file], context)
                try:
                    response, tokens = await self._call_llm(prompt)
                    total_tokens += tokens
                    
                    llm_findings = self._parse_llm_response(response, file)
                    findings.extend(llm_findings)
                except Exception as e:
                    print(f"LLM style analysis failed for {file.path}: {e}")
        
        return findings, total_tokens
    
    def _check_style_patterns(self, file: CodeFile) -> List[Finding]:
        """Check common style patterns."""
        findings = []
        lines = file.content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Trailing whitespace
            if re.search(self.common_issues["trailing_whitespace"], line):
                findings.append(Finding(
                    title="Trailing Whitespace",
                    description="Line contains trailing whitespace characters.",
                    severity=Severity.LOW,
                    confidence=Confidence.HIGH,
                    file_path=file.path,
                    line_number=line_num,
                    code_snippet=line,
                    suggestion="Remove trailing whitespace.",
                    category="style",
                    rule_id="STYLE_TRAILING_WS"
                ))
            
            # Mixed tabs and spaces
            if re.search(self.common_issues["mixed_tabs_spaces"], line):
                findings.append(Finding(
                    title="Mixed Tabs and Spaces",
                    description="Line contains mixed tabs and spaces for indentation.",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    file_path=file.path,
                    line_number=line_num,
                    code_snippet=line[:20] + "...",
                    suggestion="Use consistent indentation (either tabs or spaces, not both).",
                    category="style",
                    rule_id="STYLE_MIXED_INDENT"
                ))
        
        # Check for multiple consecutive blank lines
        blank_line_matches = re.finditer(self.common_issues["multiple_blank_lines"], file.content)
        for match in blank_line_matches:
            line_num = file.content[:match.start()].count('\n') + 1
            findings.append(Finding(
                title="Multiple Consecutive Blank Lines",
                description="Multiple consecutive blank lines found.",
                severity=Severity.LOW,
                confidence=Confidence.HIGH,
                file_path=file.path,
                line_number=line_num,
                code_snippet="(multiple blank lines)",
                suggestion="Use single blank lines to separate code sections.",
                category="style",
                rule_id="STYLE_MULTIPLE_BLANKS"
            ))
        
        return findings
    
    def _check_language_specific_style(self, file: CodeFile) -> List[Finding]:
        """Check language-specific style rules."""
        findings = []
        language = file.language
        
        if language not in self.style_patterns:
            return findings
        
        lines = file.content.split('\n')
        max_line_length = self.style_patterns[language]["line_length"]
        
        # Check line length
        for line_num, line in enumerate(lines, 1):
            if len(line) > max_line_length:
                findings.append(Finding(
                    title="Line Too Long",
                    description=f"Line exceeds maximum length of {max_line_length} characters ({len(line)} chars).",
                    severity=Severity.LOW,
                    confidence=Confidence.HIGH,
                    file_path=file.path,
                    line_number=line_num,
                    code_snippet=line[:50] + "..." if len(line) > 50 else line,
                    suggestion=f"Break line into multiple lines or refactor to stay under {max_line_length} characters.",
                    category="style",
                    rule_id="STYLE_LINE_LENGTH"
                ))
        
        # Language-specific naming conventions
        if language == "python":
            findings.extend(self._check_python_naming(file))
        elif language in ["javascript", "typescript"]:
            findings.extend(self._check_javascript_naming(file))
        elif language == "java":
            findings.extend(self._check_java_naming(file))
        
        return findings
    
    def _check_python_naming(self, file: CodeFile) -> List[Finding]:
        """Check Python naming conventions (PEP 8)."""
        findings = []
        
        # Function and variable names (snake_case)
        function_pattern = r"^def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
        variable_pattern = r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*="
        
        for line_num, line in enumerate(file.content.split('\n'), 1):
            # Check function names
            func_match = re.search(function_pattern, line)
            if func_match:
                func_name = func_match.group(1)
                if not re.match(self.style_patterns["python"]["snake_case"], func_name):
                    if not func_name.startswith('_'):  # Ignore private functions for now
                        findings.append(Finding(
                            title="Function Naming Convention",
                            description=f"Function '{func_name}' does not follow snake_case convention.",
                            severity=Severity.LOW,
                            confidence=Confidence.HIGH,
                            file_path=file.path,
                            line_number=line_num,
                            code_snippet=line.strip(),
                            suggestion="Use snake_case for function names (e.g., my_function).",
                            category="style",
                            rule_id="STYLE_PYTHON_FUNC_NAME"
                        ))
        
        return findings
    
    def _check_javascript_naming(self, file: CodeFile) -> List[Finding]:
        """Check JavaScript/TypeScript naming conventions."""
        findings = []
        
        # Function names (camelCase)
        function_pattern = r"function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\("
        arrow_function_pattern = r"const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*\("
        
        for line_num, line in enumerate(file.content.split('\n'), 1):
            # Check function names
            func_match = re.search(function_pattern, line)
            if func_match:
                func_name = func_match.group(1)
                if not re.match(self.style_patterns["javascript"]["camel_case"], func_name):
                    findings.append(Finding(
                        title="Function Naming Convention",
                        description=f"Function '{func_name}' does not follow camelCase convention.",
                        severity=Severity.LOW,
                        confidence=Confidence.HIGH,
                        file_path=file.path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Use camelCase for function names (e.g., myFunction).",
                        category="style",
                        rule_id="STYLE_JS_FUNC_NAME"
                    ))
        
        return findings
    
    def _check_java_naming(self, file: CodeFile) -> List[Finding]:
        """Check Java naming conventions."""
        findings = []
        
        # Class names (PascalCase)
        class_pattern = r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        
        for line_num, line in enumerate(file.content.split('\n'), 1):
            class_match = re.search(class_pattern, line)
            if class_match:
                class_name = class_match.group(1)
                if not re.match(self.style_patterns["java"]["class_case"], class_name):
                    findings.append(Finding(
                        title="Class Naming Convention",
                        description=f"Class '{class_name}' does not follow PascalCase convention.",
                        severity=Severity.MEDIUM,
                        confidence=Confidence.HIGH,
                        file_path=file.path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Use PascalCase for class names (e.g., MyClass).",
                        category="style",
                        rule_id="STYLE_JAVA_CLASS_NAME"
                    ))
        
        return findings
    
    def _check_documentation(self, file: CodeFile) -> List[Finding]:
        """Check documentation completeness."""
        findings = []
        lines = file.content.split('\n')
        
        in_function = False
        function_line = 0
        
        for line_num, line in enumerate(lines, 1):
            # Check for function/method definitions
            if re.match(r"^\s*(def|class|async def)\s+\w+", line):
                in_function = True
                function_line = line_num
                
                # Check if next non-empty line is a docstring
                next_line_idx = line_num
                while next_line_idx < len(lines) and not lines[next_line_idx].strip():
                    next_line_idx += 1
                
                if next_line_idx < len(lines):
                    next_line = lines[next_line_idx].strip()
                    if not (next_line.startswith('"""') or next_line.startswith("'''")):
                        # Only flag public functions/classes (not starting with _)
                        if not re.search(r"def\s+_\w+|class\s+_\w+", line):
                            findings.append(Finding(
                                title="Missing Docstring",
                                description="Public function or class lacks documentation.",
                                severity=Severity.LOW,
                                confidence=Confidence.HIGH,
                                file_path=file.path,
                                line_number=function_line,
                                code_snippet=line.strip(),
                                suggestion="Add a docstring to document the purpose, parameters, and return value.",
                                category="style",
                                rule_id="STYLE_MISSING_DOC"
                            ))
        
        return findings
    
    def _create_prompt(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> str:
        """Create style analysis prompt for LLM."""
        file_content = files[0].content if files else ""
        file_path = files[0].path if files else "unknown"
        language = files[0].language if files else "unknown"
        
        prompt = f"""
You are a senior code reviewer focusing on code style, readability, and maintainability.
Analyze the following {language} code for style issues and documentation quality.

File: {file_path}
Language: {language}

Focus on identifying:
1. Naming convention violations
2. Code formatting inconsistencies
3. Documentation quality issues
4. Code readability problems
5. Maintainability concerns
6. Comment quality and necessity
7. Code organization issues
8. Consistency with language best practices

For each issue found, provide:
- Style issue type
- Severity level (CRITICAL, HIGH, MEDIUM, LOW)
- Line number where issue occurs
- Impact on code quality
- Recommended improvement

Code to analyze:
```{language}
{file_content}
```

Format your response as:
FINDING: [Style Issue Type]
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
LINE: [Line Number]
IMPACT: [Impact on code quality]
IMPROVEMENT: [How to improve]
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
                    elif key == 'IMPROVEMENT':
                        finding_data['suggestion'] = value
            
            if 'title' in finding_data and 'description' in finding_data:
                findings.append(Finding(
                    title=f"Style: {finding_data.get('title', 'Style Issue')}",
                    description=finding_data.get('description', 'Style issue detected'),
                    severity=getattr(Severity, finding_data.get('severity', 'LOW'), Severity.LOW),
                    confidence=Confidence.MEDIUM,
                    file_path=file.path,
                    line_number=finding_data.get('line_number', 1),
                    code_snippet=self._get_code_snippet(file.content, finding_data.get('line_number', 1)),
                    suggestion=finding_data.get('suggestion', 'Improve code style'),
                    category="style",
                    rule_id="STYLE_LLM_DETECTED"
                ))
        
        return findings
    
    def _get_code_snippet(self, content: str, line_number: int) -> str:
        """Extract code snippet around the specified line."""
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""
