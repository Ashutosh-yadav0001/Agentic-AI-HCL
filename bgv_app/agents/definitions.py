from dataclasses import dataclass


@dataclass
class AnalysisResult:
    risk_level: str
    summary: str
    candidate_email: str
    next_status: str
