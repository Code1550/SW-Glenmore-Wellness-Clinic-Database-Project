# backend/repositories/staff_repository.py
"""Repository for Staff, Role, and StaffRole collection operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base_repository import BaseRepository
from ..models.staff import Staff, Role, StaffRole, RoleType, Specialization


class StaffRepository(BaseRepository[Staff]):
    """Repository for staff-specific database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Staff", Staff)
        self.role_collection = database["Role"]
        self.staff_role_collection = database["StaffRole"]
    
    async def create_staff(self, staff_data: Dict[str, Any]) -> Staff:
        """
        Create a new staff member with auto-generated staff_id
        
        Args:
            staff_data: Staff information
        
        Returns:
            Created staff member
        """
        return await self.create(staff_data, auto_id_field="staff_id")
    
    async def find_by_staff_id(self, staff_id: str) -> Optional[Staff]:
        """
        Find staff member by staff_id
        
        Args:
            staff_id: Staff ID
        
        Returns:
            Staff member or None
        """
        return await self.find_by_id(staff_id, id_field="staff_id")
    
    async def find_by_email(self, email: str) -> Optional[Staff]:
        """
        Find staff member by email
        
        Args:
            email: Staff email address
        
        Returns:
            Staff member or None
        """
        return await self.find_one({"email": email.lower()})
    
    async def find_by_license_number(self, license_number: str) -> Optional[Staff]:
        """
        Find staff member by professional license number
        
        Args:
            license_number: License number
        
        Returns:
            Staff member or None
        """
        return await self.find_one({"license_number": license_number})
    
    async def find_active_staff(self) -> List[Staff]:
        """
        Find all active staff members
        
        Returns:
            List of active staff members
        """
        return await self.find_many(
            {"is_active": True},
            sort=[("last_name", 1), ("first_name", 1)]
        )
    
    async def find_staff_by_specialization(
        self,
        specialization: Specialization
    ) -> List[Staff]:
        """
        Find staff members by specialization
        
        Args:
            specialization: Medical specialization
        
        Returns:
            List of staff with specified specialization
        """
        return await self.find_many({"specialization": specialization.value})
    
    async def get_staff_with_roles(self, staff_id: str) -> Optional[Dict[str, Any]]:
        """
        Get staff member with their assigned roles
        
        Args:
            staff_id: Staff ID
        
        Returns:
            Staff member with roles or None
        """
        pipeline = [
            {"$match": {"staff_id": staff_id}},
            {
                "$lookup": {
                    "from": "StaffRole",
                    "localField": "staff_id",
                    "foreignField": "staff_id",
                    "as": "staff_roles"
                }
            },
            {
                "$lookup": {
                    "from": "Role",
                    "let": {"role_ids": "$staff_roles.role_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$role_id", "$$role_ids"]}}}
                    ],
                    "as": "roles"
                }
            }
        ]
        
        results = await self.aggregate(pipeline)
        return results[0] if results else None
    
    async def assign_role_to_staff(
        self,
        staff_id: str,
        role_id: str,
        assigned_by: str,
        is_primary: bool = False
    ) -> bool:
        """
        Assign a role to a staff member
        
        Args:
            staff_id: Staff ID
            role_id: Role ID
            assigned_by: Staff ID who assigned the role
            is_primary: Whether this is the primary role
        
        Returns:
            True if successful, False otherwise
        """
        # Check if assignment already exists
        existing = await self.staff_role_collection.find_one({
            "staff_id": staff_id,
            "role_id": role_id
        })
        
        if existing:
            return False
        
        # If setting as primary, unset other primary roles
        if is_primary:
            await self.staff_role_collection.update_many(
                {"staff_id": staff_id},
                {"$set": {"is_primary": False}}
            )
        
        # Create new assignment
        staff_role = {
            "staff_id": staff_id,
            "role_id": role_id,
            "assigned_by": assigned_by,
            "assigned_date": datetime.utcnow(),
            "is_primary": is_primary
        }
        
        result = await self.staff_role_collection.insert_one(staff_role)
        return result.inserted_id is not None
    
    async def remove_role_from_staff(self, staff_id: str, role_id: str) -> bool:
        """
        Remove a role from a staff member
        
        Args:
            staff_id: Staff ID
            role_id: Role ID
        
        Returns:
            True if removed, False otherwise
        """
        result = await self.staff_role_collection.delete_one({
            "staff_id": staff_id,
            "role_id": role_id
        })
        return result.deleted_count > 0
    
    async def deactivate_staff(self, staff_id: str) -> Optional[Staff]:
        """
        Deactivate a staff member (soft delete)
        
        Args:
            staff_id: Staff ID
        
        Returns:
            Updated staff member or None
        """
        return await self.update_by_id(
            staff_id,
            {"is_active": False},
            id_field="staff_id"
        )
    
    async def update_staff_schedule_preference(
        self,
        staff_id: str,
        preferences: Dict[str, Any]
    ) -> Optional[Staff]:
        """
        Update staff scheduling preferences
        
        Args:
            staff_id: Staff ID
            preferences: Scheduling preferences
        
        Returns:
            Updated staff member or None
        """
        return await self.update_by_id(
            staff_id,
            {"schedule_preferences": preferences},
            id_field="staff_id"
        )


class RoleRepository(BaseRepository[Role]):
    """Repository for role-specific database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Role", Role)
    
    async def create_role(self, role_data: Dict[str, Any]) -> Role:
        """
        Create a new role with auto-generated role_id
        
        Args:
            role_data: Role information
        
        Returns:
            Created role
        """
        return await self.create(role_data, auto_id_field="role_id")
    
    async def find_by_role_id(self, role_id: str) -> Optional[Role]:
        """
        Find role by role_id
        
        Args:
            role_id: Role ID
        
        Returns:
            Role or None
        """
        return await self.find_by_id(role_id, id_field="role_id")
    
    async def find_by_role_name(self, role_name: RoleType) -> Optional[Role]:
        """
        Find role by role name
        
        Args:
            role_name: Role type
        
        Returns:
            Role or None
        """
        return await self.find_one({"role_name": role_name.value})
    
    async def find_medical_roles(self) -> List[Role]:
        """
        Find all medical professional roles
        
        Returns:
            List of medical roles
        """
        return await self.find_many({"is_medical_professional": True})
    
    async def find_roles_with_permission(self, permission: str) -> List[Role]:
        """
        Find roles that have a specific permission
        
        Args:
            permission: Permission code
        
        Returns:
            List of roles with the permission
        """
        return await self.find_many({"permissions": permission})
    
    async def update_role_permissions(
        self,
        role_id: str,
        permissions: List[str]
    ) -> Optional[Role]:
        """
        Update role permissions
        
        Args:
            role_id: Role ID
            permissions: New list of permissions
        
        Returns:
            Updated role or None
        """
        return await self.update_by_id(
            role_id,
            {"permissions": permissions},
            id_field="role_id"
        )


class StaffScheduleRepository:
    """Repository for staff scheduling operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.staff_collection = database["Staff"]
        self.role_collection = database["Role"]
        self.staff_role_collection = database["StaffRole"]
    
    async def find_available_physicians(
        self,
        date: date,
        time_slot: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Find available physicians for a given date/time
        
        Args:
            date: Date to check
            time_slot: Optional specific time slot
        
        Returns:
            List of available physicians
        """
        pipeline = [
            # Get physicians
            {"$match": {"specialization": {"$exists": True}, "is_active": True}},
            
            # Get their roles
            {
                "$lookup": {
                    "from": "StaffRole",
                    "localField": "staff_id",
                    "foreignField": "staff_id",
                    "as": "staff_roles"
                }
            },
            
            # Get role details
            {
                "$lookup": {
                    "from": "Role",
                    "let": {"role_ids": "$staff_roles.role_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$in": ["$role_id", "$$role_ids"]},
                            "can_admit_patients": True
                        }}
                    ],
                    "as": "roles"
                }
            },
            
            # Filter those with physician role
            {"$match": {"roles": {"$ne": []}}},
            
            # Check availability (would need to join with PractitionerDailySchedule)
            {
                "$lookup": {
                    "from": "PractitionerDailySchedule",
                    "let": {"staff_id": "$staff_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$staff_id", "$$staff_id"]},
                                    {"$eq": ["$schedule_date", date]}
                                ]
                            }
                        }}
                    ],
                    "as": "schedule"
                }
            },
            
            # Filter available ones
            {"$match": {
                "$or": [
                    {"schedule": {"$eq": []}},  # No schedule means available
                    {"schedule.is_available": True}
                ]
            }}
        ]
        
        return await self.staff_collection.aggregate(pipeline).to_list(length=None)
    
    async def find_available_nurses(
        self,
        date: date,
        shift: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        Find available nurses for a given date and shift
        
        Args:
            date: Date to check
            shift: Shift (day/evening/night)
        
        Returns:
            List of available nurses
        """
        pipeline = [
            # Get active staff
            {"$match": {"is_active": True}},
            
            # Get their roles
            {
                "$lookup": {
                    "from": "StaffRole",
                    "localField": "staff_id",
                    "foreignField": "staff_id",
                    "as": "staff_roles"
                }
            },
            
            # Get role details for nurses
            {
                "$lookup": {
                    "from": "Role",
                    "let": {"role_ids": "$staff_roles.role_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {"$in": ["$role_id", "$$role_ids"]},
                            "role_name": {"$in": ["registered_nurse", "nurse_practitioner"]}
                        }}
                    ],
                    "as": "roles"
                }
            },
            
            # Filter those with nurse role
            {"$match": {"roles": {"$ne": []}}},
            
            # Check schedule availability
            {
                "$lookup": {
                    "from": "PractitionerDailySchedule",
                    "let": {"staff_id": "$staff_id"},
                    "pipeline": [
                        {"$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$staff_id", "$$staff_id"]},
                                    {"$eq": ["$schedule_date", date]}
                                ]
                            }
                        }}
                    ],
                    "as": "schedule"
                }
            }
        ]
        
        return await self.staff_collection.aggregate(pipeline).to_list(length=None)
    
    async def get_staff_statistics_by_role(self) -> Dict[str, Any]:
        """
        Get statistics about staff by role
        
        Returns:
            Dictionary with staff statistics
        """
        pipeline = [
            {
                "$lookup": {
                    "from": "StaffRole",
                    "localField": "staff_id",
                    "foreignField": "staff_id",
                    "as": "staff_roles"
                }
            },
            {
                "$lookup": {
                    "from": "Role",
                    "let": {"role_ids": "$staff_roles.role_id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$in": ["$role_id", "$$role_ids"]}}}
                    ],
                    "as": "roles"
                }
            },
            {
                "$facet": {
                    "total_staff": [{"$count": "count"}],
                    "active_staff": [
                        {"$match": {"is_active": True}},
                        {"$count": "count"}
                    ],
                    "by_specialization": [
                        {"$group": {"_id": "$specialization", "count": {"$sum": 1}}}
                    ],
                    "by_role": [
                        {"$unwind": "$roles"},
                        {"$group": {"_id": "$roles.role_name", "count": {"$sum": 1}}}
                    ],
                    "can_prescribe": [
                        {"$match": {"roles.can_prescribe": True}},
                        {"$count": "count"}
                    ]
                }
            }
        ]
        
        result = await self.staff_collection.aggregate(pipeline).to_list(length=None)
        
        if result:
            stats = result[0]
            return {
                "total_staff": stats["total_staff"][0]["count"] if stats["total_staff"] else 0,
                "active_staff": stats["active_staff"][0]["count"] if stats["active_staff"] else 0,
                "by_specialization": {item["_id"]: item["count"] for item in stats["by_specialization"] if item["_id"]},
                "by_role": {item["_id"]: item["count"] for item in stats["by_role"]},
                "can_prescribe": stats["can_prescribe"][0]["count"] if stats["can_prescribe"] else 0
            }
        
        return {}
