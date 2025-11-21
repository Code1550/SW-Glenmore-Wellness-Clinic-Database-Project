import React from 'react'
import { useParams } from 'react-router-dom'
import PractitionerSchedule from '../../components/schedules/PractitionerSchedule'

export default function PractitionerDaily() {
  const { staffId } = useParams<{ staffId: string }>()
  return (
    <div><PractitionerSchedule staffId={staffId ? Number(staffId) : undefined} /></div>
  )
}