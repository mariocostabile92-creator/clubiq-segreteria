"""
SQLAlchemy model definition for a medical/sports certificate associated
with an athlete and club.

Certificates track the validity of documents such as medical exams or
insurance papers. Each certificate is linked to an athlete and their
club and includes issue and expiry dates. The ``status`` field can be
used to track whether the certificate is valid, expiring soon, or
expired. An optional ``file_path`` allows linking to a stored PDF or
image of the certificate.
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from ..db.database import Base


class Certificate(Base):
    """SQLAlchemy model representing a certificate for an athlete."""

    __tablename__ = "certificates"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys linking to the club and athlete
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)

    # Certificate details
    type = Column(String, nullable=False)  # e.g. "Medico sportivo"
    issue_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=False)
    status = Column(String, default="valid")  # valid, expiring, expired
    file_path = Column(String, nullable=True)

    # Relationships
    athlete = relationship("Athlete", back_populates="certificates")
    club = relationship("Club", back_populates="certificates")
