import React from 'react'

export default function SearchBar({ onSearch }: { onSearch?: (q: string) => void }) {
  return (
    <input
      placeholder="Search..."
      onChange={(e) => onSearch && onSearch(e.target.value)}
      style={{ padding: 8, borderRadius: 6, border: '1px solid #e5e7eb' }}
    />
  )
}
