# backend/repositories/clinical_repository.py
"""Repository for LabTestOrder, Delivery, RecoveryStay, and RecoveryObservation operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base_repository import BaseRepository
from ..models.lab import LabTestOrder, TestStatus, TestPriority
from ..models.delivery import Delivery, DeliveryType, DeliveryComplication
from ..models.recovery import RecoveryStay, RecoveryObservation, RecoveryStatus, ObservationType


class LabTestOrderRepository(BaseRepository[LabTestOrder]):
    """Repository for lab test order operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "LabTestOrder", LabTestOrder)
    
    async def create_lab_order(self, order_data: Dict[str, Any]) -> LabTestOrder:
        """Create a new lab test order"""
        # Generate order number (LAB-YYYY-NNNN format)
        year = datetime.now().year
        count = await self.count({"ordered_at": {"$gte": datetime(year, 1, 1)}})
        order_data["order_number"] = f"LAB{year}-{str(count + 1).zfill(4)}"
        
        return await self.create(order_data, auto_id_field="lab_test_id")
    
    async def find_by_lab_test_id(self, lab_test_id: str) -> Optional[LabTestOrder]:
        """Find lab test by ID"""
        return await self.find_by_id(lab_test_id, id_field="lab_test_id")
    
    async def find_patient_lab_tests(
        self,
        patient_id: str,
        status: Optional[TestStatus] = None,
        from_date: Optional[date] = None
    ) -> List[LabTestOrder]:
        """Find lab tests for a patient"""
        filter_dict = {"patient_id": patient_id}
        
        if status:
            filter_dict["status"] = status.value
        
        if from_date:
            filter_dict["ordered_at"] = {"$gte": from_date}
        
        return await self.find_many(filter_dict, sort=[("ordered_at", -1)])
    
    async def find_pending_lab_tests(self) -> List[LabTestOrder]:
        """Find all pending lab tests"""
        return await self.find_many({
            "status": {"$in": [
                TestStatus.ORDERED.value,
                TestStatus.SCHEDULED.value,
                TestStatus.SPECIMEN_COLLECTED.value,
                TestStatus.IN_PROGRESS.value
            ]}
        }, sort=[("priority", -1), ("ordered_at", 1)])
    
    async def find_critical_results(self) -> List[LabTestOrder]:
        """Find tests with critical results"""
        return await self.find_many({
            "critical_values": {"$exists": True, "$ne": []},
            "provider_notified": False
        })
    
    async def collect_specimen(
        self,
        lab_test_id: str,
        specimen_type: str,
        specimen_id: str,
        collected_by: str,
        notes: Optional[str] = None
    ) -> Optional[LabTestOrder]:
        """Record specimen collection"""
        return await self.update_by_id(
            lab_test_id,
            {
                "status": TestStatus.SPECIMEN_COLLECTED.value,
                "specimen_type": specimen_type,
                "specimen_id": specimen_id,
                "specimen_collected_by": collected_by,
                "specimen_collected_at": datetime.utcnow(),
                "collection_notes": notes
            },
            id_field="lab_test_id"
        )
    
    async def enter_result(
        self,
        lab_test_id: str,
        result: Dict[str, Any],
        result_status: str,
        performed_by: str,
        critical_values: Optional[List[str]] = None
    ) -> Optional[LabTestOrder]:
        """Enter lab test result"""
        update_data = {
            "status": TestStatus.COMPLETED.value,
            "result": result,
            "result_date": datetime.utcnow(),
            "result_status": result_status,
            "performed_by": performed_by,
            "performed_at": datetime.utcnow()
        }
        
        if critical_values:
            update_data["critical_values"] = critical_values
            update_data["requires_follow_up"] = True
        
        return await self.update_by_id(lab_test_id, update_data, id_field="lab_test_id")
    
    async def mark_result_reviewed(
        self,
        lab_test_id: str,
        reviewed_by: str,
        interpretation: Optional[str] = None
    ) -> Optional[LabTestOrder]:
        """Mark lab result as reviewed"""
        return await self.update_by_id(
            lab_test_id,
            {
                "reviewed_by": reviewed_by,
                "reviewed_at": datetime.utcnow(),
                "interpretation": interpretation,
                "status": TestStatus.PENDING_REVIEW.value
            },
            id_field="lab_test_id"
        )
    
    async def get_daily_lab_log(self, log_date: date) -> List[Dict[str, Any]]:
        """Get all lab tests for a specific date"""
        start = datetime.combine(log_date, datetime.min.time())
        end = datetime.combine(log_date, datetime.max.time())
        
        pipeline = [
            {"$match": {
                "$or": [
                    {"ordered_at": {"$gte": start, "$lte": end}},
                    {"performed_at": {"$gte": start, "$lte": end}}
                ]
            }},
            {
                "$lookup": {
                    "from": "Patient",
                    "localField": "patient_id",
                    "foreignField": "patient_id",
                    "as": "patient"
                }
            },
            {"$unwind": "$patient"},
            {
                "$project": {
                    "order_number": 1,
                    "patient_name": {
                        "$concat": ["$patient.first_name", " ", "$patient.last_name"]
                    },
                    "test_name": 1,
                    "test_category": 1,
                    "priority": 1,
                    "status": 1,
                    "ordered_at": 1,
                    "performed_at": 1,
                    "result_status": 1,
                    "critical_values": 1
                }
            },
            {"$sort": {"priority": -1, "ordered_at": 1}}
        ]
        
        return await self.aggregate(pipeline)
    
    async def get_lab_statistics(
        self,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """Get lab test statistics"""
        pipeline = [
            {"$match": {
                "ordered_at": {"$gte": from_date, "$lte": to_date}
            }},
            {
                "$facet": {
                    "total_tests": [{"$count": "count"}],
                    "by_category": [
                        {"$group": {"_id": "$test_category", "count": {"$sum": 1}}}
                    ],
                    "by_priority": [
                        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
                    ],
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "critical_results": [
                        {"$match": {"critical_values": {"$exists": True, "$ne": []}}},
                        {"$count": "count"}
                    ],
                    "avg_turnaround": [
                        {"$match": {"result_date": {"$exists": True}}},
                        {
                            "$project": {
                                "turnaround_hours": {
                                    "$divide": [
                                        {"$subtract": ["$result_date", "$ordered_at"]},
                                        3600000
                                    ]
                                }
                            }
                        },
                        {"$group": {"_id": None, "avg_hours": {"$avg": "$turnaround_hours"}}}
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            stats = result[0]
            return {
                "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
                "total_tests": stats["total_tests"][0]["count"] if stats["total_tests"] else 0,
                "by_category": {item["_id"]: item["count"] for item in stats["by_category"]},
                "by_priority": {item["_id"]: item["count"] for item in stats["by_priority"]},
                "by_status": {item["_id"]: item["count"] for item in stats["by_status"]},
                "critical_results": stats["critical_results"][0]["count"] if stats["critical_results"] else 0,
                "avg_turnaround_hours": stats["avg_turnaround"][0]["avg_hours"] if stats["avg_turnaround"] else 0
            }
        
        return {}


class DeliveryRepository(BaseRepository[Delivery]):
    """Repository for delivery operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Delivery", Delivery)
    
    async def create_delivery(self, delivery_data: Dict[str, Any]) -> Delivery:
        """Create a new delivery record"""
        return await self.create(delivery_data, auto_id_field="delivery_id")
    
    async def find_by_delivery_id(self, delivery_id: str) -> Optional[Delivery]:
        """Find delivery by ID"""
        return await self.find_by_id(delivery_id, id_field="delivery_id")
    
    async def find_patient_deliveries(self, patient_id: str) -> List[Delivery]:
        """Find all deliveries for a patient"""
        return await self.find_many(
            {"patient_id": patient_id},
            sort=[("delivery_datetime", -1)]
        )
    
    async def admit_to_delivery_room(
        self,
        patient_id: str,
        visit_id: str,
        midwife_id: str,
        room: str
    ) -> Delivery:
        """Admit patient to delivery room"""
        delivery_data = {
            "patient_id": patient_id,
            "visit_id": visit_id,
            "midwife_id": midwife_id,
            "delivery_room": room,
            "admitted_at": datetime.utcnow()
        }
        
        return await self.create_delivery(delivery_data)
    
    async def record_delivery(
        self,
        delivery_id: str,
        delivery_data: Dict[str, Any]
    ) -> Optional[Delivery]:
        """Record delivery details"""
        update_data = {
            "delivery_datetime": delivery_data.get("delivery_datetime", datetime.utcnow()),
            "delivery_type": delivery_data["delivery_type"],
            "baby_gender": delivery_data["baby_gender"],
            "baby_weight_grams": delivery_data["baby_weight_grams"],
            "baby_length_cm": delivery_data.get("baby_length_cm"),
            "apgar_1_min": delivery_data.get("apgar_1_min"),
            "apgar_5_min": delivery_data.get("apgar_5_min"),
            "complications": delivery_data.get("complications", []),
            "blood_loss_ml": delivery_data.get("blood_loss_ml"),
            "placenta_delivered_time": delivery_data.get("placenta_delivered_time"),
            "placenta_complete": delivery_data.get("placenta_complete", True)
        }
        
        # Calculate labor duration if labor start time exists
        delivery = await self.find_by_delivery_id(delivery_id)
        if delivery and delivery.labor_start_time:
            duration = (update_data["delivery_datetime"] - delivery.labor_start_time).total_seconds() / 3600
            update_data["labor_duration_hours"] = duration
        
        return await self.update_by_id(delivery_id, update_data, id_field="delivery_id")
    
    async def record_baby_assessment(
        self,
        delivery_id: str,
        assessment_data: Dict[str, Any]
    ) -> Optional[Delivery]:
        """Record baby assessment after delivery"""
        return await self.update_by_id(
            delivery_id,
            {
                "baby_vitals": assessment_data.get("vitals"),
                "apgar_10_min": assessment_data.get("apgar_10_min"),
                "baby_complications": assessment_data.get("complications", []),
                "nicu_transfer": assessment_data.get("nicu_transfer", False),
                "nicu_transfer_time": assessment_data.get("nicu_transfer_time"),
                "nicu_transfer_reason": assessment_data.get("nicu_transfer_reason")
            },
            id_field="delivery_id"
        )
    
    async def discharge_from_delivery(
        self,
        delivery_id: str,
        discharge_data: Dict[str, Any]
    ) -> Optional[Delivery]:
        """Discharge mother and baby from delivery"""
        return await self.update_by_id(
            delivery_id,
            {
                "mother_discharged_at": discharge_data.get("mother_discharge_time"),
                "baby_discharged_at": discharge_data.get("baby_discharge_time"),
                "discharge_instructions": discharge_data["instructions"],
                "follow_up_scheduled": discharge_data.get("follow_up_scheduled", False)
            },
            id_field="delivery_id"
        )
    
    async def get_daily_delivery_log(self, log_date: date) -> List[Dict[str, Any]]:
        """Get all deliveries for a specific date"""
        start = datetime.combine(log_date, datetime.min.time())
        end = datetime.combine(log_date, datetime.max.time())
        
        pipeline = [
            {"$match": {
                "delivery_datetime": {"$gte": start, "$lte": end}
            }},
            {
                "$lookup": {
                    "from": "Patient",
                    "localField": "patient_id",
                    "foreignField": "patient_id",
                    "as": "mother"
                }
            },
            {"$unwind": "$mother"},
            {
                "$lookup": {
                    "from": "Staff",
                    "localField": "midwife_id",
                    "foreignField": "staff_id",
                    "as": "midwife"
                }
            },
            {"$unwind": "$midwife"},
            {
                "$project": {
                    "delivery_id": 1,
                    "mother_name": {
                        "$concat": ["$mother.first_name", " ", "$mother.last_name"]
                    },
                    "midwife_name": {
                        "$concat": ["$midwife.first_name", " ", "$midwife.last_name"]
                    },
                    "delivery_datetime": 1,
                    "delivery_type": 1,
                    "baby_gender": 1,
                    "baby_weight_grams": 1,
                    "apgar_scores": {
                        "one_min": "$apgar_1_min",
                        "five_min": "$apgar_5_min"
                    },
                    "complications": 1,
                    "nicu_transfer": 1
                }
            },
            {"$sort": {"delivery_datetime": 1}}
        ]
        
        return await self.aggregate(pipeline)
    
    async def get_delivery_statistics(
        self,
        from_date: date,
        to_date: date
    ) -> Dict[str, Any]:
        """Get delivery statistics"""
        pipeline = [
            {"$match": {
                "delivery_datetime": {"$gte": from_date, "$lte": to_date}
            }},
            {
                "$facet": {
                    "total_deliveries": [{"$count": "count"}],
                    "by_type": [
                        {"$group": {"_id": "$delivery_type", "count": {"$sum": 1}}}
                    ],
                    "by_gender": [
                        {"$group": {"_id": "$baby_gender", "count": {"$sum": 1}}}
                    ],
                    "complications": [
                        {"$match": {"complications": {"$ne": ["none"]}}},
                        {"$count": "count"}
                    ],
                    "nicu_transfers": [
                        {"$match": {"nicu_transfer": True}},
                        {"$count": "count"}
                    ],
                    "avg_baby_weight": [
                        {"$group": {"_id": None, "avg_weight": {"$avg": "$baby_weight_grams"}}}
                    ],
                    "avg_labor_duration": [
                        {"$match": {"labor_duration_hours": {"$exists": True}}},
                        {"$group": {"_id": None, "avg_hours": {"$avg": "$labor_duration_hours"}}}
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            stats = result[0]
            return {
                "period": {"from": from_date.isoformat(), "to": to_date.isoformat()},
                "total_deliveries": stats["total_deliveries"][0]["count"] if stats["total_deliveries"] else 0,
                "by_type": {item["_id"]: item["count"] for item in stats["by_type"]},
                "by_gender": {item["_id"]: item["count"] for item in stats["by_gender"]},
                "complications": stats["complications"][0]["count"] if stats["complications"] else 0,
                "nicu_transfers": stats["nicu_transfers"][0]["count"] if stats["nicu_transfers"] else 0,
                "avg_baby_weight_grams": stats["avg_baby_weight"][0]["avg_weight"] if stats["avg_baby_weight"] else 0,
                "avg_labor_duration_hours": stats["avg_labor_duration"][0]["avg_hours"] if stats["avg_labor_duration"] else 0
            }
        
        return {}


class RecoveryRepository(BaseRepository[RecoveryStay]):
    """Repository for recovery room operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "RecoveryStay", RecoveryStay)
        self.observation_collection = database["RecoveryObservation"]
    
    async def create_recovery_stay(self, stay_data: Dict[str, Any]) -> RecoveryStay:
        """Create a new recovery stay"""
        return await self.create(stay_data, auto_id_field="stay_id")
    
    async def find_by_stay_id(self, stay_id: str) -> Optional[RecoveryStay]:
        """Find recovery stay by ID"""
        return await self.find_by_id(stay_id, id_field="stay_id")
    
    async def find_active_stays(self) -> List[RecoveryStay]:
        """Find all active recovery stays"""
        return await self.find_many({
            "status": {"$in": [
                RecoveryStatus.ADMITTED.value,
                RecoveryStatus.STABLE.value,
                RecoveryStatus.IMPROVING.value,
                RecoveryStatus.DETERIORATING.value
            ]}
        })
    
    async def admit_to_recovery(
        self,
        patient_id: str,
        visit_id: str,
        admit_data: Dict[str, Any]
    ) -> RecoveryStay:
        """Admit patient to recovery room"""
        stay_data = {
            "patient_id": patient_id,
            "visit_id": visit_id,
            "admit_time": datetime.utcnow(),
            "admit_from": admit_data["from"],
            "admit_reason": admit_data["reason"],
            "admit_diagnosis": admit_data["diagnosis"],
            "bed_number": admit_data["bed_number"],
            "admitting_staff_id": admit_data["staff_id"],
            "initial_vitals": admit_data["vitals"],
            "initial_pain_score": admit_data.get("pain_score"),
            "initial_consciousness": admit_data.get("consciousness", "alert"),
            "monitoring_frequency_minutes": admit_data.get("monitoring_frequency", 15)
        }
        
        return await self.create_recovery_stay(stay_data)
    
    async def add_observation(
        self,
        stay_id: str,
        observation_data: Dict[str, Any],
        observed_by: str
    ) -> bool:
        """Add observation to recovery stay"""
        # Get next sequence number
        count = await self.observation_collection.count_documents({"stay_id": stay_id})
        
        observation = {
            "stay_id": stay_id,
            "observation_id": f"OBS{stay_id}-{count + 1}",
            "sequence_number": count + 1,
            "observation_time": datetime.utcnow(),
            "observation_type": observation_data["type"],
            "observed_by": observed_by,
            **observation_data
        }
        
        result = await self.observation_collection.insert_one(observation)
        
        # Update stay status if critical
        if observation_data.get("is_critical"):
            await self.update_by_id(
                stay_id,
                {"status": RecoveryStatus.DETERIORATING.value},
                id_field="stay_id"
            )
        
        return result.inserted_id is not None
    
    async def discharge_from_recovery(
        self,
        stay_id: str,
        discharge_data: Dict[str, Any]
    ) -> Optional[RecoveryStay]:
        """Discharge patient from recovery"""
        return await self.update_by_id(
            stay_id,
            {
                "discharge_time": datetime.utcnow(),
                "discharge_to": discharge_data["to"],
                "discharge_status": discharge_data["status"],
                "discharge_instructions": discharge_data["instructions"],
                "discharge_vitals": discharge_data["vitals"],
                "signed_off_by": discharge_data["staff_id"],
                "status": RecoveryStatus.DISCHARGED.value
            },
            id_field="stay_id"
        )
    
    async def get_recovery_room_log(self, log_date: date) -> List[Dict[str, Any]]:
        """Get recovery room log for a specific date"""
        start = datetime.combine(log_date, datetime.min.time())
        end = datetime.combine(log_date, datetime.max.time())
        
        pipeline = [
            {"$match": {
                "$or": [
                    {"admit_time": {"$gte": start, "$lte": end}},
                    {"discharge_time": {"$gte": start, "$lte": end}},
                    {"status": {"$ne": RecoveryStatus.DISCHARGED.value}}
                ]
            }},
            {
                "$lookup": {
                    "from": "Patient",
                    "localField": "patient_id",
                    "foreignField": "patient_id",
                    "as": "patient"
                }
            },
            {"$unwind": "$patient"},
            {
                "$lookup": {
                    "from": "RecoveryObservation",
                    "localField": "stay_id",
                    "foreignField": "stay_id",
                    "as": "observations"
                }
            },
            {
                "$project": {
                    "stay_id": 1,
                    "patient_name": {
                        "$concat": ["$patient.first_name", " ", "$patient.last_name"]
                    },
                    "bed_number": 1,
                    "admit_time": 1,
                    "discharge_time": 1,
                    "status": 1,
                    "admit_reason": 1,
                    "observation_count": {"$size": "$observations"},
                    "length_of_stay_hours": {
                        "$cond": {
                            "if": {"$ne": ["$discharge_time", None]},
                            "then": {
                                "$divide": [
                                    {"$subtract": ["$discharge_time", "$admit_time"]},
                                    3600000
                                ]
                            },
                            "else": {
                                "$divide": [
                                    {"$subtract": [datetime.utcnow(), "$admit_time"]},
                                    3600000
                                ]
                            }
                        }
                    }
                }
            },
            {"$sort": {"admit_time": 1}}
        ]
        
        return await self.aggregate(pipeline)