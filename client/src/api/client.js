import axios from 'axios'

// Base URL: in dev, Vite proxies "/api" to Django (see vite.config.js). A build
// can override via VITE_API_BASE_URL.
const baseURL = import.meta.env.VITE_API_BASE_URL || '/api'

// --- Token storage -----------------------------------------------------------
// Access tokens are held in memory only (never localStorage) to limit XSS
// exposure, per our JWT security guidance. The refresh token, when used, should
// live in an httpOnly cookie set by the backend; this module does not persist
// it in JS-readable storage.
let accessToken = null

export function setAccessToken(token) {
  accessToken = token || null
}

export function getAccessToken() {
  return accessToken
}

export function clearAccessToken() {
  accessToken = null
}

const apiClient = axios.create({
  baseURL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

// Normalize errors into a consistent shape callers can rely on.
export function normalizeError(error) {
  if (axios.isCancel?.(error) || error?.code === 'ERR_CANCELED') {
    return { type: 'canceled', message: 'Request canceled', status: null }
  }
  if (error.response) {
    const { status, data } = error.response
    let message = 'Request failed'
    if (status === 401) message = 'You need to sign in to continue.'
    else if (data?.detail) message = data.detail
    else if (typeof data === 'string') message = data
    return { type: 'http', status, message, data }
  }
  if (error.request) {
    return { type: 'network', status: null, message: 'Network error: could not reach the server.' }
  }
  return { type: 'unknown', status: null, message: error.message || 'Unexpected error' }
}

apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(normalizeError(error)),
)

export default apiClient
