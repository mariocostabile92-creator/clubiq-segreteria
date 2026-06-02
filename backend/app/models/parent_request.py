"""
SQLAlchemy model for parent registration requests.
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.sql import func

from ..db.database import Base


class ParentRequest(Base):
    __tablename__ = "parent_requests"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False, index=True)

    athlete_first_name = Column(String, nullable=False)
    athlete_last_name = Column(String, nullable=False)
    athlete_birth_date = Column(Date, nullable=False)
    requested_group = Column(String, nullable=True)

    parent_name = Column(String, nullable=False)
    parent_phone = Column(String, nullable=True)
    parent_email = Column(String, nullable=False)

    notes = Column(String, nullable=True)
    certificate_file_url = Column(String, nullable=True)
    payment_receipt_url = Column(String, nullable=True)

    status = Column(String, nullable=False, default="pending")
    review_note = Column(String, nullable=True)
    created_athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)