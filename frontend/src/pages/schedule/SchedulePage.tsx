import { useEffect, useState, FormEvent } from 'react'
import { api } from '../../api/client'
import ScreenHeader from '../../components/ScreenHeader'

/**
 * Модуль 1 (владелец: <впишите имя>).
 * TODO: редактирование, повторяющиеся события (repeat_rule), недельный вид календаря.
 */

interface ScheduleEvent {
  id: number
  title: string
  starts_at: string
}

export default function SchedulePage() {
  const [events, setEvents] = useState<ScheduleEvent[]>([])
  const [title, setTitle] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    const { data } = await api.get<ScheduleEvent[]>('/schedule')
    setEvents(data)
    setLoading(false)
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!title || !startsAt) return
    await api.post('/schedule', { title, starts_at: new Date(startsAt).toISOString() })
    setTitle('')
    setStartsAt('')
    load()
  }

  async function handleDelete(id: number) {
    await api.delete(`/schedule/${id}`)
    load()
  }

  return (
    <div>
      <ScreenHeader title="Расписание" subtitle="Твой план тренировок по дням" />

      <div className="card">
        <h2>Новое событие</h2>
        <form onSubmit={handleCreate}>
          <input placeholder="Название" value={title} onChange={(e) => setTitle(e.target.value)} />
          <input type="datetime-local" value={startsAt} onChange={(e) => setStartsAt(e.target.value)} />
          <button className="primary" type="submit">Добавить</button>
        </form>
      </div>

      <div className="card">
        <h2>Ближайшие события</h2>
        {loading && <p className="muted">Загрузка...</p>}
        {!loading && events.length === 0 && <p className="muted">Пока нет событий</p>}
        {events.map((ev) => (
          <div className="list-item" key={ev.id}>
            <div className="row">
              <strong>{ev.title}</strong>
              <button className="ghost" onClick={() => handleDelete(ev.id)}>Удалить</button>
            </div>
            <div className="muted">{new Date(ev.starts_at).toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
