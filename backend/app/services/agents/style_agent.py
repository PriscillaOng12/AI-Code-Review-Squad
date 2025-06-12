"""Style agent enforces basic formatting rules."""

from typing import List, Tuple
from .base import BaseAgent
from ....models.finding import Severity


class StyleAgent(BaseAgent):
    name = "style"

    def analyze(self, changed_files: List[Tuple[str, List[str]]]) -> List[dict]:
        findings: List[dict] = []
        for file_path, lines in changed_files:
            for idx, line in enumerate(lines, start=1):
                if len(line) > 120:
                    findings.append(self.build_finding(
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        severity=Severity.low,
                        title="Line too long",
                        description="Lines should not exceed 120 characters.",
                        suggested_fix="Break the line into shorter statements.",
                        rule_id="STYLE001",
                    ))
        return findings