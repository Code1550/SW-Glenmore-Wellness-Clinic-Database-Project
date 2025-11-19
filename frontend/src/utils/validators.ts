export function required(value: any){
  return value !== undefined && value !== null && value !== ''
}

export function isNumber(value: any){
  return typeof value === 'number' && !Number.isNaN(value)
}
