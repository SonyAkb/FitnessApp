import { createContext, useContext, useState, ReactNode } from 'react'
import { api } from '../api/client'

interface AuthContextType {
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem('fitquest_token'))

  async function login(email: string, password: string) {
    // Бэкенд ждёт стандартную OAuth2PasswordRequestForm — это form-urlencoded, не JSON.
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)
    const { data } = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    localStorage.setItem('fitquest_token', data.access_token)
    setToken(data.access_token)
  }

  async function register(email: string, password: string, fullName?: string) {
    await api.post('/auth/register', { email, password, full_name: fullName })
    await login(email, password)
  }

  function logout() {
    localStorage.removeItem('fitquest_token')
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextType {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth должен использоваться внутри <AuthProvider>')
  return ctx
}
