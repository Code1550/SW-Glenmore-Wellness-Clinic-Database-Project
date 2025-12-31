import React from 'react'
import './Layout.css'
import NavBar from './NavBar' // Add this import

export default function Layout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="app-layout">
      <header className="app-header">Glenmore Clinic — Admin</header>
      <NavBar /> {/* Insert NavBar here */}
      <div className="app-body">{children}</div>
      <footer className="app-footer">© Glenmore Wellness Clinic</footer>
    </div>
  )
}
