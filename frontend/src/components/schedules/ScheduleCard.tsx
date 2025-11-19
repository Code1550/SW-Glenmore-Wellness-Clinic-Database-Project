import React from 'react'

export default function ScheduleCard({ title }: { title?: string }) {
  return <div style={{ border: '1px solid #e5e7eb', padding: 12 }}>{title ?? 'Schedule'}</div>
}
