import { useEffect, useState } from 'react'
import { Sparkles, Watch } from 'lucide-react'
import { api } from '../../api/client'
import ScreenHeader from '../../components/ScreenHeader'

/**
 * Модуль 5 (дашборд) + Модуль 6 (AI-рекомендации, эмулятор часов).
 * Объединены на одном экране "Прогресс" — на мобильном таб-баре
 * 5 вкладок это разумный потолок, поэтому смежная по смыслу
 * аналитика живёт вместе. При желании легко разнести на 2 экрана.
 */

interface Summary {
  total_workouts: number
  completed_workouts: number
  current_streak_days: number
}

interface Recommendation {
  recommendation: string
  reason: string
}

interface WatchPoint {
  steps: number
  heart_rate: number
  recorded_at: string
}

export default function ProgressPage() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null)
  const [watch, setWatch] = useState<WatchPoint | null>(null)

  useEffect(() => {
    api.get<Summary>('/dashboard/summary').then((r) => setSummary(r.data))
    api.get<Recommendation>('/ai/recommend').then((r) => setRecommendation(r.data))
  }, [])

  async function handleSimulateWatch() {
    const { data } = await api.post<WatchPoint>('/watch/simulate')
    setWatch(data)
  }

  return (
    <div>
      <ScreenHeader title="Прогресс" subtitle="Статистика и рекомендации" />

      <div className="stat-chip-row">
        <div className="stat-chip">
          <div className="value calm">{summary?.total_workouts ?? '—'}</div>
          <div className="label">Всего тренировок</div>
        </div>
        <div className="stat-chip">
          <div className="value energy">{summary?.completed_workouts ?? '—'}</div>
          <div className="label">Завершено</div>
        </div>
      </div>

      <div className="card">
        <h2><Sparkles size={16} style={{ verticalAlign: -2, marginRight: 6 }} />AI-рекомендация</h2>
        {recommendation ? (
          <>
            <p style={{ fontWeight: 700, margin: '0 0 4px' }}>{recommendation.recommendation}</p>
            <p className="muted">{recommendation.reason}</p>
          </>
        ) : (
          <p className="muted">Загрузка...</p>
        )}
      </div>

      <div className="card">
        <h2><Watch size={16} style={{ verticalAlign: -2, marginRight: 6 }} />Умные часы (эмулятор)</h2>
        <button className="secondary" onClick={handleSimulateWatch}>Сгенерировать данные</button>
        {watch && (
          <p className="muted" style={{ marginTop: 12 }}>
            Шаги: {watch.steps} · Пульс: {watch.heart_rate} уд/мин
          </p>
        )}
      </div>
    </div>
  )
}
