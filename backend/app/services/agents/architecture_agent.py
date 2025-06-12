"""Architecture agent flags large files or module boundaries."""

from typing import List, Tuple
from .base import BaseAgent
from ....models.finding import Severity


class ArchitectureAgent(BaseAgent):
    name = "architecture"

    def analyze(self, changed_files: List[Tuple[str, List[str]]]) -> List[dict]:
        findings: List[dict] = []
        for file_path, lines in changed_files:
            if len(lines) > 200:
                findings.append(self.build_finding(
                    file_path=file_path,
                    start_line=1,
                    end_line=len(lines),
                    severity=Severity.info,
                    title="Large file",
                    description="File exceeds 200 lines.  Consider refactoring into smaller modules.",
                    suggested_fix="Break the file into logically cohesive modules.",
                    rule_id="ARCH001",
                ))
        return findings