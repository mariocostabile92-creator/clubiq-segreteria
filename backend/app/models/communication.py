from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..db.database import Base


class Communication(Base):
    """Communication log for messages sent by a club secretary."""

    __tablename__ = "communications"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    channel = Column(String, nullable=False, default="whatsapp")
    type = Column(String, nullable=False, default="WhatsApp")
    recipient = Column(String, nullable=False, default="Contatto")
    recipient_email = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    athlete = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    direction = Column(String, nullable=False, default="outbound")
    status = Column(String, nullable=False, default="opened")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    club = relationship("Club")
    user = relationship("User")
