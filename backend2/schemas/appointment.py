# backend/schemas/appointment.py
"""Appointment and scheduling schemas for API requests and responses"""

from typing import Optional, List, Dict
from datetime import datetime, date, time
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import BaseResponse, TimeSlot, PaginationParams, DateRangeFilter


class AppointmentStatus(str, Enum):
    """Appointment status options"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class AppointmentType(str, Enum):
    """Appointment type options"""
    REGULAR = "regular"
    WALK_IN = "walk_in"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    CHECKUP = "checkup"
    IMMUNIZATION = "immunization"
    PRENATAL = "prenatal"
    POSTNATAL = "postnatal"
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"


class RecurrencePattern(str, Enum):
    """Appointment recurrence patterns"""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class AppointmentCreateRequest(BaseModel):
    """Appointment creation request schema"""
    patient_id: str = Field(..., description="Patient ID")
    staff_id: str = Field(..., description="Practitioner/Staff ID")
    scheduled_date: date = Field(..., description="Appointment date")
    scheduled_start: time = Field(..., description="Start time")
    scheduled_end: Optional[time] = Field(None, description="End time (auto-calculated if not provided)")
    appointment_type: AppointmentType = Field(AppointmentType.REGULAR)
    reason_for_visit: str = Field(..., min_length=1, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)
    
    # Recurrence
    is_recurring: bool = Field(False, description="Whether this is a recurring appointment")
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[date] = None
    
    # Notifications
    send_confirmation: bool = Field(True, description="Send confirmation to patient")
    reminder_days_before: Optional[int] = Field(1, ge=0, le=30, description="Days before to send reminder")
    
    @validator('scheduled_start')
    def validate_time_slot(cls, v):
        """Validate appointment starts at 10-minute intervals"""
        if v.minute % 10 != 0:
            raise ValueError('Appointments must start at 10-minute intervals (00, 10, 20, 30, 40, 50)')
        return v
    
    @validator('scheduled_end')
    def validate_end_time(cls, v, values):
        """Validate end time is after start time"""
        if v and 'scheduled_start' in values:
            if v <= values['scheduled_start']:
                raise ValueError('End time must be after start time')
        return v
    
    @validator('recurrence_end_date')
    def validate_recurrence_end(cls, v, values):
        """Validate recurrence end date"""
        if v and 'scheduled_date' in values:
            if v <= values['scheduled_date']:
                raise ValueError('Recurrence end date must be after appointment date')
        return v


class AppointmentUpdateRequest(BaseModel):
    """Appointment update request schema"""
    scheduled_date: Optional[date] = None
    scheduled_start: Optional[time] = None
    scheduled_end: Optional[time] = None
    staff_id: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    reason_for_visit: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=2000)
    send_notification: bool = Field(False, description="Send notification of changes")


class AppointmentRescheduleRequest(BaseModel):
    """Appointment reschedule request schema"""
    new_date: date = Field(..., description="New appointment date")
    new_start_time: time = Field(..., description="New start time")
    new_end_time: Optional[time] = None
    new_staff_id: Optional[str] = Field(None, description="Different practitioner if needed")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for rescheduling")
    notify_patient: bool = Field(True, description="Send notification to patient")


class AppointmentCancelRequest(BaseModel):
    """Appointment cancellation request schema"""
    reason: str = Field(..., min_length=1, max_length=500, description="Cancellation reason")
    cancelled_by: str = Field(..., description="Who cancelled (patient/staff/system)")
    notify_patient: bool = Field(True, description="Send cancellation notification")
    offer_reschedule: bool = Field(True, description="Offer rescheduling option")


class WalkInRegistrationRequest(BaseModel):
    """Walk-in registration request schema"""
    patient_id: str = Field(..., description="Patient ID")
    reason_for_visit: str = Field(..., min_length=1, max_length=500)
    preferred_staff_id: Optional[str] = Field(None, description="Preferred practitioner if any")
    urgency: str = Field("normal", regex="^(low|normal|high|urgent)$")
    notes: Optional[str] = Field(None, max_length=2000)
    estimated_duration_minutes: int = Field(10, ge=10, le=60)


class AppointmentResponse(BaseModel):
    """Appointment response schema"""
    appointment_id: str
    patient_id: str
    patient_name: str
    staff_id: str
    staff_name: str
    
    # Schedule
    scheduled_date: date
    scheduled_start: time
    scheduled_end: time
    duration_minutes: int
    
    # Details
    appointment_type: AppointmentType
    status: AppointmentStatus
    reason_for_visit: str
    notes: Optional[str]
    
    # Walk-in specific
    is_walk_in: bool
    walk_in_arrival_time: Optional[datetime]
    wait_time_minutes: Optional[int]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    confirmed_at: Optional[datetime]
    reminder_sent_at: Optional[datetime]
    
    # Cancellation/Rescheduling
    cancelled_at: Optional[datetime]
    cancelled_by: Optional[str]
    cancellation_reason: Optional[str]
    rescheduled_from: Optional[str]


class AppointmentListResponse(BaseResponse):
    """Appointment list response schema"""
    appointments: List[AppointmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AppointmentSearchRequest(BaseModel):
    """Appointment search request schema"""
    patient_id: Optional[str] = None
    staff_id: Optional[str] = None
    date_range: Optional[DateRangeFilter] = None
    status: Optional[List[AppointmentStatus]] = None
    appointment_type: Optional[List[AppointmentType]] = None
    include_cancelled: bool = Field(False)
    pagination: Optional[PaginationParams] = None


class AvailableSlotRequest(BaseModel):
    """Available slot search request schema"""
    staff_id: Optional[str] = Field(None, description="Specific practitioner")
    specialization: Optional[str] = Field(None, description="Required specialization")
    date: date = Field(..., description="Date to check availability")
    duration_minutes: int = Field(10, ge=10, le=120, description="Required duration")
    appointment_type: Optional[AppointmentType] = None
    preferred_time: Optional[str] = Field(None, regex="^(morning|afternoon|evening)$")


class AvailableSlotResponse(BaseModel):
    """Available slot response schema"""
    date: date
    start_time: time
    end_time: time
    staff_id: str
    staff_name: str
    specialization: Optional[str]
    room: Optional[str]
    available: bool = True


class AvailableSlotsListResponse(BaseResponse):
    """Available slots list response"""
    slots: List[AvailableSlotResponse]
    date: date
    total_available: int


class DailyScheduleRequest(BaseModel):
    """Daily schedule request schema"""
    date: date = Field(..., description="Date for schedule")
    staff_id: Optional[str] = Field(None, description="Specific staff member")
    include_blocked: bool = Field(False, description="Include blocked time slots")
    include_breaks: bool = Field(True, description="Include break times")


class DailyScheduleResponse(BaseModel):
    """Daily schedule response schema"""
    date: date
    staff_id: str
    staff_name: str
    start_time: time
    end_time: time
    appointments: List[AppointmentResponse]
    blocked_slots: List[TimeSlot]
    break_slots: List[TimeSlot]
    total_appointments: int
    available_slots: int
    utilization_percentage: float


class WeeklyCoverageRequest(BaseModel):
    """Weekly coverage schedule request"""
    week_start: date = Field(..., description="Monday of the week")
    staff_assignments: List[Dict[str, any]] = Field(..., description="Staff assignments")
    on_call_assignments: List[Dict[str, any]] = Field(..., description="On-call assignments")
    notes: Optional[str] = Field(None, max_length=2000)
    
    @validator('week_start')
    def validate_monday(cls, v):
        """Ensure week starts on Monday"""
        if v.weekday() != 0:
            raise ValueError('Week start must be a Monday')
        return v


class WeeklyCoverageResponse(BaseModel):
    """Weekly coverage response schema"""
    coverage_id: str
    week_start: date
    week_end: date
    staff_assignments: List[dict]
    on_call_assignments: List[dict]
    min_physicians: int
    min_nurses: int
    min_midwives: int
    approved: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_by: str
    notes: Optional[str]


class PractitionerScheduleUpdateRequest(BaseModel):
    """Practitioner schedule update request"""
    staff_id: str = Field(..., description="Staff ID")
    date: date = Field(..., description="Schedule date")
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    is_available: bool = Field(True, description="Whether available")
    available_for_walk_ins: bool = Field(True, description="Accept walk-ins")
    max_walk_ins: Optional[int] = Field(None, ge=0, le=20)
    break_slots: List[TimeSlot] = Field(default_factory=list)
    blocked_slots: List[Dict[str, any]] = Field(default_factory=list)


class AppointmentConfirmationRequest(BaseModel):
    """Appointment confirmation request"""
    appointment_id: str = Field(..., description="Appointment ID")
    confirmed_by: str = Field(..., description="Who confirmed (patient/staff)")
    confirmation_method: str = Field(..., regex="^(phone|email|sms|in_person)$")
    notes: Optional[str] = Field(None, max_length=500)


class AppointmentCheckInRequest(BaseModel):
    """Appointment check-in request"""
    appointment_id: str = Field(..., description="Appointment ID")
    arrival_time: Optional[datetime] = Field(None, description="Actual arrival time")
    update_contact_info: bool = Field(False, description="Whether to update contact info")
    insurance_verified: bool = Field(False, description="Insurance verification status")
    copay_collected: bool = Field(False, description="Whether copay was collected")
    forms_completed: bool = Field(False, description="Whether forms are completed")


class AppointmentStatisticsRequest(BaseModel):
    """Appointment statistics request"""
    date_range: DateRangeFilter
    staff_id: Optional[str] = None
    group_by: Optional[str] = Field(None, regex="^(day|week|month|staff|type|status)$")
    include_cancellations: bool = Field(False)
    include_no_shows: bool = Field(False)


class AppointmentStatisticsResponse(BaseResponse):
    """Appointment statistics response"""
    period: DateRangeFilter
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    no_show_appointments: int
    walk_in_appointments: int
    average_duration_minutes: float
    utilization_rate: float
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_staff: Optional[Dict[str, int]]
    busiest_day: Optional[str]
    busiest_hour: Optional[int]


class WaitTimeResponse(BaseModel):
    """Wait time response for walk-ins"""
    estimated_wait_minutes: int
    patients_ahead: int
    current_serving: Optional[str]
    last_updated: datetime


# Export all schemas
__all__ = [
    "AppointmentStatus",
    "AppointmentType",
    "RecurrencePattern",
    "AppointmentCreateRequest",
    "AppointmentUpdateRequest",
    "AppointmentRescheduleRequest",
    "AppointmentCancelRequest",
    "WalkInRegistrationRequest",
    "AppointmentResponse",
    "AppointmentListResponse",
    "AppointmentSearchRequest",
    "AvailableSlotRequest",
    "AvailableSlotResponse",
    "AvailableSlotsListResponse",
    "DailyScheduleRequest",
    "DailyScheduleResponse",
    "WeeklyCoverageRequest",
    "WeeklyCoverageResponse",
    "PractitionerScheduleUpdateRequest",
    "AppointmentConfirmationRequest",
    "AppointmentCheckInRequest",
    "AppointmentStatisticsRequest",
    "AppointmentStatisticsResponse",
    "WaitTimeResponse",
]