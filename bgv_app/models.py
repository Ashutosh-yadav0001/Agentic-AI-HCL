from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bgv_app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cases: Mapped[list["BGVCase"]] = relationship(back_populates="candidate")


class BGVCase(Base):
    __tablename__ = "bgv_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    vendor_name: Mapped[str] = mapped_column(String(120), default="Demo Verify")
    status: Mapped[str] = mapped_column(String(80), default="offer_sent", index=True)
    offer_accepted: Mapped[bool | None] = mapped_column(Boolean)
    risk_level: Mapped[str | None] = mapped_column(String(40))
    integrity_score: Mapped[int | None] = mapped_column(Integer, default=100)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_draft_email: Mapped[str | None] = mapped_column(Text)
    hr_notes: Mapped[str | None] = mapped_column(Text)
    candidate_response: Mapped[str | None] = mapped_column(Text)
    final_decision: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate: Mapped[Candidate] = relationship(back_populates="cases")
    documents: Mapped[list["Document"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    vendor_checks: Mapped[list["VendorCheck"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    events: Mapped[list["WorkflowEvent"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    components: Mapped[list["VerificationComponent"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("bgv_cases.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped[BGVCase] = relationship(back_populates="documents")


class VendorCheck(Base):
    __tablename__ = "vendor_checks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("bgv_cases.id"), nullable=False)
    vendor_outcome: Mapped[str] = mapped_column(String(80), nullable=False)
    vendor_remarks: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped[BGVCase] = relationship(back_populates="vendor_checks")


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("bgv_cases.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped[BGVCase] = relationship(back_populates="events")
 
 
class VerificationComponent(Base):
    __tablename__ = "verification_components"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("bgv_cases.id"), nullable=False)
    component_type: Mapped[str] = mapped_column(String(80), nullable=False)  # Identity, Employment, Education, Criminal, Address
    status: Mapped[str] = mapped_column(String(50), default="Pending")  # Pending, In Progress, Clear, Discrepancy, Red Flag
    severity: Mapped[str | None] = mapped_column(String(40), default="Low")  # None, Low, Medium, High, Critical
    remarks: Mapped[str | None] = mapped_column(Text, default="")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    case: Mapped[BGVCase] = relationship(back_populates="components")
