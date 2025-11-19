import React from 'react'
import './Layout.css'

export default function Layout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="app-layout">
      <header className="app-header">Glenmore Clinic — Admin</header>
      <div className="app-body">{children}</div>
      <footer className="app-footer">© Glenmore Wellness Clinic</footer>
    </div>
  )
}
