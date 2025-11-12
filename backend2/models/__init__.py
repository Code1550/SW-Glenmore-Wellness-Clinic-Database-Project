# backend/models/__init__.py
"""
Models package for SW Glenmore Wellness Clinic
Exports all database models and request/response schemas
"""

# Base model
from .base import MongoBaseModel, PyObjectId

# Staff models
from .staff import (
    Staff,
    Role,
    StaffRole,
    StaffWithRoles,
    StaffCreateRequest,
    StaffUpdateRequest,
    RoleType,
    Specialization
)

# Patient models
from .patient import (
    Patient,
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientSearchRequest,
    Gender,
    BloodType,
    MaritalStatus
)

# Appointment models
from .appointment import (
    Appointment,
    WeeklyCoverage,
    PractitionerDailySchedule,
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
    WalkInRequest,
    ScheduleFilterRequest,
    AppointmentStatus,
    AppointmentType
)

# Visit models
from .visit import (
    Visit,
    Diagnosis,
    Procedure,
    VisitDiagnosis,
    VisitProcedure,
    VisitCreateRequest,
    VisitUpdateRequest,
    AddDiagnosisRequest,
    AddProcedureRequest,
    VisitType,
    VisitStatus,
    DiagnosisType
)

# Billing models
from .billing import (
    Invoice,
    InvoiceLine,
    Payment,
    InvoiceCreateRequest,
    PaymentCreateRequest,
    InsuranceClaimRequest,
    MonthlyStatementRequest,
    PaymentMethod,
    InvoiceStatus,
    PaymentStatus,
    LineItemType
)

# Prescription models
from .prescription import (
    Prescription,
    Drug,
    PrescriptionCreateRequest,
    PrescriptionFillRequest,
    PrescriptionRefillRequest,
    PrescriptionLabelData,
    DrugSearchRequest,
    DrugSchedule,
    DrugForm,
    RouteOfAdministration,
    PrescriptionStatus
)

# Lab models
from .lab import (
    LabTestOrder,
    LabTestOrderCreateRequest,
    SpecimenCollectionRequest,
    LabResultEntryRequest,
    LabTestSearchRequest,
    DailyLabLogRequest,
    TestStatus,
    TestPriority,
    SpecimenType,
    TestCategory
)

# Delivery models
from .delivery import (
    Delivery,
    DeliveryAdmissionRequest,
    DeliveryRecordRequest,
    BabyAssessmentRequest,
    DeliveryDischargeRequest,
    DailyDeliveryLogRequest,
    DeliveryType,
    DeliveryComplication,
    BabyGender
)

# Recovery models
from .recovery import (
    RecoveryStay,
    RecoveryObservation,
    RecoveryAdmissionRequest,
    RecoveryObservationRequest,
    RecoveryDischargeRequest,
    RecoveryMedicationRequest,
    RecoveryRoomLogRequest,
    RecoverySearchRequest,
    RecoveryReason,
    RecoveryStatus,
    ObservationType,
    PainScale,
    ConsciousnessLevel
)

# Export all models for easy import
__all__ = [
    # Base
    "MongoBaseModel",
    "PyObjectId",
    
    # Staff
    "Staff",
    "Role",
    "StaffRole",
    "StaffWithRoles",
    "StaffCreateRequest",
    "StaffUpdateRequest",
    "RoleType",
    "Specialization",
    
    # Patient
    "Patient",
    "PatientCreateRequest",
    "PatientUpdateRequest",
    "PatientSearchRequest",
    "Gender",
    "BloodType",
    "MaritalStatus",
    
    # Appointment
    "Appointment",
    "WeeklyCoverage",
    "PractitionerDailySchedule",
    "AppointmentCreateRequest",
    "AppointmentUpdateRequest",
    "WalkInRequest",
    "ScheduleFilterRequest",
    "AppointmentStatus",
    "AppointmentType",
    
    # Visit
    "Visit",
    "Diagnosis",
    "Procedure",
    "VisitDiagnosis",
    "VisitProcedure",
    "VisitCreateRequest",
    "VisitUpdateRequest",
    "AddDiagnosisRequest",
    "AddProcedureRequest",
    "VisitType",
    "VisitStatus",
    "DiagnosisType",
    
    # Billing
    "Invoice",
    "InvoiceLine",
    "Payment",
    "InvoiceCreateRequest",
    "PaymentCreateRequest",
    "InsuranceClaimRequest",
    "MonthlyStatementRequest",
    "PaymentMethod",
    "InvoiceStatus",
    "PaymentStatus",
    "LineItemType",
    
    # Prescription
    "Prescription",
    "Drug",
    "PrescriptionCreateRequest",
    "PrescriptionFillRequest",
    "PrescriptionRefillRequest",
    "PrescriptionLabelData",
    "DrugSearchRequest",
    "DrugSchedule",
    "DrugForm",
    "RouteOfAdministration",
    "PrescriptionStatus",
    
    # Lab
    "LabTestOrder",
    "LabTestOrderCreateRequest",
    "SpecimenCollectionRequest",
    "LabResultEntryRequest",
    "LabTestSearchRequest",
    "DailyLabLogRequest",
    "TestStatus",
    "TestPriority",
    "SpecimenType",
    "TestCategory",
    
    # Delivery
    "Delivery",
    "DeliveryAdmissionRequest",
    "DeliveryRecordRequest",
    "BabyAssessmentRequest",
    "DeliveryDischargeRequest",
    "DailyDeliveryLogRequest",
    "DeliveryType",
    "DeliveryComplication",
    "BabyGender",
    
    # Recovery
    "RecoveryStay",
    "RecoveryObservation",
    "RecoveryAdmissionRequest",
    "RecoveryObservationRequest",
    "RecoveryDischargeRequest",
    "RecoveryMedicationRequest",
    "RecoveryRoomLogRequest",
    "RecoverySearchRequest",
    "RecoveryReason",
    "RecoveryStatus",
    "ObservationType",
    "PainScale",
    "ConsciousnessLevel",
]