export interface Invoice {
  id: string
  patientId: string
  amount: number
  date: string
  paid: boolean
}

export interface Statement {
  id: string
  patientId: string
  periodStart: string
  periodEnd: string
  invoices: Invoice[]
}
