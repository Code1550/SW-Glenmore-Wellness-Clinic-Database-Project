// Placeholder for calling stored procedures / functions on the backend
import api from './client'

export async function callFunction(name: string, payload?: any) {
  const { data } = await api.post(`/functions/${name}`, payload)
  return data
}
