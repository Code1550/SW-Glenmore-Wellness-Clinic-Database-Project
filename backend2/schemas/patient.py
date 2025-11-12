# backend/schemas/patient.py
"""Patient-related schemas for API requests and responses"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum

from .common import BaseResponse, Address, ContactInfo, EmergencyContact, InsuranceInfo, PaginationParams


class Gender(str, Enum):
    """Gender options"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


class BloodType(str, Enum):
    """Blood type options"""
    A_POSITIVE = "A+"
    A_NEGATIVE = "A-"
    B_POSITIVE = "B+"
    B_NEGATIVE = "B-"
    O_POSITIVE = "O+"
    O_NEGATIVE = "O-"
    AB_POSITIVE = "AB+"
    AB_NEGATIVE = "AB-"
    UNKNOWN = "unknown"


class MaritalStatus(str, Enum):
    """Marital status options"""
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    DOMESTIC_PARTNERSHIP = "domestic_partnership"


class PatientCreateRequest(BaseModel):
    """Patient creation request schema"""
    # Personal Information
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: date = Field(..., description="Patient's date of birth")
    gender: Gender = Field(...)
    marital_status: Optional[MaritalStatus] = None
    
    # Contact Information
    phone: str = Field(..., regex="^\\+?[1-9]\\d{1,14}$")
    alternate_phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    email: Optional[EmailStr] = None
    
    # Address
    address: str = Field(..., min_length=1, max_length=500)
    city: str = Field(..., min_length=1, max_length=100)
    province: str = Field(..., min_length=2, max_length=50)
    postal_code: str = Field(..., regex="^[A-Z]\\d[A-Z] \\d[A-Z]\\d$")
    
    # Medical Information
    health_card_number: Optional[str] = Field(None, max_length=20)
    blood_type: Optional[BloodType] = None
    allergies: List[str] = Field(default_factory=list)
    chronic_conditions: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    
    # Insurance Information
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)
    
    # Emergency Contact
    emergency_contact_name: str = Field(..., min_length=1, max_length=200)
    emergency_contact_phone: str = Field(..., regex="^\\+?[1-9]\\d{1,14}$")
    emergency_contact_relationship: str = Field(..., min_length=1, max_length=100)
    
    # Additional Information
    occupation: Optional[str] = Field(None, max_length=200)
    preferred_language: str = Field("English", max_length=50)
    requires_interpreter: bool = Field(False)
    family_doctor: Optional[str] = Field(None, max_length=200)
    preferred_pharmacy: Optional[str] = Field(None, max_length=300)
    
    # Consent
    consent_to_treat: bool = Field(False)
    consent_to_share_records: bool = Field(False)
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        """Validate patient age"""
        age = (date.today() - v).days / 365.25
        if age < 0:
            raise ValueError('Date of birth cannot be in the future')
        if age > 150:
            raise ValueError('Invalid date of birth')
        return v
    
    @validator('postal_code')
    def format_postal_code(cls, v):
        """Format Canadian postal code"""
        v = v.upper().replace(' ', '')
        if len(v) == 6:
            return f"{v[:3]} {v[3:]}"
        return v


class PatientUpdateRequest(BaseModel):
    """Patient update request schema"""
    # Personal Information
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[Gender] = None
    marital_status: Optional[MaritalStatus] = None
    
    # Contact Information
    phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    alternate_phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    email: Optional[EmailStr] = None
    
    # Address
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=50)
    postal_code: Optional[str] = Field(None, regex="^[A-Z]\\d[A-Z] \\d[A-Z]\\d$")
    
    # Medical Information
    blood_type: Optional[BloodType] = None
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    
    # Insurance Information
    insurance_provider: Optional[str] = Field(None, max_length=200)
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_group_number: Optional[str] = Field(None, max_length=100)
    
    # Emergency Contact
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    emergency_contact_relationship: Optional[str] = Field(None, max_length=100)
    
    # Additional Information
    occupation: Optional[str] = Field(None, max_length=200)
    preferred_language: Optional[str] = Field(None, max_length=50)
    requires_interpreter: Optional[bool] = None
    family_doctor: Optional[str] = Field(None, max_length=200)
    preferred_pharmacy: Optional[str] = Field(None, max_length=300)
    
    # Status
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=2000)


class PatientResponse(BaseModel):
    """Patient response schema"""
    patient_id: str
    first_name: str
    last_name: str
    middle_name: Optional[str]
    date_of_birth: date
    age: int
    gender: Gender
    marital_status: Optional[MaritalStatus]
    
    # Contact
    phone: str
    alternate_phone: Optional[str]
    email: Optional[str]
    
    # Address
    address: str
    city: str
    province: str
    postal_code: str
    
    # Medical
    health_card_number: Optional[str]
    blood_type: Optional[BloodType]
    allergies: List[str]
    chronic_conditions: List[str]
    current_medications: List[str]
    
    # Insurance
    insurance_provider: Optional[str]
    insurance_policy_number: Optional[str]
    insurance_group_number: Optional[str]
    
    # Emergency Contact
    emergency_contact_name: str
    emergency_contact_phone: str
    emergency_contact_relationship: str
    
    # Additional
    occupation: Optional[str]
    preferred_language: str
    requires_interpreter: bool
    is_active: bool
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    
    @property
    def full_name(self) -> str:
        """Get patient's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"


class PatientSearchRequest(BaseModel):
    """Patient search request schema"""
    search_term: Optional[str] = Field(None, description="Search in name, email, phone")
    health_card_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    city: Optional[str] = None
    is_active: Optional[bool] = True
    has_insurance: Optional[bool] = None
    has_chronic_conditions: Optional[bool] = None
    pagination: Optional[PaginationParams] = None


class PatientListResponse(BaseResponse):
    """Patient list response schema"""
    patients: List[PatientResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PatientMedicalHistoryRequest(BaseModel):
    """Patient medical history update request"""
    allergies: Optional[List[str]] = None
    chronic_conditions: Optional[List[str]] = None
    current_medications: Optional[List[str]] = None
    family_history: Optional[List[str]] = None
    surgical_history: Optional[List[str]] = None
    immunization_records: Optional[List[dict]] = None


class PatientInsuranceUpdateRequest(BaseModel):
    """Patient insurance update request"""
    provider: str = Field(..., min_length=1, max_length=200)
    policy_number: str = Field(..., min_length=1, max_length=100)
    group_number: Optional[str] = Field(None, max_length=100)
    policy_holder_name: Optional[str] = Field(None, max_length=200)
    relationship_to_patient: Optional[str] = Field(None, max_length=50)
    coverage_start_date: Optional[date] = None
    coverage_end_date: Optional[date] = None


class PatientEmergencyContactUpdateRequest(BaseModel):
    """Patient emergency contact update request"""
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., regex="^\\+?[1-9]\\d{1,14}$")
    alternate_phone: Optional[str] = Field(None, regex="^\\+?[1-9]\\d{1,14}$")
    relationship: str = Field(..., min_length=1, max_length=100)
    address: Optional[str] = Field(None, max_length=500)


class PatientConsentRequest(BaseModel):
    """Patient consent update request"""
    consent_type: str = Field(..., description="Type of consent")
    granted: bool = Field(..., description="Whether consent is granted")
    valid_until: Optional[date] = Field(None, description="Consent expiration date")
    notes: Optional[str] = Field(None, max_length=500)


class PatientDocumentUploadRequest(BaseModel):
    """Patient document upload request"""
    document_type: str = Field(..., description="Type of document")
    document_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    file_data: str = Field(..., description="Base64 encoded file data")
    file_type: str = Field(..., description="MIME type")


class PatientStatisticsResponse(BaseResponse):
    """Patient statistics response"""
    total_patients: int
    active_patients: int
    new_patients_this_month: int
    patients_with_insurance: int
    patients_with_chronic_conditions: int
    average_age: float
    gender_distribution: dict
    age_groups: dict
    top_chronic_conditions: List[dict]
    insurance_providers: List[dict]


class PatientPortalAccessRequest(BaseModel):
    """Patient portal access request"""
    patient_id: str = Field(..., description="Patient ID")
    create_account: bool = Field(True, description="Create portal account")
    send_invitation: bool = Field(True, description="Send email invitation")
    temporary_password: Optional[str] = Field(None, description="Temporary password")


class PatientMergeRequest(BaseModel):
    """Patient record merge request"""
    primary_patient_id: str = Field(..., description="Primary patient ID to keep")
    duplicate_patient_id: str = Field(..., description="Duplicate patient ID to merge")
    merge_fields: List[str] = Field(..., description="Fields to merge from duplicate")
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for merge")


# Export all schemas
__all__ = [
    "Gender",
    "BloodType",
    "MaritalStatus",
    "PatientCreateRequest",
    "PatientUpdateRequest",
    "PatientResponse",
    "PatientSearchRequest",
    "PatientListResponse",
    "PatientMedicalHistoryRequest",
    "PatientInsuranceUpdateRequest",
    "PatientEmergencyContactUpdateRequest",
    "PatientConsentRequest",
    "PatientDocumentUploadRequest",
    "PatientStatisticsResponse",
    "PatientPortalAccessRequest",
    "PatientMergeRequest",
]