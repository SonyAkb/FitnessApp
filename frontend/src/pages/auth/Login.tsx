import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await login(email, password)
      navigate('/home')
    } catch {
      setError('Неверный email или пароль')
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-brand">
        <div className="mark">🐾</div>
        <h1>FitQuest</h1>
        <p>Тренируйся — расти питомца</p>
      </div>
      <form onSubmit={handleSubmit}>
        {error && <div className="error">{error}</div>}
        <input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input placeholder="Пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button className="primary" type="submit">Войти</button>
      </form>
      <p className="auth-switch">
        Нет аккаунта? <Link to="/register">Зарегистрироваться</Link>
      </p>
    </div>
  )
}
