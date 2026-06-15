from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from db import Base
import json


class Faculty(Base):
    """Faculty login table — populated manually or via seed script."""
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)   # plain-text for now; hash in production
    name = Column(String(150), nullable=True)
    department = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    """Stores every processed upload + the computed JSON + the rendered HTML."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)

    # Section metadata (form fields)
    dept = Column(String(50), nullable=True)
    year = Column(String(20), nullable=True)
    sem = Column(String(20), nullable=True)
    section = Column(String(10), nullable=True)
    faculty_advisor_name = Column(String(150), nullable=True)

    # File reference
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=True)

    # Processing results stored as JSON text
    computed_json = Column(Text, nullable=True)   # subject stats, summary, failure list
    report_html = Column(Text, nullable=True)     # full rendered HTML (for retrieval)

    status = Column(String(50), default="processed")
    created_at = Column(DateTime, default=datetime.utcnow)

    # ---- helpers ----
    def set_computed(self, data: dict):
        self.computed_json = json.dumps(data)

    def get_computed(self) -> dict | None:
        if not self.computed_json:
            return None
        return json.loads(self.computed_json)
