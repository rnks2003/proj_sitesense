from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, JSON, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Scan(Base):
    __tablename__ = "scans"
    id = Column(String, primary_key=True, default=generate_uuid)
    url = Column(String, nullable=False)
    normalized_url = Column(String)
    status = Column(String, default="queued")  # queued, running, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    error_message = Column(Text)
    module_results = relationship("ModuleResult", back_populates="scan", cascade="all, delete-orphan")
    files = relationship("File", back_populates="scan", cascade="all, delete-orphan")

class ModuleResult(Base):
    __tablename__ = "module_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"))
    module_name = Column(String)  # ui_ux, security_hygiene, etc.
    status = Column(String)
    result_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scan = relationship("Scan", back_populates="module_results")

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(String, ForeignKey("scans.id", ondelete="CASCADE"))
    file_type = Column(String) # screenshot, attention_heatmap, click_heatmap, lighthouse_report
    content_type = Column(String) # image/png, image/jpeg, application/json
    data = Column(LargeBinary)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scan = relationship("Scan", back_populates="files")
