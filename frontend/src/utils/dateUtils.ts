export function toISO(date: Date) {
  return date.toISOString()
}

export function todayISO() {
  return toISO(new Date())
}
