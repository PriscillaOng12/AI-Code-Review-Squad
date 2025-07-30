"""
ArchitectureAgent - Evaluates code architecture, design patterns, and structural quality.
"""

import re
import ast
from typing import List, Tuple, Dict, Any, Optional, Set
from app.agents.base import BaseAgent, Finding, CodeFile
from app.core.config import Severity, Confidence


class ArchitectureAgent(BaseAgent):
    """Agent specialized in architecture and design pattern analysis."""
    
    def __init__(self):
        super().__init__("architecture")
        
        # Architecture pattern checks
        self.architecture_patterns = {
            "god_class": [
                r"class\s+\w+.*:\s*\n(?:\s*.*\n){100,}",  # Classes over 100 lines
            ],
            "long_method": [
                r"def\s+\w+.*:\s*\n(?:\s*.*\n){50,}",  # Methods over 50 lines
            ],
            "high_complexity": [
                r"if\s+.*:\s*\n\s*if\s+.*:\s*\n\s*if\s+.*:",  # Nested conditions
                r"for\s+.*:\s*\n\s*for\s+.*:\s*\n\s*for\s+.*:",  # Triple nested loops
            ],
            "tight_coupling": [
                r"from\s+\w+\s+import\s+\*",  # Wildcard imports
                r"import\s+(?:\w+\.){3,}\w+",  # Deep import paths
            ],
            "hardcoded_values": [
                r"=\s*['\"](?:http://|https://|ftp://)\S+['\"]",  # URLs
                r"=\s*['\"](?:\w+\.)+\w+['\"]",  # Email-like patterns
                r"=\s*\d{4,}",  # Large numbers (possible magic numbers)
            ],
        }
        
        # SOLID principles checks
        self.solid_patterns = {
            "srp_violation": [
                r"class\s+\w+.*:\s*(?:\s*.*\n)*\s*def\s+(?:save|load|parse|validate|send|receive)",
            ],
            "ocp_violation": [
                r"if\s+type\s*\(\s*\w+\s*\)\s*==",  # Type checking instead of polymorphism
                r"if\s+isinstance\s*\(\s*\w+\s*,\s*\w+\s*\)",
            ],
            "lsp_violation": [
                r"raise\s+NotImplementedError",  # Empty implementations
            ],
            "isp_violation": [
                r"class\s+\w+.*:\s*(?:\s*.*\n)*\s*pass\s*\n\s*def\s+\w+.*:\s*(?:\s*.*\n)*\s*pass",
            ],
            "dip_violation": [
                r"=\s*\w+\(\)",  # Direct instantiation of concrete classes
            ],
        }
        
        # Design pattern recognition
        self.design_patterns = {
            "singleton": [
                r"_instance\s*=\s*None",
                r"__new__\s*\(\s*cls\s*\)",
            ],
            "factory": [
                r"def\s+create_\w+",
                r"class\s+\w+Factory",
            ],
            "observer": [
                r"def\s+(?:add_|remove_)?(?:observer|listener)",
                r"def\s+notify",
            ],
            "decorator": [
                r"@\w+",
                r"def\s+\w+\s*\(\s*func\s*\)",
            ],
            "strategy": [
                r"class\s+\w+Strategy",
                r"def\s+execute\s*\(",
            ],
        }
    
    def _filter_relevant_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Filter files relevant for architecture analysis."""
        relevant_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs',
            '.php', '.rb', '.swift', '.kt', '.scala'
        }
        
        return [
            f for f in files 
            if any(f.path.endswith(ext) for ext in relevant_extensions)
            and not any(skip in f.path.lower() for skip in ['test', 'spec', 'mock', '__pycache__'])
        ]
    
    async def _perform_analysis(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """Perform architecture analysis on code files."""
        findings = []
        total_tokens = 0
        
        # Analyze individual files
        for file in files:
            # Pattern-based architecture checking
            pattern_findings = self._detect_architecture_patterns(file)
            findings.extend(pattern_findings)
            
            # SOLID principles analysis
            solid_findings = self._analyze_solid_principles(file)
            findings.extend(solid_findings)
            
            # Design pattern recognition
            pattern_recognition = self._recognize_design_patterns(file)
            findings.extend(pattern_recognition)
            
            # AST-based analysis for Python files
            if file.path.endswith('.py'):
                ast_findings = self._analyze_python_architecture(file)
                findings.extend(ast_findings)
        
        # Cross-file architecture analysis
        cross_file_findings = self._analyze_cross_file_architecture(files)
        findings.extend(cross_file_findings)
        
        # LLM-based architecture review for complex analysis
        if len(files) <= 5:  # Limit for detailed architectural review
            for file in files[:3]:  # Analyze top 3 files
                if len(file.content) < 5000:  # Reasonable size for architecture analysis
                    prompt = self._create_prompt([file], context)
                    try:
                        response, tokens = await self._call_llm(prompt)
                        total_tokens += tokens
                        
                        llm_findings = self._parse_llm_response(response, file)
                        findings.extend(llm_findings)
                    except Exception as e:
                        print(f"LLM architecture analysis failed for {file.path}: {e}")
        
        return findings, total_tokens
    
    def _detect_architecture_patterns(self, file: CodeFile) -> List[Finding]:
        """Detect architecture issues using regex patterns."""
        findings = []
        
        for issue_type, patterns in self.architecture_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, file.content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    line_num = file.content[:match.start()].count('\n') + 1
                    
                    findings.append(Finding(
                        title=f"Architecture: {issue_type.replace('_', ' ').title()}",
                        description=self._get_architecture_description(issue_type),
                        severity=self._get_architecture_severity(issue_type),
                        confidence=Confidence.HIGH,
                        file_path=file.path,
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(file.content, line_num),
                        suggestion=self._get_architecture_suggestion(issue_type),
                        category="architecture",
                        rule_id=f"ARCH_{issue_type.upper()}"
                    ))
        
        return findings
    
    def _analyze_solid_principles(self, file: CodeFile) -> List[Finding]:
        """Analyze SOLID principles violations."""
        findings = []
        
        for principle, patterns in self.solid_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, file.content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    line_num = file.content[:match.start()].count('\n') + 1
                    
                    findings.append(Finding(
                        title=f"SOLID Violation: {principle.upper().replace('_', ' ')}",
                        description=self._get_solid_description(principle),
                        severity=Severity.MEDIUM,
                        confidence=Confidence.MEDIUM,
                        file_path=file.path,
                        line_number=line_num,
                        code_snippet=self._get_code_snippet(file.content, line_num),
                        suggestion=self._get_solid_suggestion(principle),
                        category="architecture",
                        rule_id=f"SOLID_{principle.upper()}"
                    ))
        
        return findings
    
    def _recognize_design_patterns(self, file: CodeFile) -> List[Finding]:
        """Recognize and validate design patterns."""
        findings = []
        
        for pattern_name, patterns in self.design_patterns.items():
            pattern_count = 0
            for pattern in patterns:
                matches = list(re.finditer(pattern, file.content, re.MULTILINE))
                pattern_count += len(matches)
            
            if pattern_count >= 2:  # Likely implementing this pattern
                # Add positive finding about pattern usage
                findings.append(Finding(
                    title=f"Design Pattern: {pattern_name.title()} Pattern",
                    description=f"Implementation of {pattern_name} design pattern detected.",
                    severity=Severity.INFO,
                    confidence=Confidence.MEDIUM,
                    file_path=file.path,
                    line_number=1,
                    code_snippet=f"Pattern: {pattern_name}",
                    suggestion=f"Ensure {pattern_name} pattern is implemented correctly and consistently.",
                    category="architecture",
                    rule_id=f"PATTERN_{pattern_name.upper()}"
                ))
        
        return findings
    
    def _analyze_python_architecture(self, file: CodeFile) -> List[Finding]:
        """Analyze Python code using AST for architectural issues."""
        findings = []
        
        try:
            tree = ast.parse(file.content)
            analyzer = PythonArchitectureAnalyzer(file)
            analyzer.visit(tree)
            findings.extend(analyzer.findings)
        except SyntaxError:
            # Skip files with syntax errors
            pass
        except Exception as e:
            print(f"AST architecture analysis failed for {file.path}: {e}")
        
        return findings
    
    def _analyze_cross_file_architecture(self, files: List[CodeFile]) -> List[Finding]:
        """Analyze architecture across multiple files."""
        findings = []
        
        # Analyze module coupling
        import_graph = self._build_import_graph(files)
        coupling_findings = self._analyze_coupling(import_graph, files)
        findings.extend(coupling_findings)
        
        # Analyze code duplication
        duplication_findings = self._analyze_code_duplication(files)
        findings.extend(duplication_findings)
        
        return findings
    
    def _build_import_graph(self, files: List[CodeFile]) -> Dict[str, Set[str]]:
        """Build import dependency graph."""
        import_graph = {}
        
        for file in files:
            imports = set()
            lines = file.content.split('\n')
            
            for line in lines:
                # Python imports
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    imports.add(line.strip())
                # JavaScript/TypeScript imports
                elif 'import' in line and 'from' in line:
                    imports.add(line.strip())
            
            import_graph[file.path] = imports
        
        return import_graph
    
    def _analyze_coupling(self, import_graph: Dict[str, Set[str]], files: List[CodeFile]) -> List[Finding]:
        """Analyze coupling between modules."""
        findings = []
        
        for file_path, imports in import_graph.items():
            if len(imports) > 10:  # High number of imports
                findings.append(Finding(
                    title="High Coupling",
                    description=f"Module has {len(imports)} imports, indicating high coupling.",
                    severity=Severity.MEDIUM,
                    confidence=Confidence.HIGH,
                    file_path=file_path,
                    line_number=1,
                    code_snippet=f"Imports: {len(imports)}",
                    suggestion="Consider reducing dependencies or splitting module into smaller parts.",
                    category="architecture",
                    rule_id="ARCH_HIGH_COUPLING"
                ))
        
        return findings
    
    def _analyze_code_duplication(self, files: List[CodeFile]) -> List[Finding]:
        """Analyze code duplication across files."""
        findings = []
        
        # Simple duplication detection based on function signatures
        function_signatures = {}
        
        for file in files:
            lines = file.content.split('\n')
            for line_num, line in enumerate(lines, 1):
                # Python function definitions
                func_match = re.match(r'\s*def\s+(\w+)\s*\(([^)]*)\)', line)
                if func_match:
                    func_name = func_match.group(1)
                    func_params = func_match.group(2)
                    signature = f"{func_name}({func_params})"
                    
                    if signature in function_signatures:
                        # Potential duplication
                        original_file, original_line = function_signatures[signature]
                        if original_file != file.path:
                            findings.append(Finding(
                                title="Potential Code Duplication",
                                description=f"Similar function signature found in {original_file}:{original_line}",
                                severity=Severity.LOW,
                                confidence=Confidence.MEDIUM,
                                file_path=file.path,
                                line_number=line_num,
                                code_snippet=line.strip(),
                                suggestion="Consider extracting common functionality into shared module.",
                                category="architecture",
                                rule_id="ARCH_DUPLICATION"
                            ))
                    else:
                        function_signatures[signature] = (file.path, line_num)
        
        return findings
    
    def _create_prompt(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> str:
        """Create architecture analysis prompt for LLM."""
        file_content = files[0].content if files else ""
        file_path = files[0].path if files else "unknown"
        language = files[0].language if files else "unknown"
        
        prompt = f"""
You are a senior software architect conducting a comprehensive architecture review.
Analyze the following {language} code for architectural issues and design quality.

File: {file_path}
Language: {language}

Focus on evaluating:
1. SOLID principles adherence (SRP, OCP, LSP, ISP, DIP)
2. Design patterns usage and correctness
3. Code organization and modularity
4. Separation of concerns
5. Coupling and cohesion
6. Abstraction levels
7. Code reusability and maintainability
8. Architecture smells (God class, Feature envy, etc.)
9. Dependency management
10. Scalability considerations

For each architectural issue found, provide:
- Architecture concern type
- Severity level (CRITICAL, HIGH, MEDIUM, LOW)
- Line number or code section
- Impact on maintainability and scalability
- Recommended architectural improvement

Code to analyze:
```{language}
{file_content}
```

Format your response as:
FINDING: [Architecture Issue Type]
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
LINE: [Line Number or Section]
IMPACT: [Impact on architecture and maintainability]
IMPROVEMENT: [Recommended architectural change]
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
                    title=f"Architecture: {finding_data.get('title', 'Architecture Issue')}",
                    description=finding_data.get('description', 'Architecture issue detected'),
                    severity=getattr(Severity, finding_data.get('severity', 'MEDIUM'), Severity.MEDIUM),
                    confidence=Confidence.HIGH,
                    file_path=file.path,
                    line_number=finding_data.get('line_number', 1),
                    code_snippet=self._get_code_snippet(file.content, finding_data.get('line_number', 1)),
                    suggestion=finding_data.get('suggestion', 'Improve architecture'),
                    category="architecture",
                    rule_id="ARCH_LLM_DETECTED"
                ))
        
        return findings
    
    def _get_code_snippet(self, content: str, line_number: int) -> str:
        """Extract code snippet around the specified line."""
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""
    
    def _get_architecture_description(self, issue_type: str) -> str:
        """Get description for architecture issue type."""
        descriptions = {
            "god_class": "Class is too large and likely violates Single Responsibility Principle.",
            "long_method": "Method is too long and should be broken into smaller functions.",
            "high_complexity": "High cyclomatic complexity makes code hard to understand and maintain.",
            "tight_coupling": "Strong coupling between modules reduces maintainability.",
            "hardcoded_values": "Hardcoded values should be extracted to configuration."
        }
        return descriptions.get(issue_type, "Architecture issue detected")
    
    def _get_architecture_severity(self, issue_type: str) -> Severity:
        """Get severity level for architecture issue type."""
        severity_map = {
            "god_class": Severity.HIGH,
            "long_method": Severity.MEDIUM,
            "high_complexity": Severity.HIGH,
            "tight_coupling": Severity.MEDIUM,
            "hardcoded_values": Severity.LOW
        }
        return severity_map.get(issue_type, Severity.MEDIUM)
    
    def _get_architecture_suggestion(self, issue_type: str) -> str:
        """Get fix suggestion for architecture issue type."""
        suggestions = {
            "god_class": "Split large class into smaller, focused classes following SRP.",
            "long_method": "Extract method into smaller functions with clear responsibilities.",
            "high_complexity": "Simplify control flow and reduce nesting levels.",
            "tight_coupling": "Use dependency injection and interfaces to reduce coupling.",
            "hardcoded_values": "Move values to configuration files or constants."
        }
        return suggestions.get(issue_type, "Improve architecture design")
    
    def _get_solid_description(self, principle: str) -> str:
        """Get description for SOLID principle violation."""
        descriptions = {
            "srp_violation": "Class has multiple responsibilities, violating Single Responsibility Principle.",
            "ocp_violation": "Code is not open for extension but closed for modification.",
            "lsp_violation": "Subtypes are not substitutable for their base types.",
            "isp_violation": "Interface contains methods that clients don't need.",
            "dip_violation": "High-level modules depend on low-level modules directly."
        }
        return descriptions.get(principle, "SOLID principle violation detected")
    
    def _get_solid_suggestion(self, principle: str) -> str:
        """Get suggestion for SOLID principle violation."""
        suggestions = {
            "srp_violation": "Split class responsibilities into separate classes.",
            "ocp_violation": "Use inheritance, interfaces, or composition for extensibility.",
            "lsp_violation": "Ensure derived classes can replace base classes without breaking functionality.",
            "isp_violation": "Split large interfaces into smaller, focused interfaces.",
            "dip_violation": "Depend on abstractions, not concrete implementations."
        }
        return suggestions.get(principle, "Follow SOLID principles")


class PythonArchitectureAnalyzer(ast.NodeVisitor):
    """AST visitor for Python-specific architecture analysis."""
    
    def __init__(self, file: CodeFile):
        self.file = file
        self.findings = []
        self.class_methods = {}
        self.function_lengths = {}
        self.complexity_scores = {}
    
    def visit_ClassDef(self, node):
        """Analyze class structure and responsibilities."""
        # Count methods in class
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        self.class_methods[node.name] = len(methods)
        
        # Check for God class (too many methods)
        if len(methods) > 20:
            self.findings.append(Finding(
                title="God Class",
                description=f"Class '{node.name}' has {len(methods)} methods, indicating too many responsibilities.",
                severity=Severity.HIGH,
                confidence=Confidence.HIGH,
                file_path=self.file.path,
                line_number=node.lineno,
                code_snippet=f"class {node.name}:",
                suggestion="Split class into smaller, focused classes following SRP.",
                category="architecture",
                rule_id="ARCH_GOD_CLASS"
            ))
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node):
        """Analyze function complexity and length."""
        # Calculate function length
        if hasattr(node, 'end_lineno'):
            length = node.end_lineno - node.lineno + 1
        else:
            length = 1  # Fallback
        
        self.function_lengths[node.name] = length
        
        # Check for long methods
        if length > 50:
            self.findings.append(Finding(
                title="Long Method",
                description=f"Method '{node.name}' is {length} lines long, making it hard to understand.",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                file_path=self.file.path,
                line_number=node.lineno,
                code_snippet=f"def {node.name}:",
                suggestion="Break method into smaller, focused functions.",
                category="architecture",
                rule_id="ARCH_LONG_METHOD"
            ))
        
        # Calculate cyclomatic complexity
        complexity = self._calculate_complexity(node)
        self.complexity_scores[node.name] = complexity
        
        if complexity > 10:
            self.findings.append(Finding(
                title="High Cyclomatic Complexity",
                description=f"Method '{node.name}' has complexity of {complexity}, making it difficult to test and maintain.",
                severity=Severity.MEDIUM,
                confidence=Confidence.HIGH,
                file_path=self.file.path,
                line_number=node.lineno,
                code_snippet=f"def {node.name}:",
                suggestion="Reduce complexity by simplifying control flow and extracting functions.",
                category="architecture",
                rule_id="ARCH_HIGH_COMPLEXITY"
            ))
        
        self.generic_visit(node)
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
