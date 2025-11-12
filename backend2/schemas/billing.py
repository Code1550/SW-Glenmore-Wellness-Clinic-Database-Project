# backend/schemas/billing.py
"""Billing and payment schemas for API requests and responses"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum

from .common import BaseResponse, PaginationParams, DateRangeFilter, Address


class PaymentMethod(str, Enum):
    """Payment method options"""
    OUT_OF_POCKET = "out_of_pocket"
    INSURANCE = "insurance"
    GOVERNMENT = "government"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CASH = "cash"
    CHECK = "check"
    E_TRANSFER = "e_transfer"
    PAYMENT_PLAN = "payment_plan"


class InvoiceStatus(str, Enum):
    """Invoice status options"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    WRITTEN_OFF = "written_off"


class PaymentStatus(str, Enum):
    """Payment status options"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class LineItemType(str, Enum):
    """Invoice line item types"""
    CONSULTATION = "consultation"
    PROCEDURE = "procedure"
    PRESCRIPTION = "prescription"
    LAB_TEST = "lab_test"
    VACCINE = "vaccine"
    MEDICAL_SUPPLY = "medical_supply"
    ROOM_CHARGE = "room_charge"
    OTHER = "other"


class InvoiceLineItemRequest(BaseModel):
    """Invoice line item request schema"""
    item_type: LineItemType
    item_id: Optional[str] = Field(None, description="Reference to specific item")
    item_code: Optional[str] = Field(None, description="CPT, drug code, etc.")
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(1, ge=0)
    unit_price: Decimal = Field(..., ge=0)
    discount_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    tax_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    is_covered_by_insurance: bool = Field(False)
    insurance_coverage_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=500)


class InvoiceCreateRequest(BaseModel):
    """Invoice creation request schema"""
    patient_id: str = Field(..., description="Patient ID")
    visit_id: Optional[str] = Field(None, description="Related visit ID")
    due_date: date = Field(..., description="Payment due date")
    payment_method: PaymentMethod = Field(...)
    
    # Line items
    line_items: List[InvoiceLineItemRequest] = Field(..., min_items=1)
    
    # Billing address (if different from patient address)
    billing_name: Optional[str] = Field(None, max_length=200)
    billing_address: Optional[str] = Field(None, max_length=500)
    billing_city: Optional[str] = Field(None, max_length=100)
    billing_province: Optional[str] = Field(None, max_length=50)
    billing_postal_code: Optional[str] = Field(None, regex="^[A-Z]\\d[A-Z] \\d[A-Z]\\d$")
    billing_email: Optional[EmailStr] = None
    
    # Notes
    notes: Optional[str] = Field(None, max_length=1000)
    patient_notes: Optional[str] = Field(None, max_length=1000, description="Notes visible to patient")
    
    # Options
    send_immediately: bool = Field(False, description="Send invoice immediately")
    auto_charge: bool = Field(False, description="Auto-charge if card on file")
    
    @validator('due_date')
    def validate_due_date(cls, v):
        """Ensure due date is not in the past"""
        if v < date.today():
            raise ValueError('Due date cannot be in the past')
        return v


class InvoiceUpdateRequest(BaseModel):
    """Invoice update request schema"""
    due_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=1000)
    patient_notes: Optional[str] = Field(None, max_length=1000)
    billing_email: Optional[EmailStr] = None
    status: Optional[InvoiceStatus] = None


class PaymentCreateRequest(BaseModel):
    """Payment creation request schema"""
    invoice_id: str = Field(..., description="Invoice ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(...)
    
    # Payment details
    transaction_id: Optional[str] = Field(None, description="External transaction ID")
    reference_number: Optional[str] = Field(None, description="Check number, etc.")
    
    # Credit/Debit card
    card_last_four: Optional[str] = Field(None, regex="^\\d{4}$")
    card_type: Optional[str] = Field(None, description="Visa, Mastercard, etc.")
    
    # Notes
    notes: Optional[str] = Field(None, max_length=500)
    
    # Processing
    process_immediately: bool = Field(True)
    send_receipt: bool = Field(True)


class InsuranceClaimRequest(BaseModel):
    """Insurance claim submission request"""
    invoice_id: str = Field(..., description="Invoice ID")
    insurance_provider: str = Field(..., min_length=1, max_length=200)
    policy_number: str = Field(..., min_length=1, max_length=100)
    group_number: Optional[str] = Field(None, max_length=100)
    policy_holder_name: str = Field(..., min_length=1, max_length=200)
    relationship_to_patient: str = Field(..., description="self, spouse, child, etc.")
    
    # Claim details
    diagnosis_codes: List[str] = Field(..., min_items=1)
    procedure_codes: List[str] = Field(default_factory=list)
    
    # Authorization
    prior_authorization_number: Optional[str] = Field(None)
    referral_number: Optional[str] = Field(None)
    
    # Additional information
    accident_date: Optional[date] = None
    is_work_related: bool = Field(False)
    other_insurance: bool = Field(False)
    notes: Optional[str] = Field(None, max_length=1000)


class GovernmentClaimRequest(BaseModel):
    """Government health coverage claim request"""
    invoice_id: str = Field(..., description="Invoice ID")
    health_card_number: str = Field(..., description="Patient health card number")
    version_code: Optional[str] = Field(None, description="Health card version code")
    service_codes: List[str] = Field(..., min_items=1, description="OHIP service codes")
    diagnostic_codes: List[str] = Field(..., min_items=1)
    referring_physician: Optional[str] = Field(None)
    admission_date: Optional[date] = None


class RefundRequest(BaseModel):
    """Refund request schema"""
    payment_id: str = Field(..., description="Original payment ID")
    amount: Decimal = Field(..., gt=0, description="Refund amount")
    reason: str = Field(..., min_length=1, max_length=500)
    refund_method: Optional[PaymentMethod] = Field(None, description="If different from original")
    process_immediately: bool = Field(True)
    notify_patient: bool = Field(True)


class PaymentPlanRequest(BaseModel):
    """Payment plan setup request"""
    invoice_id: str = Field(..., description="Invoice ID")
    total_amount: Decimal = Field(..., gt=0)
    down_payment: Optional[Decimal] = Field(None, ge=0)
    number_of_installments: int = Field(..., ge=2, le=24)
    installment_frequency: str = Field("monthly", regex="^(weekly|biweekly|monthly)$")
    start_date: date = Field(...)
    auto_charge: bool = Field(False, description="Auto-charge installments")
    
    @validator('down_payment')
    def validate_down_payment(cls, v, values):
        """Ensure down payment is less than total"""
        if v and 'total_amount' in values:
            if v >= values['total_amount']:
                raise ValueError('Down payment must be less than total amount')
        return v


class InvoiceResponse(BaseModel):
    """Invoice response schema"""
    invoice_id: str
    invoice_number: str
    patient_id: str
    patient_name: str
    visit_id: Optional[str]
    
    # Dates
    invoice_date: date
    due_date: date
    
    # Status
    status: InvoiceStatus
    
    # Amounts
    subtotal: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    
    # Payment information
    payment_method: PaymentMethod
    
    # Insurance (if applicable)
    insurance_claim_number: Optional[str]
    insurance_provider: Optional[str]
    co_pay_amount: Optional[Decimal]
    insurance_covered_amount: Optional[Decimal]
    insurance_claim_status: Optional[str]
    
    # Line items count
    line_items_count: int
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    sent_at: Optional[datetime]
    paid_at: Optional[datetime]


class InvoiceDetailResponse(InvoiceResponse):
    """Detailed invoice response with line items"""
    line_items: List[Dict[str, Any]]
    payments: List[Dict[str, Any]]
    billing_address: Dict[str, str]
    notes: Optional[str]
    patient_notes: Optional[str]


class PaymentResponse(BaseModel):
    """Payment response schema"""
    payment_id: str
    invoice_id: str
    patient_id: str
    payment_date: datetime
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_id: Optional[str]
    reference_number: Optional[str]
    processed_by: Optional[str]
    notes: Optional[str]
    is_refund: bool
    refund_reason: Optional[str]
    original_payment_id: Optional[str]


class InvoiceListResponse(BaseResponse):
    """Invoice list response"""
    invoices: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    total_amount_due: Decimal
    total_overdue: Decimal


class PaymentListResponse(BaseResponse):
    """Payment list response"""
    payments: List[PaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    total_amount: Decimal


class MonthlyStatementRequest(BaseModel):
    """Monthly statement request"""
    patient_id: str = Field(..., description="Patient ID")
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020)
    include_paid: bool = Field(False, description="Include paid invoices")
    include_details: bool = Field(True, description="Include line item details")
    format: str = Field("pdf", regex="^(pdf|html|email)$")


class MonthlyStatementResponse(BaseResponse):
    """Monthly statement response"""
    patient_id: str
    patient_name: str
    statement_period: str
    statement_date: date
    
    # Summary
    previous_balance: Decimal
    total_charges: Decimal
    total_payments: Decimal
    total_adjustments: Decimal
    current_balance: Decimal
    
    # Details
    invoices: List[InvoiceResponse]
    payments: List[PaymentResponse]
    
    # Aging
    current_due: Decimal
    over_30_days: Decimal
    over_60_days: Decimal
    over_90_days: Decimal
    
    # File
    file_url: Optional[str]


class BillingSearchRequest(BaseModel):
    """Billing search request"""
    patient_id: Optional[str] = None
    invoice_number: Optional[str] = None
    date_range: Optional[DateRangeFilter] = None
    status: Optional[List[InvoiceStatus]] = None
    payment_method: Optional[List[PaymentMethod]] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    include_paid: bool = Field(False)
    only_overdue: bool = Field(False)
    pagination: Optional[PaginationParams] = None


class InsuranceVerificationRequest(BaseModel):
    """Insurance verification request"""
    patient_id: str = Field(..., description="Patient ID")
    insurance_provider: str = Field(...)
    policy_number: str = Field(...)
    group_number: Optional[str] = None
    date_of_service: date = Field(...)
    procedure_codes: List[str] = Field(default_factory=list)


class InsuranceVerificationResponse(BaseResponse):
    """Insurance verification response"""
    is_active: bool
    coverage_details: Dict[str, Any]
    copay_amount: Optional[Decimal]
    deductible_remaining: Optional[Decimal]
    out_of_pocket_remaining: Optional[Decimal]
    prior_authorization_required: bool
    covered_procedures: List[str]
    verification_date: datetime


class BillingStatisticsRequest(BaseModel):
    """Billing statistics request"""
    date_range: DateRangeFilter
    group_by: Optional[str] = Field(None, regex="^(day|week|month|payment_method|status)$")
    include_refunds: bool = Field(False)


class BillingStatisticsResponse(BaseResponse):
    """Billing statistics response"""
    period: DateRangeFilter
    total_invoiced: Decimal
    total_collected: Decimal
    total_outstanding: Decimal
    total_written_off: Decimal
    
    # Counts
    total_invoices: int
    paid_invoices: int
    overdue_invoices: int
    
    # By payment method
    by_payment_method: Dict[str, Dict[str, Any]]
    
    # Insurance
    insurance_claims_submitted: int
    insurance_claims_paid: int
    insurance_claims_denied: int
    total_insurance_payments: Decimal
    
    # Government
    government_claims_submitted: int
    government_claims_paid: int
    total_government_payments: Decimal
    
    # Averages
    average_invoice_amount: Decimal
    average_payment_time_days: float
    collection_rate: float


class ReceiptRequest(BaseModel):
    """Receipt generation request"""
    payment_id: str = Field(..., description="Payment ID")
    format: str = Field("pdf", regex="^(pdf|html|email)$")
    send_to_email: Optional[EmailStr] = None


class TaxReceiptRequest(BaseModel):
    """Tax receipt request for year"""
    patient_id: str = Field(..., description="Patient ID")
    year: int = Field(..., ge=2020)
    include_insurance_payments: bool = Field(True)
    format: str = Field("pdf", regex="^(pdf|html)$")


# Export all schemas
__all__ = [
    "PaymentMethod",
    "InvoiceStatus",
    "PaymentStatus",
    "LineItemType",
    "InvoiceLineItemRequest",
    "InvoiceCreateRequest",
    "InvoiceUpdateRequest",
    "PaymentCreateRequest",
    "InsuranceClaimRequest",
    "GovernmentClaimRequest",
    "RefundRequest",
    "PaymentPlanRequest",
    "InvoiceResponse",
    "InvoiceDetailResponse",
    "PaymentResponse",
    "InvoiceListResponse",
    "PaymentListResponse",
    "MonthlyStatementRequest",
    "MonthlyStatementResponse",
    "BillingSearchRequest",
    "InsuranceVerificationRequest",
    "InsuranceVerificationResponse",
    "BillingStatisticsRequest",
    "BillingStatisticsResponse",
    "ReceiptRequest",
    "TaxReceiptRequest",
]