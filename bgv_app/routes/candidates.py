from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bgv_app import models, schemas
from bgv_app.database import get_db

router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("", response_model=schemas.CandidateRead)
def create_candidate(payload: schemas.CandidateCreate, db: Session = Depends(get_db)):
    candidate = models.Candidate(**payload.model_dump())
    db.add(candidate)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Candidate email already exists") from exc
    db.refresh(candidate)
    return candidate


@router.get("", response_model=list[schemas.CandidateRead])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(models.Candidate).order_by(models.Candidate.created_at.desc()).all()
