from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.clock import utc_now
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    intensity = Column(String(16), nullable=True)  # light | moderate | hard
    sources = Column(JSON, nullable=True)  # [{id, title, url}]
    engine = Column(String(16), nullable=False, default="rules", server_default="rules")  # rules | rag
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
