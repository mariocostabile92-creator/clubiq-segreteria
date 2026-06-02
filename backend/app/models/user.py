"""
SQLAlchemy model definition for a user (staff member) associated with a club.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from ..db.database import Base


class User(Base):
    """SQLAlchemy model representing a user/staff member of a club."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)

    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    role = Column(String, default="member")
    is_active = Column(Boolean, default=True)

    email_verified = Column(Boolean, default=False, nullable=False)
    email_verification_token = Column(String, nullable=True, unique=True, index=True)
    email_verification_expires_at = Column(DateTime, nullable=True)

    password_reset_token = Column(String, nullable=True, unique=True, index=True)
    password_reset_expires_at = Column(DateTime, nullable=True)

    club = relationship("Club", back_populates="users")
