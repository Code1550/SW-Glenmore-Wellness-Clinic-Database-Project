import React, { useEffect, useState } from 'react'
import { get } from '../../api/client'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import ErrorMessage from '../../components/common/ErrorMessage'
import PhysicianStatement from '../../components/billing/PhysicianStatement'

export default function InsuranceForms() {
  // For insurance receipt/statement
  const [invoices, setInvoices] = useState<any[]>([])
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null)
  const [invoiceLoading, setInvoiceLoading] = useState(true)
  const [invoiceError, setInvoiceError] = useState<string | null>(null)

  // Load invoices directly from the invoices collection
  useEffect(() => {
    setInvoiceLoading(true)
    get<any[]>('/invoices')
      .then((data) => setInvoices(data || []))
      .catch(() => setInvoiceError('Failed to load invoices'))
      .finally(() => setInvoiceLoading(false))
  }, [])

  // Helper to get field values with case tolerance
  const getField = (obj: any, ...keys: string[]) => {
    if (!obj) return null
    for (const key of keys) {
      if (obj[key] !== undefined && obj[key] !== null) return obj[key]
    }
    return null
  }

  if (invoiceLoading) return <LoadingSpinner />
  if (invoiceError) return <ErrorMessage message={invoiceError} />

  return (
    <div style={{ padding: '1rem' }}>
      <h2>Insurance Receipt / Physician Statement</h2>
      <div style={{ marginBottom: '1rem' }}>
        <label htmlFor="invoice-select"><strong>Select Invoice:</strong> </label>
        {invoices.length === 0 ? (
          <span style={{ marginLeft: 8 }}>No invoices available.</span>
        ) : (
          <select
            id="invoice-select"
            value={selectedInvoiceId ?? ''}
            onChange={e => setSelectedInvoiceId(Number(e.target.value) || null)}
          >
            <option value="">-- Select Invoice --</option>
            {invoices.map((inv, idx) => {
              const invId = getField(inv, 'invoice_id', 'Invoice_Id')
              const invDate = getField(inv, 'invoice_date', 'Invoice_Date') || 'N/A'
              const patientId = getField(inv, 'patient_id', 'Patient_Id')
              const status = getField(inv, 'status', 'Status') || 'Unknown'
              const totalAmount = getField(inv, 'total_amount', 'Total_Amount') || 0
              return (
                <option key={`inv-${invId || idx}`} value={invId}>
                  Invoice #{invId} | Patient: {patientId} | {invDate} | ${Number(totalAmount).toFixed(2)} | {status}
                </option>
              )
            })}
          </select>
        )}
      </div>
      {selectedInvoiceId && (
        <div style={{ border: '1px solid #ccc', padding: '1rem', marginTop: '1rem', background: '#fafaff' }}>
          <PhysicianStatement invoiceId={selectedInvoiceId} />
        </div>
      )}
    </div>
  )
}
