"""
SQLAlchemy model definition for an athlete (tesserato).

Athletes belong to a club and can have payments and certificates associated
with them. The model captures personal information as well as
contact details for the athlete's guardians. Relationships are
established to allow easy retrieval of related payments and certificates.
"""

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from ..db.database import Base


class Athlete(Base):
    """SQLAlchemy model representing an athlete registered with a club."""

    __tablename__ = "athletes"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key linking to the club this athlete belongs to
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)

    # Personal details
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    group_name = Column(String, nullable=True)  # e.g. "Under 12", "Pulcini A"

    # Contact details for the athlete
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)

    # Parent/guardian contact details (optional)
    parent_name_1 = Column(String, nullable=True)
    parent_phone_1 = Column(String, nullable=True)
    parent_email_1 = Column(String, nullable=True)
    parent_name_2 = Column(String, nullable=True)
    parent_phone_2 = Column(String, nullable=True)
    parent_email_2 = Column(String, nullable=True)

    # Additional notes
    notes = Column(String, nullable=True)

    # Relationships
    club = relationship("Club", back_populates="athletes")
    payments = relationship("Payment", back_populates="athlete")
    certificates = relationship("Certificate", back_populates="athlete")
