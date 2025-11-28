import React, { useState, useEffect, useRef } from 'react';

interface MonthPickerProps {
  value: string; // YYYY-MM
  onChange: (value: string) => void;
}

// Utility to format year-month
function ymString(year: number, monthIndex: number) { // monthIndex 0-11
  return `${year}-${String(monthIndex + 1).padStart(2,'0')}`;
}

const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

export default function MonthPicker({ value, onChange }: MonthPickerProps) {
  const [open, setOpen] = useState(false);
  const [viewYear, setViewYear] = useState<number>(() => {
    const parts = value.split('-');
    return Number(parts[0]) || new Date().getFullYear();
  });
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [open]);

  const selectedParts = value.split('-');
  const selectedYear = Number(selectedParts[0]);
  const selectedMonthIndex = Number(selectedParts[1]) - 1;

  function selectMonth(monthIndex: number) {
    onChange(ymString(viewYear, monthIndex));
    setOpen(false);
  }

  function prevYear() { setViewYear(y => y - 1); }
  function nextYear() { setViewYear(y => y + 1); }

  return (
    <div ref={wrapperRef} style={{ position:'relative', display:'inline-block' }}>
      <button type="button" className="btn" onClick={() => setOpen(o => !o)} aria-haspopup="dialog" aria-expanded={open}>
        {value} ▾
      </button>
      {open && (
        <div role="dialog" aria-label="Select month" style={{ position:'absolute', top:'100%', left:0, zIndex:1000, background:'#fff', border:'1px solid #ccc', borderRadius:8, padding:12, boxShadow:'0 2px 8px rgba(0,0,0,0.15)', minWidth:220 }}>
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:8 }}>
            <button type="button" className="btn" onClick={prevYear}>&lt;</button>
            <strong>{viewYear}</strong>
            <button type="button" className="btn" onClick={nextYear}>&gt;</button>
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:6 }}>
            {monthNames.map((name, idx) => {
              const isSelected = viewYear === selectedYear && idx === selectedMonthIndex;
              return (
                <button
                  key={name}
                  type="button"
                  onClick={() => selectMonth(idx)}
                  className="btn"
                  style={{
                    padding:'6px 4px',
                    background: isSelected ? '#2d6cdf' : '#f7f7f7',
                    color: isSelected ? '#fff' : '#000',
                    fontWeight: isSelected ? 'bold' : 'normal'
                  }}
                >
                  {name}
                </button>
              );
            })}
          </div>
          <div style={{ marginTop:8, textAlign:'center' }}>
            <button type="button" className="btn" onClick={() => setOpen(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
