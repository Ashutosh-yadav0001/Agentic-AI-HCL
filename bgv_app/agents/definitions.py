from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    risk_level: str
    summary: str
    candidate_email: str
    next_status: str
    integrity_score: int = 100
    discrepancy_category: str = "General Discrepancy"
    policy_action: str = ""
    required_evidence: list[str] = field(default_factory=list)
