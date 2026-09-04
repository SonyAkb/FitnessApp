import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await register(email, password, fullName)
      navigate('/home')
    } catch {
      setError('Не удалось зарегистрироваться (возможно, email уже занят)')
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-brand">
        <div className="mark">🐾</div>
        <h1>Создать аккаунт</h1>
        <p>Заведи своего фитнес-питомца</p>
      </div>
      <form onSubmit={handleSubmit}>
        {error && <div className="error">{error}</div>}
        <input placeholder="Имя" value={fullName} onChange={(e) => setFullName(e.target.value)} />
        <input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input placeholder="Пароль" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <button className="primary" type="submit">Зарегистрироваться</button>
      </form>
      <p className="auth-switch">
        Уже есть аккаунт? <Link to="/login">Войти</Link>
      </p>
    </div>
  )
}
