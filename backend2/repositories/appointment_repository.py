# backend/repositories/appointment_repository.py
"""Repository for Appointment, WeeklyCoverage, and PractitionerDailySchedule operations"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, time, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase

from .base_repository import BaseRepository
from ..models.appointment import (
    Appointment, WeeklyCoverage, PractitionerDailySchedule,
    AppointmentStatus, AppointmentType
)


class AppointmentRepository(BaseRepository[Appointment]):
    """Repository for appointment-specific database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "Appointment", Appointment)
    
    async def create_appointment(self, appointment_data: Dict[str, Any]) -> Appointment:
        """
        Create a new appointment with auto-generated appointment_id
        
        Args:
            appointment_data: Appointment information
        
        Returns:
            Created appointment
        """
        return await self.create(appointment_data, auto_id_field="appointment_id")
    
    async def find_by_appointment_id(self, appointment_id: str) -> Optional[Appointment]:
        """
        Find appointment by appointment_id
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            Appointment or None
        """
        return await self.find_by_id(appointment_id, id_field="appointment_id")
    
    async def find_patient_appointments(
        self,
        patient_id: str,
        status: Optional[AppointmentStatus] = None,
        from_date: Optional[date] = None
    ) -> List[Appointment]:
        """
        Find appointments for a patient
        
        Args:
            patient_id: Patient ID
            status: Optional status filter
            from_date: Optional date filter (appointments from this date onwards)
        
        Returns:
            List of appointments
        """
        filter_dict = {"patient_id": patient_id}
        
        if status:
            filter_dict["status"] = status.value
        
        if from_date:
            filter_dict["scheduled_date"] = {"$gte": from_date}
        
        return await self.find_many(
            filter_dict,
            sort=[("scheduled_date", 1), ("scheduled_start", 1)]
        )
    
    async def find_staff_appointments(
        self,
        staff_id: str,
        date: date
    ) -> List[Appointment]:
        """
        Find appointments for a staff member on a specific date
        
        Args:
            staff_id: Staff ID
            date: Date to check
        
        Returns:
            List of appointments
        """
        return await self.find_many(
            {
                "staff_id": staff_id,
                "scheduled_date": date,
                "status": {"$ne": AppointmentStatus.CANCELLED.value}
            },
            sort=[("scheduled_start", 1)]
        )
    
    async def find_appointments_by_date_range(
        self,
        start_date: date,
        end_date: date,
        staff_id: Optional[str] = None
    ) -> List[Appointment]:
        """
        Find appointments within a date range
        
        Args:
            start_date: Start date
            end_date: End date
            staff_id: Optional staff filter
        
        Returns:
            List of appointments
        """
        filter_dict = {
            "scheduled_date": {"$gte": start_date, "$lte": end_date},
            "status": {"$ne": AppointmentStatus.CANCELLED.value}
        }
        
        if staff_id:
            filter_dict["staff_id"] = staff_id
        
        return await self.find_many(filter_dict, sort=[("scheduled_date", 1), ("scheduled_start", 1)])
    
    async def find_available_slots(
        self,
        staff_id: str,
        date: date,
        duration_minutes: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find available time slots for a staff member
        
        Args:
            staff_id: Staff ID
            date: Date to check
            duration_minutes: Appointment duration (default 10)
        
        Returns:
            List of available time slots
        """
        # Get staff schedule for the day
        schedule_repo = PractitionerDailyScheduleRepository(self.database)
        schedule = await schedule_repo.find_by_staff_and_date(staff_id, date)
        
        if not schedule or not schedule.is_available:
            return []
        
        # Get existing appointments
        appointments = await self.find_staff_appointments(staff_id, date)
        
        # Calculate available slots
        available_slots = []
        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)
        
        # Create slots every 10 minutes
        while current_time + timedelta(minutes=duration_minutes) <= end_time:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            
            # Check if slot conflicts with existing appointments
            is_available = True
            for appointment in appointments:
                appt_start = datetime.combine(date, appointment.scheduled_start)
                appt_end = datetime.combine(date, appointment.scheduled_end)
                
                if not (slot_end <= appt_start or current_time >= appt_end):
                    is_available = False
                    break
            
            # Check if slot conflicts with breaks
            for break_slot in schedule.break_slots:
                break_start = datetime.combine(date, time.fromisoformat(break_slot["start"]))
                break_end = datetime.combine(date, time.fromisoformat(break_slot["end"]))
                
                if not (slot_end <= break_start or current_time >= break_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    "start_time": current_time.time(),
                    "end_time": slot_end.time(),
                    "staff_id": staff_id,
                    "date": date
                })
            
            current_time += timedelta(minutes=10)
        
        return available_slots
    
    async def check_appointment_conflict(
        self,
        staff_id: str,
        date: date,
        start_time: time,
        end_time: time,
        exclude_appointment_id: Optional[str] = None
    ) -> bool:
        """
        Check if there's a scheduling conflict
        
        Args:
            staff_id: Staff ID
            date: Appointment date
            start_time: Start time
            end_time: End time
            exclude_appointment_id: Appointment ID to exclude (for updates)
        
        Returns:
            True if there's a conflict, False otherwise
        """
        filter_dict = {
            "staff_id": staff_id,
            "scheduled_date": date,
            "status": {"$ne": AppointmentStatus.CANCELLED.value}
        }
        
        if exclude_appointment_id:
            filter_dict["appointment_id"] = {"$ne": exclude_appointment_id}
        
        appointments = await self.find_many(filter_dict)
        
        for appointment in appointments:
            # Check for time overlap
            if not (end_time <= appointment.scheduled_start or start_time >= appointment.scheduled_end):
                return True
        
        return False
    
    async def create_walk_in_appointment(
        self,
        patient_id: str,
        reason: str,
        preferred_staff_id: Optional[str] = None
    ) -> Optional[Appointment]:
        """
        Create a walk-in appointment and assign to available practitioner
        
        Args:
            patient_id: Patient ID
            reason: Reason for visit
            preferred_staff_id: Preferred practitioner if any
        
        Returns:
            Created appointment or None if no availability
        """
        today = date.today()
        now = datetime.now().time()
        
        # Find available practitioner
        if preferred_staff_id:
            # Check if preferred staff is available
            slots = await self.find_available_slots(preferred_staff_id, today)
            available_slots = [s for s in slots if s["start_time"] >= now]
            
            if available_slots:
                selected_slot = available_slots[0]
                staff_id = preferred_staff_id
            else:
                return None
        else:
            # Find any available practitioner
            schedule_repo = PractitionerDailyScheduleRepository(self.database)
            available_practitioners = await schedule_repo.find_available_for_walk_ins(today)
            
            if not available_practitioners:
                return None
            
            # Get first available slot
            for practitioner in available_practitioners:
                slots = await self.find_available_slots(practitioner.staff_id, today)
                available_slots = [s for s in slots if s["start_time"] >= now]
                
                if available_slots:
                    selected_slot = available_slots[0]
                    staff_id = practitioner.staff_id
                    break
            else:
                return None
        
        # Create walk-in appointment
        appointment_data = {
            "patient_id": patient_id,
            "staff_id": staff_id,
            "scheduled_date": today,
            "scheduled_start": selected_slot["start_time"],
            "scheduled_end": selected_slot["end_time"],
            "appointment_type": AppointmentType.WALK_IN.value,
            "status": AppointmentStatus.CONFIRMED.value,
            "reason_for_visit": reason,
            "is_walk_in": True,
            "walk_in_arrival_time": datetime.now()
        }
        
        return await self.create_appointment(appointment_data)
    
    async def cancel_appointment(
        self,
        appointment_id: str,
        cancelled_by: str,
        reason: str
    ) -> Optional[Appointment]:
        """
        Cancel an appointment
        
        Args:
            appointment_id: Appointment ID
            cancelled_by: Staff ID who cancelled
            reason: Cancellation reason
        
        Returns:
            Updated appointment or None
        """
        return await self.update_by_id(
            appointment_id,
            {
                "status": AppointmentStatus.CANCELLED.value,
                "cancelled_at": datetime.utcnow(),
                "cancelled_by": cancelled_by,
                "cancellation_reason": reason
            },
            id_field="appointment_id"
        )
    
    async def mark_no_show(self, appointment_id: str) -> Optional[Appointment]:
        """
        Mark appointment as no-show
        
        Args:
            appointment_id: Appointment ID
        
        Returns:
            Updated appointment or None
        """
        return await self.update_by_id(
            appointment_id,
            {"status": AppointmentStatus.NO_SHOW.value},
            id_field="appointment_id"
        )
    
    async def get_daily_appointment_statistics(self, date: date) -> Dict[str, Any]:
        """
        Get appointment statistics for a specific date
        
        Args:
            date: Date to analyze
        
        Returns:
            Statistics dictionary
        """
        pipeline = [
            {"$match": {"scheduled_date": date}},
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "by_status": [
                        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
                    ],
                    "by_type": [
                        {"$group": {"_id": "$appointment_type", "count": {"$sum": 1}}}
                    ],
                    "walk_ins": [
                        {"$match": {"is_walk_in": True}},
                        {"$count": "count"}
                    ],
                    "by_hour": [
                        {
                            "$project": {
                                "hour": {"$hour": "$scheduled_start"}
                            }
                        },
                        {"$group": {"_id": "$hour", "count": {"$sum": 1}}},
                        {"$sort": {"_id": 1}}
                    ]
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        
        if result:
            stats = result[0]
            return {
                "date": date.isoformat(),
                "total_appointments": stats["total"][0]["count"] if stats["total"] else 0,
                "by_status": {item["_id"]: item["count"] for item in stats["by_status"]},
                "by_type": {item["_id"]: item["count"] for item in stats["by_type"]},
                "walk_ins": stats["walk_ins"][0]["count"] if stats["walk_ins"] else 0,
                "by_hour": stats["by_hour"]
            }
        
        return {}


class WeeklyCoverageRepository(BaseRepository[WeeklyCoverage]):
    """Repository for weekly coverage schedule operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "WeeklyCoverage", WeeklyCoverage)
    
    async def create_coverage(self, coverage_data: Dict[str, Any]) -> WeeklyCoverage:
        """Create weekly coverage schedule"""
        return await self.create(coverage_data, auto_id_field="coverage_id")
    
    async def find_by_week(self, week_start: date) -> Optional[WeeklyCoverage]:
        """Find coverage for a specific week"""
        return await self.find_one({"week_start": week_start})
    
    async def find_coverage_for_date(self, date: date) -> Optional[WeeklyCoverage]:
        """Find coverage that includes a specific date"""
        week_start = date - timedelta(days=date.weekday())
        return await self.find_by_week(week_start)
    
    async def approve_coverage(
        self,
        coverage_id: str,
        approved_by: str
    ) -> Optional[WeeklyCoverage]:
        """Approve weekly coverage schedule"""
        return await self.update_by_id(
            coverage_id,
            {
                "approved": True,
                "approved_by": approved_by,
                "approved_at": datetime.utcnow()
            },
            id_field="coverage_id"
        )
    
    async def get_on_call_staff(self, date: date) -> Optional[Dict[str, Any]]:
        """Get on-call staff for a specific date"""
        coverage = await self.find_coverage_for_date(date)
        
        if coverage:
            for assignment in coverage.on_call_assignments:
                if assignment["date"] == date:
                    return assignment
        
        return None


class PractitionerDailyScheduleRepository(BaseRepository[PractitionerDailySchedule]):
    """Repository for practitioner daily schedule operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        super().__init__(database, "PractitionerDailySchedule", PractitionerDailySchedule)
    
    async def create_schedule(self, schedule_data: Dict[str, Any]) -> PractitionerDailySchedule:
        """Create daily schedule for practitioner"""
        return await self.create(schedule_data, auto_id_field="schedule_id")
    
    async def find_by_staff_and_date(
        self,
        staff_id: str,
        date: date
    ) -> Optional[PractitionerDailySchedule]:
        """Find schedule for specific staff and date"""
        return await self.find_one({
            "staff_id": staff_id,
            "schedule_date": date
        })
    
    async def find_schedules_by_date(
        self,
        date: date,
        available_only: bool = False
    ) -> List[PractitionerDailySchedule]:
        """Find all schedules for a specific date"""
        filter_dict = {"schedule_date": date}
        
        if available_only:
            filter_dict["is_available"] = True
        
        return await self.find_many(filter_dict, sort=[("start_time", 1)])
    
    async def find_available_for_walk_ins(
        self,
        date: date
    ) -> List[PractitionerDailySchedule]:
        """Find practitioners available for walk-ins on a date"""
        return await self.find_many({
            "schedule_date": date,
            "is_available": True,
            "available_for_walk_ins": True,
            "$expr": {"$lt": ["$current_walk_ins", "$max_walk_ins"]}
        })
    
    async def update_booked_slots(
        self,
        staff_id: str,
        date: date,
        increment: int = 1
    ) -> Optional[PractitionerDailySchedule]:
        """Update the number of booked slots"""
        schedule = await self.find_by_staff_and_date(staff_id, date)
        
        if schedule:
            new_booked = schedule.booked_slots + increment
            if new_booked <= schedule.total_slots:
                return await self.update_one(
                    {"staff_id": staff_id, "schedule_date": date},
                    {"booked_slots": new_booked}
                )
        
        return None
    
    async def increment_walk_ins(
        self,
        staff_id: str,
        date: date
    ) -> Optional[PractitionerDailySchedule]:
        """Increment walk-in count for a practitioner"""
        return await self.collection.find_one_and_update(
            {"staff_id": staff_id, "schedule_date": date},
            {"$inc": {"current_walk_ins": 1}},
            return_document=True
        )
    
    async def block_time_slot(
        self,
        staff_id: str,
        date: date,
        start_time: time,
        end_time: time,
        reason: str
    ) -> Optional[PractitionerDailySchedule]:
        """Block a time slot in practitioner's schedule"""
        blocked_slot = {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "reason": reason
        }
        
        return await self.collection.find_one_and_update(
            {"staff_id": staff_id, "schedule_date": date},
            {"$push": {"blocked_slots": blocked_slot}},
            return_document=True
        )
    
    async def get_schedule_utilization(
        self,
        date: date
    ) -> Dict[str, Any]:
        """Get schedule utilization statistics for a date"""
        pipeline = [
            {"$match": {"schedule_date": date}},
            {
                "$group": {
                    "_id": None,
                    "total_slots": {"$sum": "$total_slots"},
                    "booked_slots": {"$sum": "$booked_slots"},
                    "total_walk_ins": {"$sum": "$current_walk_ins"},
                    "practitioners_scheduled": {"$sum": 1}
                }
            },
            {
                "$project": {
                    "total_slots": 1,
                    "booked_slots": 1,
                    "total_walk_ins": 1,
                    "practitioners_scheduled": 1,
                    "utilization_rate": {
                        "$multiply": [
                            {"$divide": ["$booked_slots", "$total_slots"]},
                            100
                        ]
                    }
                }
            }
        ]
        
        result = await self.aggregate(pipeline)
        return result[0] if result else {}
# End of backend/repositories/appointment_repository.py