"""
Security Agent for identifying security vulnerabilities and threats.
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple

from app.agents.base import BaseAgent, Finding, CodeFile
from app.core.config import Severity, Confidence


class SecurityAgent(BaseAgent):
    """
    Security-focused code review agent that identifies:
    - SQL injection vulnerabilities
    - XSS vulnerabilities
    - Authentication/authorization issues
    - Cryptographic problems
    - Input validation issues
    - OWASP Top 10 vulnerabilities
    """
    
    def __init__(self):
        super().__init__("security")
        
        # Security-specific patterns for quick detection
        self.vulnerability_patterns = {
            "sql_injection": [
                r"(execute|query|sql).*\+.*%s",
                r"cursor\.execute\([^,]+%",
                r"\.format\([^)]*\).*execute",
                r"f['\"][^'\"]*{[^}]*}[^'\"]*['\"].*execute"
            ],
            "xss": [
                r"innerHTML\s*=\s*[^;]*\+",
                r"document\.write\([^)]*\+",
                r"\.html\([^)]*\+",
                r"dangerouslySetInnerHTML"
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]{8,}['\"]",
                r"api[_-]?key\s*=\s*['\"][^'\"]{20,}['\"]",
                r"secret\s*=\s*['\"][^'\"]{16,}['\"]",
                r"token\s*=\s*['\"][^'\"]{20,}['\"]"
            ],
            "weak_crypto": [
                r"md5\(|MD5\(",
                r"sha1\(|SHA1\(",
                r"DES\(|des\(",
                r"Random\(\)\.next"
            ],
            "path_traversal": [
                r"open\([^)]*\.\./",
                r"readFile\([^)]*\.\./",
                r"include\([^)]*\.\./",
                r"require\([^)]*\.\./"
            ]
        }
    
    def _is_file_relevant(self, file: CodeFile) -> bool:
        """Security analysis is relevant for most code files."""
        # Skip binary files, images, and documentation
        skip_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.md', '.txt', '.log'}
        return not any(file.path.endswith(ext) for ext in skip_extensions)
    
    async def _perform_analysis(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """Perform security analysis on the given files."""
        findings = []
        total_tokens = 0
        
        # First, run pattern-based detection for quick wins
        for file in files:
            pattern_findings = self._analyze_patterns(file)
            findings.extend(pattern_findings)
        
        # Then, use LLM for deeper analysis on suspicious files
        suspicious_files = self._identify_suspicious_files(files)
        
        if suspicious_files:
            llm_findings, tokens = await self._analyze_with_llm(suspicious_files, context)
            findings.extend(llm_findings)
            total_tokens += tokens
        
        return findings, total_tokens
    
    def _analyze_patterns(self, file: CodeFile) -> List[Finding]:
        """Analyze file using predefined security patterns."""
        findings = []
        
        for vulnerability_type, patterns in self.vulnerability_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, file.content, re.IGNORECASE | re.MULTILINE)
                
                for match in matches:
                    line_number = file.content[:match.start()].count('\n') + 1
                    
                    finding = Finding(
                        title=f"Potential {vulnerability_type.replace('_', ' ').title()}",
                        description=self._get_vulnerability_description(vulnerability_type),
                        severity=self._get_vulnerability_severity(vulnerability_type),
                        confidence=Confidence.MEDIUM,  # Pattern-based detection has medium confidence
                        file_path=file.path,
                        line_number=line_number,
                        code_snippet=self._extract_code_snippet(file.content, line_number),
                        suggestion=self._get_vulnerability_suggestion(vulnerability_type),
                        category="security",
                        rule_id=f"sec_{vulnerability_type}"
                    )
                    findings.append(finding)
        
        return findings
    
    def _identify_suspicious_files(self, files: List[CodeFile]) -> List[CodeFile]:
        """Identify files that need deeper LLM analysis."""
        suspicious_files = []
        
        # Security-sensitive file patterns
        security_keywords = [
            'auth', 'login', 'password', 'crypto', 'encrypt', 'decrypt',
            'token', 'session', 'cookie', 'permission', 'role', 'admin',
            'sql', 'database', 'query', 'api', 'endpoint', 'route'
        ]
        
        for file in files:
            # Check file path for security-sensitive terms
            file_path_lower = file.path.lower()
            if any(keyword in file_path_lower for keyword in security_keywords):
                suspicious_files.append(file)
                continue
            
            # Check file content for security-sensitive imports/functions
            content_lower = file.content.lower()
            if any(keyword in content_lower for keyword in security_keywords):
                suspicious_files.append(file)
        
        # Limit to prevent excessive API calls
        return suspicious_files[:5]
    
    async def _analyze_with_llm(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> Tuple[List[Finding], int]:
        """Perform deep security analysis using LLM."""
        prompt = self._create_prompt(files, context)
        
        try:
            response, tokens = await self._call_llm(prompt)
            findings = self._parse_security_response(response, files)
            return findings, tokens
        except Exception as e:
            # Return empty findings if LLM call fails
            return [], 0
    
    def _create_prompt(self, files: List[CodeFile], context: Optional[Dict[str, Any]]) -> str:
        """Create security analysis prompt for LLM."""
        
        prompt = """You are a senior security engineer performing a comprehensive security review. 
Analyze the following code for security vulnerabilities, focusing on:

1. **Input Validation**: SQL injection, XSS, command injection, path traversal
2. **Authentication & Authorization**: Weak authentication, privilege escalation, session management
3. **Cryptography**: Weak algorithms, poor key management, insecure random number generation
4. **Data Protection**: Sensitive data exposure, insufficient encryption
5. **Error Handling**: Information disclosure through error messages
6. **Configuration Security**: Hardcoded secrets, insecure defaults
7. **OWASP Top 10**: All major web application security risks

For each vulnerability found, provide:
- **Title**: Brief description of the issue
- **Severity**: CRITICAL, HIGH, MEDIUM, LOW, INFO
- **Confidence**: VERY_HIGH, HIGH, MEDIUM, LOW, VERY_LOW
- **Line Number**: Specific line where the issue occurs
- **Description**: Detailed explanation of the vulnerability
- **Impact**: Potential consequences if exploited
- **Recommendation**: Specific steps to fix the issue

Format your response as JSON:
```json
{
  "findings": [
    {
      "title": "SQL Injection in User Query",
      "severity": "HIGH",
      "confidence": "HIGH",
      "file_path": "path/to/file.py",
      "line_number": 42,
      "description": "The user input is directly concatenated into SQL query without sanitization",
      "impact": "Attacker could execute arbitrary SQL commands, potentially accessing or modifying database",
      "recommendation": "Use parameterized queries or prepared statements",
      "code_snippet": "cursor.execute('SELECT * FROM users WHERE id = ' + user_id)"
    }
  ]
}
```

"""
        
        # Add file contents
        for i, file in enumerate(files):
            prompt += f"\n\n**File {i+1}: {file.path}**\n"
            prompt += f"Language: {file.language}\n"
            prompt += f"```{file.language}\n{file.content}\n```"
        
        # Add context if available
        if context:
            prompt += f"\n\n**Additional Context:**\n"
            if context.get('pr_number'):
                prompt += f"- Pull Request #{context['pr_number']}\n"
            if context.get('branch'):
                prompt += f"- Branch: {context['branch']}\n"
            if context.get('repository'):
                prompt += f"- Repository: {context['repository']}\n"
        
        return prompt
    
    def _parse_security_response(self, response: str, files: List[CodeFile]) -> List[Finding]:
        """Parse LLM response into Finding objects."""
        findings = []
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                return findings
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            for finding_data in data.get('findings', []):
                try:
                    finding = Finding(
                        title=finding_data.get('title', 'Security Issue'),
                        description=f"{finding_data.get('description', '')}. Impact: {finding_data.get('impact', 'Unknown impact')}",
                        severity=getattr(Severity, finding_data.get('severity', 'MEDIUM').upper()),
                        confidence=getattr(Confidence, finding_data.get('confidence', 'MEDIUM').upper()),
                        file_path=finding_data.get('file_path', ''),
                        line_number=finding_data.get('line_number'),
                        code_snippet=finding_data.get('code_snippet'),
                        suggestion=finding_data.get('recommendation'),
                        category="security",
                        rule_id="sec_llm_analysis"
                    )
                    findings.append(finding)
                except (AttributeError, ValueError) as e:
                    # Skip malformed findings
                    continue
        
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract issues from text
            findings = self._parse_text_response(response, files)
        
        return findings
    
    def _parse_text_response(self, response: str, files: List[CodeFile]) -> List[Finding]:
        """Fallback text parsing if JSON parsing fails."""
        findings = []
        
        # Simple text parsing as fallback
        lines = response.split('\n')
        current_finding = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('**') and 'vulnerability' in line.lower():
                if current_finding:
                    # Process previous finding
                    finding = self._create_finding_from_text(current_finding, files)
                    if finding:
                        findings.append(finding)
                current_finding = {'title': line.replace('**', '')}
            elif line.startswith('- Severity:'):
                current_finding['severity'] = line.replace('- Severity:', '').strip()
            elif line.startswith('- Line:'):
                try:
                    current_finding['line_number'] = int(line.replace('- Line:', '').strip())
                except ValueError:
                    pass
            elif line.startswith('- Description:'):
                current_finding['description'] = line.replace('- Description:', '').strip()
        
        # Process last finding
        if current_finding:
            finding = self._create_finding_from_text(current_finding, files)
            if finding:
                findings.append(finding)
        
        return findings
    
    def _create_finding_from_text(self, finding_data: Dict[str, Any], files: List[CodeFile]) -> Optional[Finding]:
        """Create Finding object from parsed text data."""
        try:
            return Finding(
                title=finding_data.get('title', 'Security Issue'),
                description=finding_data.get('description', 'Security vulnerability detected'),
                severity=getattr(Severity, finding_data.get('severity', 'MEDIUM').upper()),
                confidence=Confidence.MEDIUM,
                file_path=files[0].path if files else '',
                line_number=finding_data.get('line_number'),
                category="security",
                rule_id="sec_text_analysis"
            )
        except (AttributeError, ValueError):
            return None
    
    def _get_vulnerability_description(self, vulnerability_type: str) -> str:
        """Get description for vulnerability type."""
        descriptions = {
            "sql_injection": "Potential SQL injection vulnerability detected. User input appears to be directly concatenated into SQL queries.",
            "xss": "Potential Cross-Site Scripting (XSS) vulnerability. User input may be rendered without proper sanitization.",
            "hardcoded_secrets": "Hardcoded secrets detected. Credentials should be stored in environment variables or secure configuration.",
            "weak_crypto": "Weak cryptographic algorithm detected. Consider using stronger, modern algorithms.",
            "path_traversal": "Potential path traversal vulnerability. File paths should be validated to prevent directory traversal attacks."
        }
        return descriptions.get(vulnerability_type, "Security vulnerability detected.")
    
    def _get_vulnerability_severity(self, vulnerability_type: str) -> Severity:
        """Get severity for vulnerability type."""
        severities = {
            "sql_injection": Severity.HIGH,
            "xss": Severity.HIGH,
            "hardcoded_secrets": Severity.MEDIUM,
            "weak_crypto": Severity.MEDIUM,
            "path_traversal": Severity.HIGH
        }
        return severities.get(vulnerability_type, Severity.MEDIUM)
    
    def _get_vulnerability_suggestion(self, vulnerability_type: str) -> str:
        """Get remediation suggestion for vulnerability type."""
        suggestions = {
            "sql_injection": "Use parameterized queries or prepared statements instead of string concatenation.",
            "xss": "Sanitize and escape user input before rendering. Use templating engines with auto-escaping.",
            "hardcoded_secrets": "Move secrets to environment variables or a secure configuration management system.",
            "weak_crypto": "Use strong, modern cryptographic algorithms like AES-256, SHA-256, or bcrypt.",
            "path_traversal": "Validate and sanitize file paths. Use whitelist validation for allowed directories."
        }
        return suggestions.get(vulnerability_type, "Review and remediate the security issue.")
    
    def _extract_code_snippet(self, content: str, line_number: int, context_lines: int = 2) -> str:
        """Extract code snippet around the specified line."""
        lines = content.split('\n')
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        snippet_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_number - 1 else "    "
            snippet_lines.append(f"{prefix}{lines[i]}")
        
        return '\n'.join(snippet_lines)
