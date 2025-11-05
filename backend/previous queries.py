# Initialize counters for primary keys in the database 2025-11-05
'''db = client[db_name]
ids = [
    "Staff_id", "Sched_id", "Patient_id", "Invoice_id",
    "Appointment_id", "Coverage_id", "Role_id", "Diagnosis_id",
    "Procedure_id", "Drug_id", "Visit_id", "Payment_id",
    "Delivery_id", "Stay_id", "Labtest_id"
]

for id_name in ids:
    db.counters_primary_key_collection.update_one(
        {"_id": id_name},
        {"$setOnInsert": {"sequence_value": 0}},
        upsert=True
    )

print("✅ Counters initialized.") '''