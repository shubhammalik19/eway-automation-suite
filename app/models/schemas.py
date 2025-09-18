from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

# Enums
class OperationStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class EwayBillStatus(str, Enum):
    PENDING = "pending"
    EXTENDED = "extended" 
    FAILED = "failed"
    EXPIRED = "expired"

# Request Models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)
    remember_session: bool = True

class LoginResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    requires_captcha: bool = False
    captcha_image_url: Optional[str] = None
    session_saved: bool = False
    error_code: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class EwayExtensionRequest(BaseModel):
    ewb_number: str = Field(..., min_length=11, max_length=12)
    vehicle_number: Optional[str] = None
    kilometers: Optional[float] = None
    reason: str = "Vehicle Breakdown"

class BulkExtensionRequest(BaseModel):
    csv_data: str  # Base64 encoded CSV content
    filename: str
    filter_today_only: bool = True

# Response Models
class LoginResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None

class EwayBillResponse(BaseModel):
    id: Optional[int] = None
    ewb_number: str
    valid_until: Optional[str] = None
    from_place: Optional[str] = None
    to_place: Optional[str] = None
    document_no: Optional[str] = None
    vehicle_number: Optional[str] = None
    kilometers: Optional[float] = None
    status: EwayBillStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class OperationResponse(BaseModel):
    id: int
    operation_type: str
    status: OperationStatus
    details: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

class BulkOperationResponse(BaseModel):
    id: int
    operation_name: str
    total_items: int
    processed_items: int
    successful_items: int
    failed_items: int
    status: OperationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None

class SessionInfo(BaseModel):
    is_logged_in: bool
    username: Optional[str] = None
    session_created: Optional[datetime] = None
    session_expires: Optional[datetime] = None
    auto_refresh_enabled: bool = True

class DashboardStats(BaseModel):
    total_eway_bills: int
    pending_extensions: int
    successful_extensions: int
    failed_extensions: int
    active_sessions: int
    recent_operations: List[OperationResponse] = []

# Configuration Models
class AutomationSettings(BaseModel):
    browser_type: str = "chromium"
    headless: bool = True
    slow_mo: int = 0
    timeout: int = 30000
    auto_refresh_session: bool = True
    session_timeout_hours: int = 8

# File Upload Models
class FileUpload(BaseModel):
    filename: str
    content: str  # Base64 encoded
    content_type: str = "text/csv"

# Dataclasses for automation system (used by eway_extensions)
@dataclass
class EwayBillData:
    """Data structure for E-way Bill information"""
    ewb_number: str
    valid_until: Optional[str] = None
    from_place: Optional[str] = None
    to_place: Optional[str] = None
    document_no: Optional[str] = None
    vehicle_number: Optional[str] = None
    kilometers: Optional[float] = None
    status: str = "pending"

@dataclass
class AutomationResult:
    """Result of automation operation"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    screenshot_path: Optional[str] = None
