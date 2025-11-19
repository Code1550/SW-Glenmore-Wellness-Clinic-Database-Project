export interface Shift {
  id: string
  practitionerId: string
  start: string
  end: string
  room?: string
}

export interface DailySchedule {
  date: string
  shifts: Shift[]
}
