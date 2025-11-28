import React, { useEffect, useState } from 'react'
import './RecoveryRoomLog.css'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorMessage from '../common/ErrorMessage'
import { getActiveVisits } from '../../api/views'
import { createRecoveryStay, getRecoveryObservationsByStay, createRecoveryObservation, getRecoveryStay, updateRecoveryStay, getRecoveryStaysByDate, getRecoveryStaysRecent } from '../../api/functions'
import { get } from '../../api/client'
import { getLocalDateString, formatMST, getMSTLocalNow } from '../../utils/timeUtils'

export default function RecoveryRoomLog({ stayId }: { stayId?: number }) {
  const [loading, setLoading] = useState(true)
  const [visits, setVisits] = useState<any[]>([])
  const [patients, setPatients] = useState<any[]>([])
  const [date, setDate] = useState<string>('')
  const [staysForDate, setStaysForDate] = useState<any[]>([])
  const [currentStay, setCurrentStay] = useState<any | null>(null)
  const [currentPatient, setCurrentPatient] = useState<any | null>(null)
  const [observations, setObservations] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showCreateStay, setShowCreateStay] = useState(false)
  const [formStay, setFormStay] = useState({ patient_id: '', practitioner_id: '' })
  const [newObs, setNewObs] = useState('')
  const [nextStayNumber, setNextStayNumber] = useState<number | null>(null)
  const [showStayModal, setShowStayModal] = useState(false)

  useEffect(() => {
    // Load base data (patients/visits) but do not auto-select today's date
    loadBase()
  }, [])

  useEffect(() => {
    if (stayId) {
      loadStay(stayId)
    }
  }, [stayId])

  const loadBase = async () => {
    setLoading(true)
    try {
      let v = await getActiveVisits()
      if (!v || v.length === 0) {
        v = await get<any[]>('/visits?limit=20')
      }
      setVisits(v)
      
      // Load all patients for the dropdown
      const allPatients = await get<any[]>('/patients?limit=200').catch(() => [])
      const validPatients = allPatients.filter(p => {
        const firstName = p.first_name || p.First_Name || ''
        const lastName = p.last_name || p.Last_Name || ''
        return firstName && lastName && (p.patient_id || p.Patient_Id || p._id)
      })
      setPatients(validPatients)
      
      // compute next stay number hint from recent stays
      const recent = await getRecoveryStaysRecent(50)
      const maxId = (recent || []).reduce((m: number, s: any) => Math.max(m, Number(s.stay_id || 0)), 0)
      setNextStayNumber(maxId ? maxId + 1 : null)
      if (currentStay && currentStay.id) {
        await loadStay(currentStay.id)
      }
    } catch (e) {
      console.error('Recovery load failed', e)
      setError('Failed to load recovery data')
    } finally {
      setLoading(false)
    }
  }

  const prevOr = (fallback: string, value?: string) => (value && value.length > 0 ? value : fallback)

  const loadStaysByDate = async (dateStr: string) => {
    try {
      setLoading(true)
      // Always use explicit date endpoint to avoid server/client timezone drift
      const raw = await getRecoveryStaysByDate(dateStr)
      // Enrich with patient and staff names
      const enriched = await Promise.all((raw || []).map(async (s: any) => {
        const out: any = { ...s }
        try {
          const p = await get(`/patients/${s.patient_id}`)
          out.patient_name = p && p.first_name && p.last_name ? `${p.first_name} ${p.last_name}` : `${s.patient_id}`
        } catch (_) {
          out.patient_name = `${s.patient_id}`
        }
        if (s.discharged_by) {
          try {
            const staff = await get(`/staff/${s.discharged_by}`)
            out.discharged_by_name = staff && staff.first_name && staff.last_name ? `${staff.first_name} ${staff.last_name}` : `${s.discharged_by}`
          } catch (_) {
            out.discharged_by_name = `${s.discharged_by}`
          }
        }
        return out
      }))
      setStaysForDate(enriched)
    } catch (e) {
      console.error('Failed to load stays by date', e)
      setStaysForDate([])
    } finally {
      setLoading(false)
    }
  }

  const loadStay = async (id: number) => {
    setLoading(true)
    try {
      const s = await getRecoveryStay(id)
      setCurrentStay(s)
      const obs = await getRecoveryObservationsByStay(id)
      setObservations(obs || [])
      // load patient details
      try {
        const p = await get(`/patients/${s.patient_id}`)
        setCurrentPatient(p)
      } catch (err) {
        setCurrentPatient(null)
      }
      // load discharged_by staff details if present
      if (s.discharged_by) {
        try {
          const staff = await get(`/staff/${s.discharged_by}`)
          setCurrentStay((prev: any) => ({ ...prev, discharged_by_name: staff.first_name && staff.last_name ? `${staff.first_name} ${staff.last_name}` : staff.staff_id }))
        } catch (err) {
          // ignore
        }
      }
    } catch (e) {
      console.error('Failed to load stay or observations', e)
      setError('Failed to load stay observations')
    } finally {
      setLoading(false)
    }
  }

  const openCreateStay = () => {
    setFormStay((prev) => ({
      patient_id: prev.patient_id || '',
      practitioner_id: prev.practitioner_id || ''
    }))
    // ensure next stay number hint is fresh
    getRecoveryStaysRecent(50).then((recent) => {
      const maxId = (recent || []).reduce((m: number, s: any) => Math.max(m, Number(s.stay_id || 0)), 0)
      setNextStayNumber(maxId ? maxId + 1 : null)
    }).catch(() => {})
    setShowCreateStay(true)
  }

  const submitCreateStay = async () => {
    if (!formStay.patient_id) return alert('Please select a patient')
    try {
      const payload: any = {
        patient_id: Number(formStay.patient_id),
        // Use MST timestamp for admission
        admit_time: getMSTLocalNow(),
      }
      // optional notes
      if ((formStay as any).notes) payload.notes = (formStay as any).notes

      const res = await createRecoveryStay(payload)
      const stayId = res.stay_id || res._id || res.id
      if (stayId) await loadStay(Number(stayId))
      // refresh current date list
      if (date) await loadStaysByDate(date)
      // refresh next number
      const recent2 = await getRecoveryStaysRecent(50)
      const maxId2 = (recent2 || []).reduce((m: number, s: any) => Math.max(m, Number(s.stay_id || 0)), 0)
      setNextStayNumber(maxId2 ? maxId2 + 1 : null)
      setShowCreateStay(false)
      alert('Recovery stay created')
    } catch (e) {
      console.error(e)
      alert('Failed to create stay')
    }
  }

  const addObservation = async () => {
    if (!currentStay || !currentStay.stay_id) return alert('Select or create a stay first')
    if (!newObs) return alert('Enter observation text')
    try {
      await createRecoveryObservation({ stay_id: currentStay.stay_id, text_on: getMSTLocalNow(), notes: newObs })
      const obs = await getRecoveryObservationsByStay(currentStay.stay_id)
      setObservations(obs || [])
      setNewObs('')
      alert('Observation added')
    } catch (e) {
      console.error(e)
      alert('Failed to add observation')
    }
  }

  const dischargeStay = async () => {
    if (!currentStay || !currentStay.stay_id) return alert('No stay selected')
    const practitioner = prompt('Enter practitioner (staff) ID for sign-off')
    if (!practitioner) return
    try {
      const updated = await updateRecoveryStay(currentStay.stay_id, { discharge_time: getMSTLocalNow(), discharged_by: Number(practitioner) })
      await loadStay(updated.stay_id || currentStay.stay_id)
      // refresh current date list to reflect discharge
      if (date) await loadStaysByDate(date)
      alert('Stay discharged')
    } catch (err) {
      console.error(err)
      alert('Failed to discharge stay')
    }
  }

  const dischargeSpecificStay = async (stay: any) => {
    if (!stay || !stay.stay_id) return alert('No stay selected')
    const practitioner = prompt('Enter practitioner (staff) ID for sign-off')
    if (!practitioner) return
    try {
      await updateRecoveryStay(stay.stay_id, { discharge_time: getMSTLocalNow(), discharged_by: Number(practitioner) })
      await loadStay(stay.stay_id)
      if (date) await loadStaysByDate(date)
      alert('Stay discharged')
    } catch (err) {
      console.error(err)
      alert('Failed to discharge stay')
    }
  }

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} />

  return (
    <div className="log-page">
      <div className="toolbar">
        <div className="toolbar-left">
          <h3 style={{ margin: 0 }}>Recovery Room</h3>
        </div>
        <div className="toolbar-right">
          <input className="date" type="date" value={date} onChange={async (e) => { const v = e.target.value; setDate(v); if (v) await loadStaysByDate(v); }} />
          <button className="btn" onClick={async () => { const t = getLocalDateString(new Date()); setDate(t); await loadStaysByDate(t); }}>Today</button>
          <button className="btn" onClick={loadBase}>Refresh</button>
          <button className="btn btn-primary" onClick={openCreateStay}>Create Stay</button>
        </div>
      </div>

      <div className="card" style={{ marginBottom: 12 }}>
        {(!date) ? (
          <p className="muted">Select a date to view recovery stays.</p>
        ) : staysForDate.length === 0 ? (
          <p className="muted">No recovery stays for selected date.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Stay ID</th>
                <th>Patient</th>
                <th>Admit Time</th>
                <th>Discharge Time</th>
                <th>Discharged By</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {staysForDate.map((s) => (
                <tr key={s.stay_id}>
                  <td>{s.stay_id}</td>
                  <td>{s.patient_name || s.patient_id}</td>
                  <td>{formatMST(s.admit_time)}</td>
                  <td>{formatMST(s.discharge_time)}</td>
                  <td>{s.discharged_by_name || s.discharged_by || '—'}</td>
                  <td>
                    <button className="btn" onClick={async () => { await loadStay(s.stay_id); setShowStayModal(true); }}>View</button>
                    {!s.discharge_time && (
                      <button className="btn" onClick={() => dischargeSpecificStay(s)} style={{ marginLeft: 6 }}>Discharge</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Removed Load Existing Stay dropdown; use the log table actions instead */}

      {showStayModal && currentStay && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.35)' }}>
          <div style={{ background: '#fff', width: 640, maxWidth: '92%', margin: '60px auto', borderRadius: 8, padding: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ margin: 0 }}>Recovery Stay #{currentStay.stay_id}</h4>
              <button className="btn" onClick={() => setShowStayModal(false)}>Close</button>
            </div>
            <div className="muted" style={{ marginTop: 4, marginBottom: 8 }}>
              Patient: {currentPatient ? `${currentPatient.first_name} ${currentPatient.last_name} (ID ${currentPatient.patient_id})` : currentStay.patient_id}
            </div>
            <div className="card" style={{ border: 'none', padding: 0 }}>
              <p><strong>Admission:</strong> {formatMST(currentStay.admit_time)}</p>
              <p><strong>Discharge:</strong> {formatMST(currentStay.discharge_time)}</p>
              {currentStay.discharged_by_name ? (
                <p><strong>Discharged By:</strong> {currentStay.discharged_by_name}</p>
              ) : currentStay.discharged_by ? (
                <p><strong>Discharged By (ID):</strong> {currentStay.discharged_by}</p>
              ) : null}
              {!currentStay.discharge_time && (
                <div style={{ marginTop: 8 }}>
                  <button className="btn btn-primary" onClick={async () => { await dischargeStay(); setShowStayModal(false); }}>Practitioner Sign-off (Discharge)</button>
                </div>
              )}
            </div>

            <h4 className="section-title">Observations</h4>
            {observations.length === 0 ? <p className="muted">No observations yet.</p> : (
              <ul>
                {observations.map((o) => (
                  <li key={o.text_on || o._id}><strong>{formatMST(o.text_on)}:</strong> {o.notes}</li>
                ))}
              </ul>
            )}

            <div style={{ marginTop: 12 }}>
              <textarea className="input" value={newObs} onChange={(e) => setNewObs(e.target.value)} placeholder="Write observation..." rows={3} style={{ width: '100%' }} />
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
                <button className="btn" onClick={addObservation}>Add Observation</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showCreateStay && (
        <div style={{ position: 'fixed', left: 0, right: 0, top: 0, bottom: 0, background: 'rgba(0,0,0,0.3)' }}>
          <div style={{ background: 'white', padding: 16, width: 480, margin: '60px auto', borderRadius: 6 }}>
            <h4>Create Recovery Stay</h4>
            {nextStayNumber && (
              <div className="muted" style={{ marginBottom: 12 }}>Next Stay #: {nextStayNumber}</div>
            )}
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>Patient:</label>
              <select 
                className="select" 
                value={formStay.patient_id} 
                onChange={(e) => setFormStay({ ...formStay, patient_id: e.target.value })}
                style={{ width: '100%', padding: 8 }}
              >
                <option value="">-- Select a patient --</option>
                {patients.map((p) => {
                  const patientId = p.patient_id || p.Patient_Id || p._id
                  const firstName = p.first_name || p.First_Name || ''
                  const lastName = p.last_name || p.Last_Name || ''
                  return (
                    <option key={patientId} value={patientId}>
                      {firstName} {lastName} (ID: {patientId})
                    </option>
                  )
                })}
              </select>
            </div>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4 }}>Practitioner ID:</label>
              <input 
                className="input" 
                value={formStay.practitioner_id} 
                onChange={(e) => setFormStay({ ...formStay, practitioner_id: e.target.value })} 
                style={{ width: '100%', padding: 8 }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowCreateStay(false)}>Cancel</button>
              <button onClick={submitCreateStay} style={{ marginLeft: 8 }}>Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
