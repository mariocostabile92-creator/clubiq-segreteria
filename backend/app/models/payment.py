from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey
from sqlalchemy.orm import relationship

from ..db.database import Base


class Payment(Base):
    """
    SQLAlchemy model representing a payment record associated with an athlete
    and club.
    """

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("athletes.id"), nullable=False)
    amount_due = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0.0)
    due_date = Column(Date, nullable=False)
    status = Column(String, default="pending")  # pending, overdue, paid
    method = Column(String, nullable=True)      # e.g. "bonifico", "contanti"
    notes = Column(String, nullable=True)

    # Relationships to other models
    athlete = relationship("Athlete", back_populates="payments")
    club = relationship("Club", back_populates="payments")