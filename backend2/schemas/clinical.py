# backend/schemas/clinical.py
"""Clinical operations schemas for prescriptions, lab tests, deliveries, and recovery"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, time
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

from .common import BaseResponse, VitalSigns, PaginationParams, DateRangeFilter


# ==================== PRESCRIPTION SCHEMAS ====================

class DrugForm(str, Enum):
    """Drug form/type options"""
    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    INJECTION = "injection"
    CREAM = "cream"
    OINTMENT = "ointment"
    DROPS = "drops"
    INHALER = "inhaler"
    PATCH = "patch"
    SUPPOSITORY = "suppository"
    OTHER = "other"


class RouteOfAdministration(str, Enum):
    """Drug administration routes"""
    ORAL = "oral"
    SUBLINGUAL = "sublingual"
    RECTAL = "rectal"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    SUBCUTANEOUS = "subcutaneous"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    NASAL = "nasal"
    OPHTHALMIC = "ophthalmic"
    OTIC = "otic"


class PrescriptionStatus(str, Enum):
    """Prescription status options"""
    PENDING = "pending"
    ACTIVE = "active"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    ON_HOLD = "on_hold"


class PrescriptionCreateRequest(BaseModel):
    """Prescription creation request"""
    visit_id: str = Field(..., description="Visit ID")
    patient_id: str = Field(..., description="Patient ID")
    drug_id: str = Field(..., description="Drug ID from formulary")
    
    # Dosage information
    dosage: str = Field(..., description="Dosage amount (e.g., '500mg')")
    frequency: str = Field(..., description="How often (e.g., 'twice daily')")
    route: RouteOfAdministration = Field(...)
    duration_days: Optional[int] = Field(None, ge=1, le=365)
    
    # Quantity and refills
    quantity_prescribed: int = Field(..., ge=1)
    refills_authorized: int = Field(0, ge=0, le=12)
    
    # Instructions
    instructions: str = Field(..., min_length=1, max_length=500)
    pharmacy_notes: Optional[str] = Field(None, max_length=500)
    
    # Options
    generic_substitution_allowed: bool = Field(True)
    brand_medically_necessary: bool = Field(False)
    prn: bool = Field(False, description="Take as needed")
    prn_instructions: Optional[str] = Field(None, max_length=200)
    
    # Special instructions
    take_with_food: Optional[bool] = None
    avoid_alcohol: Optional[bool] = None
    warning_labels: List[str] = Field(default_factory=list)


class PrescriptionFillRequest(BaseModel):
    """Prescription fill request"""
    prescription_id: str = Field(..., description="Prescription ID")
    quantity_dispensed: int = Field(..., ge=1)
    pharmacy_id: Optional[str] = Field(None, description="Pharmacy ID")
    substituted_drug_id: Optional[str] = Field(None, description="If generic substituted")
    notes: Optional[str] = Field(None, max_length=500)


class PrescriptionRefillRequest(BaseModel):
    """Prescription refill request"""
    prescription_id: str = Field(..., description="Prescription ID")
    quantity: int = Field(..., ge=1)
    early_refill_reason: Optional[str] = Field(None, max_length=200)


class PrescriptionResponse(BaseModel):
    """Prescription response"""
    prescription_id: str
    prescription_number: str
    patient_id: str
    patient_name: str
    visit_id: str
    drug_name: str
    drug_strength: str
    
    # Dosage
    dosage: str
    frequency: str
    route: RouteOfAdministration
    duration_days: Optional[int]
    
    # Quantity
    quantity_prescribed: int
    quantity_dispensed: Optional[int]
    refills_authorized: int
    refills_remaining: int
    
    # Status
    status: PrescriptionStatus
    
    # Dates
    prescription_date: datetime
    expiry_date: date
    last_filled: Optional[datetime]
    
    # Provider
    prescribed_by: str
    prescriber_name: str
    
    # Instructions
    instructions: str
    prn: bool


class DrugSearchRequest(BaseModel):
    """Drug search request"""
    search_term: str = Field(..., min_length=1)
    drug_class: Optional[str] = None
    form: Optional[DrugForm] = None
    in_stock_only: bool = Field(False)
    covered_by_insurance: Optional[bool] = None
    limit: int = Field(20, ge=1, le=100)


class DrugResponse(BaseModel):
    """Drug/medication response"""
    drug_id: str
    generic_name: str
    brand_name: Optional[str]
    drug_class: str
    form: DrugForm
    strength: str
    strength_units: str
    route: RouteOfAdministration
    in_stock: bool
    unit_price: Decimal
    is_controlled: bool
    is_covered_by_ohip: bool
    requires_prior_auth: bool
    side_effects: List[str]
    contraindications: List[str]


# ==================== LAB TEST SCHEMAS ====================

class TestStatus(str, Enum):
    """Lab test status options"""
    ORDERED = "ordered"
    SCHEDULED = "scheduled"
    SPECIMEN_COLLECTED = "specimen_collected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    PENDING_REVIEW = "pending_review"


class TestPriority(str, Enum):
    """Test priority levels"""
    ROUTINE = "routine"
    URGENT = "urgent"
    STAT = "stat"


class SpecimenType(str, Enum):
    """Specimen types"""
    BLOOD = "blood"
    URINE = "urine"
    STOOL = "stool"
    SPUTUM = "sputum"
    SWAB = "swab"
    TISSUE = "tissue"
    FLUID = "fluid"
    OTHER = "other"


class LabTestOrderRequest(BaseModel):
    """Lab test order request"""
    patient_id: str = Field(..., description="Patient ID")
    visit_id: Optional[str] = Field(None, description="Visit ID if applicable")
    
    # Test information
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: Optional[str] = Field(None, max_length=50)
    test_category: str = Field(..., description="Test category")
    priority: TestPriority = Field(TestPriority.ROUTINE)
    
    # Clinical information
    clinical_notes: Optional[str] = Field(None, max_length=1000)
    diagnosis_codes: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    
    # Requirements
    fasting_required: bool = Field(False)
    special_instructions: Optional[str] = Field(None, max_length=500)
    
    # Scheduling
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[time] = None


class SpecimenCollectionRequest(BaseModel):
    """Specimen collection request"""
    lab_test_id: str = Field(..., description="Lab test ID")
    specimen_type: SpecimenType = Field(...)
    specimen_id: str = Field(..., description="Specimen tracking ID")
    collection_site: Optional[str] = Field(None, max_length=100)
    collection_notes: Optional[str] = Field(None, max_length=500)


class LabResultEntryRequest(BaseModel):
    """Lab result entry request"""
    lab_test_id: str = Field(..., description="Lab test ID")
    result_value: str = Field(..., description="Result value")
    result_unit: Optional[str] = Field(None, description="Unit of measurement")
    reference_range: Optional[str] = Field(None, description="Normal range")
    result_status: str = Field(..., regex="^(normal|abnormal|critical)$")
    abnormal_flags: List[str] = Field(default_factory=list)
    critical_values: List[str] = Field(default_factory=list)
    interpretation: Optional[str] = Field(None, max_length=1000)
    comments: Optional[str] = Field(None, max_length=500)


class LabTestResponse(BaseModel):
    """Lab test response"""
    lab_test_id: str
    order_number: str
    patient_id: str
    patient_name: str
    visit_id: Optional[str]
    
    # Test details
    test_name: str
    test_code: Optional[str]
    test_category: str
    priority: TestPriority
    status: TestStatus
    
    # Timing
    ordered_at: datetime
    ordered_by: str
    scheduled_date: Optional[date]
    specimen_collected_at: Optional[datetime]
    result_date: Optional[datetime]
    
    # Results
    result: Optional[Dict[str, Any]]
    result_status: Optional[str]
    reference_range: Optional[str]
    abnormal_flags: List[str]
    critical_values: List[str]
    interpretation: Optional[str]
    
    # Review
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    requires_follow_up: bool


class LabReportRequest(BaseModel):
    """Lab report generation request"""
    patient_id: Optional[str] = None
    date_range: DateRangeFilter
    test_category: Optional[str] = None
    include_normal_results: bool = Field(True)
    format: str = Field("pdf", regex="^(pdf|html|csv)$")


# ==================== DELIVERY SCHEMAS ====================

class DeliveryType(str, Enum):
    """Delivery type options"""
    VAGINAL_SPONTANEOUS = "vaginal_spontaneous"
    VAGINAL_ASSISTED = "vaginal_assisted"
    CESAREAN_PLANNED = "cesarean_planned"
    CESAREAN_EMERGENCY = "cesarean_emergency"
    VBAC = "vbac"
    BREECH = "breech"
    MULTIPLE = "multiple"


class DeliveryComplication(str, Enum):
    """Delivery complications"""
    NONE = "none"
    PROLONGED_LABOR = "prolonged_labor"
    FETAL_DISTRESS = "fetal_distress"
    HEMORRHAGE = "hemorrhage"
    PLACENTA_PREVIA = "placenta_previa"
    PLACENTAL_ABRUPTION = "placental_abruption"
    CORD_PROLAPSE = "cord_prolapse"
    SHOULDER_DYSTOCIA = "shoulder_dystocia"
    PREECLAMPSIA = "preeclampsia"
    OTHER = "other"


class BabyGender(str, Enum):
    """Baby gender options"""
    MALE = "male"
    FEMALE = "female"
    UNDETERMINED = "undetermined"


class DeliveryAdmissionRequest(BaseModel):
    """Delivery admission request"""
    patient_id: str = Field(..., description="Mother's patient ID")
    visit_id: str = Field(..., description="Visit ID")
    midwife_id: str = Field(..., description="Primary midwife ID")
    physician_id: Optional[str] = Field(None, description="Physician if involved")
    
    # Labor information
    labor_start_time: Optional[datetime] = None
    membrane_rupture_time: Optional[datetime] = None
    contractions_frequency: Optional[str] = Field(None, description="Contraction frequency")
    cervical_dilation_cm: Optional[int] = Field(None, ge=0, le=10)
    
    # Mother's condition
    mother_vitals: VitalSigns
    epidural_requested: bool = Field(False)
    high_risk_factors: List[str] = Field(default_factory=list)
    delivery_room: str = Field(..., description="Room number/name")


class DeliveryRecordRequest(BaseModel):
    """Delivery record request"""
    delivery_id: str = Field(..., description="Delivery ID")
    delivery_type: DeliveryType = Field(...)
    delivery_datetime: datetime = Field(...)
    
    # Baby information
    baby_gender: BabyGender = Field(...)
    baby_weight_grams: int = Field(..., ge=300, le=7000)
    baby_length_cm: Optional[float] = Field(None, ge=20, le=70)
    
    # APGAR scores
    apgar_1_min: Optional[int] = Field(None, ge=0, le=10)
    apgar_5_min: Optional[int] = Field(None, ge=0, le=10)
    apgar_10_min: Optional[int] = Field(None, ge=0, le=10)
    
    # Delivery details
    labor_duration_hours: Optional[float] = None
    blood_loss_ml: Optional[int] = Field(None, ge=0, le=5000)
    complications: List[DeliveryComplication] = Field(default_factory=list)
    complication_notes: Optional[str] = Field(None, max_length=1000)
    
    # Multiple births
    is_multiple_birth: bool = Field(False)
    birth_order: Optional[int] = Field(None, ge=1, le=8)
    
    # Placenta
    placenta_delivered_time: Optional[datetime] = None
    placenta_complete: bool = Field(True)
    cord_blood_collected: bool = Field(False)
    cord_complications: Optional[str] = Field(None, max_length=200)


class BabyAssessmentRequest(BaseModel):
    """Baby assessment request"""
    delivery_id: str = Field(..., description="Delivery ID")
    baby_vitals: VitalSigns
    baby_complications: List[str] = Field(default_factory=list)
    nicu_transfer: bool = Field(False)
    nicu_transfer_reason: Optional[str] = Field(None, max_length=500)
    skin_to_skin_time: Optional[datetime] = None
    first_feeding_time: Optional[datetime] = None
    newborn_screening_completed: bool = Field(False)


class DeliveryResponse(BaseModel):
    """Delivery response"""
    delivery_id: str
    patient_id: str
    mother_name: str
    visit_id: str
    
    # Team
    midwife_name: str
    physician_name: Optional[str]
    
    # Timing
    admitted_at: datetime
    delivery_datetime: datetime
    labor_duration_hours: Optional[float]
    
    # Delivery details
    delivery_type: DeliveryType
    delivery_room: str
    
    # Baby information
    baby_gender: BabyGender
    baby_weight_grams: int
    baby_weight_lbs: float
    baby_length_cm: Optional[float]
    apgar_scores: Dict[str, Optional[int]]
    
    # Complications
    complications: List[DeliveryComplication]
    nicu_transfer: bool
    
    # Status
    mother_discharged: bool
    baby_discharged: bool
    birth_certificate_filed: bool


# ==================== RECOVERY SCHEMAS ====================

class RecoveryReason(str, Enum):
    """Recovery admission reasons"""
    POST_SURGERY = "post_surgery"
    POST_DELIVERY = "post_delivery"
    POST_PROCEDURE = "post_procedure"
    OBSERVATION = "observation"
    STABILIZATION = "stabilization"
    MEDICATION_REACTION = "medication_reaction"
    OTHER = "other"


class RecoveryStatus(str, Enum):
    """Recovery status options"""
    ADMITTED = "admitted"
    STABLE = "stable"
    IMPROVING = "improving"
    DETERIORATING = "deteriorating"
    READY_FOR_DISCHARGE = "ready_for_discharge"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"


class ObservationType(str, Enum):
    """Observation types"""
    VITALS = "vitals"
    PAIN_ASSESSMENT = "pain_assessment"
    CONSCIOUSNESS = "consciousness"
    BLEEDING = "bleeding"
    MEDICATION_GIVEN = "medication_given"
    INTAKE_OUTPUT = "intake_output"
    WOUND_CHECK = "wound_check"
    NEUROLOGICAL = "neurological"
    RESPIRATORY = "respiratory"
    CARDIOVASCULAR = "cardiovascular"
    OTHER = "other"


class PainScale(str, Enum):
    """Pain scale ratings"""
    NO_PAIN = "0"
    MILD = "1-3"
    MODERATE = "4-6"
    SEVERE = "7-9"
    WORST = "10"


class ConsciousnessLevel(str, Enum):
    """Consciousness levels"""
    ALERT = "alert"
    CONFUSED = "confused"
    DROWSY = "drowsy"
    STUPOROUS = "stuporous"
    UNCONSCIOUS = "unconscious"


class RecoveryAdmissionRequest(BaseModel):
    """Recovery admission request"""
    patient_id: str = Field(..., description="Patient ID")
    visit_id: str = Field(..., description="Visit ID")
    
    # Admission details
    admit_from: str = Field(..., description="Where admitted from")
    admit_reason: RecoveryReason = Field(...)
    admit_diagnosis: str = Field(..., max_length=500)
    bed_number: str = Field(..., max_length=20)
    
    # Medical information
    procedure_performed: Optional[str] = Field(None, max_length=200)
    anesthesia_type: Optional[str] = Field(None, max_length=100)
    
    # Initial assessment
    initial_vitals: VitalSigns
    initial_pain_score: Optional[PainScale] = None
    initial_consciousness: ConsciousnessLevel = Field(ConsciousnessLevel.ALERT)
    
    # Monitoring
    monitoring_frequency_minutes: int = Field(15, ge=5, le=60)
    special_monitoring: List[str] = Field(default_factory=list)
    allergies_verified: bool = Field(False)


class RecoveryObservationRequest(BaseModel):
    """Recovery observation request"""
    stay_id: str = Field(..., description="Recovery stay ID")
    observation_type: ObservationType = Field(...)
    
    # Vitals
    vitals: Optional[VitalSigns] = None
    
    # Assessments
    pain_score: Optional[PainScale] = None
    pain_location: Optional[str] = Field(None, max_length=200)
    consciousness_level: Optional[ConsciousnessLevel] = None
    pupil_response: Optional[str] = Field(None, max_length=100)
    
    # Monitoring
    bleeding_assessment: Optional[str] = Field(None, max_length=200)
    drainage_amount: Optional[str] = Field(None, max_length=100)
    skin_assessment: Optional[str] = Field(None, max_length=200)
    wound_assessment: Optional[str] = Field(None, max_length=200)
    
    # Intake/Output
    intake_ml: Optional[int] = Field(None, ge=0, le=5000)
    output_ml: Optional[int] = Field(None, ge=0, le=5000)
    
    # Medications
    medication_given: Optional[Dict[str, str]] = None
    
    # Alert indicators
    is_critical: bool = Field(False)
    alert_physician: bool = Field(False)
    intervention_performed: Optional[str] = Field(None, max_length=500)
    
    # Notes
    notes: Optional[str] = Field(None, max_length=1000)


class RecoveryDischargeRequest(BaseModel):
    """Recovery discharge request"""
    stay_id: str = Field(..., description="Recovery stay ID")
    discharge_to: str = Field(..., description="Where patient is going")
    discharge_status: str = Field(..., description="Patient condition")
    discharge_vitals: VitalSigns
    discharge_instructions: str = Field(..., max_length=1000)
    follow_up_required: bool = Field(False)
    medications_prescribed: List[str] = Field(default_factory=list)
    patient_education_provided: bool = Field(False)


class RecoveryStayResponse(BaseModel):
    """Recovery stay response"""
    stay_id: str
    patient_id: str
    patient_name: str
    visit_id: str
    
    # Admission
    admit_time: datetime
    admit_from: str
    admit_reason: RecoveryReason
    bed_number: str
    
    # Status
    status: RecoveryStatus
    length_of_stay_hours: Optional[float]
    
    # Medical team
    primary_nurse_name: Optional[str]
    physician_name: Optional[str]
    
    # Observations
    total_observations: int
    last_observation_time: Optional[datetime]
    current_pain_score: Optional[PainScale]
    
    # Discharge
    discharge_time: Optional[datetime]
    discharge_to: Optional[str]
    signed_off_by: Optional[str]


class RecoveryObservationResponse(BaseModel):
    """Recovery observation response"""
    observation_id: str
    stay_id: str
    sequence_number: int
    observation_time: datetime
    observation_type: ObservationType
    observed_by: str
    observer_name: str
    
    # Observations
    vitals: Optional[Dict[str, Any]]
    pain_score: Optional[PainScale]
    consciousness_level: Optional[ConsciousnessLevel]
    
    # Flags
    is_critical: bool
    physician_alerted: bool
    intervention_performed: Optional[str]
    
    # Notes
    notes: Optional[str]


# ==================== REPORT SCHEMAS ====================

class DailyLogRequest(BaseModel):
    """Daily log report request"""
    log_date: date = Field(default_factory=date.today)
    log_type: str = Field(..., regex="^(lab|delivery|recovery)$")
    include_details: bool = Field(True)
    format: str = Field("pdf", regex="^(pdf|html|excel)$")


class MonthlyActivityReportRequest(BaseModel):
    """Monthly activity report request"""
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    include_statistics: bool = Field(True)
    include_financials: bool = Field(True)
    format: str = Field("pdf", regex="^(pdf|html|excel)$")


class ClinicalStatisticsResponse(BaseResponse):
    """Clinical statistics response"""
    period: DateRangeFilter
    
    # Prescriptions
    total_prescriptions: int
    controlled_substances: int
    refills_processed: int
    
    # Lab tests
    total_lab_tests: int
    critical_results: int
    average_turnaround_hours: float
    
    # Deliveries
    total_deliveries: int
    cesarean_rate: float
    nicu_transfer_rate: float
    average_apgar_scores: Dict[str, float]
    
    # Recovery
    total_admissions: int
    average_recovery_hours: float
    complications_rate: float


# Export all schemas
__all__ = [
    # Prescriptions
    "DrugForm",
    "RouteOfAdministration",
    "PrescriptionStatus",
    "PrescriptionCreateRequest",
    "PrescriptionFillRequest",
    "PrescriptionRefillRequest",
    "PrescriptionResponse",
    "DrugSearchRequest",
    "DrugResponse",
    
    # Lab Tests
    "TestStatus",
    "TestPriority",
    "SpecimenType",
    "LabTestOrderRequest",
    "SpecimenCollectionRequest",
    "LabResultEntryRequest",
    "LabTestResponse",
    "LabReportRequest",
    
    # Deliveries
    "DeliveryType",
    "DeliveryComplication",
    "BabyGender",
    "DeliveryAdmissionRequest",
    "DeliveryRecordRequest",
    "BabyAssessmentRequest",
    "DeliveryResponse",
    
    # Recovery
    "RecoveryReason",
    "RecoveryStatus",
    "ObservationType",
    "PainScale",
    "ConsciousnessLevel",
    "RecoveryAdmissionRequest",
    "RecoveryObservationRequest",
    "RecoveryDischargeRequest",
    "RecoveryStayResponse",
    "RecoveryObservationResponse",
    
    # Reports
    "DailyLogRequest",
    "MonthlyActivityReportRequest",
    "ClinicalStatisticsResponse",
]