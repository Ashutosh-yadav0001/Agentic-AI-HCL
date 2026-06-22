from bgv_app.agents.definitions import AnalysisResult


def analyze_vendor_issue(candidate_name: str, vendor_outcome: str, vendor_remarks: str) -> AnalysisResult:
    outcome = vendor_outcome.strip().lower()
    remarks = vendor_remarks.strip() or "No vendor remarks were provided."

    if "red" in outcome or "fail" in outcome or "criminal" in remarks.lower():
        risk = "High"
        next_status = "hr_final_review"
    elif "missing" in outcome or "document" in remarks.lower():
        risk = "Medium"
        next_status = "awaiting_hr_review"
    elif "discrep" in outcome or "mismatch" in remarks.lower():
        risk = "Medium"
        next_status = "awaiting_hr_review"
    else:
        risk = "Low"
        next_status = "awaiting_hr_review"

    summary = (
        f"Vendor reported '{vendor_outcome}'. Key note: {remarks} "
        f"Recommended HR action: review the evidence, request clarification if needed, "
        f"and send the candidate a precise correction request."
    )
    candidate_email = (
        f"Dear {candidate_name},\n\n"
        "Thank you for submitting your background verification details. "
        f"Our verification partner needs clarification on the following item: {remarks}\n\n"
        "Please reply with the corrected information or upload the supporting document through the BGV form. "
        "Once received, we will send the updated details for re-verification.\n\n"
        "Regards,\nHR Team"
    )
    return AnalysisResult(
        risk_level=risk,
        summary=summary,
        candidate_email=candidate_email,
        next_status=next_status,
    )
