from sqlalchemy import Column, DateTime, String, Text

from app.db.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id = Column(String, primary_key=True)
    period = Column(String, nullable=False)
    # daily | weekly | monthly
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    executive_summary = Column(Text, nullable=False)
    top_violations = Column(Text, nullable=False)
    trend_analysis = Column(Text, nullable=False)
    recommended_actions = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
