"""Base class for all agents."""

from typing import List, Tuple
from ....models.finding import Severity
from ....models.finding import Finding


class BaseAgent:
    name = "base"

    def analyze(self, changed_files: List[Tuple[str, List[str]]]) -> List[dict]:
        """Override to implement analysis.  Returns a list of finding dicts."""
        raise NotImplementedError

    def build_finding(self, file_path: str, start_line: int, end_line: int, severity: Severity, title: str, description: str, suggested_fix: str | None = None, confidence: float | None = None, rule_id: str | None = None) -> dict:
        return {
            "file_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "severity": severity.value if isinstance(severity, Severity) else severity,
            "title": title,
            "description": description,
            "suggested_fix": suggested_fix,
            "confidence": confidence or 0.8,
            "rule_id": rule_id or self.name,
        }