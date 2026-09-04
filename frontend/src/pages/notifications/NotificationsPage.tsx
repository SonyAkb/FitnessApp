import { useEffect, useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'
import { api } from '../../api/client'

/**
 * Модуль 5 (владелец: <впишите имя>).
 * Не вынесена в таб-бар (на мобильном разумный потолок — 5 вкладок),
 * доступна через колокольчик на главном экране / профиль.
 * TODO: UI настройки NotificationRule, авто-генерация системой, web push.
 */

interface Notification {
  id: number
  title: string
  created_at: string
}

export default function NotificationsPage() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [title, setTitle] = useState('')

  async function load() {
    const { data } = await api.get<Notification[]>('/notifications')
    setNotifications(data)
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!title) return
    await api.post('/notifications', { title })
    setTitle('')
    load()
  }

  return (
    <div>
      <div className="back-row" onClick={() => navigate(-1)}>
        <ChevronLeft size={18} /> Назад
      </div>
      <h1 style={{ fontSize: 22, fontWeight: 800, margin: '0 0 16px' }}>Уведомления</h1>

      <div className="card">
        <h2>Тестовое уведомление</h2>
        <form onSubmit={handleCreate}>
          <input placeholder="Текст уведомления" value={title} onChange={(e) => setTitle(e.target.value)} />
          <button className="primary" type="submit">Создать</button>
        </form>
      </div>

      <div className="card">
        <h2>Все уведомления</h2>
        {notifications.length === 0 && <p className="muted">Пока нет уведомлений</p>}
        {notifications.map((n) => (
          <div className="list-item" key={n.id}>
            <strong>{n.title}</strong>
            <div className="muted">{new Date(n.created_at).toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
