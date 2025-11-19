import { useCallback } from 'react'
import { callFunction } from '../api/functions'

export function useFunctions(){
  const run = useCallback(async (name: string, payload?: any) => {
    return callFunction(name, payload)
  }, [])

  return { run }
}
