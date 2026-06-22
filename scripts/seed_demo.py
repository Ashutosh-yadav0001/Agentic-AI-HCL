import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bgv_app.agents.runner import analyze_vendor_issue
from bgv_app.database import SessionLocal, init_db
from bgv_app.models import BGVCase, Candidate, Document, VendorCheck, WorkflowEvent


def event(case: BGVCase, event_type: str, detail: str) -> WorkflowEvent:
    return WorkflowEvent(case=case, event_type=event_type, detail=detail)


def clear_existing() -> None:
    db = SessionLocal()
    try:
        db.query(WorkflowEvent).delete()
        db.query(VendorCheck).delete()
        db.query(Document).delete()
        db.query(BGVCase).delete()
        db.query(Candidate).delete()
        db.commit()
    finally:
        db.close()


def seed() -> None:
    init_db()
    clear_existing()
    db = SessionLocal()
    try:
        anita = Candidate(name="Anita Sharma", email="anita.sharma@example.com", phone="+91 98765 43210")
        rohan = Candidate(name="Rohan Mehta", email="rohan.mehta@example.com", phone="+91 91234 56780")
        priya = Candidate(name="Priya Nair", email="priya.nair@example.com", phone="+91 99887 76655")
        db.add_all([anita, rohan, priya])
        db.flush()

        clear_case = BGVCase(
            candidate=anita,
            vendor_name="Demo Verify",
            status="completed",
            offer_accepted=True,
            risk_level="None",
            final_decision="Approved",
        )
        clear_case.documents.append(
            Document(document_type="Identity Proof", file_name="aadhaar.pdf", file_url="https://example.com/aadhaar.pdf")
        )
        clear_case.vendor_checks.append(
            VendorCheck(vendor_outcome="Clear", vendor_remarks="Identity, address, and employment checks completed.")
        )
        clear_case.events.extend(
            [
                event(clear_case, "offer_email", "Offer email sent with acceptance form."),
                event(clear_case, "bgv_form_email", "BGV form sent after candidate accepted."),
                event(clear_case, "sent_to_vendor", "Candidate details sent to Demo Verify."),
                event(clear_case, "vendor_clear", "Vendor cleared all checks."),
            ]
        )

        medium_analysis = analyze_vendor_issue(
            rohan.name,
            "Discrepancy",
            "Address proof does not match the current address submitted by the candidate.",
        )
        medium_case = BGVCase(
            candidate=rohan,
            vendor_name="Demo Verify",
            status="awaiting_hr_review",
            offer_accepted=True,
            risk_level=medium_analysis.risk_level,
            ai_summary=medium_analysis.summary,
            ai_draft_email=medium_analysis.candidate_email,
        )
        medium_case.documents.append(
            Document(document_type="Address Proof", file_name="utility-bill.pdf", file_url="https://example.com/bill.pdf")
        )
        medium_case.vendor_checks.append(
            VendorCheck(
                vendor_outcome="Discrepancy",
                vendor_remarks="Address proof does not match the current address submitted by the candidate.",
            )
        )
        medium_case.events.extend(
            [
                event(medium_case, "offer_email", "Offer email sent with acceptance form."),
                event(medium_case, "sent_to_vendor", "Candidate details sent to Demo Verify."),
                event(medium_case, "vendor_issue", medium_analysis.summary),
                event(medium_case, "ai_draft_ready", "AI drafted a clarification email for HR review."),
            ]
        )

        high_analysis = analyze_vendor_issue(
            priya.name,
            "Red Flag",
            "Vendor found an unresolved employment verification concern requiring HR decision.",
        )
        high_case = BGVCase(
            candidate=priya,
            vendor_name="TrustCheck",
            status="hr_final_review",
            offer_accepted=True,
            risk_level=high_analysis.risk_level,
            ai_summary=high_analysis.summary,
            ai_draft_email=high_analysis.candidate_email,
            hr_notes="Escalated to HR lead for final decision.",
        )
        high_case.documents.append(
            Document(document_type="Employment Proof", file_name="experience-letter.pdf", file_url="https://example.com/exp.pdf")
        )
        high_case.vendor_checks.append(
            VendorCheck(
                vendor_outcome="Red Flag",
                vendor_remarks="Vendor found an unresolved employment verification concern requiring HR decision.",
            )
        )
        high_case.events.extend(
            [
                event(high_case, "offer_email", "Offer email sent with acceptance form."),
                event(high_case, "sent_to_vendor", "Candidate details sent to TrustCheck."),
                event(high_case, "vendor_issue", high_analysis.summary),
                event(high_case, "hr_escalation", "High-risk case escalated for final HR decision."),
            ]
        )

        db.add_all([clear_case, medium_case, high_case])
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seeded hackathon demo data.")
