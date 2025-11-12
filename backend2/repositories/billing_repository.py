# backend/repositories/billing_repository.py
"""Repository for Invoice, InvoiceLine, and Payment collection operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base_repository import BaseRepository
from ..models.billing import (
    Invoice, InvoiceLine, Payment,
    InvoiceStatus, PaymentStatus, PaymentMethod, LineItemType
)


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for invoice-specific database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Invoice", Invoice)
        self.invoice_line_collection = database["InvoiceLine"]
        self.payment_collection = database["Payment"]
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Invoice:
        """
        Create a new invoice with auto-generated invoice_id
        
        Args:
            invoice_data: Invoice information
        
        Returns:
            Created invoice
        """
        # Generate invoice number (YYYY-NNNN format)
        year = datetime.now().year
        count = await self.count({"invoice_date": {"$gte": date(year, 1, 1)}})
        invoice_data["invoice_number"] = f"{year}-{str(count + 1).zfill(4)}"
        
        return await self.create(invoice_data, auto_id_field="invoice_id")
    
    async def find_by_invoice_id(self, invoice_id: str) -> Optional[Invoice]:
        """Find invoice by invoice_id"""
        return await self.find_by_id(invoice_id, id_field="invoice_id")
    
    async def find_by_invoice_number(self, invoice_number: str) -> Optional[Invoice]:
        """Find invoice by invoice number"""
        return await self.find_one({"invoice_number": invoice_number})
    
    async def find_patient_invoices(
        self,
        patient_id: str,
        status: Optional[InvoiceStatus] = None,
        from_date: Optional[date] = None
    ) -> List[Invoice]:
        """
        Find invoices for a patient
        
        Args:
            patient_id: Patient ID
            status: Optional status filter
            from_date: Optional date filter
        
        Returns:
            List of invoices
        """
        filter_dict = {"patient_id": patient_id}
        
        if status:
            filter_dict["status"] = status.value
        
        if from_date:
            filter_dict["invoice_date"] = {"$gte": from_date}
        
        return await self.find_many(filter_dict, sort=[("invoice_date", -1)])
    
    async def find_unpaid_invoices(self) -> List[Invoice]:
        """Find all unpaid invoices"""
        return await self.find_many({
            "status": {"$in": [
                InvoiceStatus.PENDING.value,
                InvoiceStatus.SENT.value,
                InvoiceStatus.PARTIALLY_PAID.value
            ]}
        })
    
    async def find_overdue_invoices(self, as_of_date: date = None) -> List[Invoice]:
        """Find overdue invoices"""
        check_date = as_of_date or date.today()
        
        return await self.find_many({
            "due_date": {"$lt": check_date},
            "status": {"$in": [
                InvoiceStatus.PENDING.value,
                InvoiceStatus.SENT.value,
                InvoiceStatus.PARTIALLY_PAID.value
            ]}
        })
    
    async def add_line_item(
        self,
        invoice_id: str,
        line_item_data: Dict[str, Any]
    ) -> bool:
        """
        Add line item to invoice
        
        Args:
            invoice_id: Invoice ID
            line_item_data: Line item information
        
        Returns:
            True if successful, False otherwise
        """
        # Get next line number
        line_count = await self.invoice_line_collection.count_documents({"invoice_id": invoice_id})
        line_item_data["line_number"] = line_count + 1
        line_item_data["invoice_id"] = invoice_id
        
        # Generate line_id
        next_id = await self.get_next_sequence("InvoiceLine")
        line_item_data["line_id"] = f"LIN{str(next_id).zfill(3)}"
        
        result = await self.invoice_line_collection.insert_one(line_item_data)
        
        if result.inserted_id:
            # Update invoice totals
            await self.recalculate_invoice_totals(invoice_id)
            return True
        
        return False
    
    async def recalculate_invoice_totals(self, invoice_id: str) -> Optional[Invoice]:
        """
        Recalculate invoice totals based on line items
        
        Args:
            invoice_id: Invoice ID
        
        Returns:
            Updated invoice or None
        """
        pipeline = [
            {"$match": {"invoice_id": invoice_id}},
            {
                "$group": {
                    "_id": None,
                    "subtotal": {"$sum": "$subtotal"},
                    "tax_amount": {"$sum": "$tax_amount"},
                    "discount_amount": {"$sum": "$discount_amount"},
                    "total": {"$sum": "$total"}
                }
            }
        ]
        
        result = await self.invoice_line_collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            totals = result[0]
            return await self.update_by_id(
                invoice_id,
                {
                    "subtotal": totals["subtotal"],
                    "tax_amount": totals.get("tax_amount", 0),
                    "discount_amount": totals.get("discount_amount", 0),
                    "total_amount": totals["total"],
                    "balance_due": totals["total"] - totals.get("amount_paid", 0)
                },
                id_field="invoice_id"
            )
        
        return None
    
    async def apply_insurance_coverage(
        self,
        invoice_id: str,
        insurance_data: Dict[str, Any]
    ) -> Optional[Invoice]:
        """
        Apply insurance coverage to invoice
        
        Args:
            invoice_id: Invoice ID
            insurance_data: Insurance information
        
        Returns:
            Updated invoice or None
        """
        update_data = {
            "payment_method": PaymentMethod.INSURANCE.value,
            "insurance_provider": insurance_data["provider"],
            "insurance_policy_number": insurance_data["policy_number"],
            "insurance_group_number": insurance_data.get("group_number"),
            "co_pay_amount": insurance_data.get("co_pay_amount", 0),
            "insurance_covered_amount": insurance_data.get("covered_amount", 0),
            "insurance_claim_status": "pending"
        }
        
        return await self.update_by_id(invoice_id, update_data, id_field="invoice_id")
    
    async def submit_insurance_claim(
        self,
        invoice_id: str,
        claim_number: str
    ) -> Optional[Invoice]:
        """Submit insurance claim"""
        return await self.update_by_id(
            invoice_id,
            {
                "insurance_claim_number": claim_number,
                "insurance_claim_submitted_at": datetime.utcnow(),
                "insurance_claim_status": "submitted"
            },
            id_field="invoice_id"
        )
    
    async def submit_government_claim(
        self,
        invoice_id: str,
        health_number: str
    ) -> Optional[Invoice]:
        """Submit government health coverage claim"""
        return await self.update_by_id(
            invoice_id,
            {
                "payment_method": PaymentMethod.GOVERNMENT.value,
                "government_health_number": health_number,
                "government_claim_status": "submitted"
            },
            id_field="invoice_id"
        )
    
    async def mark_invoice_sent(self, invoice_id: str) -> Optional[Invoice]:
        """Mark invoice as sent to patient"""
        return await self.update_by_id(
            invoice_id,
            {
                "status": InvoiceStatus.SENT.value,
                "sent_at": datetime.utcnow()
            },
            id_field="invoice_id"
        )
    
    async def get_invoice_with_details(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get invoice with all line items and payments"""
        pipeline = [
            {"$match": {"invoice_id": invoice_id}},
            
            # Join with patient
            {
                "$lookup": {
                    "from": "Patient",
                    "localField": "patient_id",
                    "foreignField": "patient_id",
                    "as": "patient"
                }
            },
            {"$unwind": {"path": "$patient", "preserveNullAndEmptyArrays": True}},
            
            # Join with line items
            {
                "$lookup": {
                    "from": "InvoiceLine",
                    "localField": "invoice_id",
                    "foreignField": "invoice_id",
                    "as": "line_items"
                }
            },
            
            # Join with payments
            {
                "$lookup": {
                    "from": "Payment",
                    "localField": "invoice_id",
                    "foreignField": "invoice_id",
                    "as": "payments"
                }
            },
            
            # Join with visit if applicable
            {
                "$lookup": {
                    "from": "Visit",
                    "localField": "visit_id",
                    "foreignField": "visit_id",
                    "as": "visit"
                }
            },
            {"$unwind": {"path": "$visit", "preserveNullAndEmptyArrays": True}}
        ]
        
        results = await self.aggregate(pipeline)
        return results[0] if results else None
    
    async def generate_monthly_statement(
        self,
        patient_id: str,
        month: int,
        year: int
    ) -> Dict[str, Any]:
        """
        Generate monthly statement for patient
        
        Args:
            patient_id: Patient ID
            month: Month number (1-12)
            year: Year
        
        Returns:
            Statement data
        """
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get all invoices for the month
        invoices = await self.find_many({
            "patient_id": patient_id,
            "invoice_date": {"$gte": start_date, "$lte": end_date}
        })
        
        # Get all payments for the month
        payments = await self.payment_collection.find({
            "patient_id": patient_id,
            "payment_date": {"$gte": start_date, "$lte": end_date}
        }).to_list(length=None)
        
        # Calculate totals
        total_charges = sum(inv.total_amount for inv in invoices)
        total_payments = sum(pay["amount"] for pay in payments)
        
        # Get outstanding balance
        unpaid_invoices = await self.find_patient_invoices(
            patient_id,
            status=InvoiceStatus.PENDING
        )
        outstanding_balance = sum(inv.balance_due for inv in unpaid_invoices)
        
        return {
            "patient_id": patient_id,
            "statement_period": f"{month}/{year}",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "invoices": [inv.dict() for inv in invoices],
            "payments": payments,
            "total_charges": float(total_charges),
            "total_payments": float(total_payments),
            "period_balance": float(total_charges - total_payments),
            "outstanding_balance": float(outstanding_balance)
        }
    
    async def get_revenue_statistics(
        self,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """Get revenue statistics for date range"""
        pipeline = [
            {"$match": {
                "invoice_date": {"$gte": from_date, "$lte": to_date}
            }},
            {
                "$facet": {
                    "total_invoiced": [
                        {"$group": {"_id": None, "amount": {"$sum": "$total_amount"}}}
                    ],
                    "total_paid": [
                        {"$group": {"_id": None, "amount": {"$sum": "$amount_paid"}}}
                    ],
                    "by_payment_method": [
                        {"$group": {
                            "_id": "$payment_method",
                            "count": {"$sum": 1},
                            "amount": {"$sum": "$total_amount"}
                        }}
                    ],
                    "by_status": [
                        {"$group": {
                            "_id": "$status",
                            "count": {"$sum": 1},
                            "amount": {"$sum": "$balance_due"}
                        }}
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            stats = result[0]
            return {
                "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
                "total_invoiced": stats["total_invoiced"][0]["amount"] if stats["total_invoiced"] else 0,
                "total_paid": stats["total_paid"][0]["amount"] if stats["total_paid"] else 0,
                "by_payment_method": {
                    item["_id"]: {"count": item["count"], "amount": item["amount"]}
                    for item in stats["by_payment_method"]
                },
                "by_status": {
                    item["_id"]: {"count": item["count"], "amount": item["amount"]}
                    for item in stats["by_status"]
                }
            }
        
        return {}


class PaymentRepository(BaseRepository[Payment]):
    """Repository for payment operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Payment", Payment)
        self.invoice_collection = database["Invoice"]
    
    async def create_payment(self, payment_data: Dict[str, Any]) -> Payment:
        """
        Create a new payment and update invoice
        
        Args:
            payment_data: Payment information
        
        Returns:
            Created payment
        """
        payment = await self.create(payment_data, auto_id_field="payment_id")
        
        if payment:
            # Update invoice with payment
            await self.apply_payment_to_invoice(payment.invoice_id, payment.amount)
        
        return payment
    
    async def apply_payment_to_invoice(
        self,
        invoice_id: str,
        amount: Decimal
    ) -> bool:
        """
        Apply payment to invoice and update status
        
        Args:
            invoice_id: Invoice ID
            amount: Payment amount
        
        Returns:
            True if successful, False otherwise
        """
        invoice = await self.invoice_collection.find_one({"invoice_id": invoice_id})
        
        if not invoice:
            return False
        
        new_amount_paid = float(invoice.get("amount_paid", 0)) + float(amount)
        new_balance = float(invoice["total_amount"]) - new_amount_paid
        
        # Determine new status
        if new_balance <= 0:
            new_status = InvoiceStatus.PAID.value
        elif new_amount_paid > 0:
            new_status = InvoiceStatus.PARTIALLY_PAID.value
        else:
            new_status = invoice["status"]
        
        result = await self.invoice_collection.update_one(
            {"invoice_id": invoice_id},
            {
                "$set": {
                    "amount_paid": new_amount_paid,
                    "balance_due": new_balance,
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return result.modified_count > 0
    
    async def find_payment_by_id(self, payment_id: str) -> Optional[Payment]:
        """Find payment by payment_id"""
        return await self.find_by_id(payment_id, id_field="payment_id")
    
    async def find_invoice_payments(self, invoice_id: str) -> List[Payment]:
        """Find all payments for an invoice"""
        return await self.find_many(
            {"invoice_id": invoice_id},
            sort=[("payment_date", -1)]
        )
    
    async def find_patient_payments(
        self,
        patient_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Payment]:
        """Find payments made by a patient"""
        filter_dict = {"patient_id": patient_id}
        
        if from_date:
            filter_dict["payment_date"] = {"$gte": from_date}
        
        if to_date:
            if "payment_date" in filter_dict:
                filter_dict["payment_date"]["$lte"] = to_date
            else:
                filter_dict["payment_date"] = {"$lte": to_date}
        
        return await self.find_many(filter_dict, sort=[("payment_date", -1)])
    
    async def process_insurance_payment(
        self,
        invoice_id: str,
        payment_data: Dict[str, Any]
    ) -> Optional[Payment]:
        """Process insurance payment"""
        payment_data.update({
            "payment_method": PaymentMethod.INSURANCE.value,
            "status": PaymentStatus.COMPLETED.value,
            "insurance_claim_number": payment_data.get("claim_number"),
            "insurance_check_number": payment_data.get("check_number"),
            "eob_date": payment_data.get("eob_date")
        })
        
        return await self.create_payment(payment_data)
    
    async def process_government_payment(
        self,
        invoice_id: str,
        payment_data: Dict[str, Any]
    ) -> Optional[Payment]:
        """Process government reimbursement"""
        payment_data.update({
            "payment_method": PaymentMethod.GOVERNMENT.value,
            "status": PaymentStatus.COMPLETED.value,
            "government_claim_number": payment_data.get("claim_number"),
            "government_payment_reference": payment_data.get("reference")
        })
        
        return await self.create_payment(payment_data)
    
    async def process_refund(
        self,
        original_payment_id: str,
        refund_amount: Decimal,
        reason: str
    ) -> Optional[Payment]:
        """Process a refund"""
        original_payment = await self.find_payment_by_id(original_payment_id)
        
        if not original_payment:
            return None
        
        refund_data = {
            "invoice_id": original_payment.invoice_id,
            "patient_id": original_payment.patient_id,
            "amount": -float(refund_amount),  # Negative amount for refund
            "payment_method": original_payment.payment_method,
            "status": PaymentStatus.COMPLETED.value,
            "is_refund": True,
            "refund_reason": reason,
            "original_payment_id": original_payment_id,
            "payment_date": datetime.utcnow()
        }
        
        return await self.create_payment(refund_data)
    
    async def get_daily_payment_summary(self, date: date) -> Dict[str, Any]:
        """Get payment summary for a specific date"""
        start = datetime.combine(date, datetime.min.time())
        end = datetime.combine(date, datetime.max.time())
        
        pipeline = [
            {"$match": {
                "payment_date": {"$gte": start, "$lte": end},
                "status": PaymentStatus.COMPLETED.value
            }},
            {
                "$facet": {
                    "total": [
                        {"$group": {"_id": None, "amount": {"$sum": "$amount"}}}
                    ],
                    "by_method": [
                        {"$group": {
                            "_id": "$payment_method",
                            "count": {"$sum": 1},
                            "amount": {"$sum": "$amount"}
                        }}
                    ],
                    "refunds": [
                        {"$match": {"is_refund": True}},
                        {"$group": {
                            "_id": None,
                            "count": {"$sum": 1},
                            "amount": {"$sum": "$amount"}
                        }}
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            summary = result[0]
            return {
                "date": date.isoformat(),
                "total_collected": summary["total"][0]["amount"] if summary["total"] else 0,
                "by_payment_method": {
                    item["_id"]: {"count": item["count"], "amount": item["amount"]}
                    for item in summary["by_method"]
                },
                "refunds": summary["refunds"][0] if summary["refunds"] else {"count": 0, "amount": 0}
            }
        
        return {}