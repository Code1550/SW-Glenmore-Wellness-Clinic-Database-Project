from database import get_next_sequence
from .connection_DB import db

# Insert appointment-related functions here
def insert_weekly_coverage(staff_id: int, week_start, on_call_phone: str, notes: str = None):
    """
    Inserts a new WeeklyCoverage record into the database.
    Auto-generates Coverage_Id using sequence counter.
    """
    coverage_id = get_next_sequence("Coverage_Id")

    new_coverage = {
        "Coverage_Id": coverage_id,
        "Staff_Id": staff_id,
        "Week_Start": week_start,
        "On_Call_Phone": on_call_phone,
        "Notes": notes
    }

    db.WeeklyCoverage.insert_one(new_coverage)
    print(f"Weekly coverage added with Coverage_Id {coverage_id} for Staff_Id {staff_id}")

# Insert practitioner schedule function
def insert_practitioner_schedule(staff_id: int, work_date, slot_start, slot_end, is_walkin: bool):
    """
    Inserts a new PractitionerDailySchedule record into the database.
    Auto-generates Sched_Id using sequence counter.
    """
    sched_id = get_next_sequence("Sched_Id")

    new_schedule = {
        "Sched_Id": sched_id,
        "Staff_Id": staff_id,
        "Work_Date": work_date,
        "Slot_Start": slot_start,
        "Slot_End": slot_end,
        "Is_Walkin": is_walkin
    }

    db.PractitionerDailySchedule.insert_one(new_schedule)
    print(f"Schedule added with Sched_Id {sched_id} for Staff_Id {staff_id} on {work_date}")

# Update weekly coverage function
def update_weekly_coverage(coverage_id: int, staff_id=None, week_start=None, on_call_phone=None, notes=None):
    """
    Updates a WeeklyCoverage record.
    Any field can be updated except the primary key (Coverage_Id).
    """
    # Find record
    coverage = db.WeeklyCoverage.find_one({"Coverage_Id": coverage_id})
    if not coverage:
        print(f"No WeeklyCoverage found with Coverage_Id: {coverage_id}")
        return False

    # Build update object
    update_fields = {}
    if staff_id is not None:
        update_fields["Staff_Id"] = staff_id
    if week_start is not None:
        update_fields["Week_Start"] = week_start
    if on_call_phone is not None:
        update_fields["On_Call_Phone"] = on_call_phone
    if notes is not None:
        update_fields["Notes"] = notes

    # Perform update if any field was provided
    if update_fields:
        db.WeeklyCoverage.update_one(
            {"Coverage_Id": coverage_id},
            {"$set": update_fields}
        )
        print(f"WeeklyCoverage {coverage_id} updated with: {update_fields}")
    else:
        print("No fields provided to update.")

    return True

def update_practitioner_schedule(sched_id: int, staff_id=None, work_date=None, slot_start=None, slot_end=None, is_walkin=None):
    """
    Updates a PractitionerDailySchedule record.
    Any field can be updated except the primary key (Sched_Id).
    """
    # Find record
    schedule = db.PractitionerDailySchedule.find_one({"Sched_Id": sched_id})
    if not schedule:
        print(f"No PractitionerDailySchedule found with Sched_Id: {sched_id}")
        return False

    # Build update object
    update_fields = {}
    if staff_id is not None:
        update_fields["Staff_Id"] = staff_id
    if work_date is not None:
        update_fields["Work_Date"] = work_date
    if slot_start is not None:
        update_fields["Slot_Start"] = slot_start
    if slot_end is not None:
        update_fields["Slot_End"] = slot_end
    if is_walkin is not None:
        update_fields["Is_Walkin"] = is_walkin

    # Perform update if any field was provided
    if update_fields:
        db.PractitionerDailySchedule.update_one(
            {"Sched_Id": sched_id},
            {"$set": update_fields}
        )
        print(f"PractitionerDailySchedule {sched_id} updated with: {update_fields}")
    else:
        print("No fields provided to update.")

    return True 