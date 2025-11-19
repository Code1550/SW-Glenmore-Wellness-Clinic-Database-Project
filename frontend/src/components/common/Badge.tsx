import React from 'react'

export default function Badge({ children }: { children?: React.ReactNode }) {
  return (
    <span style={{ background: '#e6f0ff', color: '#063c8a', padding: '2px 8px', borderRadius: 999 }}>
      {children}
    </span>
  )
}
