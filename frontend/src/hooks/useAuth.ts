import { useState } from 'react'

export function useAuth(){
  const [user, setUser] = useState<any>(null)
  const login = async () => setUser({ name: 'Dev User' })
  const logout = async () => setUser(null)
  return { user, login, logout }
}
