from typing import List, Dict, Any
from datetime import datetime, date
from ..database import Database
from bson import ObjectId
from bson.decimal128 import Decimal128
from bson.dbref import DBRef

def _sanitize_for_json(obj):
    """Recursively convert MongoDB/BSON types to JSON-serializable values."""
    if isinstance(obj, ObjectId) or isinstance(obj, DBRef):
        return str(obj)
    if isinstance(obj, Decimal128):
        try:
            return float(obj.to_decimal())
        except Exception:
            return str(obj)
    if isinstance(obj, datetime) or isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items() if k != "_id"}
    if isinstance(obj, (list, tuple, set)):
        return [_sanitize_for_json(v) for v in obj]
    return obj

class ReportService:

    @classmethod
    def get_monthly_activity_report(cls, month: int, year: int) -> Dict[str, Any]:
        """Generates the Monthly Activity Report with correct counts."""
        db = Database.get_db()

        # Define start and end of month
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

        # --- 1. Get Visits in month ---
        visit_pipeline = [
            {"$match": {"$or": [
                {"start_time": {"$gte": start_date, "$lt": end_date}},            # datetime
                {"start_time": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}}  # string
            ]}},
            {"$group": {
                "_id": None,
                "total_visits": {"$sum": 1},
                "avg_duration_minutes": {
                    "$avg": {
                        "$dateDiff": {
                            "startDate": {"$toDate": "$start_time"},
                            "endDate": {"$toDate": "$end_time"},
                            "unit": "minute"
                        }
                    }
                }
            }},
            {"$project": {"_id": 0, "total_visits": 1, "avg_duration_minutes": 1}}
        ]
        visit_res = list(db.Visit.aggregate(visit_pipeline))
        visit_stats = visit_res[0] if visit_res else {"total_visits": 0, "avg_duration_minutes": 0}

        # --- 2. Get visit_ids in month for filtering other collections ---
        visit_ids_pipeline = [
            {"$match": {"$or": [
                {"start_time": {"$gte": start_date, "$lt": end_date}},
                {"start_time": {"$gte": start_date.isoformat(), "$lt": end_date.isoformat()}}
            ]}},
            {"$project": {"visit_id": 1}}
        ]
        visits_in_month = list(db.Visit.aggregate(visit_ids_pipeline))
        visit_ids = [v["visit_id"] for v in visits_in_month]

        # --- 3. Count Deliveries, Lab Tests, Prescriptions for this month ---
        deliveries = db.Delivery.count_documents({"visit_id": {"$in": visit_ids}})
        lab_tests = db.LabTestOrder.count_documents({"visit_id": {"$in": visit_ids}})
        prescriptions = db.Prescription.count_documents({"visit_id": {"$in": visit_ids}})

        return _sanitize_for_json({
            "report_month": f"{month}/{year}",
            "metrics": {
                "total_patient_visits": visit_stats.get("total_visits", 0),
                "average_visit_duration_mins": round(visit_stats.get("avg_duration_minutes") or 0, 2),
                "total_deliveries": deliveries,
                "total_lab_tests": lab_tests,
                "total_prescriptions": prescriptions
            }
        })

    @classmethod
    def get_outstanding_balances(cls) -> List[Dict[str, Any]]:
        """Returns list of invoices with balances > 0"""
        db = Database.get_db()
        pipeline = [
            {"$match": {"status": {"$ne": "paid"}}},
            {"$lookup": {
                "from": "Patient",
                "localField": "patient_id",
                "foreignField": "patient_id",
                "as": "patient"
            }},
            {"$unwind": "$patient"},
            {"$lookup": {
                "from": "Payment",
                "localField": "invoice_id",
                "foreignField": "invoice_id",
                "as": "payments"
            }},
            {"$addFields": {
                "total_paid": {"$sum": "$payments.amount"},
                "balance_due": {"$subtract": ["$patient_portion", {"$sum": "$payments.amount"}]},
                "patient_name": {"$concat": ["$patient.first_name", " ", "$patient.last_name"]}
            }},
            {"$match": {"balance_due": {"$gt": 0}}}
        ]
        return _sanitize_for_json(list(db.Invoice.aggregate(pipeline)))

    @classmethod
    def get_daily_delivery_log(cls, log_date: date) -> List[Dict[str, Any]]:
        """Daily Delivery Log"""
        db = Database.get_db()
        start_iso = datetime.combine(log_date, datetime.min.time()).isoformat()
        end_iso = datetime.combine(log_date, datetime.max.time()).isoformat()
        pipeline = [
            {"$match": {"start_time": {"$gte": start_iso, "$lte": end_iso}}},
            {"$lookup": {"from": "Delivery", "localField": "visit_id", "foreignField": "visit_id", "as": "delivery_info"}},
            {"$unwind": "$delivery_info"},
            {"$lookup": {"from": "Patient", "localField": "patient_id", "foreignField": "patient_id", "as": "patient"}},
            {"$unwind": "$patient"},
            {"$lookup": {"from": "Staff", "localField": "delivery_info.performed_by", "foreignField": "staff_id", "as": "staff"}},
            {"$unwind": "$staff"},
            {"$project": {
                "time": "$start_time",
                "patient": {"$concat": ["$patient.first_name", " ", "$patient.last_name"]},
                "performed_by": {"$concat": ["$staff.first_name", " ", "$staff.last_name"]},
                "visit_type": "$visit_type"
            }}
        ]
        return _sanitize_for_json(list(db.Visit.aggregate(pipeline)))

    @classmethod
    def get_monthly_statements(cls, month: int, year: int) -> Dict[str, Any]:
        """Generates per-patient monthly statements with paid/unpaid classification."""
        db = Database.get_db()
        start_date = datetime(year, month, 1)
        end_date = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)

        pipeline = [
            {"$addFields": {"invoice_date_dt": {"$toDate": "$invoice_date"}}},
            {"$match": {"invoice_date_dt": {"$gte": start_date, "$lt": end_date}}},
            {"$lookup": {"from": "Patient", "localField": "patient_id", "foreignField": "patient_id", "as": "patient"}},
            {"$unwind": "$patient"},
            {"$lookup": {"from": "Payment", "let": {"inv": "$invoice_id"},
                         "pipeline": [{"$match": {"$expr": {"$and": [
                             {"$eq": ["$invoice_id", "$$inv"]},
                             {"$lte": [{"$toDate": "$payment_date"}, end_date]}
                         ]}}}],
                         "as": "payments"}},
            {"$lookup": {"from": "InvoiceLine", "localField": "invoice_id", "foreignField": "invoice_id", "as": "lines"}},
            {"$addFields": {
                "total_paid": {"$sum": "$payments.amount"},
                "balance_due": {"$subtract": ["$patient_portion", {"$sum": "$payments.amount"}]},
                "patient_name": {"$concat": ["$patient.first_name", " ", "$patient.last_name"]}
            }}
        ]

        raw_invoices = list(db.Invoice.aggregate(pipeline))

        patients: Dict[Any, Dict[str, Any]] = {}
        now = datetime.utcnow()
        for inv in raw_invoices:
            pid = inv.get("patient_id")
            if pid not in patients:
                patients[pid] = {
                    "patient_id": pid,
                    "patient_name": inv.get("patient_name"),
                    "invoices": [],
                    "total_invoiced": 0.0,
                    "payments_received": 0.0,
                    "balance": 0.0,
                    "services": {},  # temp dict description -> agg
                    "payments": [],
                    "max_aging_days": 0
                }

            # Aging & bucket (only relevant if unpaid portion remains)
            invoice_date_dt: datetime = inv.get("invoice_date_dt")
            days_outstanding = (now - invoice_date_dt).days if isinstance(invoice_date_dt, datetime) else 0
            balance_due = inv.get("balance_due") or 0.0
            if balance_due > 0 and days_outstanding > patients[pid]["max_aging_days"]:
                patients[pid]["max_aging_days"] = days_outstanding
            if balance_due > 0:
                if days_outstanding <= 30:
                    aging_bucket = "0-30"
                elif days_outstanding <= 60:
                    aging_bucket = "31-60"
                else:
                    aging_bucket = "61+"
            else:
                aging_bucket = "paid"

            # Enrich lines with totals & accumulate services
            for line in inv.get("lines", []):
                qty = line.get("qty", 1)
                unit_price = line.get("unit_price", 0.0)
                line_total = qty * unit_price
                line["line_total"] = line_total
                desc = line.get("description", "Unknown")
                svc = patients[pid]["services"].setdefault(desc, {"description": desc, "qty": 0, "amount": 0.0})
                svc["qty"] += qty
                svc["amount"] += line_total

            # Aggregate payments list (flatten)
            for pay in inv.get("payments", []):
                patients[pid]["payments"].append({
                    "payment_date": pay.get("payment_date"),
                    "method": pay.get("method") or pay.get("payment_method"),
                    "amount": pay.get("amount")
                })

            # Add enriched invoice snapshot
            inv_enriched = inv.copy()
            inv_enriched["days_outstanding"] = days_outstanding
            inv_enriched["aging_bucket"] = aging_bucket
            patients[pid]["invoices"].append(_sanitize_for_json(inv_enriched))

            patients[pid]["total_invoiced"] += inv.get("patient_portion") or 0.0
            patients[pid]["payments_received"] += inv.get("total_paid") or 0.0
            patients[pid]["balance"] += balance_due

        # Transform services temp dicts to list & determine status
        for p in patients.values():
            p["services"] = sorted([_sanitize_for_json(v) for v in p["services"].values()], key=lambda x: x["description"])
            p["payments"] = sorted(p["payments"], key=lambda x: x.get("payment_date") or "")
            p["status"] = "paid" if round(p["balance"], 2) <= 0 else ("partial" if p["payments_received"] > 0 else "unpaid")

        paid_list, unpaid_list = [], []
        totals = {"paid": {"total_invoiced": 0.0, "payments_received": 0.0, "balance": 0.0},
                  "unpaid": {"total_invoiced": 0.0, "payments_received": 0.0, "balance": 0.0}}

        for p in patients.values():
            # Exclude fully paid from unpaid list
            if round(p["balance"], 2) <= 0:
                paid_list.append(_sanitize_for_json(p))
                for k in totals["paid"]:
                    totals["paid"][k] += p[k]
            else:
                unpaid_list.append(_sanitize_for_json(p))
                for k in totals["unpaid"]:
                    totals["unpaid"][k] += p[k]

        return _sanitize_for_json({
            "month": f"{month}/{year}",
            "summary": {
                "paid": {"patients": paid_list, "totals": totals["paid"]},
                "unpaid": {"patients": unpaid_list, "totals": totals["unpaid"]}
            }
        })
