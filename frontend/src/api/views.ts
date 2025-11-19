// Placeholder typed view calls
import api from './client'

export async function fetchViews() {
  const { data } = await api.get('/views')
  return data
}
