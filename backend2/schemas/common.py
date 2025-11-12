# backend/schemas/common.py
"""Common schemas used across the application"""

from typing import Optional, List, Dict, Any, Generic, TypeVar
from datetime import datetime, date
from pydantic import BaseModel, Field
from enum import Enum


T = TypeVar('T')


class ResponseStatus(str, Enum):
    """API response status"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints"""
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", regex="^(asc|desc)$", description="Sort order")


class DateRangeFilter(BaseModel):
    """Date range filter for queries"""
    from_date: Optional[date] = Field(None, description="Start date")
    to_date: Optional[date] = Field(None, description="End date")
    
    def validate_date_range(self) -> bool:
        """Validate that from_date is before to_date"""
        if self.from_date and self.to_date:
            return self.from_date <= self.to_date
        return True


class BaseResponse(BaseModel):
    """Base response model"""
    status: ResponseStatus = Field(ResponseStatus.SUCCESS, description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class SingleItemResponse(BaseResponse, Generic[T]):
    """Response for single item"""
    data: Optional[T] = Field(None, description="Response data")


class ListResponse(BaseResponse, Generic[T]):
    """Response for list of items with pagination"""
    data: List[T] = Field(default_factory=list, description="List of items")
    total: int = Field(0, description="Total number of items")
    page: int = Field(1, description="Current page")
    page_size: int = Field(20, description="Items per page")
    total_pages: int = Field(1, description="Total number of pages")
    
    def calculate_total_pages(self):
        """Calculate total pages based on total items and page size"""
        if self.page_size > 0:
            self.total_pages = (self.total + self.page_size - 1) // self.page_size
        return self


class ErrorDetail(BaseModel):
    """Error detail information"""
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseResponse):
    """Error response model"""
    status: ResponseStatus = Field(ResponseStatus.ERROR, description="Response status")
    errors: List[ErrorDetail] = Field(default_factory=list, description="List of errors")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


class BulkOperationResult(BaseModel):
    """Result of bulk operation"""
    total: int = Field(0, description="Total items processed")
    successful: int = Field(0, description="Successfully processed items")
    failed: int = Field(0, description="Failed items")
    errors: List[ErrorDetail] = Field(default_factory=list, description="Errors encountered")


class SearchRequest(BaseModel):
    """Generic search request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    pagination: Optional[PaginationParams] = Field(None, description="Pagination parameters")


class DeleteResponse(BaseResponse):
    """Response for delete operations"""
    deleted: bool = Field(False, description="Whether item was deleted")
    deleted_count: int = Field(0, description="Number of items deleted")


class FileUploadResponse(BaseResponse):
    """Response for file upload operations"""
    file_id: Optional[str] = Field(None, description="Uploaded file ID")
    file_name: Optional[str] = Field(None, description="Original file name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    file_type: Optional[str] = Field(None, description="File MIME type")
    url: Optional[str] = Field(None, description="File access URL")


class StatisticsResponse(BaseResponse):
    """Response for statistics endpoints"""
    data: Dict[str, Any] = Field(default_factory=dict, description="Statistics data")
    period: Optional[DateRangeFilter] = Field(None, description="Period for statistics")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="When statistics were generated")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field("healthy", description="Service health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, bool] = Field(default_factory=dict, description="Service statuses")


class Address(BaseModel):
    """Address schema"""
    street: str = Field(..., min_length=1, max_length=200)
    city: str = Field(..., min_length=1, max_length=100)
    province: str = Field(..., min_length=2, max_length=50)
    postal_code: str = Field(..., regex="^[A-Z]\\d[A-Z] \\d[A-Z]\\d$", description="Canadian postal code")
    country: str = Field("Canada", max_length=100)


class ContactInfo(BaseModel):
    """Contact information schema"""
    phone: str = Field(..., regex="^\\+?[1-9]\\d{1,14}$", description="Phone in E.164 format")
    alternate_phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    email: Optional[str] = Field(None, regex="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$")


class EmergencyContact(BaseModel):
    """Emergency contact schema"""
    name: str = Field(..., min_length=1, max_length=200)
    relationship: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., regex="^\\+?[1-9]\\d{1,14}$")
    alternate_phone: Optional[str] = Field(None)


class InsuranceInfo(BaseModel):
    """Insurance information schema"""
    provider: str = Field(..., min_length=1, max_length=200, description="Insurance company name")
    policy_number: str = Field(..., min_length=1, max_length=100)
    group_number: Optional[str] = Field(None, max_length=100)
    policy_holder_name: Optional[str] = Field(None, max_length=200)
    relationship_to_patient: Optional[str] = Field(None, max_length=50)


class VitalSigns(BaseModel):
    """Vital signs schema"""
    temperature: Optional[float] = Field(None, ge=35.0, le=42.0, description="Temperature in Celsius")
    blood_pressure_systolic: Optional[int] = Field(None, ge=60, le=250, description="Systolic BP")
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=150, description="Diastolic BP")
    pulse: Optional[int] = Field(None, ge=30, le=250, description="Pulse rate")
    respiratory_rate: Optional[int] = Field(None, ge=8, le=60, description="Breaths per minute")
    oxygen_saturation: Optional[int] = Field(None, ge=70, le=100, description="O2 saturation percentage")
    weight_kg: Optional[float] = Field(None, ge=0.5, le=500, description="Weight in kilograms")
    height_cm: Optional[float] = Field(None, ge=20, le=300, description="Height in centimeters")
    
    @property
    def blood_pressure(self) -> Optional[str]:
        """Format blood pressure as string"""
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    @property
    def bmi(self) -> Optional[float]:
        """Calculate BMI"""
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            return round(self.weight_kg / (height_m ** 2), 1)
        return None


class TimeSlot(BaseModel):
    """Time slot schema"""
    date: date = Field(..., description="Date of the slot")
    start_time: str = Field(..., regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="Start time (HH:MM)")
    end_time: str = Field(..., regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", description="End time (HH:MM)")
    available: bool = Field(True, description="Whether slot is available")
    
    def validate_time_order(self) -> bool:
        """Validate that start_time is before end_time"""
        return self.start_time < self.end_time


class AuditLog(BaseModel):
    """Audit log entry schema"""
    user_id: str = Field(..., description="User who performed the action")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: str = Field(..., description="ID of affected resource")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, description="Client user agent")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class NotificationRequest(BaseModel):
    """Notification request schema"""
    recipient_id: str = Field(..., description="Recipient user/patient ID")
    type: str = Field(..., description="Notification type")
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    priority: str = Field("normal", regex="^(low|normal|high|urgent)$")
    send_email: bool = Field(False, description="Send via email")
    send_sms: bool = Field(False, description="Send via SMS")
    schedule_at: Optional[datetime] = Field(None, description="Schedule for later sending")


class ReportParameters(BaseModel):
    """Report generation parameters"""
    report_type: str = Field(..., description="Type of report to generate")
    date_range: DateRangeFilter = Field(..., description="Date range for report")
    format: str = Field("pdf", regex="^(pdf|excel|csv|json)$", description="Report format")
    include_details: bool = Field(True, description="Include detailed information")
    group_by: Optional[str] = Field(None, description="Grouping field")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


# Export all schemas
__all__ = [
    "ResponseStatus",
    "PaginationParams",
    "DateRangeFilter",
    "BaseResponse",
    "SingleItemResponse",
    "ListResponse",
    "ErrorDetail",
    "ErrorResponse",
    "BulkOperationResult",
    "SearchRequest",
    "DeleteResponse",
    "FileUploadResponse",
    "StatisticsResponse",
    "HealthCheckResponse",
    "Address",
    "ContactInfo",
    "EmergencyContact",
    "InsuranceInfo",
    "VitalSigns",
    "TimeSlot",
    "AuditLog",
    "NotificationRequest",
    "ReportParameters",
]