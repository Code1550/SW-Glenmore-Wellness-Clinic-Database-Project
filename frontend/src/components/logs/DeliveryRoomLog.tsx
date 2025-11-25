import React, { useEffect, useState } from 'react'
import LoadingSpinner from '../common/LoadingSpinner'
import ErrorMessage from '../common/ErrorMessage'
import { getDeliveryByVisit, createDelivery } from '../../api/functions'
import { getActiveVisits } from '../../api/views'
import { get } from '../../api/client'

export default function DeliveryRoomLog({ visitId }: { visitId?: number }) {
  const [loading, setLoading] = useState(true)
  const [visits, setVisits] = useState<any[]>([])
  const [staff, setStaff] = useState<any[]>([])
  const [deliveries, setDeliveries] = useState<any[]>([])
  const [error, setError] = useState<string | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ visit_id: '', practitioner_id: '', notes: '' })
  const [selectedDate, setSelectedDate] = useState<string>('')

  useEffect(() => {
    loadData()
    loadStaff()
  }, [visitId])

  const loadStaff = async () => {
    try {
      const staffList = await get<any[]>('/staff?limit=100').catch(() => [])
      // Filter to only show valid staff with names and filter out test/duplicate entries
      const validStaff = staffList.filter(s => {
        const firstName = s.first_name || s.First_Name || ''
        const lastName = s.last_name || s.Last_Name || ''
        const name = `${firstName} ${lastName}`.trim()
        // Filter out entries without proper names or test entries
        return name && 
               name !== 'test' && 
               !name.toLowerCase().includes('deactivate') &&
               !name.toLowerCase().includes('updated name') &&
               (s.staff_id || s.Staff_Id || s._id)
      })
      setStaff(validStaff)
    } catch (e) {
      console.error('Failed to load staff', e)
    }
  }

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      // Load all visits (not just active ones, since getActiveVisits might be empty)
      let v = await get<any[]>('/visits?limit=50').catch(() => [])
      
      // If a date is selected in the UI, load deliveries for that date
      if (selectedDate) {
        const dateDeliveries = await get<any[]>(`/deliveries/date/${selectedDate}`).catch(() => null)
        if (Array.isArray(dateDeliveries)) {
          // Enrich visits with patient names
          const enriched = await enrichVisitsWithPatients(v)
          setVisits(enriched)
          const withVisits = dateDeliveries.map((d: any) => ({ ...d, visit: enriched.find((x: any) => (x.visit_id || x._id) === (d.visit_id || d.visit) ) }))
          setDeliveries(withVisits)
          return
        }
      }

      // prefer a daily deliveries endpoint when available (today)
      const todayDeliveries = await get<any[]>('/deliveries/today').catch(() => null)
      if (todayDeliveries && Array.isArray(todayDeliveries) && todayDeliveries.length > 0) {
        // Try to attach visit info to each delivery if possible
        const enriched = await enrichVisitsWithPatients(v)
        setVisits(enriched)
        const withVisits = todayDeliveries.map((d: any) => ({ ...d, visit: enriched.find((x: any) => (x.visit_id || x._id) === (d.visit_id || d.visit) ) }))
        setDeliveries(withVisits)
        if (visitId) {
          const filtered = withVisits.filter((d) => (d.visit as any)?.visit_id === visitId || d.visit_id === visitId)
          setDeliveries(filtered)
        }
        return
      }

      if (visitId) {
        const data = await getDeliveryByVisit(visitId)
        setDeliveries([data])
        const enriched = await enrichVisitsWithPatients(v)
        setVisits(enriched)
        return
      }

      const enriched = await enrichVisitsWithPatients(v)
      setVisits(enriched)

      const promises = enriched.map((vis) => getDeliveryByVisit((vis as any).visit_id || (vis as any)._id || (vis as any).id).catch(() => null))
      const results = await Promise.all(promises)
      const combined = results.filter(Boolean).map((d: any, i: number) => ({ ...d, visit: enriched[i] }))
      setDeliveries(combined as any[])
    } catch (e) {
      console.error('Delivery load failed', e)
      setError('Failed to load delivery records')
    } finally {
      setLoading(false)
    }
  }

  const enrichVisitsWithPatients = async (visits: any[]) => {
    const enriched = await Promise.all(
      visits.map(async (v) => {
        const visitId = v.visit_id || v.Visit_Id || v._id
        const patientId = v.patient_id || v.Patient_Id
        if (patientId) {
          try {
            const patient = await get<any>(`/patients/${patientId}`)
            const first = patient.first_name || patient.First_Name || ''
            const last = patient.last_name || patient.Last_Name || ''
            const name = `${first} ${last}`.trim()
            return { 
              ...v, 
              patient_name: name || `Patient ${patientId}`,
              display_name: `Visit ${visitId} - ${name || `Patient ${patientId}`}`
            }
          } catch {
            return { 
              ...v, 
              patient_name: `Patient ${patientId}`,
              display_name: `Visit ${visitId} - Patient ${patientId}`
            }
          }
        }
        return { 
          ...v, 
          patient_name: 'Unknown',
          display_name: `Visit ${visitId} - Unknown Patient`
        }
      })
    )
    return enriched
  }

  const openModal = () => {
    setForm({ visit_id: visits[0]?.visit_id || visits[0]?._id || '', practitioner_id: '', notes: '' })
    setShowModal(true)
  }

  const loadByDate = async (dateStr: string) => {
    setSelectedDate(dateStr)
    setLoading(true)
    try {
      const dateDeliveries = await get<any[]>(`/deliveries/date/${dateStr}`)
      const v = await get<any[]>('/visits?limit=50').catch(() => [])
      const enriched = await enrichVisitsWithPatients(v)
      setVisits(enriched)
      const withVisits = (dateDeliveries || []).map((d: any) => ({ ...d, visit: enriched.find((x: any) => (x.visit_id || x._id) === (d.visit_id || d.visit) ) }))
      setDeliveries(withVisits)
    } catch (err) {
      console.error('Failed to load deliveries for date', err)
      setError('Failed to load deliveries for selected date')
    } finally {
      setLoading(false)
    }
  }

  const submit = async () => {
    const targetVisit = visitId || Number(form.visit_id)
    if (!targetVisit) {
      alert('Please select a visit')
      return
    }
    if (!form.practitioner_id) {
      alert('Please select a practitioner')
      return
    }
    try {
      // Backend expects 'performed_by' not 'practitioner_id'
      await createDelivery({ 
        visit_id: Number(targetVisit), 
        performed_by: Number(form.practitioner_id),
        delivery_date: new Date().toISOString(), 
        notes: form.notes 
      })
      setShowModal(false)
      // Load today's deliveries to show the newly created one
      const today = new Date().toISOString().slice(0, 10)
      setSelectedDate(today)
      await loadByDate(today)
      alert('Delivery created successfully!')
    } catch (err) {
      console.error(err)
      alert('Failed to create delivery')
    }
  }

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} />

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Daily Delivery Room Log</h2>
        {!visitId && (
          <div>
            <button onClick={openModal}>Add Delivery</button>
            <button onClick={loadData} style={{ marginLeft: 8 }}>Refresh</button>
          </div>
        )}
      </div>
      <div style={{ marginTop: 12 }}>
        <label>Load deliveries for date: </label>
        <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} />
        <button onClick={() => selectedDate && loadByDate(selectedDate)} style={{ marginLeft: 8 }}>Load</button>
        <button onClick={() => { const today = new Date().toISOString().slice(0,10); loadByDate(today); }} style={{ marginLeft: 8 }}>Today</button>
      </div>
      {deliveries.length === 0 ? (
        <p style={{ marginTop: 12 }}>No delivery record found for the selected filters or date.</p>
      ) : (
        <table>
        <thead>
          <tr>
            <th>Delivery ID</th>
            <th>Visit</th>
            <th>Patient</th>
            <th>Practitioner</th>
            <th>Date</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {deliveries.map((entry, i) => (
            <tr key={entry.delivery_id || entry._id || i}>
              <td>{entry.delivery_id ?? entry._id ?? 'N/A'}</td>
              <td>{(entry.visit as any)?.visit_id || entry.visit_id || (entry.visit as any)?._id || '—'}</td>
              <td>{(entry.visit as any)?.patient_name || (entry.visit as any)?.patient?.name || entry.patient_id || 'Unknown'}</td>
              <td>{entry.performed_by || entry.practitioner_id || '—'}</td>
              <td>{entry.delivery_date ? new Date(entry.delivery_date).toLocaleString() : '—'}</td>
              <td>{entry.notes || '—'}</td>
            </tr>
          ))}
        </tbody>
        </table>
      )}

      {showModal && (
        <div style={{ position: 'fixed', left: 0, right: 0, top: 0, bottom: 0, background: 'rgba(0,0,0,0.3)' }}>
          <div style={{ background: 'white', padding: 16, width: 480, margin: '60px auto', borderRadius: 6 }}>
            <h4>Create Delivery</h4>
            {!visitId && (
              <div style={{ marginBottom: 8 }}>
                <label>Visit:</label>
                <select value={form.visit_id} onChange={(e) => setForm({ ...form, visit_id: e.target.value })}>
                  <option value="">Select visit</option>
                  {visits.map((v) => (
                    <option key={(v as any).visit_id || (v as any)._id} value={(v as any).visit_id || (v as any)._id}>
                      {(v as any).display_name || (v as any).patient_name || `Visit ${(v as any).visit_id || (v as any)._id}`}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div style={{ marginBottom: 8 }}>
              <label>Practitioner:</label>
              <select value={form.practitioner_id} onChange={(e) => setForm({ ...form, practitioner_id: e.target.value })}>
                <option value="">Select practitioner</option>
                {staff.map((s) => {
                  const staffId = s.staff_id || s.Staff_Id || s._id
                  const firstName = s.first_name || s.First_Name || ''
                  const lastName = s.last_name || s.Last_Name || ''
                  const specialty = s.specialty || s.Specialty || ''
                  const name = `${firstName} ${lastName}`.trim()
                  return (
                    <option key={staffId} value={staffId}>
                      {name} {specialty ? `(${specialty})` : ''} - ID: {staffId}
                    </option>
                  )
                })}
              </select>
            </div>
            <div style={{ marginBottom: 8 }}>
              <label>Notes:</label>
              <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowModal(false)}>Cancel</button>
              <button onClick={submit} style={{ marginLeft: 8 }}>Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
