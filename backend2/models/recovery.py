"""RecoveryStay and RecoveryObservation models"""

from typing import Optional, List, Dict
from datetime import datetime, date, time
from pydantic import BaseModel, Field, validator
from enum import Enum
from .base import MongoBaseModel


class RecoveryReason(str, Enum):
    """Reasons for recovery room admission"""
    POST_SURGERY = "post_surgery"
    POST_DELIVERY = "post_delivery"
    POST_PROCEDURE = "post_procedure"
    OBSERVATION = "observation"
    STABILIZATION = "stabilization"
    MEDICATION_REACTION = "medication_reaction"
    OTHER = "other"


class RecoveryStatus(str, Enum):
    """Recovery room status"""
    ADMITTED = "admitted"
    STABLE = "stable"
    IMPROVING = "improving"
    DETERIORATING = "deteriorating"
    READY_FOR_DISCHARGE = "ready_for_discharge"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"


class ObservationType(str, Enum):
    """Types of observations"""
    VITALS = "vitals"
    PAIN_ASSESSMENT = "pain_assessment"
    CONSCIOUSNESS = "consciousness"
    BLEEDING = "bleeding"
    MEDICATION_GIVEN = "medication_given"
    INTAKE_OUTPUT = "intake_output"
    WOUND_CHECK = "wound_check"
    NEUROLOGICAL = "neurological"
    RESPIRATORY = "respiratory"
    CARDIOVASCULAR = "cardiovascular"
    OTHER = "other"


class PainScale(str, Enum):
    """Pain scale ratings"""
    NO_PAIN = "0"
    MILD = "1-3"
    MODERATE = "4-6"
    SEVERE = "7-9"
    WORST = "10"


class ConsciousnessLevel(str, Enum):
    """Level of consciousness"""
    ALERT = "alert"
    CONFUSED = "confused"
    DROWSY = "drowsy"
    STUPOROUS = "stuporous"
    UNCONSCIOUS = "unconscious"


class RecoveryStay(MongoBaseModel):
    """RecoveryStay collection model"""
    stay_id: str = Field(..., description="Unique recovery stay identifier")
    patient_id: str = Field(..., description="Reference to Patient")
    visit_id: str = Field(..., description="Reference to Visit")
    
    # Admission information
    admit_time: datetime = Field(..., description="When admitted to recovery")
    admit_from: str = Field(..., max_length=100, description="Where admitted from (OR, delivery, etc.)")
    admit_reason: RecoveryReason = Field(..., description="Reason for recovery admission")
    admit_diagnosis: str = Field(..., max_length=500, description="Admission diagnosis")
    
    # Recovery details
    bed_number: str = Field(..., max_length=20, description="Recovery bed number")
    status: RecoveryStatus = Field(default=RecoveryStatus.ADMITTED)
    
    # Medical team
    admitting_staff_id: str = Field(..., description="Staff who admitted patient")
    primary_nurse_id: Optional[str] = Field(None, description="Primary recovery nurse")
    physician_id: Optional[str] = Field(None, description="Supervising physician")
    
    # Procedure/Surgery details (if applicable)
    procedure_performed: Optional[str] = Field(None, description="What procedure was done")
    anesthesia_type: Optional[str] = Field(None, description="Type of anesthesia used")
    anesthesia_end_time: Optional[datetime] = Field(None, description="When anesthesia ended")
    
    # Initial assessment
    initial_vitals: Dict = Field(..., description="Initial vital signs")
    initial_pain_score: Optional[PainScale] = None
    initial_consciousness: ConsciousnessLevel = Field(default=ConsciousnessLevel.ALERT)
    allergies_verified: bool = Field(default=False)
    
    # Monitoring requirements
    monitoring_frequency_minutes: int = Field(default=15, description="How often to check patient")
    special_monitoring: List[str] = Field(default_factory=list, description="Special monitoring needs")
    
    # Medications
    medications_given: List[dict] = Field(default_factory=list, description="Medications administered")
    # Format: [{"drug_name": "", "dose": "", "route": "", "time": "", "given_by": ""}]
    
    # Recovery milestones
    consciousness_restored: Optional[datetime] = Field(None, description="When fully conscious")
    pain_controlled: Optional[datetime] = Field(None, description="When pain under control")
    vitals_stable: Optional[datetime] = Field(None, description="When vitals stabilized")
    
    # Discharge information
    discharge_time: Optional[datetime] = Field(None, description="When discharged from recovery")
    discharge_to: Optional[str] = Field(None, description="Where discharged to")
    discharge_status: Optional[str] = Field(None, description="Patient condition at discharge")
    discharge_instructions: Optional[str] = Field(None, description="Instructions given")
    signed_off_by: Optional[str] = Field(None, description="Staff ID who signed off discharge")
    discharge_vitals: Optional[Dict] = Field(None, description="Vital signs at discharge")
    
    # Complications
    complications: List[str] = Field(default_factory=list, description="Any complications")
    incident_reports: List[str] = Field(default_factory=list, description="Any incident report IDs")
    
    # Family
    family_notified: bool = Field(default=False)
    family_present: bool = Field(default=False)
    visitor_names: List[str] = Field(default_factory=list)
    
    # Notes
    notes: Optional[str] = Field(None, description="General recovery notes")
    
    @validator('discharge_time')
    def validate_discharge_after_admit(cls, v, values):
        if v and 'admit_time' in values and v <= values['admit_time']:
            raise ValueError('Discharge time must be after admission time')
        return v
    
    @property
    def length_of_stay_hours(self) -> Optional[float]:
        """Calculate length of stay in hours"""
        if self.admit_time and self.discharge_time:
            delta = self.discharge_time - self.admit_time
            return delta.total_seconds() / 3600
        elif self.admit_time:
            delta = datetime.utcnow() - self.admit_time
            return delta.total_seconds() / 3600
        return None
    
    @property
    def is_prolonged_stay(self) -> bool:
        """Check if stay is longer than typical (>4 hours)"""
        los = self.length_of_stay_hours
        return los is not None and los > 4
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "stay_id": "REC001",
                "patient_id": "PAT001",
                "visit_id": "VIS001",
                "admit_time": "2024-02-01T10:00:00",
                "admit_from": "Operating Room 2",
                "admit_reason": "post_surgery",
                "admit_diagnosis": "Post appendectomy",
                "bed_number": "R-03",
                "status": "admitted",
                "admitting_staff_id": "STF002",
                "primary_nurse_id": "STF003",
                "initial_vitals": {
                    "blood_pressure": "110/70",
                    "pulse": 68,
                    "temperature": 98.2,
                    "respiratory_rate": 14,
                    "oxygen_saturation": 98
                },
                "initial_pain_score": "4-6",
                "initial_consciousness": "drowsy"
            }
        }


class RecoveryObservation(MongoBaseModel):
    """RecoveryObservation collection model"""
    stay_id: str = Field(..., description="Reference to RecoveryStay")
    observation_id: str = Field(..., description="Unique observation identifier")
    sequence_number: int = Field(..., description="Sequential observation number")
    
    # Observation details
    observation_time: datetime = Field(default_factory=datetime.utcnow)
    observation_type: ObservationType = Field(..., description="Type of observation")
    observed_by: str = Field(..., description="Staff ID who made observation (nurse)")
    
    # Vital signs (if applicable)
    vitals: Optional[Dict] = Field(None, description="Vital signs if checked")
    # Format: {"bp": "120/80", "pulse": 72, "temp": 98.6, "resp": 16, "o2": 98}
    
    # Pain assessment
    pain_score: Optional[PainScale] = None
    pain_location: Optional[str] = Field(None, max_length=200)
    pain_intervention: Optional[str] = Field(None, description="What was done for pain")
    
    # Consciousness assessment
    consciousness_level: Optional[ConsciousnessLevel] = None
    pupil_response: Optional[str] = Field(None, description="Pupil response check")
    orientation: Optional[str] = Field(None, description="Oriented to person/place/time")
    
    # Bleeding/Drainage
    bleeding_assessment: Optional[str] = Field(None, description="Bleeding status")
    drainage_amount: Optional[str] = Field(None, description="Drainage amount if applicable")
    drainage_color: Optional[str] = Field(None, description="Drainage appearance")
    
    # Medications
    medication_given: Optional[dict] = Field(None, description="Medication administered")
    # Format: {"drug": "", "dose": "", "route": "", "reason": ""}
    medication_response: Optional[str] = Field(None, description="Response to medication")
    
    # Intake/Output
    intake_ml: Optional[int] = Field(None, description="Fluid intake in ml")
    output_ml: Optional[int] = Field(None, description="Urine output in ml")
    
    # Other assessments
    skin_assessment: Optional[str] = Field(None, description="Skin color, temperature, etc.")
    wound_assessment: Optional[str] = Field(None, description="Surgical site check")
    nausea_vomiting: Optional[bool] = None
    
    # Alert indicators
    is_critical: bool = Field(default=False, description="Critical observation requiring immediate attention")
    alert_physician: bool = Field(default=False, description="Whether physician was alerted")
    physician_alerted_at: Optional[datetime] = None
    
    # Intervention
    intervention_performed: Optional[str] = Field(None, description="Any intervention done")
    intervention_response: Optional[str] = Field(None, description="Patient response to intervention")
    
    # Notes
    notes: Optional[str] = Field(None, max_length=1000, description="Observation notes")
    
    @validator('sequence_number')
    def validate_sequence(cls, v):
        if v < 1:
            raise ValueError('Sequence number must be positive')
        return v
    
    @property
    def requires_intervention(self) -> bool:
        """Check if observation requires intervention"""
        critical_indicators = [
            self.is_critical,
            self.pain_score in [PainScale.SEVERE, PainScale.WORST],
            self.consciousness_level in [ConsciousnessLevel.STUPOROUS, ConsciousnessLevel.UNCONSCIOUS],
            self.alert_physician
        ]
        return any(critical_indicators)
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "stay_id": "REC001",
                "observation_id": "OBS001",
                "sequence_number": 1,
                "observation_time": "2024-02-01T10:15:00",
                "observation_type": "vitals",
                "observed_by": "STF003",
                "vitals": {
                    "blood_pressure": "115/75",
                    "pulse": 70,
                    "temperature": 98.4,
                    "respiratory_rate": 14,
                    "oxygen_saturation": 99
                },
                "pain_score": "4-6",
                "consciousness_level": "alert",
                "notes": "Patient responding well, vitals stable"
            }
        }


# Request models for API
class RecoveryAdmissionRequest(BaseModel):
    """Request model for admitting to recovery"""
    patient_id: str
    visit_id: str
    admit_from: str
    admit_reason: RecoveryReason
    admit_diagnosis: str
    bed_number: str
    initial_vitals: Dict
    initial_pain_score: Optional[PainScale] = None
    initial_consciousness: ConsciousnessLevel = ConsciousnessLevel.ALERT
    procedure_performed: Optional[str] = None
    anesthesia_type: Optional[str] = None


class RecoveryObservationRequest(BaseModel):
    """Request model for recording observation"""
    stay_id: str
    observation_type: ObservationType
    vitals: Optional[Dict] = None
    pain_score: Optional[PainScale] = None
    pain_location: Optional[str] = None
    consciousness_level: Optional[ConsciousnessLevel] = None
    medication_given: Optional[dict] = None
    intake_ml: Optional[int] = None
    output_ml: Optional[int] = None
    is_critical: bool = False
    notes: Optional[str] = None


class RecoveryDischargeRequest(BaseModel):
    """Request model for discharge from recovery"""
    stay_id: str
    discharge_to: str
    discharge_status: str
    discharge_instructions: str
    discharge_vitals: Dict


class RecoveryMedicationRequest(BaseModel):
    """Request model for administering medication in recovery"""
    stay_id: str
    drug_name: str
    dose: str
    route: str
    reason: str


class RecoveryRoomLogRequest(BaseModel):
    """Request model for recovery room log report"""
    log_date: date = Field(default_factory=date.today)
    include_observations: bool = True
    include_medications: bool = True
    active_only: bool = False


class RecoverySearchRequest(BaseModel):
    """Request model for searching recovery stays"""
    patient_id: Optional[str] = None
    status: Optional[RecoveryStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    prolonged_stays_only: bool = False