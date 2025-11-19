import React from 'react'

export default function ErrorMessage({ children }: { children?: React.ReactNode }) {
  return <div style={{ color: 'crimson' }}>{children ?? 'An error occurred'}</div>
}
