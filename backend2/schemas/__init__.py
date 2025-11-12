# backend/schemas/__init__.py
"""
Schemas package for SW Glenmore Wellness Clinic
Exports all request/response schemas for API validation
"""

# Common schemas
from .common import (
    ResponseStatus,
    PaginationParams,
    DateRangeFilter,
    BaseResponse,
    SingleItemResponse,
    ListResponse,
    ErrorDetail,
    ErrorResponse,
    BulkOperationResult,
    SearchRequest,
    DeleteResponse,
    FileUploadResponse,
    StatisticsResponse,
    HealthCheckResponse,
    Address,
    ContactInfo,
    EmergencyContact,
    InsuranceInfo,
    VitalSigns,
    TimeSlot,
    AuditLog,
    NotificationRequest,
    ReportParameters
)

# Auth schemas
from .auth import (
    TokenType,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserPermission,
    UserRole,
    CurrentUser,
    SessionInfo,
    TwoFactorAuthRequest,
    TwoFactorAuthSetupResponse,
    AccessControlRequest,
    AccessControlResponse,
    ApiKeyRequest,
    ApiKeyResponse,
    SecurityAuditLog
)

# Patient schemas
from .patient import (
    Gender,
    BloodType,
    MaritalStatus,
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientResponse,
    PatientSearchRequest,
    PatientListResponse,
    PatientMedicalHistoryRequest,
    PatientInsuranceUpdateRequest,
    PatientEmergencyContactUpdateRequest,
    PatientConsentRequest,
    PatientDocumentUploadRequest,
    PatientStatisticsResponse,
    PatientPortalAccessRequest,
    PatientMergeRequest
)

# Appointment schemas
from .appointment import (
    AppointmentStatus,
    AppointmentType,
    RecurrencePattern,
    AppointmentCreateRequest,
    AppointmentUpdateRequest,
    AppointmentRescheduleRequest,
    AppointmentCancelRequest,
    WalkInRegistrationRequest,
    AppointmentResponse,
    AppointmentListResponse,
    AppointmentSearchRequest,
    AvailableSlotRequest,
    AvailableSlotResponse,
    AvailableSlotsListResponse,
    DailyScheduleRequest,
    DailyScheduleResponse,
    WeeklyCoverageRequest,
    WeeklyCoverageResponse,
    PractitionerScheduleUpdateRequest,
    AppointmentConfirmationRequest,
    AppointmentCheckInRequest,
    AppointmentStatisticsRequest,
    AppointmentStatisticsResponse,
    WaitTimeResponse
)

# Visit schemas
from .visit import (
    VisitType,
    VisitStatus,
    DiagnosisType,
    VisitCreateRequest,
    VisitCheckInRequest,
    VisitUpdateRequest,
    VisitCompleteRequest,
    DiagnosisAddRequest,
    ProcedureAddRequest,
    VisitResponse,
    VisitWithDetailsResponse,
    VisitListResponse,
    VisitSearchRequest,
    DiagnosisSearchRequest,
    DiagnosisResponse,
    ProcedureSearchRequest,
    ProcedureResponse,
    VisitSummaryRequest,
    VisitSummaryResponse,
    ClinicalNoteRequest,
    ReferralRequest,
    VisitStatisticsRequest,
    VisitStatisticsResponse,
    PatientHistoryRequest,
    PatientHistoryResponse
)

# Billing schemas
from .billing import (
    PaymentMethod,
    InvoiceStatus,
    PaymentStatus,
    LineItemType,
    InvoiceLineItemRequest,
    InvoiceCreateRequest,
    InvoiceUpdateRequest,
    PaymentCreateRequest,
    InsuranceClaimRequest,
    GovernmentClaimRequest,
    RefundRequest,
    PaymentPlanRequest,
    InvoiceResponse,
    InvoiceDetailResponse,
    PaymentResponse,
    InvoiceListResponse,
    PaymentListResponse,
    MonthlyStatementRequest,
    MonthlyStatementResponse,
    BillingSearchRequest,
    InsuranceVerificationRequest,
    InsuranceVerificationResponse,
    BillingStatisticsRequest,
    BillingStatisticsResponse,
    ReceiptRequest,
    TaxReceiptRequest
)

# Clinical schemas
from .clinical import (
    # Prescriptions
    DrugForm,
    RouteOfAdministration,
    PrescriptionStatus,
    PrescriptionCreateRequest,
    PrescriptionFillRequest,
    PrescriptionRefillRequest,
    PrescriptionResponse,
    DrugSearchRequest,
    DrugResponse,
    
    # Lab Tests
    TestStatus,
    TestPriority,
    SpecimenType,
    LabTestOrderRequest,
    SpecimenCollectionRequest,
    LabResultEntryRequest,
    LabTestResponse,
    LabReportRequest,
    
    # Deliveries
    DeliveryType,
    DeliveryComplication,
    BabyGender,
    DeliveryAdmissionRequest,
    DeliveryRecordRequest,
    BabyAssessmentRequest,
    DeliveryResponse,
    
    # Recovery
    RecoveryReason,
    RecoveryStatus,
    ObservationType,
    PainScale,
    ConsciousnessLevel,
    RecoveryAdmissionRequest,
    RecoveryObservationRequest,
    RecoveryDischargeRequest,
    RecoveryStayResponse,
    RecoveryObservationResponse,
    
    # Reports
    DailyLogRequest,
    MonthlyActivityReportRequest,
    ClinicalStatisticsResponse
)

# Report schemas
from .reports import (
    ReportType,
    ReportFormat,
    ReportFrequency,
    
    # Daily logs
    DailyLabLogRequest,
    DailyLabLogResponse,
    DailyDeliveryLogRequest,
    DailyDeliveryLogResponse,
    RecoveryRoomLogRequest,
    RecoveryRoomLogResponse,
    
    # Monthly reports
    MonthlyActivityReportRequest as MonthlyReportRequest,
    MonthlyActivityReportResponse as MonthlyReportResponse,
    
    # Insurance & Billing reports
    PhysicianStatementRequest,
    PhysicianStatementResponse,
    PatientStatementRequest,
    PatientStatementResponse,
    
    # Operational reports
    WeeklyCoverageReportRequest,
    WeeklyCoverageReportResponse,
    DailyScheduleReportRequest,
    DailyScheduleReportResponse,
    
    # Prescription labels
    PrescriptionLabelRequest,
    PrescriptionLabelResponse,
    
    # Statistical reports
    StatisticalReportRequest,
    StatisticalReportResponse,
    
    # Custom reports
    CustomReportRequest,
    CustomReportResponse,
    
    # Report scheduling
    ReportScheduleRequest,
    ReportScheduleResponse
)

# Export all schemas
__all__ = [
    # Common
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
    
    # Auth
    "TokenType",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "RefreshTokenResponse",
    "LogoutRequest",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "UserPermission",
    "UserRole",
    "CurrentUser",
    "SessionInfo",
    "TwoFactorAuthRequest",
    "TwoFactorAuthSetupResponse",
    "AccessControlRequest",
    "AccessControlResponse",
    "ApiKeyRequest",
    "ApiKeyResponse",
    "SecurityAuditLog",
    
    # ... (continuing with all other exports)
]