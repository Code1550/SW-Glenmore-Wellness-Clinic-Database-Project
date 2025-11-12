# backend/repositories/visit_repository.py
"""Repository for Visit, VisitDiagnosis, VisitProcedure, Diagnosis, and Procedure operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base_repository import BaseRepository
from ..models.visit import (
    Visit, Diagnosis, Procedure, VisitDiagnosis, VisitProcedure,
    VisitStatus, VisitType, DiagnosisType
)


class VisitRepository(BaseRepository[Visit]):
    """Repository for visit-specific database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Visit", Visit)
        self.visit_diagnosis_collection = database["VisitDiagnosis"]
        self.visit_procedure_collection = database["VisitProcedure"]
    
    async def create_visit(self, visit_data: Dict[str, Any]) -> Visit:
        """
        Create a new visit with auto-generated visit_id
        
        Args:
            visit_data: Visit information
        
        Returns:
            Created visit
        """
        return await self.create(visit_data, auto_id_field="visit_id")
    
    async def find_by_visit_id(self, visit_id: str) -> Optional[Visit]:
        """Find visit by visit_id"""
        return await self.find_by_id(visit_id, id_field="visit_id")
    
    async def find_patient_visits(
        self,
        patient_id: str,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        status: Optional[VisitStatus] = None
    ) -> List[Visit]:
        """
        Find visits for a patient
        
        Args:
            patient_id: Patient ID
            from_date: Start date filter
            to_date: End date filter
            status: Visit status filter
        
        Returns:
            List of visits
        """
        filter_dict = {"patient_id": patient_id}
        
        if from_date:
            filter_dict["visit_date"] = {"$gte": from_date}
        
        if to_date:
            if "visit_date" in filter_dict:
                filter_dict["visit_date"]["$lte"] = to_date
            else:
                filter_dict["visit_date"] = {"$lte": to_date}
        
        if status:
            filter_dict["status"] = status.value
        
        return await self.find_many(filter_dict, sort=[("visit_date", -1)])
    
    async def find_staff_visits(
        self,
        staff_id: str,
        date: date
    ) -> List[Visit]:
        """Find visits for a staff member on a specific date"""
        return await self.find_many({
            "staff_id": staff_id,
            "visit_date": date,
            "status": {"$ne": VisitStatus.CANCELLED.value}
        }, sort=[("check_in_time", 1)])
    
    async def find_active_visits(self) -> List[Visit]:
        """Find all currently active visits"""
        return await self.find_many({
            "status": {"$in": [
                VisitStatus.CHECKED_IN.value,
                VisitStatus.IN_PROGRESS.value,
                VisitStatus.AWAITING_LAB.value,
                VisitStatus.AWAITING_PRESCRIPTION.value
            ]}
        })
    
    async def check_in_patient(
        self,
        visit_id: str,
        vitals: Dict[str, Any]
    ) -> Optional[Visit]:
        """
        Check in patient and record vitals
        
        Args:
            visit_id: Visit ID
            vitals: Vital signs
        
        Returns:
            Updated visit or None
        """
        return await self.update_by_id(
            visit_id,
            {
                "check_in_time": datetime.utcnow(),
                "status": VisitStatus.CHECKED_IN.value,
                "vitals": vitals
            },
            id_field="visit_id"
        )
    
    async def start_visit(self, visit_id: str, staff_id: str) -> Optional[Visit]:
        """Start a visit with a practitioner"""
        return await self.update_by_id(
            visit_id,
            {
                "start_time": datetime.utcnow(),
                "status": VisitStatus.IN_PROGRESS.value,
                "staff_id": staff_id
            },
            id_field="visit_id"
        )
    
    async def complete_visit(
        self,
        visit_id: str,
        assessment_plan: str,
        follow_up_required: bool = False
    ) -> Optional[Visit]:
        """
        Complete a visit and trigger billing
        
        Args:
            visit_id: Visit ID
            assessment_plan: Assessment and plan
            follow_up_required: Whether follow-up is needed
        
        Returns:
            Updated visit or None
        """
        visit = await self.update_by_id(
            visit_id,
            {
                "end_time": datetime.utcnow(),
                "status": VisitStatus.COMPLETED.value,
                "assessment_plan": assessment_plan,
                "follow_up_required": follow_up_required
            },
            id_field="visit_id"
        )
        
        if visit:
            # Trigger stored procedure for invoice generation
            await self.database.command({
                "eval": "generateInvoiceWhenVisitCompleted",
                "args": [visit_id]
            })
        
        return visit
    
    async def add_diagnosis_to_visit(
        self,
        visit_id: str,
        diagnosis_id: str,
        diagnosed_by: str,
        diagnosis_type: DiagnosisType = DiagnosisType.PRIMARY,
        notes: Optional[str] = None
    ) -> bool:
        """
        Add diagnosis to visit
        
        Args:
            visit_id: Visit ID
            diagnosis_id: Diagnosis ID
            diagnosed_by: Staff ID who made diagnosis
            diagnosis_type: Type of diagnosis
            notes: Additional notes
        
        Returns:
            True if successful, False otherwise
        """
        visit_diagnosis = {
            "visit_id": visit_id,
            "diagnosis_id": diagnosis_id,
            "diagnosis_type": diagnosis_type.value,
            "diagnosed_by": diagnosed_by,
            "diagnosed_at": datetime.utcnow(),
            "notes": notes
        }
        
        result = await self.visit_diagnosis_collection.insert_one(visit_diagnosis)
        return result.inserted_id is not None
    
    async def add_procedure_to_visit(
        self,
        visit_id: str,
        procedure_id: str,
        performed_by: str,
        fee: Decimal,
        quantity: int = 1,
        notes: Optional[str] = None
    ) -> bool:
        """
        Add procedure to visit
        
        Args:
            visit_id: Visit ID
            procedure_id: Procedure ID
            performed_by: Staff ID who performed
            fee: Procedure fee
            quantity: Number of times performed
            notes: Procedure notes
        
        Returns:
            True if successful, False otherwise
        """
        visit_procedure = {
            "visit_id": visit_id,
            "procedure_id": procedure_id,
            "performed_by": performed_by,
            "performed_at": datetime.utcnow(),
            "quantity": quantity,
            "fee": float(fee),
            "final_fee": float(fee * quantity),
            "notes": notes
        }
        
        result = await self.visit_procedure_collection.insert_one(visit_procedure)
        return result.inserted_id is not None
    
    async def get_visit_with_details(self, visit_id: str) -> Optional[Dict[str, Any]]:
        """
        Get visit with all diagnoses and procedures
        
        Args:
            visit_id: Visit ID
        
        Returns:
            Visit with full details or None
        """
        pipeline = [
            {"$match": {"visit_id": visit_id}},
            
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
            
            # Join with staff
            {
                "$lookup": {
                    "from": "Staff",
                    "localField": "staff_id",
                    "foreignField": "staff_id",
                    "as": "staff"
                }
            },
            {"$unwind": {"path": "$staff", "preserveNullAndEmptyArrays": True}},
            
            # Join with diagnoses
            {
                "$lookup": {
                    "from": "VisitDiagnosis",
                    "localField": "visit_id",
                    "foreignField": "visit_id",
                    "as": "visit_diagnoses"
                }
            },
            
            # Join diagnosis details
            {
                "$lookup": {
                    "from": "Diagnosis",
                    "let": {"diagnosis_ids": "$visit_diagnoses.diagnosis_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$diagnosis_id", "$$diagnosis_ids"]}}}
                    ],
                    "as": "diagnoses"
                }
            },
            
            # Join with procedures
            {
                "$lookup": {
                    "from": "VisitProcedure",
                    "localField": "visit_id",
                    "foreignField": "visit_id",
                    "as": "visit_procedures"
                }
            },
            
            # Join procedure details
            {
                "$lookup": {
                    "from": "Procedure",
                    "let": {"procedure_ids": "$visit_procedures.procedure_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$procedure_id", "$$procedure_ids"]}}}
                    ],
                    "as": "procedures"
                }
            }
        ]
        
        results = await self.aggregate(pipeline)
        return results[0] if results else None
    
    async def find_unbilled_visits(self) -> List[Visit]:
        """Find visits that haven't been billed yet"""
        return await self.find_many({
            "status": VisitStatus.COMPLETED.value,
            "is_billed": False
        })
    
    async def mark_visit_billed(
        self,
        visit_id: str,
        invoice_id: str
    ) -> Optional[Visit]:
        """Mark visit as billed"""
        return await self.update_by_id(
            visit_id,
            {
                "is_billed": True,
                "billed_at": datetime.utcnow(),
                "invoice_id": invoice_id
            },
            id_field="visit_id"
        )
    
    async def get_visit_statistics(
        self,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """
        Get visit statistics for a date range
        
        Args:
            from_date: Start date
            to_date: End date
        
        Returns:
            Statistics dictionary
        """
        pipeline = [
            {"$match": {
                "visit_date": {"$gte": from_date, "$lte": to_date}
            }},
            {
                "$facet": {
                    "total_visits": [{"$count": "count"}],
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "by_type": [
                        {"$group": {"_id": "$visit_type", "count": {"$sum": 1}}}
                    ],
                    "avg_duration": [
                        {"$match": {"start_time": {"$exists": True}, "end_time": {"$exists": True}}},
                        {
                            "$project": {
                                "duration": {
                                    "$divide": [
                                        {"$subtract": ["$end_time", "$start_time"]},
                                        60000  # Convert to minutes
                                    ]
                                }
                            }
                        },
                        {"$group": {"_id": None, "avg": {"$avg": "$duration"}}}
                    ],
                    "follow_ups_required": [
                        {"$match": {"follow_up_required": True}},
                        {"$count": "count"}
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            stats = result[0]
            return {
                "date_range": {"from": from_date.isoformat(), "to": to_date.isoformat()},
                "total_visits": stats["total_visits"][0]["count"] if stats["total_visits"] else 0,
                "by_status": {item["_id"]: item["count"] for item in stats["by_status"]},
                "by_type": {item["_id"]: item["count"] for item in stats["by_type"]},
                "avg_duration_minutes": stats["avg_duration"][0]["avg"] if stats["avg_duration"] else 0,
                "follow_ups_required": stats["follow_ups_required"][0]["count"] if stats["follow_ups_required"] else 0
            }
        
        return {}


class DiagnosisRepository(BaseRepository[Diagnosis]):
    """Repository for diagnosis operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Diagnosis", Diagnosis)
    
    async def create_diagnosis(self, diagnosis_data: Dict[str, Any]) -> Diagnosis:
        """Create a new diagnosis"""
        return await self.create(diagnosis_data, auto_id_field="diagnosis_id")
    
    async def find_by_code(self, code: str) -> Optional[Diagnosis]:
        """Find diagnosis by ICD code"""
        return await self.find_one({"code": code})
    
    async def search_diagnoses(self, search_term: str) -> List[Diagnosis]:
        """Search diagnoses by code or description"""
        search_regex = {"$regex": search_term, "$options": "i"}
        return await self.find_many({
            "$or": [
                {"code": search_regex},
                {"description": search_regex},
                {"category": search_regex}
            ]
        })
    
    async def find_chronic_diagnoses(self) -> List[Diagnosis]:
        """Find all chronic condition diagnoses"""
        return await self.find_many({"is_chronic": True})
    
    async def find_infectious_diagnoses(self) -> List[Diagnosis]:
        """Find all infectious diagnoses"""
        return await self.find_many({"is_infectious": True})


class ProcedureRepository(BaseRepository[Procedure]):
    """Repository for procedure operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Procedure", Procedure)
    
    async def create_procedure(self, procedure_data: Dict[str, Any]) -> Procedure:
        """Create a new procedure"""
        return await self.create(procedure_data, auto_id_field="procedure_id")
    
    async def find_by_code(self, code: str) -> Optional[Procedure]:
        """Find procedure by CPT code"""
        return await self.find_one({"code": code})
    
    async def search_procedures(self, search_term: str) -> List[Procedure]:
        """Search procedures by code or description"""
        search_regex = {"$regex": search_term, "$options": "i"}
        return await self.find_many({
            "$or": [
                {"code": search_regex},
                {"description": search_regex},
                {"category": search_regex}
            ]
        })
    
    async def find_covered_procedures(self) -> List[Procedure]:
        """Find procedures covered by government insurance"""
        return await self.find_many({"is_covered_by_ohip": True})
    
    async def find_procedures_requiring_consent(self) -> List[Procedure]:
        """Find procedures that require consent forms"""
        return await self.find_many({"requires_consent": True})
    
    async def update_procedure_fee(
        self,
        procedure_id: str,
        new_fee: Decimal
    ) -> Optional[Procedure]:
        """Update procedure fee"""
        return await self.update_by_id(
            procedure_id,
            {"standard_fee": float(new_fee)},
            id_field="procedure_id"
        )
    
    async def get_most_common_procedures(
        self,
        from_date: date,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get most commonly performed procedures"""
        pipeline = [
            {
                "$lookup": {
                    "from": "VisitProcedure",
                    "localField": "procedure_id",
                    "foreignField": "procedure_id",
                    "as": "performances"
                }
            },
            {
                "$lookup": {
                    "from": "Visit",
                    "let": {"visit_ids": "$performances.visit_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$in": ["$visit_id", "$$visit_ids"]},
                            "visit_date": {"$gte": from_date}
                        }}
                    ],
                    "as": "recent_visits"
                }
            },
            {
                "$project": {
                    "procedure_id": 1,
                    "code": 1,
                    "description": 1,
                    "standard_fee": 1,
                    "performance_count": {"$size": "$recent_visits"}
                }
            },
            {"$sort": {"performance_count": -1}},
            {"$limit": limit}
        ]
        
        return await self.aggregate(pipeline)