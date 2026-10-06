import logging
from bgv_app.agents.definitions import AnalysisResult
from bgv_app.config import get_settings

logger = logging.getLogger(__name__)


def classify_issue_details(outcome_text: str, remarks_text: str) -> tuple[str, str, int, str, list[str]]:
    """
    Classifies discrepancy into category, risk level, integrity score penalty,
    HR policy action, and itemized required evidence list.
    """
    combined = f"{outcome_text} {remarks_text}".lower()

    if any(k in combined for k in ["criminal", "court", "arrest", "fir", "felony", "police"]):
        category = "Adverse Legal / Judicial Record"
        risk = "Critical"
        score = 30
        policy = (
            "POLICY ALERT [SEC-4.8]: Put onboarding on immediate administrative freeze. "
            "Escalate case to Chief People Officer and Legal Compliance Directorate. "
            "Candidate must provide judicial certified clearance before any offer advancement."
        )
        evidence = [
            "Certified Court Order / Judicial Clearance Certificate",
            "Police Verification Report / No Objection Certificate",
            "Signed legal disclosure statement",
        ]
    elif any(k in combined for k in ["moonlight", "dual employ", "concurrent", "tenure overlap", "service overlap"]):
        category = "Dual Employment & Service Period Conflict"
        risk = "High"
        score = 55
        policy = (
            "POLICY ALERT [HR-3.2]: Cross-verify service records against EPFO Unified Portal. "
            "Examine Form 26AS for simultaneous salary credits across overlapping periods. "
            "Candidate must submit formal relieving letters confirming zero overlap."
        )
        evidence = [
            "EPFO Service History (Passbook PDF showing date of joining & exit)",
            "Form 26AS Tax Credit Statement for the overlapping financial years",
            "Official Relieving and Experience Letter on company letterhead",
        ]
    elif any(k in combined for k in ["fake", "unaccredited", "education", "degree", "university", "marksheet"]):
        category = "Educational Credential Inconsistency"
        risk = "High"
        score = 50
        policy = (
            "POLICY ALERT [EDU-2.1]: Verify institution accreditation against UGC/AICTE/National Board registries. "
            "Initiate direct registrar verification via institutional portal."
        )
        evidence = [
            "Original Degree Certificate (high-resolution scan)",
            "All semester consolidated marksheets / transcripts",
            "Institutional Student Enrollment ID / Roll Number",
        ]
    elif any(k in combined for k in ["address", "residence", "utility", "rental", "geo"]):
        category = "Residential Address Verification Mismatch"
        risk = "Medium"
        score = 75
        policy = (
            "POLICY NOTICE [OPS-1.4]: Secondary address proof required. "
            "Verify geo-tagging or request registered lease agreement / utility bill dated within 60 days."
        )
        evidence = [
            "Registered Rent/Lease Agreement (duly signed)",
            "Utility Bill (Electricity, Piped Gas, or Broadband) dated within the last 60 days",
            "Government ID showing current residence",
        ]
    elif any(k in combined for k in ["identity", "pan", "aadhaar", "passport", "dob", "name mismatch"]):
        category = "Identity Record Typographical Mismatch"
        risk = "Medium"
        score = 80
        policy = (
            "POLICY NOTICE [KYC-1.1]: Request name reconciliation affidavit or gazette notification if surname differed. "
            "Re-validate via national identity portal."
        )
        evidence = [
            "Clear scanned copy of Government Photo ID (Passport / Aadhaar / PAN)",
            "Name Change Affidavit or Gazette Notification (if applicable)",
        ]
    elif any(k in combined for k in ["missing", "incomplete", "unreadable", "blur"]):
        category = "Incomplete Documentation / Illegible Upload"
        risk = "Low"
        score = 85
        policy = (
            "POLICY NOTICE [OPS-1.1]: Request clean, high-resolution document resubmission within 48 hours."
        )
        evidence = [
            "High-resolution color scan of the requested document in PDF format",
        ]
    else:
        category = "General Discrepancy"
        risk = "Medium"
        score = 70
        policy = (
            "POLICY NOTICE [GEN-1.0]: Review submitted remarks with verification vendor and request clarification."
        )
        evidence = [
            "Official supporting document clarifying vendor remarks",
        ]

    return category, risk, score, policy, evidence


def generate_candidate_email(candidate_name: str, category: str, remarks: str, evidence: list[str]) -> str:
    checklist_str = "\n".join(f"  • {item}" for item in evidence)
    return (
        f"Dear {candidate_name},\n\n"
        f"Thank you for your active participation in our onboarding process. "
        f"Our background verification team has completed initial processing and identified an item that requires "
        f"your prompt clarification:\n\n"
        f"Item Category: {category}\n"
        f"Verification Note: {remarks}\n\n"
        f"To proceed with your verification, please upload the following supporting documents:\n"
        f"{checklist_str}\n\n"
        f"Please submit these documents via the secure BGV portal within 3 business days to prevent any "
        f"onboarding delays. If you have questions, reply directly to this email.\n\n"
        f"Warm regards,\n"
        f"Talent Acquisition & Compliance Team"
    )


def analyze_vendor_issue(candidate_name: str, vendor_outcome: str, vendor_remarks: str) -> AnalysisResult:
    """
    Standard vendor issue analysis with backward-compatible signature.
    """
    outcome = vendor_outcome.strip()
    remarks = vendor_remarks.strip() or "No vendor remarks were provided."

    if outcome.lower() == "clear":
        return AnalysisResult(
            risk_level="None",
            summary="Vendor completed all checks with zero discrepancies. Candidate cleared for onboarding.",
            candidate_email=f"Dear {candidate_name},\n\nWe are pleased to inform you that your background verification has completed successfully.",
            next_status="completed",
            integrity_score=100,
            discrepancy_category="Clean Record",
            policy_action="Proceed to onboarding and system account provisioning.",
            required_evidence=[],
        )

    category, risk, score, policy, evidence = classify_issue_details(outcome, remarks)

    next_status = "hr_final_review" if risk in ["High", "Critical"] else "awaiting_hr_review"

    summary = (
        f"[{category}] Vendor reported '{vendor_outcome}'. Findings: {remarks} | "
        f"Calculated Risk: {risk} (Integrity Score: {score}/100). {policy}"
    )

    candidate_email = generate_candidate_email(candidate_name, category, remarks, evidence)

    return AnalysisResult(
        risk_level=risk,
        summary=summary,
        candidate_email=candidate_email,
        next_status=next_status,
        integrity_score=score,
        discrepancy_category=category,
        policy_action=policy,
        required_evidence=evidence,
    )


def analyze_case_integrity(candidate_name: str, components: list) -> AnalysisResult:
    """
    Multi-component holistic analysis evaluating all 5 verification tracks.
    """
    if not components:
        return AnalysisResult(
            risk_level="Pending",
            summary="Verification tracks have not been initiated yet.",
            candidate_email="",
            next_status="offer_sent",
            integrity_score=100,
            discrepancy_category="Not Started",
            policy_action="Initiate verification components upon document receipt.",
            required_evidence=[],
        )

    score = 100
    discrepancies: list[str] = []
    red_flags: list[str] = []
    all_evidence: list[str] = []
    pending_count = 0

    for comp in components:
        st = getattr(comp, "status", comp.get("status") if isinstance(comp, dict) else "Pending")
        c_type = getattr(comp, "component_type", comp.get("component_type") if isinstance(comp, dict) else "Unknown")
        rem = getattr(comp, "remarks", comp.get("remarks") if isinstance(comp, dict) else "") or ""

        if st in ["Clear", "Verified Clear"]:
            continue
        elif st in ["Pending", "In Progress"]:
            score -= 5
            pending_count += 1
        elif st in ["Discrepancy", "Discrepancy Found"]:
            score -= 20
            discrepancies.append(f"{c_type}: {rem}")
            _, _, _, _, ev = classify_issue_details(c_type, rem)
            all_evidence.extend(ev)
        elif st in ["Red Flag", "Critical Flag", "Failed"]:
            score -= 45
            red_flags.append(f"{c_type}: {rem}")
            _, _, _, _, ev = classify_issue_details(c_type, rem)
            all_evidence.extend(ev)

    score = max(5, min(100, score))

    if red_flags:
        risk = "Critical"
        next_status = "hr_final_review"
        category = "Multiple High-Severity Red Flags"
        policy = "Immediate freeze on case. Requires Review by Head of HR and Corporate Legal."
    elif discrepancies:
        risk = "High" if score < 65 else "Medium"
        next_status = "awaiting_hr_review"
        category = "Verification Discrepancies Requiring Reconciliation"
        policy = "Request itemized candidate clarification and secondary verification documents."
    elif pending_count > 0:
        risk = "Low"
        next_status = "sent_to_vendor"
        category = "Verification In Progress"
        policy = "Awaiting final confirmation from external verification partner."
    else:
        risk = "None"
        next_status = "completed"
        category = "All Tracks Verified Clear"
        policy = "Candidate cleared. Issue formal clearance certificate."

    summary_items = []
    if red_flags:
        summary_items.append(f"CRITICAL FLAGS: {'; '.join(red_flags)}")
    if discrepancies:
        summary_items.append(f"DISCREPANCIES: {'; '.join(discrepancies)}")
    if not summary_items:
        summary_items.append("All components verified without adverse findings.")

    summary = f"Overall Integrity Score: {score}/100 ({risk} Risk). " + " | ".join(summary_items) + f" Policy: {policy}"

    candidate_email = ""
    if discrepancies or red_flags:
        items_desc = "\n".join(f"  • {d}" for d in (red_flags + discrepancies))
        candidate_email = generate_candidate_email(
            candidate_name,
            category,
            f"The following items need clarification:\n{items_desc}",
            list(set(all_evidence)) or ["Official clarification statement", "Supporting documentation"],
        )

    return AnalysisResult(
        risk_level=risk,
        summary=summary,
        candidate_email=candidate_email,
        next_status=next_status,
        integrity_score=score,
        discrepancy_category=category,
        policy_action=policy,
        required_evidence=list(set(all_evidence)),
    )
