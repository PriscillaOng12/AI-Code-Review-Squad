"""Logic agent flags TODO and FIXME markers."""

from typing import List, Tuple
from .base import BaseAgent
from ....models.finding import Severity


class LogicAgent(BaseAgent):
    name = "logic"

    def analyze(self, changed_files: List[Tuple[str, List[str]]]) -> List[dict]:
        findings: List[dict] = []
        for file_path, lines in changed_files:
            for idx, line in enumerate(lines, start=1):
                if "TODO" in line or "FIXME" in line:
                    findings.append(self.build_finding(
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        severity=Severity.medium,
                        title="Todo/Fixme comment present",
                        description="Leftover TODO or FIXME markers should be addressed before merging.",
                        suggested_fix="Address the TODO or remove the comment.",
                        rule_id="LOGIC001",
                    ))
        return findings