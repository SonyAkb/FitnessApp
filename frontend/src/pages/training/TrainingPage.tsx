import { useEffect, useState, FormEvent } from 'react'
import { api } from '../../api/client'
import ScreenHeader from '../../components/ScreenHeader'

/**
 * Модуль 2 (владелец: <впишите имя>).
 * TODO: редактирование планов, несколько упражнений на форме, таймер отдыха,
 * экран "во время тренировки".
 */

interface Exercise { id: number; name: string }
interface Plan { id: number; name: string; exercises: Exercise[] }
interface Session { id: number; status: string; started_at: string }

export default function TrainingPage() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [sessions, setSessions] = useState<Session[]>([])
  const [name, setName] = useState('')
  const [exerciseName, setExerciseName] = useState('')

  async function load() {
    const [plansRes, sessionsRes] = await Promise.all([
      api.get<Plan[]>('/training/plans'),
      api.get<Session[]>('/training/sessions'),
    ])
    setPlans(plansRes.data)
    setSessions(sessionsRes.data)
  }

  useEffect(() => {
    load()
  }, [])

  async function handleCreatePlan(e: FormEvent) {
    e.preventDefault()
    if (!name) return
    await api.post('/training/plans', {
      name,
      description: null,
      exercises: exerciseName ? [{ name: exerciseName, sets: 3, reps: 10 }] : [],
    })
    setName('')
    setExerciseName('')
    load()
  }

  async function handleStart(planId: number) {
    await api.post(`/training/plans/${planId}/start`)
    load()
  }

  async function handleComplete(sessionId: number) {
    await api.post(`/training/sessions/${sessionId}/complete`)
    load()
  }

  return (
    <div>
      <ScreenHeader title="Тренировки" subtitle="Планы и история" />

      <div className="card">
        <h2>Новый план</h2>
        <form onSubmit={handleCreatePlan}>
          <input placeholder="Название плана" value={name} onChange={(e) => setName(e.target.value)} />
          <input placeholder="Упражнение (необязательно)" value={exerciseName} onChange={(e) => setExerciseName(e.target.value)} />
          <button className="primary" type="submit">Создать план</button>
        </form>
      </div>

      <div className="card">
        <h2>Мои планы</h2>
        {plans.length === 0 && <p className="muted">Пока нет планов</p>}
        {plans.map((p) => (
          <div className="list-item" key={p.id}>
            <div className="row">
              <strong>{p.name}</strong>
              <button className="secondary" style={{ width: 'auto', padding: '8px 14px' }} onClick={() => handleStart(p.id)}>
                Начать
              </button>
            </div>
            <div className="muted">{p.exercises.map((ex) => ex.name).join(', ') || 'без упражнений'}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <h2>История</h2>
        {sessions.length === 0 && <p className="muted">Пока нет тренировок</p>}
        {sessions.map((s) => (
          <div className="list-item" key={s.id}>
            <div className="row">
              <span>#{s.id} · {new Date(s.started_at).toLocaleDateString()}</span>
              {s.status === 'in_progress' ? (
                <button className="ghost" onClick={() => handleComplete(s.id)}>Завершить</button>
              ) : (
                <span className="muted">{s.status}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
