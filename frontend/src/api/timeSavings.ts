import client from './client'

export interface TimeSavingBreakdownItem {
  event_type: string
  label: string
  count: number
  seconds: number
}

export interface TimeSavingSummary {
  total_seconds: number
  total_events: number
  breakdown: TimeSavingBreakdownItem[]
}

export const timeSavingsApi = {
  getSummary: () => client.get<TimeSavingSummary>('/users/me/time-savings'),
}

export function formatDuration(seconds: number): string {
  if (!seconds || seconds < 0) return '0min'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h === 0) return `${m}min`
  if (m === 0) return `${h}h`
  return `${h}h ${m}min`
}
