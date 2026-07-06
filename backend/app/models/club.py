"""
SQLAlchemy model definition for a sports club (società).
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..db.database import Base


class Club(Base):
    """SQLAlchemy model representing a sports club/society."""

    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False, index=True)

    # Public code used by parents to submit registration requests.
    # Generated automatically from the real club name at signup.
    public_code = Column(String, nullable=True, unique=True, index=True)

    logo = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    president = Column(String, nullable=True)
    secretary = Column(String, nullable=True)

    plan = Column(String, default="free")
    subscription_status = Column(String, default="active")
    admin_notes = Column(Text, nullable=True)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    stripe_current_period_end = Column(DateTime, nullable=True)
    stripe_last_event_id = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="club")
    athletes = relationship("Athlete", back_populates="club")
    payments = relationship("Payment", back_populates="club")
    certificates = relationship("Certificate", back_populates="club")
