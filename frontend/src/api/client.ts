import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const client = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Attach Bearer token from auth store
client.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

// Redirect to login on 401
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      const auth = useAuthStore()
      if (auth.token) {
        auth.logout()
      }
    }
    return Promise.reject(err)
  },
)

export function extractApiError(e: unknown): string {
  if (e && typeof e === 'object' && 'response' in e) {
    const detail = (e as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail))
      return detail
        .map((d: unknown) =>
          d && typeof d === 'object' && 'msg' in d ? (d as { msg: string }).msg : String(d)
        )
        .join('; ')
  }
  return (e as Error).message || String(e)
}

export default client
