"""
SQLAlchemy model definition for a user (staff member) associated with a club.

Users represent the staff or administrators of a club. Each user
belongs to a single club and can have one of several roles, such as
``owner``, ``president``, ``secretary``, or ``member``. The
``hashed_password`` field stores the securely hashed password. Additional
fields track whether the user is active and can be used for future
authentication or permission logic.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..db.database import Base


class User(Base):
    """SQLAlchemy model representing a user/staff member of a club."""

    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Foreign key linking to the club this user belongs to
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)

    # Basic login and identification details
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # User role within the club (e.g. owner, president, secretary, member)
    role = Column(String, default="member")

    # Whether the user account is active. This could be used to disable
    # accounts without deleting them.
    is_active = Column(Boolean, default=True)

    # Relationship back to the club
    club = relationship("Club", back_populates="users")
