# backend/repositories/__init__.py
"""
Repositories package for SW Glenmore Wellness Clinic
Exports all repository classes for database operations
"""

from .base_repository import BaseRepository

from .patient_repository import PatientRepository

from .staff_repository import (
    StaffRepository,
    RoleRepository,
    StaffScheduleRepository
)

from .appointment_repository import (
    AppointmentRepository,
    WeeklyCoverageRepository,
    PractitionerDailyScheduleRepository
)

from .visit_repository import (
    VisitRepository,
    DiagnosisRepository,
    ProcedureRepository
)

from .billing_repository import (
    InvoiceRepository,
    PaymentRepository
)

from .prescription_repository import (
    PrescriptionRepository,
    DrugRepository
)

from .clinical_repository import (
    LabTestOrderRepository,
    DeliveryRepository,
    RecoveryRepository
)

__all__ = [
    # Base
    "BaseRepository",
    
    # Patient
    "PatientRepository",
    
    # Staff
    "StaffRepository",
    "RoleRepository",
    "StaffScheduleRepository",
    
    # Appointment
    "AppointmentRepository",
    "WeeklyCoverageRepository",
    "PractitionerDailyScheduleRepository",
    
    # Visit
    "VisitRepository",
    "DiagnosisRepository",
    "ProcedureRepository",
    
    # Billing
    "InvoiceRepository",
    "PaymentRepository",
    
    # Prescription
    "PrescriptionRepository",
    "DrugRepository",
    
    # Clinical
    "LabTestOrderRepository",
    "DeliveryRepository",
    "RecoveryRepository",
]
