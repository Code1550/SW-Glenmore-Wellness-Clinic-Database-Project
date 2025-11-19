import React from 'react'

export default function StatCard({ label, value }: { label?: string; value?: string | number }){
  return (
    <div style={{ padding: 12, background: '#fff', borderRadius: 8 }}>
      <div style={{ fontSize: 12, color: '#6b7280' }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 600 }}>{value}</div>
    </div>
  )
}
