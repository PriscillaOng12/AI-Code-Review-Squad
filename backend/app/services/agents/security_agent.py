"""Security agent looks for potentially dangerous patterns in code."""

from typing import List, Tuple
from .base import BaseAgent
from ....models.finding import Severity


class SecurityAgent(BaseAgent):
    name = "security"

    def analyze(self, changed_files: List[Tuple[str, List[str]]]) -> List[dict]:
        findings: List[dict] = []
        for file_path, lines in changed_files:
            for idx, line in enumerate(lines, start=1):
                lower = line.lower()
                if "password" in lower or "exec(" in lower or "eval(" in lower:
                    findings.append(self.build_finding(
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        severity=Severity.high,
                        title="Potential security issue",
                        description=f"Suspicious code detected: '{line.strip()}'",
                        suggested_fix="Review the use of sensitive functions or hardcoded secrets.",
                        rule_id="SEC001",
                    ))
        return findings