import React, { useEffect, useState } from 'react'
import '../../styles/logLayout.css'
import MonthPicker from '../../components/billing/MonthPicker'

interface PatientStatementPatient {
  patient_id: number
  patient_name: string
  total_invoiced: number
  payments_received: number
  balance: number
  status: string
  max_aging_days?: number
  invoices: any[]
  services?: { description: string; qty: number; amount: number }[]
  payments?: { payment_date: string; method: string; amount: number }[]
}

interface MonthlyStatementsResponse {
  month: string
  summary: {
    paid: { patients: PatientStatementPatient[]; totals: Totals }
    unpaid: { patients: PatientStatementPatient[]; totals: Totals }
  }
}

interface Totals { total_invoiced: number; payments_received: number; balance: number }

export default function MonthlyStatements() {
  const now = new Date()
  const defaultMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  const [monthValue, setMonthValue] = useState<string>(defaultMonth)
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<MonthlyStatementsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})

  useEffect(() => { load() }, [])

  async function load() {
    setLoading(true); setError(null)
    try {
      const [year, month] = monthValue.split('-')
      const res = await fetch(`${import.meta.env.VITE_API_URL}/statements/monthly?year=${Number(year)}&month=${Number(month)}`)
      if (!res.ok) throw new Error(`Server returned ${res.status}`)
      const json: MonthlyStatementsResponse = await res.json()
      setData(json)
    } catch (err: any) {
      setError(err.message || String(err)); setData(null)
    } finally { setLoading(false) }
  }

  function toggle(pid: number) {
    setExpanded(s => ({ ...s, [String(pid)]: !s[String(pid)] }))
  }

  function downloadCSV(section: 'paid' | 'unpaid') {
    if (!data) return
    const rows: string[] = []
    rows.push('patient_id,patient_name,total_invoiced,payments_received,balance,status,max_aging_days')
    const patients = data.summary?.[section]?.patients || []
    for (const p of patients) {
      rows.push(`${p.patient_id},"${(p.patient_name||'').replace(/"/g,'""')}",${p.total_invoiced},${p.payments_received},${p.balance},${p.status},${p.max_aging_days||''}`)
    }
    const csv = rows.join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `statements_${data.month}_${section}.csv`; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
  }

  const unpaidPatients = data?.summary.unpaid.patients || []
  const paidPatients = data?.summary.paid.patients || []

  function formatCurrency(v: number | undefined) { return typeof v === 'number' ? v.toFixed(2) : '0.00' }

  return (
    <div className="log-page">
      <div className="toolbar">
        <div className="toolbar-left" style={{ flexWrap: 'wrap' }}>
          <h3 style={{ margin:0 }}>Patient Monthly Statements</h3>
          <MonthPicker value={monthValue} onChange={setMonthValue} />
          <button className="btn" disabled={loading} onClick={load}>{loading ? 'Loading…' : 'Load'}</button>
          {data && <span className="muted">Showing: {data.month}</span>}
        </div>
        <div className="toolbar-right">
          {data && <>
            <button className="btn" onClick={() => downloadCSV('unpaid')}>CSV Unpaid</button>
            <button className="btn" onClick={() => downloadCSV('paid')}>CSV Paid</button>
          </>}
        </div>
      </div>

      {error && <div style={{ color:'red', marginBottom:12 }}>{error}</div>}
      {!data && !error && <div className="card">No data. Click Load.</div>}

      {data && (
        <>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(180px,1fr))', gap:12, marginBottom:16 }}>
            <div className="card"><strong>Total Invoiced</strong><div style={{ fontSize:'1.3rem' }}>{formatCurrency(data.summary.paid.totals.total_invoiced + data.summary.unpaid.totals.total_invoiced)}</div></div>
            <div className="card"><strong>Payments Received</strong><div style={{ fontSize:'1.3rem' }}>{formatCurrency(data.summary.paid.totals.payments_received + data.summary.unpaid.totals.payments_received)}</div></div>
            <div className="card"><strong>Outstanding</strong><div style={{ fontSize:'1.3rem', color:'#b00020' }}>{formatCurrency(data.summary.unpaid.totals.balance)}</div></div>
            <div className="card"><strong>Paid Patients</strong><div style={{ fontSize:'1.3rem' }}>{paidPatients.length}</div></div>
            <div className="card"><strong>Unpaid Patients</strong><div style={{ fontSize:'1.3rem' }}>{unpaidPatients.length}</div></div>
          </div>

          {/* Unpaid Accounts */}
          <section style={{ marginBottom:32 }}>
              <h4 style={{ marginBottom:8 }}>Unpaid Accounts</h4>
              <table className="table">
                <thead>
                  <tr>
                    <th>Patient</th>
                    <th style={{ textAlign:'right' }}>Invoiced</th>
                    <th style={{ textAlign:'right' }}>Payments</th>
                    <th style={{ textAlign:'right' }}>Balance</th>
                    <th style={{ textAlign:'right' }}>Max Aging (days)</th>
                    <th>Status</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {unpaidPatients.map(p => (
                    <React.Fragment key={p.patient_id}>
                      <tr>
                        <td>{p.patient_name || p.patient_id}</td>
                        <td style={{ textAlign:'right' }}>{formatCurrency(p.total_invoiced)}</td>
                        <td style={{ textAlign:'right' }}>{formatCurrency(p.payments_received)}</td>
                        <td style={{ textAlign:'right', color:'#b00020' }}>{formatCurrency(p.balance)}</td>
                        <td style={{ textAlign:'right' }}>{p.max_aging_days || 0}</td>
                        <td>{p.status}</td>
                        <td><button className="btn" onClick={() => toggle(p.patient_id)}>{expanded[String(p.patient_id)] ? 'Hide' : 'Show'}</button></td>
                      </tr>
                      {expanded[String(p.patient_id)] && (
                        <tr>
                          <td colSpan={7}>
                            <div style={{ display:'flex', flexWrap:'wrap', gap:16 }}>
                              <div className="card" style={{ flex:'1 1 300px' }}>
                                <strong>Services</strong>
                                <table className="table" style={{ marginTop:8 }}>
                                  <thead><tr><th>Description</th><th style={{ textAlign:'right' }}>Qty</th><th style={{ textAlign:'right' }}>Amount</th></tr></thead>
                                  <tbody>
                                    {p.services?.map(s => (
                                      <tr key={s.description}><td>{s.description}</td><td style={{ textAlign:'right' }}>{s.qty}</td><td style={{ textAlign:'right' }}>{formatCurrency(s.amount)}</td></tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                              <div className="card" style={{ flex:'2 1 400px' }}>
                                <strong>Invoices</strong>
                                <table className="table" style={{ marginTop:8 }}>
                                  <thead><tr><th>ID</th><th>Date</th><th style={{ textAlign:'right' }}>Portion</th><th style={{ textAlign:'right' }}>Paid</th><th style={{ textAlign:'right' }}>Balance</th><th style={{ textAlign:'right' }}>Aging</th><th>Bucket</th></tr></thead>
                                  <tbody>
                                    {p.invoices.map(inv => (
                                      <tr key={inv.invoice_id}><td>{inv.invoice_id}</td><td>{inv.invoice_date}</td><td style={{ textAlign:'right' }}>{formatCurrency(inv.patient_portion)}</td><td style={{ textAlign:'right' }}>{formatCurrency(inv.total_paid)}</td><td style={{ textAlign:'right', color: inv.balance_due>0?'#b00020':undefined }}>{formatCurrency(inv.balance_due)}</td><td style={{ textAlign:'right' }}>{inv.days_outstanding}</td><td>{inv.aging_bucket}</td></tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                              <div className="card" style={{ flex:'1 1 250px' }}>
                                <strong>Payments</strong>
                                <table className="table" style={{ marginTop:8 }}>
                                  <thead><tr><th>Date</th><th>Method</th><th style={{ textAlign:'right' }}>Amount</th></tr></thead>
                                  <tbody>
                                    {p.payments?.map(pay => (<tr key={pay.payment_date+pay.amount}><td>{pay.payment_date}</td><td>{pay.method}</td><td style={{ textAlign:'right' }}>{formatCurrency(pay.amount)}</td></tr>))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </section>

          {/* Paid Accounts */}
          <section style={{ marginBottom:32 }}>
              <h4 style={{ marginBottom:8 }}>Paid Accounts</h4>
              <table className="table">
                <thead>
                  <tr>
                    <th>Patient</th>
                    <th style={{ textAlign:'right' }}>Invoiced</th>
                    <th style={{ textAlign:'right' }}>Payments</th>
                    <th style={{ textAlign:'right' }}>Balance</th>
                    <th>Status</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {paidPatients.map(p => (
                    <React.Fragment key={p.patient_id}>
                      <tr>
                        <td>{p.patient_name || p.patient_id}</td>
                        <td style={{ textAlign:'right' }}>{formatCurrency(p.total_invoiced)}</td>
                        <td style={{ textAlign:'right' }}>{formatCurrency(p.payments_received)}</td>
                        <td style={{ textAlign:'right' }}>{formatCurrency(p.balance)}</td>
                        <td>{p.status}</td>
                        <td><button className="btn" onClick={() => toggle(p.patient_id)}>{expanded[String(p.patient_id)] ? 'Hide' : 'Show'}</button></td>
                      </tr>
                      {expanded[String(p.patient_id)] && (
                        <tr>
                          <td colSpan={6}>
                            <div style={{ display:'flex', flexWrap:'wrap', gap:16 }}>
                              <div className="card" style={{ flex:'1 1 300px' }}>
                                <strong>Services</strong>
                                <table className="table" style={{ marginTop:8 }}>
                                  <thead><tr><th>Description</th><th style={{ textAlign:'right' }}>Qty</th><th style={{ textAlign:'right' }}>Amount</th></tr></thead>
                                  <tbody>
                                    {p.services?.map(s => (<tr key={s.description}><td>{s.description}</td><td style={{ textAlign:'right' }}>{s.qty}</td><td style={{ textAlign:'right' }}>{formatCurrency(s.amount)}</td></tr>))}
                                  </tbody>
                                </table>
                              </div>
                              <div className="card" style={{ flex:'2 1 400px' }}>
                                <strong>Invoices</strong>
                                <table className="table" style={{ marginTop:8 }}>
                                  <thead><tr><th>ID</th><th>Date</th><th style={{ textAlign:'right' }}>Portion</th><th style={{ textAlign:'right' }}>Paid</th><th style={{ textAlign:'right' }}>Balance</th></tr></thead>
                                  <tbody>
                                    {p.invoices.map(inv => (<tr key={inv.invoice_id}><td>{inv.invoice_id}</td><td>{inv.invoice_date}</td><td style={{ textAlign:'right' }}>{formatCurrency(inv.patient_portion)}</td><td style={{ textAlign:'right' }}>{formatCurrency(inv.total_paid)}</td><td style={{ textAlign:'right' }}>{formatCurrency(inv.balance_due)}</td></tr>))}
                                  </tbody>
                                </table>
                              </div>
                              <div className="card" style={{ flex:'1 1 250px' }}>
                                <strong>Payments</strong>
                                <table className="table" style={{ marginTop:8 }}>
                                  <thead><tr><th>Date</th><th>Method</th><th style={{ textAlign:'right' }}>Amount</th></tr></thead>
                                  <tbody>
                                    {p.payments?.map(pay => (<tr key={pay.payment_date+pay.amount}><td>{pay.payment_date}</td><td>{pay.method}</td><td style={{ textAlign:'right' }}>{formatCurrency(pay.amount)}</td></tr>))}
                                  </tbody>
                                </table>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </section>
        </>
      )}
    </div>
  )
}
