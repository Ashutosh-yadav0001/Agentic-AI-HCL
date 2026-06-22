from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from bgv_app import models, schemas
from bgv_app.agents.runner import analyze_vendor_issue
from bgv_app.database import get_db
from bgv_app.integrations.gmail import send_email
from bgv_app.integrations.microsoft_forms import bgv_form_url, offer_form_url

router = APIRouter(prefix="/agentic-bgv", tags=["agentic-bgv"])


def get_case_or_404(case_id: int, db: Session) -> models.BGVCase:
    case = (
        db.query(models.BGVCase)
        .options(
            joinedload(models.BGVCase.candidate),
            joinedload(models.BGVCase.documents),
            joinedload(models.BGVCase.vendor_checks),
            joinedload(models.BGVCase.events),
        )
        .filter(models.BGVCase.id == case_id)
        .first()
    )
    if case is None:
        raise HTTPException(status_code=404, detail="BGV case not found")
    return case


def add_event(db: Session, case: models.BGVCase, event_type: str, detail: str) -> None:
    db.add(models.WorkflowEvent(case=case, event_type=event_type, detail=detail))


@router.post("/cases", response_model=schemas.CaseRead)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    candidate = db.get(models.Candidate, payload.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    case = models.BGVCase(candidate=candidate, vendor_name=payload.vendor_name, status="offer_sent")
    db.add(case)
    db.flush()
    email = send_email(
        candidate.email,
        "Offer released - response requested",
        f"Dear {candidate.name}, please accept or decline your offer here: {offer_form_url()}",
    )
    add_event(db, case, "offer_email", f"Demo email queued to {email.to}: {email.subject}")
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
        case.final_decision = "Approved"
        add_event(db, case, "vendor_clear", payload.vendor_remarks or "Vendor cleared the case.")
        send_email(case.candidate.email, "BGV completed", "Your background verification has been completed.")
    else:
        analysis = analyze_vendor_issue(case.candidate.name, payload.vendor_outcome, payload.vendor_remarks)
        case.status = analysis.next_status
        case.risk_level = analysis.risk_level
        case.ai_summary = analysis.summary
        case.ai_draft_email = analysis.candidate_email
        add_event(db, case, "vendor_issue", analysis.summary)
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
        )
        .order_by(models.BGVCase.updated_at.desc())
        .all()
    )


@router.get("/cases/{case_id}", response_model=schemas.CaseRead)
def read_case(case_id: int, db: Session = Depends(get_db)):
    return get_case_or_404(case_id, db)
