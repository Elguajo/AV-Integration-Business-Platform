// Unknown values are shown as a dash, never as zero (MVP-SPEC §5).
export const UNKNOWN = '—'

export function money(value: number | null | undefined, currency: string | null | undefined) {
  if (value === null || value === undefined || !currency) return UNKNOWN
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value)
}

export function quantity(value: number | null | undefined, uom?: string | null) {
  if (value === null || value === undefined) return UNKNOWN
  const n = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 3 }).format(value)
  return uom ? `${n} ${uom}` : n
}

export function date(value: string | null | undefined) {
  if (!value) return UNKNOWN
  const d = new Date(value.length === 10 ? `${value}T00:00:00` : value.replace(' ', 'T'))
  if (Number.isNaN(d.getTime())) return value
  return new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' }).format(d)
}
