# backend/schemas/visit.py
"""Visit management schemas for API requests and responses"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import BaseResponse, VitalSigns, PaginationParams, DateRangeFilter


class VisitType(str, Enum):
    """Visit type options"""
    REGULAR = "regular"
    EMERGENCY = "emergency"
    FOLLOW_UP = "follow_up"
    CHECKUP = "checkup"
    IMMUNIZATION = "immunization"
    PRENATAL = "prenatal"
    POSTNATAL = "postnatal"
    DELIVERY = "delivery"
    LAB_ONLY = "lab_only"
    PROCEDURE = "procedure"
    CONSULTATION = "consultation"


class VisitStatus(str, Enum):
    """Visit status options"""
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    AWAITING_LAB = "awaiting_lab"
    AWAITING_PRESCRIPTION = "awaiting_prescription"
    AWAITING_PROCEDURE = "awaiting_procedure"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class DiagnosisType(str, Enum):
    """Diagnosis type options"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    ADMITTING = "admitting"
    DIFFERENTIAL = "differential"
    WORKING = "working"
    NURSING = "nursing"
    FINAL = "final"


class VisitCreateRequest(BaseModel):
    """Visit creation request schema"""
    patient_id: str = Field(..., description="Patient ID")
    staff_id: str = Field(..., description="Primary practitioner ID")
    appointment_id: Optional[str] = Field(None, description="Related appointment ID")
    visit_type: VisitType = Field(VisitType.REGULAR)
    chief_complaint: str = Field(..., min_length=1, max_length=500)
    presenting_symptoms: List[str] = Field(default_factory=list)
    vitals: Optional[VitalSigns] = None
    is_walk_in: bool = Field(False)
    urgency_level: str = Field("normal", regex="^(low|normal|high|critical)$")
    
    class Config:
        schema_extra = {
            "example": {
                "patient_id": "PAT001",
                "staff_id": "STF001",
                "visit_type": "regular",
                "chief_complaint": "Persistent cough for 2 weeks",
                "presenting_symptoms": ["cough", "fatigue", "mild fever"],
                "urgency_level": "normal"
            }
        }


class VisitCheckInRequest(BaseModel):
    """Visit check-in request schema"""
    visit_id: str = Field(..., description="Visit ID")
    vitals: VitalSigns = Field(..., description="Initial vital signs")
    weight_changed: Optional[bool] = Field(None, description="Significant weight change")
    allergies_updated: Optional[bool] = Field(None, description="Allergies verification")
    medications_reviewed: Optional[bool] = Field(None, description="Medications reviewed")
    nurse_notes: Optional[str] = Field(None, max_length=1000)


class VisitUpdateRequest(BaseModel):
    """Visit update request schema"""
    status: Optional[VisitStatus] = None
    history_of_present_illness: Optional[str] = Field(None, max_length=2000)
    review_of_systems: Optional[str] = Field(None, max_length=2000)
    physical_exam_findings: Optional[str] = Field(None, max_length=2000)
    assessment_plan: Optional[str] = Field(None, max_length=2000)
    additional_notes: Optional[str] = Field(None, max_length=2000)
    follow_up_required: Optional[bool] = None
    follow_up_instructions: Optional[str] = Field(None, max_length=1000)
    referrals: Optional[List[Dict[str, str]]] = None


class VisitCompleteRequest(BaseModel):
    """Visit completion request schema"""
    visit_id: str = Field(..., description="Visit ID")
    assessment_plan: str = Field(..., min_length=1, max_length=2000)
    follow_up_required: bool = Field(False)
    follow_up_instructions: Optional[str] = Field(None, max_length=1000)
    follow_up_days: Optional[int] = Field(None, ge=1, le=365)
    patient_education_provided: bool = Field(False)
    discharge_instructions: Optional[str] = Field(None, max_length=1000)
    trigger_billing: bool = Field(True, description="Trigger invoice generation")


class DiagnosisAddRequest(BaseModel):
    """Add diagnosis to visit request"""
    visit_id: str = Field(..., description="Visit ID")
    diagnosis_code: str = Field(..., description="ICD-10 or other code")
    diagnosis_description: str = Field(..., min_length=1, max_length=500)
    diagnosis_type: DiagnosisType = Field(DiagnosisType.PRIMARY)
    notes: Optional[str] = Field(None, max_length=500)
    severity: Optional[str] = Field(None, regex="^(mild|moderate|severe|critical)$")
    is_chronic: bool = Field(False)
    requires_followup: bool = Field(False)


class ProcedureAddRequest(BaseModel):
    """Add procedure to visit request"""
    visit_id: str = Field(..., description="Visit ID")
    procedure_code: str = Field(..., description="CPT or other code")
    procedure_description: str = Field(..., min_length=1, max_length=500)
    performed_by: str = Field(..., description="Staff ID who performed")
    quantity: int = Field(1, ge=1)
    duration_minutes: Optional[int] = Field(None, ge=1)
    fee: Decimal = Field(..., ge=0, description="Procedure fee")
    notes: Optional[str] = Field(None, max_length=500)
    complications: Optional[str] = Field(None, max_length=500)
    consent_obtained: bool = Field(False)


class VisitResponse(BaseModel):
    """Visit response schema"""
    visit_id: str
    patient_id: str
    patient_name: str
    staff_id: str
    staff_name: str
    appointment_id: Optional[str]
    
    # Timing
    visit_date: date
    check_in_time: datetime
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration_minutes: Optional[int]
    
    # Visit details
    visit_type: VisitType
    status: VisitStatus
    chief_complaint: str
    presenting_symptoms: List[str]
    
    # Clinical information
    vitals: Optional[Dict[str, Any]]
    history_of_present_illness: Optional[str]
    review_of_systems: Optional[str]
    physical_exam_findings: Optional[str]
    assessment_plan: Optional[str]
    
    # Additional staff
    nurse_id: Optional[str]
    additional_staff_ids: List[str]
    
    # Follow-up
    follow_up_required: bool
    follow_up_instructions: Optional[str]
    referrals: List[dict]
    
    # Billing
    is_billed: bool
    billed_at: Optional[datetime]
    invoice_id: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime


class VisitWithDetailsResponse(VisitResponse):
    """Visit with full details including diagnoses and procedures"""
    diagnoses: List[Dict[str, Any]]
    procedures: List[Dict[str, Any]]
    prescriptions: List[Dict[str, Any]]
    lab_orders: List[Dict[str, Any]]
    total_charges: Optional[Decimal]


class VisitListResponse(BaseResponse):
    """Visit list response schema"""
    visits: List[VisitResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VisitSearchRequest(BaseModel):
    """Visit search request schema"""
    patient_id: Optional[str] = None
    staff_id: Optional[str] = None
    date_range: Optional[DateRangeFilter] = None
    visit_type: Optional[List[VisitType]] = None
    status: Optional[List[VisitStatus]] = None
    is_billed: Optional[bool] = None
    has_follow_up: Optional[bool] = None
    search_text: Optional[str] = Field(None, description="Search in complaints, symptoms, notes")
    pagination: Optional[PaginationParams] = None


class DiagnosisSearchRequest(BaseModel):
    """Diagnosis search request schema"""
    search_term: str = Field(..., min_length=1, description="Search in code or description")
    category: Optional[str] = None
    is_chronic: Optional[bool] = None
    is_infectious: Optional[bool] = None
    limit: int = Field(20, ge=1, le=100)


class DiagnosisResponse(BaseModel):
    """Diagnosis response schema"""
    diagnosis_id: str
    code: str
    description: str
    category: Optional[str]
    is_chronic: bool
    is_infectious: bool
    requires_followup: bool


class ProcedureSearchRequest(BaseModel):
    """Procedure search request schema"""
    search_term: str = Field(..., min_length=1, description="Search in code or description")
    category: Optional[str] = None
    is_covered_by_insurance: Optional[bool] = None
    requires_consent: Optional[bool] = None
    limit: int = Field(20, ge=1, le=100)


class ProcedureResponse(BaseModel):
    """Procedure response schema"""
    procedure_id: str
    code: str
    description: str
    category: Optional[str]
    typical_duration_minutes: int
    standard_fee: Decimal
    is_covered_by_ohip: bool
    requires_consent: bool
    requires_preparation: bool
    preparation_instructions: Optional[str]


class VisitSummaryRequest(BaseModel):
    """Visit summary generation request"""
    visit_id: str = Field(..., description="Visit ID")
    include_diagnoses: bool = Field(True)
    include_procedures: bool = Field(True)
    include_prescriptions: bool = Field(True)
    include_lab_results: bool = Field(True)
    include_vitals: bool = Field(True)
    format: str = Field("pdf", regex="^(pdf|html|text)$")


class VisitSummaryResponse(BaseResponse):
    """Visit summary response"""
    visit_id: str
    summary: Dict[str, Any]
    generated_at: datetime
    file_url: Optional[str]


class ClinicalNoteRequest(BaseModel):
    """Clinical note request"""
    visit_id: str = Field(..., description="Visit ID")
    note_type: str = Field(..., regex="^(progress|consultation|discharge|operative|procedure)$")
    content: str = Field(..., min_length=1, max_length=5000)
    is_draft: bool = Field(False)
    sign_off: bool = Field(False)


class ReferralRequest(BaseModel):
    """Referral request schema"""
    visit_id: str = Field(..., description="Visit ID")
    specialty: str = Field(..., min_length=1, max_length=100)
    provider_name: Optional[str] = Field(None, max_length=200)
    provider_phone: Optional[str] = Field(None)
    reason: str = Field(..., min_length=1, max_length=1000)
    urgency: str = Field("routine", regex="^(routine|urgent|emergent)$")
    clinical_information: str = Field(..., min_length=1, max_length=2000)
    send_records: bool = Field(True)


class VisitStatisticsRequest(BaseModel):
    """Visit statistics request"""
    date_range: DateRangeFilter
    group_by: Optional[str] = Field(None, regex="^(day|week|month|type|staff|diagnosis)$")
    staff_id: Optional[str] = None
    include_diagnoses: bool = Field(False)
    include_procedures: bool = Field(False)


class VisitStatisticsResponse(BaseResponse):
    """Visit statistics response"""
    period: DateRangeFilter
    total_visits: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    average_duration_minutes: float
    follow_ups_required: int
    unbilled_visits: int
    top_diagnoses: Optional[List[Dict[str, Any]]]
    top_procedures: Optional[List[Dict[str, Any]]]
    revenue_generated: Optional[Decimal]


class PatientHistoryRequest(BaseModel):
    """Patient visit history request"""
    patient_id: str = Field(..., description="Patient ID")
    date_range: Optional[DateRangeFilter] = None
    visit_type: Optional[List[VisitType]] = None
    include_details: bool = Field(False)
    pagination: Optional[PaginationParams] = None


class PatientHistoryResponse(BaseResponse):
    """Patient visit history response"""
    patient_id: str
    patient_name: str
    total_visits: int
    visits: List[VisitResponse]
    chronic_conditions: List[str]
    allergies: List[str]
    current_medications: List[str]
    last_visit_date: Optional[date]
    next_appointment: Optional[Dict[str, Any]]


# Export all schemas
__all__ = [
    "VisitType",
    "VisitStatus",
    "DiagnosisType",
    "VisitCreateRequest",
    "VisitCheckInRequest",
    "VisitUpdateRequest",
    "VisitCompleteRequest",
    "DiagnosisAddRequest",
    "ProcedureAddRequest",
    "VisitResponse",
    "VisitWithDetailsResponse",
    "VisitListResponse",
    "VisitSearchRequest",
    "DiagnosisSearchRequest",
    "DiagnosisResponse",
    "ProcedureSearchRequest",
    "ProcedureResponse",
    "VisitSummaryRequest",
    "VisitSummaryResponse",
    "ClinicalNoteRequest",
    "ReferralRequest",
    "VisitStatisticsRequest",
    "VisitStatisticsResponse",
    "PatientHistoryRequest",
    "PatientHistoryResponse",
]