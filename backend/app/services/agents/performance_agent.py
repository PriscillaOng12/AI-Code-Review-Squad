"""Performance agent flags inefficient patterns."""

from typing import List, Tuple
from .base import BaseAgent
from ....models.finding import Severity


class PerformanceAgent(BaseAgent):
    name = "performance"

    def analyze(self, changed_files: List[Tuple[str, List[str]]]) -> List[dict]:
        findings: List[dict] = []
        for file_path, lines in changed_files:
            for idx, line in enumerate(lines, start=1):
                if "time.sleep(" in line:
                    findings.append(self.build_finding(
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        severity=Severity.low,
                        title="Potential blocking sleep",
                        description="Use of sleep can block execution and slow down performance.",
                        suggested_fix="Avoid sleep in production code or use async equivalents.",
                        rule_id="PERF001",
                    ))
                if "range(" in line and ".__len__" in line:
                    findings.append(self.build_finding(
                        file_path=file_path,
                        start_line=idx,
                        end_line=idx,
                        severity=Severity.low,
                        title="Inefficient loop",
                        description="Use direct iteration over the collection instead of range(len(x)).",
                        suggested_fix="for item in x:",
                        rule_id="PERF002",
                    ))
        return findings