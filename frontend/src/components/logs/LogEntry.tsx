import React from 'react'

export default function LogEntry({ text }: { text?: string }){
  return <div style={{ padding: 8, borderBottom: '1px solid #f3f4f6' }}>{text}</div>
}
