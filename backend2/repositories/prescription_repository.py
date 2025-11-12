# backend/repositories/prescription_repository.py
"""Repository for Prescription and Drug collection operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base_repository import BaseRepository
from ..models.prescription import (
    Prescription, Drug,
    PrescriptionStatus, DrugForm, RouteOfAdministration
)


class PrescriptionRepository(BaseRepository[Prescription]):
    """Repository for prescription-specific database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Prescription", Prescription)
        self.drug_collection = database["Drug"]
    
    async def create_prescription(self, prescription_data: Dict[str, Any]) -> Prescription:
        """
        Create a new prescription with auto-generated prescription_id
        
        Args:
            prescription_data: Prescription information
        
        Returns:
            Created prescription
        """
        # Generate prescription number (RX-YYYY-NNNN format)
        year = datetime.now().year
        count = await self.count({"prescription_date": {"$gte": datetime(year, 1, 1)}})
        prescription_data["prescription_number"] = f"RX{year}-{str(count + 1).zfill(4)}"
        
        # Set expiry date if not provided (1 year from prescription date)
        if "expiry_date" not in prescription_data:
            prescription_data["expiry_date"] = date.today() + timedelta(days=365)
        
        prescription = await self.create(prescription_data, auto_id_field="prescription_id")
        
        if prescription:
            # Trigger stored procedure for prescription billing
            await self.database.command({
                "eval": "createInvoiceFromPrescription",
                "args": [prescription.prescription_id]
            })
        
        return prescription
    
    async def find_by_prescription_id(self, prescription_id: str) -> Optional[Prescription]:
        """Find prescription by prescription_id"""
        return await self.find_by_id(prescription_id, id_field="prescription_id")
    
    async def find_by_prescription_number(self, prescription_number: str) -> Optional[Prescription]:
        """Find prescription by prescription number"""
        return await self.find_one({"prescription_number": prescription_number})
    
    async def find_patient_prescriptions(
        self,
        patient_id: str,
        status: Optional[PrescriptionStatus] = None,
        active_only: bool = False
    ) -> List[Prescription]:
        """
        Find prescriptions for a patient
        
        Args:
            patient_id: Patient ID
            status: Optional status filter
            active_only: Whether to return only active prescriptions
        
        Returns:
            List of prescriptions
        """
        filter_dict = {"patient_id": patient_id}
        
        if status:
            filter_dict["status"] = status.value
        
        if active_only:
            filter_dict["status"] = PrescriptionStatus.ACTIVE.value
            filter_dict["expiry_date"] = {"$gte": date.today()}
        
        return await self.find_many(filter_dict, sort=[("prescription_date", -1)])
    
    async def find_visit_prescriptions(self, visit_id: str) -> List[Prescription]:
        """Find all prescriptions from a visit"""
        return await self.find_many(
            {"visit_id": visit_id},
            sort=[("prescription_date", 1)]
        )
    
    async def find_prescriptions_by_drug(
        self,
        drug_id: str,
        from_date: Optional[date] = None
    ) -> List[Prescription]:
        """Find prescriptions for a specific drug"""
        filter_dict = {"drug_id": drug_id}
        
        if from_date:
            filter_dict["prescription_date"] = {"$gte": from_date}
        
        return await self.find_many(filter_dict)
    
    async def find_expiring_prescriptions(
        self,
        days_ahead: int = 30
    ) -> List[Prescription]:
        """Find prescriptions expiring soon"""
        expiry_date = date.today() + timedelta(days=days_ahead)
        
        return await self.find_many({
            "status": PrescriptionStatus.ACTIVE.value,
            "expiry_date": {"$lte": expiry_date, "$gte": date.today()}
        })
    
    async def fill_prescription(
        self,
        prescription_id: str,
        quantity_dispensed: int,
        dispensed_by: str,
        pharmacy_id: Optional[str] = None
    ) -> Optional[Prescription]:
        """
        Fill a prescription
        
        Args:
            prescription_id: Prescription ID
            quantity_dispensed: Quantity dispensed
            dispensed_by: Pharmacist ID
            pharmacy_id: Pharmacy ID if external
        
        Returns:
            Updated prescription or None
        """
        prescription = await self.find_by_prescription_id(prescription_id)
        
        if not prescription:
            return None
        
        # Check if fully filled
        status = PrescriptionStatus.FILLED.value
        if quantity_dispensed < prescription.quantity_prescribed:
            status = PrescriptionStatus.PARTIALLY_FILLED.value
        
        # Update prescription
        return await self.update_by_id(
            prescription_id,
            {
                "status": status,
                "quantity_dispensed": quantity_dispensed,
                "dispensed_by": dispensed_by,
                "dispensed_at": datetime.utcnow(),
                "pharmacy_id": pharmacy_id
            },
            id_field="prescription_id"
        )
    
    async def refill_prescription(
        self,
        prescription_id: str,
        dispensed_by: str
    ) -> Optional[Prescription]:
        """
        Process prescription refill
        
        Args:
            prescription_id: Prescription ID
            dispensed_by: Pharmacist ID
        
        Returns:
            Updated prescription or None
        """
        prescription = await self.find_by_prescription_id(prescription_id)
        
        if not prescription or prescription.refills_remaining <= 0:
            return None
        
        # Decrement refills and update
        return await self.update_by_id(
            prescription_id,
            {
                "refills_remaining": prescription.refills_remaining - 1,
                "status": PrescriptionStatus.FILLED.value,
                "dispensed_by": dispensed_by,
                "dispensed_at": datetime.utcnow()
            },
            id_field="prescription_id"
        )
    
    async def cancel_prescription(
        self,
        prescription_id: str,
        reason: str
    ) -> Optional[Prescription]:
        """Cancel a prescription"""
        return await self.update_by_id(
            prescription_id,
            {
                "status": PrescriptionStatus.CANCELLED.value,
                "pharmacy_notes": f"Cancelled: {reason}"
            },
            id_field="prescription_id"
        )
    
    async def get_prescription_with_details(
        self,
        prescription_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get prescription with drug and patient details"""
        pipeline = [
            {"$match": {"prescription_id": prescription_id}},
            
            # Join with drug
            {
                "$lookup": {
                    "from": "Drug",
                    "localField": "drug_id",
                    "foreignField": "drug_id",
                    "as": "drug"
                }
            },
            {"$unwind": "$drug"},
            
            # Join with patient
            {
                "$lookup": {
                    "from": "Patient",
                    "localField": "patient_id",
                    "foreignField": "patient_id",
                    "as": "patient"
                }
            },
            {"$unwind": "$patient"},
            
            # Join with prescriber (staff)
            {
                "$lookup": {
                    "from": "Staff",
                    "localField": "prescribed_by",
                    "foreignField": "staff_id",
                    "as": "prescriber"
                }
            },
            {"$unwind": "$prescriber"}
        ]
        
        results = await self.aggregate(pipeline)
        return results[0] if results else None
    
    async def generate_prescription_label(
        self,
        prescription_id: str
    ) -> Optional[Dict[str, Any]]:
        """Generate prescription label data"""
        prescription_data = await self.get_prescription_with_details(prescription_id)
        
        if not prescription_data:
            return None
        
        return {
            "patient_name": f"{prescription_data['patient']['first_name']} {prescription_data['patient']['last_name']}",
            "patient_address": prescription_data['patient']['address'],
            "patient_phone": prescription_data['patient']['phone'],
            "prescription_number": prescription_data['prescription_number'],
            "drug_name": prescription_data['drug']['generic_name'],
            "brand_name": prescription_data['drug'].get('brand_name'),
            "strength": f"{prescription_data['drug']['strength']} {prescription_data['drug']['strength_units']}",
            "quantity": prescription_data['quantity_prescribed'],
            "instructions": prescription_data['instructions'],
            "prescriber_name": f"Dr. {prescription_data['prescriber']['first_name']} {prescription_data['prescriber']['last_name']}",
            "prescriber_license": prescription_data['prescriber'].get('license_number'),
            "date_prescribed": prescription_data['prescription_date'],
            "expiry_date": prescription_data['expiry_date'],
            "refills_remaining": prescription_data.get('refills_remaining', 0),
            "warning_labels": prescription_data.get('warning_labels', [])
        }
    
    async def get_prescription_statistics(
        self,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """Get prescription statistics for date range"""
        pipeline = [
            {"$match": {
                "prescription_date": {"$gte": from_date, "$lte": to_date}
            }},
            {
                "$facet": {
                    "total_prescriptions": [{"$count": "count"}],
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "by_route": [
                        {"$group": {"_id": "$route", "count": {"$sum": 1}}}
                    ],
                    "with_refills": [
                        {"$match": {"refills_authorized": {"$gt": 0}}},
                        {"$count": "count"}
                    ],
                    "controlled_substances": [
                        {
                            "$lookup": {
                                "from": "Drug",
                                "localField": "drug_id",
                                "foreignField": "drug_id",
                                "as": "drug"
                            }
                        },
                        {"$unwind": "$drug"},
                        {"$match": {"drug.is_controlled": True}},
                        {"$count": "count"}
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            stats = result[0]
            return {
                "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
                "total_prescriptions": stats["total_prescriptions"][0]["count"] if stats["total_prescriptions"] else 0,
                "by_status": {item["_id"]: item["count"] for item in stats["by_status"]},
                "by_route": {item["_id"]: item["count"] for item in stats["by_route"]},
                "with_refills": stats["with_refills"][0]["count"] if stats["with_refills"] else 0,
                "controlled_substances": stats["controlled_substances"][0]["count"] if stats["controlled_substances"] else 0
            }
        
        return {}


class DrugRepository(BaseRepository[Drug]):
    """Repository for drug operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Drug", Drug)
    
    async def create_drug(self, drug_data: Dict[str, Any]) -> Drug:
        """Create a new drug"""
        return await self.create(drug_data, auto_id_field="drug_id")
    
    async def find_by_drug_id(self, drug_id: str) -> Optional[Drug]:
        """Find drug by drug_id"""
        return await self.find_by_id(drug_id, id_field="drug_id")
    
    async def find_by_generic_name(self, generic_name: str) -> Optional[Drug]:
        """Find drug by generic name"""
        return await self.find_one({"generic_name": {"$regex": generic_name, "$options": "i"}})
    
    async def find_by_ndc_code(self, ndc_code: str) -> Optional[Drug]:
        """Find drug by NDC code"""
        return await self.find_one({"ndc_code": ndc_code})
    
    async def search_drugs(
        self,
        search_term: str,
        in_stock_only: bool = False
    ) -> List[Drug]:
        """Search drugs by name or code"""
        filter_dict = {
            "$or": [
                {"generic_name": {"$regex": search_term, "$options": "i"}},
                {"brand_name": {"$regex": search_term, "$options": "i"}},
                {"ndc_code": search_term},
                {"din_number": search_term}
            ]
        }
        
        if in_stock_only:
            filter_dict["in_stock"] = True
        
        return await self.find_many(filter_dict, sort=[("generic_name", 1)])
    
    async def find_drugs_by_class(self, drug_class: str) -> List[Drug]:
        """Find drugs by therapeutic class"""
        return await self.find_many(
            {"drug_class": {"$regex": drug_class, "$options": "i"}},
            sort=[("generic_name", 1)]
        )
    
    async def find_controlled_substances(self) -> List[Drug]:
        """Find all controlled substances"""
        return await self.find_many(
            {"is_controlled": True},
            sort=[("drug_schedule", 1), ("generic_name", 1)]
        )
    
    async def find_covered_drugs(self) -> List[Drug]:
        """Find drugs covered by government insurance"""
        return await self.find_many(
            {"is_covered_by_ohip": True},
            sort=[("generic_name", 1)]
        )
    
    async def update_drug_stock(
        self,
        drug_id: str,
        quantity_change: int
    ) -> Optional[Drug]:
        """Update drug stock level"""
        drug = await self.find_by_drug_id(drug_id)
        
        if not drug:
            return None
        
        new_quantity = (drug.quantity_in_stock or 0) + quantity_change
        in_stock = new_quantity > 0
        
        return await self.update_by_id(
            drug_id,
            {
                "quantity_in_stock": new_quantity,
                "in_stock": in_stock
            },
            id_field="drug_id"
        )
    
    async def update_drug_price(
        self,
        drug_id: str,
        new_price: float
    ) -> Optional[Drug]:
        """Update drug unit price"""
        return await self.update_by_id(
            drug_id,
            {"unit_price": new_price},
            id_field="drug_id"
        )
    
    async def get_low_stock_drugs(
        self,
        threshold: int = 10
    ) -> List[Drug]:
        """Find drugs with low stock"""
        return await self.find_many(
            {
                "in_stock": True,
                "quantity_in_stock": {"$lte": threshold}
            },
            sort=[("quantity_in_stock", 1)]
        )
    
    async def get_drug_usage_statistics(
        self,
        drug_id: str,
        from_date: date
    ) -> Dict[str, Any]:
        """Get usage statistics for a drug"""
        pipeline = [
            {"$match": {"drug_id": drug_id}},
            {
                "$lookup": {
                    "from": "Prescription",
                    "let": {"drug_id": "$drug_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$eq": ["$drug_id", "$$drug_id"]},
                            "prescription_date": {"$gte": from_date}
                        }}
                    ],
                    "as": "prescriptions"
                }
            },
            {
                "$project": {
                    "drug_id": 1,
                    "generic_name": 1,
                    "brand_name": 1,
                    "total_prescriptions": {"$size": "$prescriptions"},
                    "total_quantity": {"$sum": "$prescriptions.quantity_prescribed"},
                    "unique_patients": {"$size": {"$setUnion": ["$prescriptions.patient_id", []]}},
                    "avg_quantity_per_prescription": {"$avg": "$prescriptions.quantity_prescribed"}
                }
            }
        ]
        
        results = await self.aggregate(pipeline)
        return results[0] if results else {}