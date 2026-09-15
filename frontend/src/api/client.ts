import axios from 'axios'

// Базовый URL бэкенда. В докере пробрасывается через VITE_API_URL (см. docker-compose.yml).
const apiBaseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({ baseURL: apiBaseUrl })

// Автоматически подставляем JWT-токен во все запросы, если он есть.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('fitquest_token')
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
