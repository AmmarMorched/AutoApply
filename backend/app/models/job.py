import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, Float, ARRAY, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("external_id", "source", name="uq_job_external_source"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str] = mapped_column(String(500), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    company: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    apply_url: Mapped[str] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(50))
    salary_min: Mapped[int] = mapped_column(nullable=True)
    salary_max: Mapped[int] = mapped_column(nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    keywords_found: Mapped[list] = mapped_column(ARRAY(String), default=[])
    raw_data: Mapped[dict] = mapped_column(JSONB, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    resumes = relationship("Resume", back_populates="job")