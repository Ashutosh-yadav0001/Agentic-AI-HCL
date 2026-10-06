from fastapi import APIRouter

from bgv_app.agents.runner import analyze_case_integrity, analyze_vendor_issue

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/preview")
def preview(candidate_name: str = "Candidate", outcome: str = "Discrepancy", remarks: str = "Address mismatch"):
    return analyze_vendor_issue(candidate_name, outcome, remarks)


@router.get("/preview-components")
def preview_components(candidate_name: str = "Candidate"):
    dummy_components = [
        {"component_type": "Identity Verification", "status": "Clear", "remarks": "DigiLocker verified"},
        {"component_type": "Employment History", "status": "Discrepancy Found", "remarks": "Tenure mismatch of 2 months"},
        {"component_type": "Education Verification", "status": "Clear", "remarks": "University verified"},
        {"component_type": "Criminal Record Check", "status": "Clear", "remarks": "Clean judicial record"},
        {"component_type": "Address Verification", "status": "In Progress", "remarks": "Geo-tag pending"},
    ]
    return analyze_case_integrity(candidate_name, dummy_components)
