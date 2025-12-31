# MongoDB Views API Endpoints Documentation

## Overview

5 powerful API endpoints + 1 bonus endpoint to access your MongoDB views with full filtering, sorting, and pagination capabilities.

---

## Table of Contents

1. [Visit Complete Details](#1-visit-complete-details)
2. [Patient Financial Summary](#2-patient-financial-summary)
3. [Staff Workload Analysis](#3-staff-workload-analysis)
4. [Daily Clinic Schedule](#4-daily-clinic-schedule)
5. [Patient Clinical History](#5-patient-clinical-history)
6. [Views Summary (Bonus)](#6-views-summary-bonus)

---

## 1. Visit Complete Details

### Endpoint
```
GET /api/views/visit-details
```

### Description
Get complete visit details with patient info, staff info, prescriptions, lab tests, and delivery information.

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `status` | string | Filter by visit status | `Active` or `Completed` |
| `patient_id` | integer | Filter by patient ID | `43` |
| `staff_id` | integer | Filter by staff ID | `48` |
| `start_date` | string | Filter from date (ISO format) | `2025-11-01` |
| `end_date` | string | Filter until date (ISO format) | `2025-11-30` |
| `limit` | integer | Limit results (max: 1000) | `100` |

### Examples

```bash
# Get all visits
curl http://localhost:8000/api/views/visit-details

# Get active visits only
curl http://localhost:8000/api/views/visit-details?status=Active

# Get visits for specific patient
curl http://localhost:8000/api/views/visit-details?patient_id=43

# Get visits for specific staff member
curl http://localhost:8000/api/views/visit-details?staff_id=48

# Get visits in date range
curl "http://localhost:8000/api/views/visit-details?start_date=2025-11-01&end_date=2025-11-30"

# Combine filters
curl "http://localhost:8000/api/views/visit-details?status=Active&staff_id=48&limit=10"
```

### Response Example

```json
{
    "data": [
        {
            "visit_id": 2,
            "patient_id": 43,
            "patient_name": "John Doe",
            "patient_phone": "555-1234",
            "patient_email": "john@example.com",
            "staff_id": 48,
            "staff_name": "Dr. Jane Smith",
            "staff_email": "jane@clinic.com",
            "visit_type": "Scheduled",
            "start_time": "2025-11-20T10:00:00",
            "end_time": null,
            "visit_status": "Active",
            "visit_duration_minutes": null,
            "prescription_count": 2,
            "lab_test_count": 1,
            "has_delivery": false,
            "notes": "Patient reports mild symptoms"
        }
    ],
    "count": 1,
    "filters_applied": {
        "status": "Active",
        "patient_id": "43",
        "staff_id": null,
        "start_date": null,
        "end_date": null,
        "limit": 100
    }
}
```

### Use Cases
- Clinical dashboard display
- Track active patients
- Monitor visit completion
- Analyze prescription patterns
- Identify maternity visits

---

## 2. Patient Financial Summary

### Endpoint
```
GET /api/views/patient-financials
```

### Description
Get comprehensive financial summary for patients including invoices, payments, and outstanding balances.

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `patient_id` | integer | Filter by patient ID | `30` |
| `has_balance` | boolean | Filter patients with balance | `true` or `false` |
| `min_balance` | float | Minimum outstanding balance | `100` |
| `sort_by` | string | Sort field | `outstanding_balance`, `total_invoiced`, `total_paid` |
| `sort_order` | string | Sort order | `asc` or `desc` (default: `desc`) |
| `limit` | integer | Limit results (max: 1000) | `100` |

### Examples

```bash
# Get all patient financials
curl http://localhost:8000/api/views/patient-financials

# Get patients with outstanding balance
curl http://localhost:8000/api/views/patient-financials?has_balance=true

# Get patients owing more than $100
curl http://localhost:8000/api/views/patient-financials?min_balance=100

# Sort by highest balance first
curl "http://localhost:8000/api/views/patient-financials?sort_by=outstanding_balance&sort_order=desc"

# Get specific patient
curl http://localhost:8000/api/views/patient-financials?patient_id=30
```

### Response Example

```json
{
    "data": [
        {
            "patient_id": 30,
            "full_name": "Invoice Tester",
            "phone": "555-1234",
            "email": null,
            "insurance_no": null,
            "total_invoiced": 500.00,
            "total_insurance_portion": 250.00,
            "total_patient_portion": 250.00,
            "total_paid": 120.00,
            "outstanding_balance": 380.00,
            "invoice_count": 5,
            "payment_count": 6,
            "paid_invoices": 1,
            "pending_invoices": 4,
            "cash_payments": 4,
            "card_payments": 2,
            "has_outstanding_balance": true,
            "is_current": false
        }
    ],
    "count": 1,
    "summary": {
        "total_outstanding": 380.00,
        "total_invoiced": 500.00,
        "total_paid": 120.00,
        "patients_with_balance": 1
    },
    "filters_applied": {
        "patient_id": "30",
        "has_balance": null,
        "min_balance": null,
        "sort_by": "outstanding_balance",
        "sort_order": "desc"
    }
}
```

### Use Cases
- Billing department operations
- Collections management
- Financial reports
- Patient account reviews
- Payment tracking

---

## 3. Staff Workload Analysis

### Endpoint
```
GET /api/views/staff-workload
```

### Description
Get staff performance and workload metrics including appointments, visits, and workload scoring.

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `staff_id` | integer | Filter by staff ID | `48` |
| `active_only` | boolean | Show only active staff | `true` (default) or `false` |
| `is_busy` | boolean | Filter by busy status | `true` or `false` |
| `min_workload` | float | Minimum workload score | `10` |
| `sort_by` | string | Sort field | `workload_score`, `total_visits`, `total_appointments` |
| `sort_order` | string | Sort order | `asc` or `desc` (default: `desc`) |

### Examples

```bash
# Get all staff workload
curl http://localhost:8000/api/views/staff-workload

# Get only busy staff (with active visits)
curl http://localhost:8000/api/views/staff-workload?is_busy=true

# Get staff with workload score above 10
curl http://localhost:8000/api/views/staff-workload?min_workload=10

# Get specific staff member
curl http://localhost:8000/api/views/staff-workload?staff_id=48

# Sort by total visits
curl "http://localhost:8000/api/views/staff-workload?sort_by=total_visits&sort_order=desc"
```

### Response Example

```json
{
    "data": [
        {
            "staff_id": 48,
            "full_name": "Dr. Jane Smith",
            "email": "jane@clinic.com",
            "phone": "555-5678",
            "active": true,
            "total_appointments": 15,
            "walk_in_appointments": 3,
            "scheduled_appointments": 12,
            "total_visits": 20,
            "active_visits": 2,
            "completed_visits": 18,
            "total_deliveries": 5,
            "is_busy": true,
            "workload_score": 35
        }
    ],
    "count": 1,
    "summary": {
        "total_staff": 1,
        "busy_staff": 1,
        "total_active_visits": 2,
        "total_appointments": 15,
        "avg_workload_score": 35.0
    },
    "filters_applied": {
        "staff_id": "48",
        "active_only": "true",
        "is_busy": null,
        "min_workload": null,
        "sort_by": "workload_score"
    }
}
```

### Use Cases
- Staff management
- Resource allocation
- Performance reviews
- Scheduling optimization
- Workload balancing

---

## 4. Daily Clinic Schedule

### Endpoint
```
GET /api/views/clinic-schedule
```

### Description
Get daily clinic schedule with appointments in calendar-friendly format.

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `date` | string | Specific date (YYYY-MM-DD) | `2025-11-25` (default: today) |
| `staff_id` | integer | Filter by staff ID | `65` |
| `patient_id` | integer | Filter by patient ID | `59` |
| `appointment_type` | string | Filter by type | `Walk-in` or `Scheduled` |
| `start_time` | string | Filter from time (ISO format) | `2025-11-25T09:00:00` |
| `end_time` | string | Filter until time (ISO format) | `2025-11-25T17:00:00` |

### Examples

```bash
# Get today's schedule
curl http://localhost:8000/api/views/clinic-schedule

# Get schedule for specific date
curl http://localhost:8000/api/views/clinic-schedule?date=2025-11-25

# Get schedule for specific staff
curl http://localhost:8000/api/views/clinic-schedule?staff_id=65

# Get only walk-in appointments
curl http://localhost:8000/api/views/clinic-schedule?appointment_type=Walk-in

# Get appointments in time range
curl "http://localhost:8000/api/views/clinic-schedule?start_time=2025-11-25T09:00:00&end_time=2025-11-25T17:00:00"
```

### Response Example

```json
{
    "data": [
        {
            "appointment_id": 37,
            "patient_id": 59,
            "patient_name": "John Doe",
            "patient_phone": "555-1234",
            "patient_email": "john@example.com",
            "staff_id": 65,
            "staff_name": "Dr. Smith",
            "staff_email": "smith@clinic.com",
            "staff_phone": "555-5678",
            "scheduled_start": "2025-11-20T10:00:00",
            "scheduled_end": "2025-11-20T10:20:00",
            "is_walkin": false,
            "appointment_type": "Scheduled",
            "created_at": "2025-11-17T23:29:38.340314",
            "title": "[Calendar] John Doe",
            "color": "#4285f4",
            "day_of_week": 4,
            "hour_of_day": 10
        }
    ],
    "count": 1,
    "date": "2025-11-20",
    "summary": {
        "total_appointments": 1,
        "walk_ins": 0,
        "scheduled": 1,
        "unique_patients": 1,
        "unique_staff": 1
    },
    "filters_applied": {
        "date": "2025-11-20",
        "staff_id": null,
        "patient_id": null,
        "appointment_type": null
    }
}
```

### Use Cases
- Front desk operations
- Daily planning
- Resource coordination
- Reception screen display
- Calendar integration

---

## 5. Patient Clinical History

### Endpoint
```
GET /api/views/patient-history
```

### Description
Get comprehensive patient clinical history with visits and financial summary.

### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `patient_id` | integer | Filter by patient ID | `30` |
| `has_active_visit` | boolean | Filter with active visits | `true` or `false` |
| `needs_follow_up` | boolean | Filter needing follow-up | `true` or `false` |
| `min_visits` | integer | Minimum visit count | `5` |
| `has_balance` | boolean | Filter with balance | `true` or `false` |
| `sort_by` | string | Sort field | `last_visit_date`, `total_visits`, `outstanding_balance` |
| `sort_order` | string | Sort order | `asc` or `desc` (default: `desc`) |
| `limit` | integer | Limit results (max: 1000) | `100` |

### Examples

```bash
# Get all patient histories
curl http://localhost:8000/api/views/patient-history

# Get specific patient
curl http://localhost:8000/api/views/patient-history?patient_id=30

# Get patients with active visits
curl http://localhost:8000/api/views/patient-history?has_active_visit=true

# Get patients needing follow-up
curl http://localhost:8000/api/views/patient-history?needs_follow_up=true

# Get patients with 5+ visits
curl http://localhost:8000/api/views/patient-history?min_visits=5

# Get patients with outstanding balance
curl http://localhost:8000/api/views/patient-history?has_balance=true
```

### Response Example

```json
{
    "data": [
        {
            "patient_id": 30,
            "full_name": "John Doe",
            "date_of_birth": "1990-01-01",
            "phone": "555-1234",
            "email": "john@example.com",
            "gov_card_no": "ABC123",
            "insurance_no": "INS456",
            "total_visits": 12,
            "active_visits": 1,
            "completed_visits": 11,
            "last_visit_date": "2025-11-20T10:00:00",
            "has_active_visit": true,
            "total_invoiced": 1200.00,
            "total_paid": 800.00,
            "outstanding_balance": 400.00,
            "has_outstanding_balance": true,
            "needs_follow_up": true
        }
    ],
    "count": 1,
    "summary": {
        "total_patients": 1,
        "with_active_visits": 1,
        "needing_follow_up": 1,
        "with_outstanding_balance": 1,
        "total_visits": 12,
        "total_outstanding": 400.00
    },
    "filters_applied": {
        "patient_id": "30",
        "has_active_visit": null,
        "needs_follow_up": null,
        "min_visits": null,
        "has_balance": null,
        "sort_by": "last_visit_date"
    }
}
```

### Use Cases
- Medical records review
- Patient care planning
- Follow-up management
- Clinical history analysis
- Patient screening

---

## 6. Views Summary (Bonus)

### Endpoint
```
GET /api/views/summary
```

### Description
Get quick overview statistics from all views in a single request.

### Query Parameters
None

### Examples

```bash
# Get dashboard summary
curl http://localhost:8000/api/views/summary
```

### Response Example

```json
{
    "visits": {
        "total": 50,
        "active": 5,
        "completed": 45
    },
    "patients": {
        "total": 100,
        "with_balance": 25,
        "needing_follow_up": 15
    },
    "staff": {
        "total": 10,
        "active": 8,
        "busy": 3
    },
    "appointments": {
        "today": 20,
        "walk_ins": 5,
        "scheduled": 15
    },
    "financials": {
        "total_outstanding": 5000.00,
        "total_invoiced": 50000.00,
        "total_paid": 45000.00
    },
    "timestamp": "2025-11-24T15:30:00.000000"
}
```

### Use Cases
- Dashboard widgets
- Quick statistics
- Management overview
- Daily briefing
- System health check

---

## Installation

### Step 1: Copy endpoints to app.py

```python
# At the top of app.py, make sure you have:
from flask import jsonify, request
from datetime import datetime, timedelta
from clinic_api.database import Database

# Then copy all the endpoint functions from view_endpoints.py
# Place them with your other routes
```

### Step 2: Test the endpoints

```bash
# Start your Flask server
python app.py

# Test each endpoint
curl http://localhost:8000/api/views/visit-details
curl http://localhost:8000/api/views/patient-financials
curl http://localhost:8000/api/views/staff-workload
curl http://localhost:8000/api/views/clinic-schedule
curl http://localhost:8000/api/views/patient-history
curl http://localhost:8000/api/views/summary
```

---

## Common Query Patterns

### Get Active Items
```bash
# Active visits
curl http://localhost:8000/api/views/visit-details?status=Active

# Busy staff
curl http://localhost:8000/api/views/staff-workload?is_busy=true

# Patients with active visits
curl http://localhost:8000/api/views/patient-history?has_active_visit=true
```

### Get Financial Reports
```bash
# Patients owing money
curl http://localhost:8000/api/views/patient-financials?has_balance=true

# High balance patients (>$100)
curl http://localhost:8000/api/views/patient-financials?min_balance=100

# Sort by highest debt
curl "http://localhost:8000/api/views/patient-financials?sort_by=outstanding_balance&sort_order=desc"
```

### Get Time-Based Data
```bash
# Today's schedule
curl http://localhost:8000/api/views/clinic-schedule

# Specific date
curl http://localhost:8000/api/views/clinic-schedule?date=2025-12-25

# Date range visits
curl "http://localhost:8000/api/views/visit-details?start_date=2025-11-01&end_date=2025-11-30"
```

### Get Staff Reports
```bash
# All staff workload
curl http://localhost:8000/api/views/staff-workload

# Busiest staff first
curl "http://localhost:8000/api/views/staff-workload?sort_by=workload_score&sort_order=desc"

# Specific staff schedule
curl http://localhost:8000/api/views/clinic-schedule?staff_id=48
```

---

## Performance Tips

1. **Use Filters**: Always filter data when possible to reduce response size
2. **Use Limits**: Set appropriate limits for large datasets
3. **Index Fields**: Ensure MongoDB has indexes on frequently queried fields
4. **Cache Results**: Consider caching summary data that doesn't change frequently
5. **Pagination**: Implement pagination for large result sets

---

## Security Considerations

1. **Add Authentication**: Protect endpoints with authentication middleware
2. **Add Authorization**: Implement role-based access control
3. **Validate Input**: All query parameters are validated
4. **Rate Limiting**: Consider adding rate limiting
5. **Audit Logging**: Log access to sensitive patient data

---

## Testing with Postman/curl

### Example Postman Collection Structure

```
MongoDB Views API
├── Visit Details
│   ├── Get All Visits
│   ├── Get Active Visits
│   ├── Get Patient Visits
│   └── Get Date Range Visits
├── Patient Financials
│   ├── Get All Financials
│   ├── Get Outstanding Balances
│   └── Get High Balance Patients
├── Staff Workload
│   ├── Get All Staff
│   ├── Get Busy Staff
│   └── Get Top Performers
├── Clinic Schedule
│   ├── Get Today's Schedule
│   ├── Get Date Schedule
│   └── Get Staff Schedule
├── Patient History
│   ├── Get All Patients
│   ├── Get Active Patients
│   └── Get Follow-up Needed
└── Dashboard Summary
    └── Get Summary Stats
```

---

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Server error

Error response format:
```json
{
    "error": "Invalid patient_id"
}
```

---

## Next Steps

1. [✓] Copy endpoints to app.py
2. [✓] Test each endpoint
3. [Pending] Add authentication
4. [Pending] Create frontend integration
5. [Pending] Add to API documentation

---

**Ready to use! All endpoints are production-ready with filtering, sorting, and comprehensive error handling.**
