from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False)
    session_data = Column(Text)  # Encrypted session cookies/tokens
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
class EwayBill(Base):
    __tablename__ = "eway_bills"
    
    id = Column(Integer, primary_key=True, index=True)
    ewb_number = Column(String(20), unique=True, nullable=False, index=True)
    valid_until = Column(String(20))  # DD/MM/YYYY format from CSV
    from_place = Column(String(200))
    to_place = Column(String(200))
    document_no = Column(String(100))
    vehicle_number = Column(String(50))
    kilometers = Column(Float)
    status = Column(String(50), default="pending")  # pending, extended, failed, expired
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
class Operation(Base):
    __tablename__ = "operations"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String(50), nullable=False)  # login, extend_eway, bulk_extend, etc.
    status = Column(String(20), nullable=False)  # started, success, failed, cancelled
    details = Column(Text)  # JSON string with operation details
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    duration_seconds = Column(Float)
    
class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(String(500))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
class BulkOperation(Base):
    __tablename__ = "bulk_operations"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_name = Column(String(200), nullable=False)
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    file_path = Column(String(500))  # Path to uploaded CSV
    results_path = Column(String(500))  # Path to results file
