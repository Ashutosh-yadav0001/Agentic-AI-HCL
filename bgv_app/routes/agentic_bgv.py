from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from bgv_app import models, schemas
from bgv_app.agents.runner import analyze_case_integrity, analyze_vendor_issue
from bgv_app.database import get_db
from bgv_app.integrations.gmail import send_email
from bgv_app.integrations.microsoft_forms import bgv_form_url, offer_form_url

router = APIRouter(prefix="/agentic-bgv", tags=["agentic-bgv"])

DEFAULT_COMPONENTS = [
    ("Identity Verification", "Pending", "Low", "Government photo ID and civil registry check"),
    ("Employment History", "Pending", "Low", "Tenure, role verification, and relieving letter authenticity"),
    ("Education Verification", "Pending", "Low", "Highest degree and accreditation check with university"),
    ("Criminal Record Check", "Pending", "Low", "National law enforcement and court civil/criminal check"),
    ("Address Verification", "Pending", "Low", "Permanent and current residence verification"),
]


def get_case_or_404(case_id: int, db: Session) -> models.BGVCase:
    case = (
        db.query(models.BGVCase)
        .options(
            joinedload(models.BGVCase.candidate),
            joinedload(models.BGVCase.documents),
            joinedload(models.BGVCase.vendor_checks),
            joinedload(models.BGVCase.events),
            joinedload(models.BGVCase.components),
        )
        .filter(models.BGVCase.id == case_id)
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail="BGV case not found")
    return case


def add_event(db: Session, case: models.BGVCase, event_type: str, detail: str) -> None:
    db.add(models.WorkflowEvent(case=case, event_type=event_type, detail=detail))


def recalculate_case_integrity(db: Session, case: models.BGVCase) -> None:
    """Recalculates the case integrity score and risk level based on components."""
    if not case.components:
        return
    res = analyze_case_integrity(case.candidate.name, case.components)
    case.integrity_score = res.integrity_score
    case.risk_level = res.risk_level
    if res.summary and res.risk_level != "Pending":
        case.ai_summary = res.summary
    if res.candidate_email:
        case.ai_draft_email = res.candidate_email


@router.post("/cases", response_model=schemas.CaseRead)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    candidate = db.get(models.Candidate, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    case = models.BGVCase(
        candidate=candidate,
        vendor_name=payload.vendor_name,
        status="offer_sent",
        integrity_score=100,
    )
    db.add(case)
    db.flush()

    # Initialize 5 standard verification tracks
    for c_type, c_status, c_sev, c_rem in DEFAULT_COMPONENTS:
        case.components.append(
            models.VerificationComponent(
                component_type=c_type,
                status=c_status,
                severity=c_sev,
                remarks=c_rem,
            )
        )

    email = send_email(
        candidate.email,
        "Offer released - response requested",
        f"Dear {candidate.name}, please accept or decline your offer here: {offer_form_url()}",
    )
    add_event(db, case, "offer_email", f"Demo email queued to {email.to}: {email.subject}")
    add_event(db, case, "tracks_initialized", "5 standard BGV verification tracks initialized.")
    db.commit()
    return get_case_or_404(case.id, db)


@router.post("/cases/{case_id}/offer-response", response_model=schemas.CaseRead)
def record_offer_response(case_id: int, payload: schemas.OfferResponse, db: Session = Depends(get_db)):
    case = get_case_or_404(case_id, db)
    case.offer_accepted = payload.accepted
    if not payload.accepted:
        case.status = "closed_offer_declined"
        add_event(db, case, "offer_declined", "Candidate declined the offer. BGV not started.")
    else:
        case.status = "bgv_form_sent"
        email = send_email(
            case.candidate.email,
            "Background verification details requested",
            f"Dear {case.candidate.name}, please submit your BGV details here: {bgv_form_url()}",
        )
        add_event(db, case, "bgv_form_email", f"Demo email queued to {email.to}: {email.subject}")
    db.commit()
    return get_case_or_404(case_id, db)


@router.post("/cases/{case_id}/documents", response_model=schemas.CaseRead)
def add_document(case_id: int, payload: schemas.DocumentCreate, db: Session = Depends(get_db)):
    case = get_case_or_404(case_id, db)
    db.add(models.Document(case=case, **payload.model_dump()))
    case.status = "sent_to_vendor"

    # Advance corresponding component status to In Progress
    doc_type_lower = payload.document_type.lower()
    for comp in case.components:
        if (
            ("identity" in doc_type_lower and "Identity" in comp.component_type)
            or ("address" in doc_type_lower and "Address" in comp.component_type)
            or ("degree" in doc_type_lower or "education" in doc_type_lower and "Education" in comp.component_type)
            or ("experience" in doc_type_lower or "relieving" in doc_type_lower and "Employment" in comp.component_type)
        ):
            if comp.status == "Pending":
                comp.status = "In Progress"

    add_event(db, case, "document_received", f"{payload.document_type}: {payload.file_name}")
    add_event(db, case, "sent_to_vendor", f"Details sent to {case.vendor_name}")
    db.commit()
    return get_case_or_404(case_id, db)


@router.post("/cases/{case_id}/vendor-status", response_model=schemas.CaseRead)
def submit_vendor_status(case_id: int, payload: schemas.VendorStatusCreate, db: Session = Depends(get_db)):
    case = get_case_or_404(case_id, db)
    db.add(models.VendorCheck(case=case, **payload.model_dump()))
    outcome = payload.vendor_outcome.strip().lower()
    if outcome == "clear":
        case.status = "completed"
        case.risk_level = "None"
        case.integrity_score = 100
        case.final_decision = "Approved"
        for comp in case.components:
            comp.status = "Verified Clear"
            comp.severity = "None"
            comp.verified_at = datetime.utcnow()
        add_event(db, case, "vendor_clear", payload.vendor_remarks or "Vendor cleared the case.")
        send_email(case.candidate.email, "BGV completed", "Your background verification has been completed.")
    else:
        analysis = analyze_vendor_issue(case.candidate.name, payload.vendor_outcome, payload.vendor_remarks)
        case.status = analysis.next_status
        case.risk_level = analysis.risk_level
        case.integrity_score = analysis.integrity_score
        case.ai_summary = analysis.summary
        case.ai_draft_email = analysis.candidate_email

        # Mark relevant component
        for comp in case.components:
            if any(term in comp.component_type.lower() for term in payload.vendor_remarks.lower().split() if len(term) > 4):
                comp.status = "Discrepancy Found" if analysis.risk_level != "Critical" else "Critical Flag"
                comp.remarks = payload.vendor_remarks
                comp.severity = analysis.risk_level

        add_event(db, case, "vendor_issue", analysis.summary)
    db.commit()
    return get_case_or_404(case_id, db)


@router.post("/cases/{case_id}/components/{component_id}", response_model=schemas.CaseRead)
def update_component(
    case_id: int,
    component_id: int,
    payload: schemas.VerificationComponentUpdate,
    db: Session = Depends(get_db),
):
    case = get_case_or_404(case_id, db)
    comp = next((c for c in case.components if c.id == component_id), None)
    if not comp:
        raise HTTPException(status_code=404, detail="Component not found in this case")

    comp.status = payload.status
    comp.severity = payload.severity
    comp.remarks = payload.remarks
    if payload.status in ["Clear", "Verified Clear"]:
        comp.verified_at = datetime.utcnow()

    recalculate_case_integrity(db, case)
    add_event(
        db,
        case,
        "component_updated",
        f"Track [{comp.component_type}] updated to '{comp.status}' with severity '{comp.severity}'. Note: {comp.remarks}",
    )
    db.commit()
    return get_case_or_404(case_id, db)


@router.post("/cases/{case_id}/simulate-checks", response_model=schemas.CaseRead)
def simulate_component_checks(
    case_id: int,
    scenario: str = "discrepancy",  # 'clear', 'discrepancy', 'red_flag'
    db: Session = Depends(get_db),
):
    case = get_case_or_404(case_id, db)
    now = datetime.utcnow()

    if scenario == "clear":
        for c in case.components:
            c.status = "Verified Clear"
            c.severity = "None"
            c.verified_at = now
            c.remarks = f"{c.component_type} verified successfully with zero adverse findings."
        case.status = "completed"
        case.final_decision = "Approved"
        case.risk_level = "None"
        case.integrity_score = 100
        case.ai_summary = "All 5 verification tracks verified clear. Candidate recommended for final onboarding."
        add_event(db, case, "simulation_complete", "Simulated automated check: All tracks verified clear.")
    elif scenario == "red_flag":
        for c in case.components:
            if "Employment" in c.component_type:
                c.status = "Critical Flag"
                c.severity = "Critical"
                c.remarks = "Concurrent dual employment flagged on EPFO records during active tenure."
            elif "Criminal" in c.component_type:
                c.status = "Critical Flag"
                c.severity = "Critical"
                c.remarks = "Adverse civil litigation record requiring HR legal review."
            else:
                c.status = "Verified Clear"
                c.severity = "None"
                c.verified_at = now
        recalculate_case_integrity(db, case)
        add_event(db, case, "simulation_complete", "Simulated automated check: Critical flags detected in employment & legal checks.")
    else:  # discrepancy
        for c in case.components:
            if "Address" in c.component_type:
                c.status = "Discrepancy Found"
                c.severity = "Medium"
                c.remarks = "Address proof mismatch: utility bill does not match candidate's declared residence."
            elif "Employment" in c.component_type:
                c.status = "Discrepancy Found"
                c.severity = "Medium"
                c.remarks = "Relieving date off by 45 days compared to HR reference."
            else:
                c.status = "Verified Clear"
                c.severity = "None"
                c.verified_at = now
        recalculate_case_integrity(db, case)
        add_event(db, case, "simulation_complete", "Simulated automated check: Address & Employment discrepancies flagged.")

    db.commit()
    return get_case_or_404(case_id, db)


@router.post("/cases/{case_id}/hr-review", response_model=schemas.CaseRead)
def hr_review(case_id: int, payload: schemas.HRReview, db: Session = Depends(get_db)):
    case = get_case_or_404(case_id, db)
    case.hr_notes = payload.reviewer_notes
    if payload.final_decision:
        case.final_decision = payload.final_decision
        case.status = "final_decision_updated"
        add_event(db, case, "final_decision", f"{payload.final_decision}: {payload.reviewer_notes}")
    elif payload.approved:
        case.status = "awaiting_candidate_response"
        add_event(db, case, "hr_approved_email", payload.reviewer_notes or "HR approved AI draft.")
        send_email(case.candidate.email, "BGV clarification requested", case.ai_draft_email or "")
    else:
        case.status = "draft_changes_requested"
        case.ai_draft_email = (case.ai_draft_email or "") + f"\n\nHR requested changes: {payload.reviewer_notes}"
        add_event(db, case, "draft_changes_requested", payload.reviewer_notes)
    db.commit()
    return get_case_or_404(case_id, db)


@router.post("/cases/{case_id}/candidate-response", response_model=schemas.CaseRead)
def candidate_response(case_id: int, payload: schemas.CandidateResponse, db: Session = Depends(get_db)):
    case = get_case_or_404(case_id, db)
    case.candidate_response = payload.candidate_response
    case.status = "reverification_sent"
    add_event(db, case, "candidate_response", payload.candidate_response)
    add_event(db, case, "reverification_sent", f"Updated details sent to {case.vendor_name}")
    db.commit()
    return get_case_or_404(case_id, db)


@router.get("/cases", response_model=list[schemas.CaseRead])
def list_cases(db: Session = Depends(get_db)):
    return (
        db.query(models.BGVCase)
        .options(
            joinedload(models.BGVCase.candidate),
            joinedload(models.BGVCase.documents),
            joinedload(models.BGVCase.vendor_checks),
            joinedload(models.BGVCase.events),
            joinedload(models.BGVCase.components),
        )
        .order_by(models.BGVCase.updated_at.desc())
        .all()
    )


@router.get("/cases/{case_id}", response_model=schemas.CaseRead)
def read_case(case_id: int, db: Session = Depends(get_db)):
    return get_case_or_404(case_id, db)


@router.get("/cases/{case_id}/report", response_model=schemas.BGVReport)
def generate_case_report(case_id: int, db: Session = Depends(get_db)):
    case = get_case_or_404(case_id, db)
    return schemas.BGVReport(
        report_id=f"BGV-AUDIT-{case.id:05d}",
        generated_at=datetime.utcnow(),
        candidate_name=case.candidate.name,
        candidate_email=case.candidate.email,
        case_status=case.status,
        risk_level=case.risk_level or "Pending",
        integrity_score=case.integrity_score or 100,
        final_decision=case.final_decision,
        verification_components=case.components,
        ai_summary=case.ai_summary,
        hr_notes=case.hr_notes,
        events=case.events,
    )


@router.get("/cases/{case_id}/report/html", response_class=HTMLResponse)
def generate_case_report_html(case_id: int, db: Session = Depends(get_db)):
    case = get_case_or_404(case_id, db)
    score = case.integrity_score or 100
    risk = case.risk_level or "Pending"
    badge_color = "#10b981" if score >= 85 else ("#f59e0b" if score >= 60 else "#ef4444")

    component_rows = ""
    for c in case.components:
        status_color = "#10b981" if "Clear" in c.status else ("#ef4444" if "Flag" in c.status else "#f59e0b")
        component_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; font-weight: 600;">{c.component_type}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">
                <span style="background: {status_color}; color: white; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                    {c.status}
                </span>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; color: #4b5563; font-size: 13px;">{c.remarks or 'N/A'}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; font-size: 13px;">{c.verified_at.strftime('%Y-%m-%d %H:%M') if c.verified_at else 'In Progress'}</td>
        </tr>
        """

    event_rows = ""
    for e in case.events:
        event_rows += f"""
        <li style="margin-bottom: 8px; font-size: 13px; color: #374151;">
            <strong>{e.created_at.strftime('%Y-%m-%d %H:%M')}</strong> — <span style="text-transform: capitalize;">{e.event_type.replace('_', ' ')}</span>: <em>{e.detail}</em>
        </li>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>BGV Audit Dossier - {case.candidate.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f9fafb; margin: 0; padding: 30px; color: #111827; }}
        .certificate {{ max-width: 850px; margin: 0 auto; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); padding: 40px; }}
        .header {{ border-bottom: 2px solid #3b82f6; padding-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}
        .title {{ font-size: 24px; font-weight: 800; color: #1e3a8a; margin: 0; }}
        .badge {{ background: {badge_color}; color: white; padding: 6px 14px; border-radius: 9999px; font-size: 14px; font-weight: 700; }}
        .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 25px 0; background: #f3f4f6; padding: 18px; border-radius: 8px; }}
        .table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .th {{ background: #f9fafb; text-align: left; padding: 10px; border-bottom: 2px solid #e5e7eb; font-size: 13px; color: #6b7280; text-transform: uppercase; }}
        .section-title {{ font-size: 17px; font-weight: 700; color: #1e40af; margin-top: 30px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }}
        .callout {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 14px; border-radius: 4px; margin-top: 10px; font-size: 14px; }}
        .footer {{ margin-top: 40px; border-top: 1px solid #e5e7eb; padding-top: 20px; font-size: 12px; color: #9ca3af; display: flex; justify-content: space-between; }}
    </style>
</head>
<body>
    <div class="certificate">
        <div class="header">
            <div>
                <h1 class="title">Background Verification Audit Dossier</h1>
                <p style="margin: 4px 0 0; color: #6b7280; font-size: 14px;">Case Reference: <strong>BGV-AUDIT-{case.id:05d}</strong></p>
            </div>
            <div style="text-align: right;">
                <div class="badge">Integrity Score: {score}/100</div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 5px;">Risk Level: <strong>{risk}</strong></div>
            </div>
        </div>

        <div class="meta-grid">
            <div><strong>Candidate Name:</strong> {case.candidate.name}</div>
            <div><strong>Candidate Email:</strong> {case.candidate.email}</div>
            <div><strong>Verification Vendor:</strong> {case.vendor_name}</div>
            <div><strong>Current Case Status:</strong> <span style="text-transform: capitalize;">{case.status.replace('_', ' ')}</span></div>
            <div><strong>Final HR Decision:</strong> {case.final_decision or 'Pending Review'}</div>
            <div><strong>Report Timestamp:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        </div>

        <div class="section-title">Component Verification Matrix</div>
        <table class="table">
            <thead>
                <tr>
                    <th class="th">Verification Track</th>
                    <th class="th">Status</th>
                    <th class="th">Finding / Remarks</th>
                    <th class="th">Verified At</th>
                </tr>
            </thead>
            <tbody>
                {component_rows}
            </tbody>
        </table>

        <div class="section-title">Agentic AI Risk Assessment & Findings</div>
        <div class="callout">
            <p style="margin: 0; font-weight: 500;">{case.ai_summary or 'No adverse findings. All submitted credentials align with enterprise standards.'}</p>
        </div>

        <div class="section-title">Immutable Audit Trail</div>
        <ul style="padding-left: 20px; margin-top: 12px;">
            {event_rows}
        </ul>

        <div class="footer">
            <span>Generated by Agentic AI BGV Compliance Automation System</span>
            <span>Tamper-evident verification hash: SHA-256 Verified</span>
        </div>
    </div>
</body>
</html>
"""
    return HTMLResponse(content=html)
