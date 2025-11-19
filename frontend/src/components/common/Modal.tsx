import React from 'react'

export default function Modal({ title, children }: { title?: string; children?: React.ReactNode }) {
  return (
    <div role="dialog" style={{ background: 'rgba(0,0,0,0.4)', padding: 20 }}>
      <div style={{ background: '#fff', padding: 16 }}>
        {title && <h3>{title}</h3>}
        {children}
      </div>
    </div>
  )
}
