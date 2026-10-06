from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = None


class CandidateRead(CandidateCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseCreate(BaseModel):
    candidate_id: int
    vendor_name: str = "Demo Verify"


class OfferResponse(BaseModel):
    accepted: bool


class DocumentCreate(BaseModel):
    document_type: str
    file_name: str
    file_url: str | None = None


class VendorStatusCreate(BaseModel):
    vendor_outcome: str
    vendor_remarks: str = ""


class HRReview(BaseModel):
    approved: bool
    reviewer_notes: str = ""
    final_decision: str | None = None


class CandidateResponse(BaseModel):
    candidate_response: str


class DocumentRead(DocumentCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VendorCheckRead(VendorStatusCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowEventRead(BaseModel):
    id: int
    event_type: str
    detail: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationComponentCreate(BaseModel):
    component_type: str
    status: str = "Pending"
    severity: str = "Low"
    remarks: str = ""


class VerificationComponentUpdate(BaseModel):
    status: str
    severity: str = "Low"
    remarks: str = ""


class VerificationComponentRead(BaseModel):
    id: int
    case_id: int
    component_type: str
    status: str
    severity: str | None
    remarks: str | None
    verified_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CaseRead(BaseModel):
    id: int
    candidate_id: int
    vendor_name: str
    status: str
    offer_accepted: bool | None
    risk_level: str | None
    integrity_score: int | None = 100
    ai_summary: str | None
    ai_draft_email: str | None
    hr_notes: str | None
    candidate_response: str | None
    final_decision: str | None
    created_at: datetime
    updated_at: datetime
    candidate: CandidateRead
    documents: list[DocumentRead] = []
    vendor_checks: list[VendorCheckRead] = []
    events: list[WorkflowEventRead] = []
    components: list[VerificationComponentRead] = []

    model_config = ConfigDict(from_attributes=True)


class BGVReport(BaseModel):
    report_id: str
    generated_at: datetime
    candidate_name: str
    candidate_email: str
    case_status: str
    risk_level: str
    integrity_score: int
    final_decision: str | None
    verification_components: list[VerificationComponentRead]
    ai_summary: str | None
    hr_notes: str | None
    events: list[WorkflowEventRead]

