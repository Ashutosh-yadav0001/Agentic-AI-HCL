from fastapi import APIRouter

from bgv_app.agents.runner import analyze_vendor_issue

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/preview")
def preview(candidate_name: str = "Candidate", outcome: str = "Discrepancy", remarks: str = "Address mismatch"):
    return analyze_vendor_issue(candidate_name, outcome, remarks)
