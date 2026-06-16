import uuid
from datetime import datetime
from sqlalchemy import String, Float, Text, ARRAY, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Resume(Base):
    __tablename__ = "resumes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("jobs.id"))
    tailored_content: Mapped[dict] = mapped_column(JSONB, default={})
    docx_path: Mapped[str] = mapped_column(String(1000), nullable=True)
    match_score: Mapped[float] = mapped_column(Float, nullable=True)
    keywords_matched: Mapped[list] = mapped_column(ARRAY(String), default=[])
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    job = relationship("Job", back_populates="resumes")