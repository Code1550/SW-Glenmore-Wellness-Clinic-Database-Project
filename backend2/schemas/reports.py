# backend/schemas/reports.py
"""Report generation schemas for various clinic reports"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import BaseResponse, DateRangeFilter


class ReportType(str, Enum):
    """Available report types"""
    DAILY_LAB_LOG = "daily_lab_log"
    DAILY_DELIVERY_LOG = "daily_delivery_log"
    RECOVERY_ROOM_LOG = "recovery_room_log"
    MONTHLY_ACTIVITY = "monthly_activity"
    PHYSICIAN_STATEMENT = "physician_statement"
    PATIENT_STATEMENT = "patient_statement"
    PRESCRIPTION_LABEL = "prescription_label"
    WEEKLY_COVERAGE = "weekly_coverage"
    DAILY_SCHEDULE = "daily_schedule"
    FINANCIAL_SUMMARY = "financial_summary"
    STATISTICAL_REPORT = "statistical_report"


class ReportFormat(str, Enum):
    """Report output formats"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"
    JSON = "json"
    PRINT = "print"


class ReportFrequency(str, Enum):
    """Report generation frequency"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ON_DEMAND = "on_demand"


# ==================== DAILY LOGS ====================

class DailyLabLogRequest(BaseModel):
    """Daily laboratory log request"""
    log_date: date = Field(default_factory=date.today)
    include_pending: bool = Field(True, description="Include pending tests")
    include_completed: bool = Field(True, description="Include completed tests")
    group_by_category: bool = Field(True, description="Group by test category")
    format: ReportFormat = Field(ReportFormat.PDF)


class DailyLabLogResponse(BaseResponse):
    """Daily laboratory log response"""
    log_date: date
    total_tests: int
    tests_ordered: int
    tests_completed: int
    tests_pending: int
    critical_results: int
    
    tests_by_category: Dict[str, int]
    tests_by_priority: Dict[str, int]
    
    test_details: List[Dict[str, Any]]
    file_url: Optional[str]


class DailyDeliveryLogRequest(BaseModel):
    """Daily delivery room log request"""
    log_date: date = Field(default_factory=date.today)
    include_complications: bool = Field(True)
    include_nicu_transfers: bool = Field(True)
    format: ReportFormat = Field(ReportFormat.PDF)


class DailyDeliveryLogResponse(BaseResponse):
    """Daily delivery room log response"""
    log_date: date
    total_deliveries: int
    
    # Delivery types
    vaginal_deliveries: int
    cesarean_deliveries: int
    
    # Baby statistics
    male_babies: int
    female_babies: int
    average_weight_grams: float
    average_apgar_1min: float
    average_apgar_5min: float
    
    # Complications
    deliveries_with_complications: int
    nicu_transfers: int
    
    delivery_details: List[Dict[str, Any]]
    file_url: Optional[str]


class RecoveryRoomLogRequest(BaseModel):
    """Recovery room log request"""
    log_date: date = Field(default_factory=date.today)
    include_observations: bool = Field(True)
    include_medications: bool = Field(True)
    active_only: bool = Field(False, description="Only active stays")
    format: ReportFormat = Field(ReportFormat.PDF)


class RecoveryRoomLogResponse(BaseResponse):
    """Recovery room log response"""
    log_date: date
    total_patients: int
    new_admissions: int
    discharges: int
    currently_in_recovery: int
    
    average_stay_hours: float
    total_observations: int
    critical_observations: int
    
    patient_details: List[Dict[str, Any]]
    bed_utilization: Dict[str, bool]
    file_url: Optional[str]


# ==================== MONTHLY REPORTS ====================

class MonthlyActivityReportRequest(BaseModel):
    """Monthly activity report request"""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    include_comparisons: bool = Field(True, description="Compare to previous month")
    include_year_to_date: bool = Field(True)
    department_breakdown: bool = Field(True)
    format: ReportFormat = Field(ReportFormat.PDF)


class MonthlyActivityReportResponse(BaseResponse):
    """Monthly activity report response"""
    report_month: str
    report_year: int
    
    # Patient visits
    total_visits: int
    new_patients: int
    follow_up_visits: int
    walk_in_visits: int
    emergency_visits: int
    average_visit_duration_minutes: float
    
    # Clinical activities
    total_procedures: int
    total_surgeries: int
    total_deliveries: int
    total_lab_tests: int
    total_prescriptions: int
    
    # Financial summary
    total_revenue: Decimal
    total_collected: Decimal
    outstanding_balance: Decimal
    
    # Comparisons
    previous_month_comparison: Optional[Dict[str, Any]]
    year_to_date_totals: Optional[Dict[str, Any]]
    
    # Department breakdown
    department_statistics: Optional[Dict[str, Dict[str, Any]]]
    
    file_url: Optional[str]


# ==================== INSURANCE & BILLING REPORTS ====================

class PhysicianStatementRequest(BaseModel):
    """Physician statement for insurance request"""
    visit_id: str = Field(..., description="Visit ID")
    include_diagnoses: bool = Field(True)
    include_procedures: bool = Field(True)
    include_prescriptions: bool = Field(True)
    physician_notes: Optional[str] = Field(None, max_length=1000)
    format: ReportFormat = Field(ReportFormat.PDF)


class PhysicianStatementResponse(BaseResponse):
    """Physician statement response"""
    statement_number: str
    visit_id: str
    visit_date: date
    
    # Patient information
    patient_name: str
    patient_id: str
    date_of_birth: date
    health_card_number: Optional[str]
    
    # Provider information
    physician_name: str
    physician_license: str
    clinic_name: str
    clinic_address: str
    
    # Clinical information
    chief_complaint: str
    diagnoses: List[Dict[str, str]]
    procedures: List[Dict[str, Any]]
    prescriptions: List[Dict[str, str]]
    
    # Billing
    total_charges: Decimal
    
    file_url: Optional[str]


class PatientStatementRequest(BaseModel):
    """Patient monthly statement request"""
    patient_id: str = Field(..., description="Patient ID")
    statement_month: int = Field(..., ge=1, le=12)
    statement_year: int = Field(..., ge=2020)
    include_paid_invoices: bool = Field(False)
    include_payment_history: bool = Field(True)
    format: ReportFormat = Field(ReportFormat.PDF)


class PatientStatementResponse(BaseResponse):
    """Patient statement response"""
    statement_date: date
    patient_name: str
    patient_address: str
    
    # Account summary
    previous_balance: Decimal
    new_charges: Decimal
    payments_received: Decimal
    adjustments: Decimal
    current_balance: Decimal
    
    # Aging summary
    current: Decimal
    over_30_days: Decimal
    over_60_days: Decimal
    over_90_days: Decimal
    
    # Transaction details
    charges: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    
    # Payment options
    payment_due_date: date
    minimum_payment: Optional[Decimal]
    
    file_url: Optional[str]


# ==================== OPERATIONAL REPORTS ====================

class WeeklyCoverageReportRequest(BaseModel):
    """Weekly coverage schedule report request"""
    week_start: date = Field(..., description="Monday of the week")
    include_on_call: bool = Field(True)
    include_contact_info: bool = Field(True)
    format: ReportFormat = Field(ReportFormat.PDF)
    
    @validator('week_start')
    def validate_monday(cls, v):
        if v.weekday() != 0:
            raise ValueError('Week start must be a Monday')
        return v


class WeeklyCoverageReportResponse(BaseResponse):
    """Weekly coverage report response"""
    week_start: date
    week_end: date
    
    # Coverage by day
    daily_coverage: Dict[str, List[Dict[str, str]]]
    
    # On-call schedule
    on_call_schedule: List[Dict[str, Any]]
    
    # Staff summary
    total_staff_scheduled: int
    physicians_per_day: Dict[str, int]
    nurses_per_day: Dict[str, int]
    midwives_per_day: Dict[str, int]
    
    # Compliance check
    meets_minimum_requirements: bool
    coverage_gaps: List[Dict[str, str]]
    
    file_url: Optional[str]


class DailyScheduleReportRequest(BaseModel):
    """Daily master schedule report request"""
    schedule_date: date = Field(default_factory=date.today)
    practitioner_id: Optional[str] = Field(None, description="Specific practitioner")
    include_appointments: bool = Field(True)
    include_walk_ins: bool = Field(True)
    include_breaks: bool = Field(True)
    format: ReportFormat = Field(ReportFormat.PDF)


class DailyScheduleReportResponse(BaseResponse):
    """Daily schedule report response"""
    schedule_date: date
    
    # If practitioner specific
    practitioner_name: Optional[str]
    practitioner_schedule: Optional[Dict[str, Any]]
    
    # Master schedule
    practitioners_on_duty: List[Dict[str, Any]]
    total_appointments: int
    total_available_slots: int
    walk_in_availability: bool
    
    # Time slots
    schedule_grid: List[Dict[str, Any]]
    
    file_url: Optional[str]


# ==================== PRESCRIPTION LABELS ====================

class PrescriptionLabelRequest(BaseModel):
    """Prescription label generation request"""
    prescription_id: str = Field(..., description="Prescription ID")
    include_receipt: bool = Field(True, description="Include receipt portion")
    format: ReportFormat = Field(ReportFormat.PRINT)


class PrescriptionLabelResponse(BaseResponse):
    """Prescription label response"""
    prescription_number: str
    
    # Label portion
    patient_name: str
    patient_address: str
    patient_phone: str
    
    drug_name: str
    strength: str
    quantity: int
    instructions: str
    
    prescriber: str
    prescriber_license: str
    date_prescribed: date
    expiry_date: date
    refills: str
    
    warning_labels: List[str]
    
    # Receipt portion
    prescription_fee: Optional[Decimal]
    dispensing_fee: Optional[Decimal]
    total_charge: Optional[Decimal]
    insurance_covered: Optional[Decimal]
    patient_pays: Optional[Decimal]
    
    # Pharmacy info
    pharmacy_name: str
    pharmacy_address: str
    pharmacy_phone: str
    
    file_url: Optional[str]


# ==================== STATISTICAL REPORTS ====================

class StatisticalReportRequest(BaseModel):
    """Statistical analysis report request"""
    date_range: DateRangeFilter
    report_categories: List[str] = Field(..., description="Categories to include")
    comparison_period: Optional[DateRangeFilter] = None
    group_by: Optional[str] = Field(None, regex="^(day|week|month|quarter|year)$")
    include_trends: bool = Field(True)
    include_projections: bool = Field(False)
    format: ReportFormat = Field(ReportFormat.EXCEL)


class StatisticalReportResponse(BaseResponse):
    """Statistical report response"""
    report_period: DateRangeFilter
    
    # Patient statistics
    patient_demographics: Dict[str, Any]
    patient_visits: Dict[str, Any]
    patient_satisfaction: Optional[Dict[str, Any]]
    
    # Clinical statistics
    clinical_services: Dict[str, Any]
    procedure_statistics: Dict[str, Any]
    diagnosis_frequency: List[Dict[str, Any]]
    
    # Operational statistics
    staff_utilization: Dict[str, Any]
    appointment_statistics: Dict[str, Any]
    wait_time_analysis: Dict[str, Any]
    
    # Financial statistics
    revenue_analysis: Dict[str, Any]
    payment_methods: Dict[str, Any]
    collection_rates: Dict[str, Any]
    
    # Comparisons
    period_comparison: Optional[Dict[str, Any]]
    
    # Trends
    trend_analysis: Optional[Dict[str, Any]]
    
    # Projections
    projections: Optional[Dict[str, Any]]
    
    file_url: Optional[str]


# ==================== CUSTOM REPORTS ====================

class CustomReportRequest(BaseModel):
    """Custom report generation request"""
    report_name: str = Field(..., min_length=1, max_length=200)
    report_type: str = Field(..., description="Type of custom report")
    parameters: Dict[str, Any] = Field(..., description="Report parameters")
    filters: Optional[Dict[str, Any]] = None
    grouping: Optional[List[str]] = None
    sorting: Optional[List[Dict[str, str]]] = None
    format: ReportFormat = Field(ReportFormat.PDF)
    schedule: Optional[ReportFrequency] = None


class CustomReportResponse(BaseResponse):
    """Custom report response"""
    report_id: str
    report_name: str
    generated_at: datetime
    parameters_used: Dict[str, Any]
    
    # Report data
    data: Dict[str, Any]
    summary: Optional[Dict[str, Any]]
    
    # File info
    file_url: Optional[str]
    file_size: Optional[int]
    
    # Scheduling info
    next_scheduled_run: Optional[datetime]


# ==================== REPORT SCHEDULING ====================

class ReportScheduleRequest(BaseModel):
    """Report scheduling request"""
    report_type: ReportType
    frequency: ReportFrequency
    parameters: Dict[str, Any]
    recipients: List[str] = Field(..., description="Email addresses")
    format: ReportFormat = Field(ReportFormat.PDF)
    start_date: date = Field(default_factory=date.today)
    end_date: Optional[date] = None
    time_of_day: Optional[time] = Field(None, description="Time to generate report")
    enabled: bool = Field(True)


class ReportScheduleResponse(BaseResponse):
    """Report schedule response"""
    schedule_id: str
    report_type: ReportType
    frequency: ReportFrequency
    next_run: datetime
    last_run: Optional[datetime]
    status: str
    created_by: str
    created_at: datetime


# Export all schemas
__all__ = [
    "ReportType",
    "ReportFormat",
    "ReportFrequency",
    
    # Daily logs
    "DailyLabLogRequest",
    "DailyLabLogResponse",
    "DailyDeliveryLogRequest",
    "DailyDeliveryLogResponse",
    "RecoveryRoomLogRequest",
    "RecoveryRoomLogResponse",
    
    # Monthly reports
    "MonthlyActivityReportRequest",
    "MonthlyActivityReportResponse",
    
    # Insurance & Billing
    "PhysicianStatementRequest",
    "PhysicianStatementResponse",
    "PatientStatementRequest",
    "PatientStatementResponse",
    
    # Operational
    "WeeklyCoverageReportRequest",
    "WeeklyCoverageReportResponse",
    "DailyScheduleReportRequest",
    "DailyScheduleReportResponse",
    
    # Prescription labels
    "PrescriptionLabelRequest",
    "PrescriptionLabelResponse",
    
    # Statistical
    "StatisticalReportRequest",
    "StatisticalReportResponse",
    
    # Custom reports
    "CustomReportRequest",
    "CustomReportResponse",
    
    # Scheduling
    "ReportScheduleRequest",
    "ReportScheduleResponse",
]