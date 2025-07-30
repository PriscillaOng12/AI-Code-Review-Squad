"""
SecurityAgent - Identifies security vulnerabilities and threats.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from app.agents.base import BaseAgent, Finding, CodeFile
from app.core.config import Severity, Confidence


class SecurityAgent(BaseAgent):
    """Agent specialized in security vulnerability detection."""
    
    def __init__(self):
        super().__init__("security")
        
        # Security patterns to check
        self.vulnerability_patterns = {
            "sql_injection": [
                r"(?i)execute\s*\(\s*['\"].*\+.*['\"]",
                r"(?i)query\s*\(\s*['\"].*\+.*['\"]",
                r"(?i)cursor\.execute\s*\(\s*['\"].*%.*['\"]",
                r"(?i)SELECT.*WHERE.*=.*\+",
            ],
            "xss": [
                r"innerHTML\s*=\s*.*\+",
                r"document\.write\s*\(\s*.*\+",
                r"eval\s*\(\s*.*\+",
                r"setTimeout\s*\(\s*['\"].*\+.*['\"]",
            ],
            "hardcoded_secrets": [
                r"(?i)(password|pwd|secret|key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
                r"(?i)api[_-]?key\s*[=:]\s*['\"][a-zA-Z0-9]{20,}['\"]",
                r"(?i)(access|refresh)[_-]?token\s*[=:]\s*['\"][^'\"]{10,}['\"]",
            ],
            "insecure_random": [
                r"(?i)random\.random\(\)",
                r"(?i)Math\.random\(\)",
                r"(?i)rand\(\)",
            ],
            "path_traversal": [
                r"open\s*\(\s*.*\+.*['\"]",
                r"file\s*\(\s*.*\+.*['\"]",
                r"readFile\s*\(\s*.*\+.*['\"]",
            ],
        }
    
    def _filter_relevant_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Filter files relevant for security analysis."""
        # Security analysis is relevant for most code files
        relevant_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', '.go', '.rs',
            '.php', '.rb', '.swift', '.kt', '.scala', '.sql', '.sh', '.bash'
        }
        
        return [
            f for f in files 
            if any(f.path.endswith(ext) for ext in relevant_extensions)
            or 'dockerfile' in f.path.lower()
            or 'config' in f.path.lower()
        ]
    
    async def _perform_analysis(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """Perform security analysis on code files."""
        findings = []
        total_tokens = 0
        
        # First, run pattern-based detection
        for file in files:
            pattern_findings = self._detect_security_patterns(file)
            findings.extend(pattern_findings)
        
        # Then run LLM-based analysis for deeper insights
        for file in files:
            if len(file.content) > 10000:  # Skip very large files for LLM analysis
                continue
                
            prompt = self._create_prompt([file], context)
            try:
                response, tokens = await self._call_llm(prompt)
                total_tokens += tokens
                
                llm_findings = self._parse_llm_response(response, file)
                findings.extend(llm_findings)
            except Exception as e:
                # Continue with pattern-based findings if LLM fails
                print(f"LLM analysis failed for {file.path}: {e}")
        
        return findings, total_tokens
    
    def _detect_security_patterns(self, file: CodeFile) -> List[Finding]:
        """Detect security issues using regex patterns."""
        findings = []
        lines = file.content.split('\n')
        
        for vuln_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line):
                        findings.append(Finding(
                            title=f"Potential {vuln_type.replace('_', ' ').title()}",
                            description=self._get_vulnerability_description(vuln_type),
                            severity=self._get_vulnerability_severity(vuln_type),
                            confidence=Confidence.HIGH,
                            file_path=file.path,
                            line_number=line_num,
                            code_snippet=line.strip(),
                            suggestion=self._get_vulnerability_suggestion(vuln_type),
                            category="security",
                            rule_id=f"SEC_{vuln_type.upper()}"
                        ))
        
        return findings
    
    def _create_prompt(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> str:
        """Create security analysis prompt for LLM."""
        file_content = files[0].content if files else ""
        file_path = files[0].path if files else "unknown"
        language = files[0].language if files else "unknown"
        
        prompt = f"""
You are a senior cybersecurity expert conducting a thorough security review of code.
Analyze the following {language} code for security vulnerabilities and threats.

File: {file_path}
Language: {language}

Focus on identifying:
1. OWASP Top 10 vulnerabilities
2. Injection attacks (SQL, XSS, Command injection)
3. Authentication and authorization flaws
4. Cryptographic issues
5. Insecure configurations
6. Sensitive data exposure
7. Security misconfigurations
8. Cross-Site Request Forgery (CSRF)
9. Using components with known vulnerabilities
10. Insufficient logging and monitoring

For each issue found, provide:
- Specific vulnerability type
- Severity level (CRITICAL, HIGH, MEDIUM, LOW)
- Line number where issue occurs
- Brief explanation of the risk
- Recommended fix

Code to analyze:
```{language}
{file_content}
```

Format your response as a structured list:
FINDING: [Vulnerability Type]
SEVERITY: [CRITICAL/HIGH/MEDIUM/LOW]
LINE: [Line Number]
DESCRIPTION: [Risk explanation]
SUGGESTION: [How to fix]
---
"""
        return prompt
    
    def _parse_llm_response(self, response: str, file: CodeFile) -> List[Finding]:
        """Parse LLM response into Finding objects."""
        findings = []
        
        # Split response into individual findings
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
                    elif key == 'DESCRIPTION':
                        finding_data['description'] = value
                    elif key == 'SUGGESTION':
                        finding_data['suggestion'] = value
            
            # Create finding if we have minimum required data
            if 'title' in finding_data and 'description' in finding_data:
                findings.append(Finding(
                    title=finding_data.get('title', 'Security Issue'),
                    description=finding_data.get('description', 'Security vulnerability detected'),
                    severity=getattr(Severity, finding_data.get('severity', 'MEDIUM'), Severity.MEDIUM),
                    confidence=Confidence.HIGH,
                    file_path=file.path,
                    line_number=finding_data.get('line_number', 1),
                    code_snippet=self._get_code_snippet(file.content, finding_data.get('line_number', 1)),
                    suggestion=finding_data.get('suggestion', 'Review and fix security issue'),
                    category="security",
                    rule_id="SEC_LLM_DETECTED"
                ))
        
        return findings
    
    def _get_code_snippet(self, content: str, line_number: int) -> str:
        """Extract code snippet around the specified line."""
        lines = content.split('\n')
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1].strip()
        return ""
    
    def _get_vulnerability_description(self, vuln_type: str) -> str:
        """Get description for vulnerability type."""
        descriptions = {
            "sql_injection": "Potential SQL injection vulnerability. User input may be directly concatenated into SQL queries.",
            "xss": "Potential Cross-Site Scripting (XSS) vulnerability. User input may be directly inserted into DOM.",
            "hardcoded_secrets": "Hardcoded credentials or secrets found in source code. This poses a security risk.",
            "insecure_random": "Use of insecure random number generator. This may be predictable for cryptographic purposes.",
            "path_traversal": "Potential path traversal vulnerability. User input may access unauthorized files."
        }
        return descriptions.get(vuln_type, "Security vulnerability detected")
    
    def _get_vulnerability_severity(self, vuln_type: str) -> Severity:
        """Get severity level for vulnerability type."""
        severity_map = {
            "sql_injection": Severity.CRITICAL,
            "xss": Severity.HIGH,
            "hardcoded_secrets": Severity.HIGH,
            "insecure_random": Severity.MEDIUM,
            "path_traversal": Severity.HIGH
        }
        return severity_map.get(vuln_type, Severity.MEDIUM)
    
    def _get_vulnerability_suggestion(self, vuln_type: str) -> str:
        """Get fix suggestion for vulnerability type."""
        suggestions = {
            "sql_injection": "Use parameterized queries or prepared statements. Never concatenate user input directly into SQL.",
            "xss": "Sanitize and escape user input before inserting into DOM. Use Content Security Policy (CSP).",
            "hardcoded_secrets": "Move credentials to environment variables or secure configuration management.",
            "insecure_random": "Use cryptographically secure random number generators (e.g., secrets module in Python).",
            "path_traversal": "Validate and sanitize file paths. Use allowlists for permitted files/directories."
        }
        return suggestions.get(vuln_type, "Review and apply security best practices")
