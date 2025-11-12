# backend/repositories/patient_repository.py
"""Repository for Patient collection operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from motor.motor_asyncio import AsyncIOMotorDatabase
import re

from .base_repository import BaseRepository
from ..models.patient import Patient, PatientSearchRequest


class PatientRepository(BaseRepository[Patient]):
    """Repository for patient-specific database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Patient", Patient)
    
    async def create_patient(self, patient_data: Dict[str, Any]) -> Patient:
        """
        Create a new patient with auto-generated patient_id
        
        Args:
            patient_data: Patient information
        
        Returns:
            Created patient
        """
        return await self.create(patient_data, auto_id_field="patient_id")
    
    async def find_by_patient_id(self, patient_id: str) -> Optional[Patient]:
        """
        Find patient by patient_id
        
        Args:
            patient_id: Patient ID
        
        Returns:
            Patient or None
        """
        return await self.find_by_id(patient_id, id_field="patient_id")
    
    async def find_by_health_card(self, health_card_number: str) -> Optional[Patient]:
        """
        Find patient by health card number
        
        Args:
            health_card_number: Government health card number
        
        Returns:
            Patient or None
        """
        return await self.find_one({"health_card_number": health_card_number})
    
    async def find_by_email(self, email: str) -> Optional[Patient]:
        """
        Find patient by email address
        
        Args:
            email: Patient email
        
        Returns:
            Patient or None
        """
        return await self.find_one({"email": email.lower()})
    
    async def find_by_phone(self, phone: str) -> Optional[Patient]:
        """
        Find patient by phone number
        
        Args:
            phone: Phone number (will be normalized)
        
        Returns:
            Patient or None
        """
        # Normalize phone number - remove all non-digits
        normalized_phone = re.sub(r'\D', '', phone)
        
        # Search in both phone and alternate_phone
        return await self.find_one({
            "$or": [
                {"phone": {"$regex": normalized_phone}},
                {"alternate_phone": {"$regex": normalized_phone}}
            ]
        })
    
    async def search_patients(self, search_params: PatientSearchRequest) -> List[Patient]:
        """
        Search patients with multiple criteria
        
        Args:
            search_params: Search parameters
        
        Returns:
            List of matching patients
        """
        filter_dict = {}
        
        # Text search in name, email, phone
        if search_params.search_term:
            search_regex = {"$regex": search_params.search_term, "$options": "i"}
            filter_dict["$or"] = [
                {"first_name": search_regex},
                {"last_name": search_regex},
                {"email": search_regex},
                {"phone": search_regex}
            ]
        
        # Specific field searches
        if search_params.health_card_number:
            filter_dict["health_card_number"] = search_params.health_card_number
        
        if search_params.phone:
            normalized_phone = re.sub(r'\D', '', search_params.phone)
            filter_dict["$or"] = [
                {"phone": {"$regex": normalized_phone}},
                {"alternate_phone": {"$regex": normalized_phone}}
            ]
        
        if search_params.date_of_birth:
            filter_dict["date_of_birth"] = search_params.date_of_birth
        
        if search_params.is_active is not None:
            filter_dict["is_active"] = search_params.is_active
        
        return await self.find_many(
            filter_dict,
            sort=[("last_name", 1), ("first_name", 1)]
        )
    
    async def find_patients_by_birthday_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[Patient]:
        """
        Find patients with birthdays in date range (useful for birthday reminders)
        
        Args:
            start_date: Start of date range
            end_date: End of date range
        
        Returns:
            List of patients with birthdays in range
        """
        # Extract month and day for birthday matching
        pipeline = [
            {
                "$project": {
                    "document": "$$ROOT",
                    "month": {"$month": "$date_of_birth"},
                    "day": {"$dayOfMonth": "$date_of_birth"}
                }
            },
            {
                "$match": {
                    "$or": [
                        {
                            "month": {"$gte": start_date.month, "$lte": end_date.month},
                            "day": {"$gte": start_date.day, "$lte": end_date.day}
                        }
                    ]
                }
            },
            {
                "$replaceRoot": {"newRoot": "$document"}
            }
        ]
        
        results = await self.aggregate(pipeline)
        return [Patient(**doc) for doc in results]
    
    async def find_patients_with_chronic_conditions(self) -> List[Patient]:
        """
        Find all patients with chronic conditions
        
        Returns:
            List of patients with chronic conditions
        """
        return await self.find_many(
            {"chronic_conditions": {"$exists": True, "$ne": []}}
        )
    
    async def find_patients_by_insurance_provider(
        self,
        insurance_provider: str
    ) -> List[Patient]:
        """
        Find patients by insurance provider
        
        Args:
            insurance_provider: Name of insurance company
        
        Returns:
            List of patients with specified insurance
        """
        return await self.find_many(
            {"insurance_provider": {"$regex": insurance_provider, "$options": "i"}}
        )
    
    async def update_patient_insurance(
        self,
        patient_id: str,
        insurance_data: Dict[str, Any]
    ) -> Optional[Patient]:
        """
        Update patient's insurance information
        
        Args:
            patient_id: Patient ID
            insurance_data: New insurance information
        
        Returns:
            Updated patient or None
        """
        update_dict = {
            "insurance_provider": insurance_data.get("provider"),
            "insurance_policy_number": insurance_data.get("policy_number"),
            "insurance_group_number": insurance_data.get("group_number")
        }
        
        # Remove None values
        update_dict = {k: v for k, v in update_dict.items() if v is not None}
        
        return await self.update_by_id(patient_id, update_dict, id_field="patient_id")
    
    async def update_patient_medications(
        self,
        patient_id: str,
        medications: List[str]
    ) -> Optional[Patient]:
        """
        Update patient's current medications list
        
        Args:
            patient_id: Patient ID
            medications: List of current medications
        
        Returns:
            Updated patient or None
        """
        return await self.update_by_id(
            patient_id,
            {"current_medications": medications},
            id_field="patient_id"
        )
    
    async def update_patient_allergies(
        self,
        patient_id: str,
        allergies: List[str]
    ) -> Optional[Patient]:
        """
        Update patient's allergies list
        
        Args:
            patient_id: Patient ID
            allergies: List of allergies
        
        Returns:
            Updated patient or None
        """
        return await self.update_by_id(
            patient_id,
            {"allergies": allergies},
            id_field="patient_id"
        )
    
    async def add_chronic_condition(
        self,
        patient_id: str,
        condition: str
    ) -> Optional[Patient]:
        """
        Add a chronic condition to patient's record
        
        Args:
            patient_id: Patient ID
            condition: Chronic condition to add
        
        Returns:
            Updated patient or None
        """
        patient = await self.find_by_patient_id(patient_id)
        if not patient:
            return None
        
        conditions = patient.chronic_conditions
        if condition not in conditions:
            conditions.append(condition)
            return await self.update_by_id(
                patient_id,
                {"chronic_conditions": conditions},
                id_field="patient_id"
            )
        
        return patient
    
    async def deactivate_patient(self, patient_id: str) -> Optional[Patient]:
        """
        Deactivate a patient record (soft delete)
        
        Args:
            patient_id: Patient ID
        
        Returns:
            Updated patient or None
        """
        return await self.update_by_id(
            patient_id,
            {"is_active": False},
            id_field="patient_id"
        )
    
    async def get_patient_statistics(self) -> Dict[str, Any]:
        """
        Get patient statistics for reporting
        
        Returns:
            Dictionary with patient statistics
        """
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "active": [
                        {"$match": {"is_active": True}},
                        {"$count": "count"}
                    ],
                    "by_gender": [
                        {"$group": {"_id": "$gender", "count": {"$sum": 1}}}
                    ],
                    "by_province": [
                        {"$group": {"_id": "$province", "count": {"$sum": 1}}}
                    ],
                    "with_insurance": [
                        {"$match": {"insurance_provider": {"$exists": True, "$ne": None}}},
                        {"$count": "count"}
                    ],
                    "with_chronic_conditions": [
                        {"$match": {"chronic_conditions": {"$exists": True, "$ne": []}}},
                        {"$count": "count"}
                    ],
                    "age_groups": [
                        {
                            "$project": {
                                "age": {
                                    "$divide": [
                                        {"$subtract": [datetime.utcnow(), "$date_of_birth"]},
                                        365 * 24 * 60 * 60 * 1000
                                    ]
                                }
                            }
                        },
                        {
                            "$bucket": {
                                "groupBy": "$age",
                                "boundaries": [0, 18, 30, 40, 50, 60, 70, 80, 100],
                                "default": "100+",
                                "output": {"count": {"$sum": 1}}
                            }
                        }
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            stats = result[0]
            return {
                "total_patients": stats["total"][0]["count"] if stats["total"] else 0,
                "active_patients": stats["active"][0]["count"] if stats["active"] else 0,
                "by_gender": {item["_id"]: item["count"] for item in stats["by_gender"]},
                "by_province": {item["_id"]: item["count"] for item in stats["by_province"]},
                "with_insurance": stats["with_insurance"][0]["count"] if stats["with_insurance"] else 0,
                "with_chronic_conditions": stats["with_chronic_conditions"][0]["count"] if stats["with_chronic_conditions"] else 0,
                "age_groups": stats["age_groups"]
            }
        
        return {}