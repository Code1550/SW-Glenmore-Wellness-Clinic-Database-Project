/**
 * Time utilities for consistent MST formatting across the application
 */

/**
 * Get current local date in YYYY-MM-DD format (MST)
 */
export const getLocalDateString = (date: Date = new Date()): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

/**
 * Format a datetime string or Date to MST with nice formatting
 * @param dateTime - ISO string, Date object, or null
 * @returns Formatted string like "Nov 27, 2025 2:30 PM" or "—" if null
 */
export const formatMST = (dateTime: string | Date | null | undefined): string => {
  if (!dateTime) return '—'
  
  try {
    const date = typeof dateTime === 'string' ? new Date(dateTime) : dateTime
    
    // Format in MST (Mountain Standard Time - UTC-7)
    const options: Intl.DateTimeFormatOptions = {
      timeZone: 'America/Denver',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }
    
    return new Intl.DateTimeFormat('en-US', options).format(date)
  } catch (e) {
    return String(dateTime)
  }
}

/**
 * Get current MST timestamp as ISO string for server submission
 */
export const getMSTNow = (): string => {
  // Create a date in MST timezone and return ISO format
  const now = new Date()
  const mstDate = new Date(now.toLocaleString('en-US', { timeZone: 'America/Denver' }))
  return mstDate.toISOString()
}

/**
 * Get an ISO-like timestamp that preserves the Mountain local date (no UTC shift).
 * Returns format YYYY-MM-DDTHH:MM:SS-07:00 (or -06:00 during MDT) so string prefix (YYYY-MM-DD)
 * matches the local calendar day used in regex date queries.
 */
export const getMSTLocalNow = (): string => {
  const now = new Date()
  // Get components in Denver timezone via Intl
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Denver',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
  })
  const parts = formatter.formatToParts(now)
  const lookup: Record<string,string> = {}
  parts.forEach(p => { if (p.type !== 'literal') lookup[p.type] = p.value })
  const year = lookup.year
  const month = lookup.month
  const day = lookup.day
  const hour = lookup.hour
  const minute = lookup.minute
  const second = lookup.second
  // Determine offset (MST = -07:00 standard, MDT = -06:00 daylight). Use current offset from Date.
  // Offset minutes: getTimezoneOffset gives minutes from UTC for local machine; instead compute Denver offset by creating date string.
  // Simpler: infer from UTC vs local Denver hour difference.
  const denverNow = new Date(now.toLocaleString('en-US', { timeZone: 'America/Denver' }))
  const offsetMinutes = (denverNow.getTime() - Date.UTC(denverNow.getUTCFullYear(), denverNow.getUTCMonth(), denverNow.getUTCDate(), denverNow.getUTCHours(), denverNow.getUTCMinutes(), denverNow.getUTCSeconds(), denverNow.getUTCMilliseconds())) / 60000
  // offsetMinutes will be negative for timezones behind UTC
  const totalMinutes = Math.round(offsetMinutes) // -420 or -360 typically
  const sign = totalMinutes <= 0 ? '-' : '+'
  const absMinutes = Math.abs(totalMinutes)
  const offHours = String(Math.floor(absMinutes / 60)).padStart(2,'0')
  const offMins = String(absMinutes % 60).padStart(2,'0')
  const offset = `${sign}${offHours}:${offMins}`
  return `${year}-${month}-${day}T${hour}:${minute}:${second}${offset}`
}

/**
 * Format date only (no time) in MST
 */
export const formatMSTDate = (dateTime: string | Date | null | undefined): string => {
  if (!dateTime) return '—'
  
  try {
    const date = typeof dateTime === 'string' ? new Date(dateTime) : dateTime
    
    const options: Intl.DateTimeFormatOptions = {
      timeZone: 'America/Denver',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }
    
    return new Intl.DateTimeFormat('en-US', options).format(date)
  } catch (e) {
    return String(dateTime)
  }
}
