import { useState, useEffect } from 'react'
import { fetchViews } from '../api/views'

export function useViews(){
  const [views, setViews] = useState<any[]>([])
  useEffect(() => { fetchViews().then((d) => setViews(d)).catch(()=>{}) }, [])
  return { views }
}
