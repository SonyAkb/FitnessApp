from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from app.core.clock import utc_now
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
