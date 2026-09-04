import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell } from 'lucide-react'
import { api } from '../../api/client'
import ScreenHeader from '../../components/ScreenHeader'

/**
 * Главный экран — герой продукта (Модуль 3, "Персонаж").
 * Питомец сейчас нарисован как простое "блоб"-существо (SVG-заглушка).
 * TODO(module-3): заменить <PetAvatar> на настоящего анимированного
 * персонажа (спрайты/Lottie/rive) — сама механика энергии/уровня уже
 * подключена к реальным данным и менять её не придётся.
 */

interface Companion {
  name: string
  level: number
  energy: number
  mood: string
}

interface Summary {
  total_workouts: number
  current_streak_days: number
}

const moodLabel: Record<string, string> = {
  sad: 'Грустит — давно не было тренировок',
  neutral: 'Спокоен',
  happy: 'Доволен',
  excited: 'В восторге!',
}

function PetAvatar() {
  return (
    <svg viewBox="0 0 120 120" width="132" height="132">
      <defs>
        <linearGradient id="petBodyGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#22e6b0" />
          <stop offset="100%" stopColor="#b6ff3c" />
        </linearGradient>
      </defs>
      <ellipse cx="60" cy="68" rx="46" ry="40" fill="url(#petBodyGrad)" />
      <ellipse cx="60" cy="32" rx="29" ry="25" fill="url(#petBodyGrad)" />
      <circle cx="47" cy="31" r="5" fill="#0b0e14" />
      <circle cx="73" cy="31" r="5" fill="#0b0e14" />
      <ellipse cx="60" cy="42" rx="5" ry="3" fill="#0b0e14" opacity="0.25" />
    </svg>
  )
}

function EnergyRing({ energy }: { energy: number }) {
  const r = 90
  const circumference = 2 * Math.PI * r
  const offset = circumference * (1 - energy / 100)
  return (
    <svg viewBox="0 0 200 200">
      <defs>
        <linearGradient id="petRingGrad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#22e6b0" />
          <stop offset="100%" stopColor="#b6ff3c" />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r={r} fill="none" stroke="#262b38" strokeWidth="10" />
      <circle
        cx="100"
        cy="100"
        r={r}
        fill="none"
        stroke="url(#petRingGrad)"
        strokeWidth="10"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        style={{ transition: 'stroke-dashoffset 0.6s ease' }}
      />
    </svg>
  )
}

export default function HomePage() {
  const navigate = useNavigate()
  const [companion, setCompanion] = useState<Companion | null>(null)
  const [summary, setSummary] = useState<Summary | null>(null)

  async function load() {
    const [companionRes, summaryRes] = await Promise.all([
      api.get<Companion>('/companion/me'),
      api.get<Summary>('/dashboard/summary'),
    ])
    setCompanion(companionRes.data)
    setSummary(summaryRes.data)
  }

  useEffect(() => {
    load()
  }, [])

  async function handleInteract() {
    const { data } = await api.post<Companion>('/companion/interact')
    setCompanion(data)
  }

  return (
    <div>
      <ScreenHeader
        title="Привет!"
        subtitle="Вот как дела у твоего питомца"
        right={
          <button className="icon-btn" onClick={() => navigate('/notifications')} aria-label="Уведомления">
            <Bell size={20} strokeWidth={2} />
          </button>
        }
      />

      <div className="pet-stage">
        <div className="pet-aura" />
        <div className="pet-ring-wrap">
          <EnergyRing energy={companion?.energy ?? 0} />
          <div className="pet-avatar">
            <PetAvatar />
          </div>
        </div>
        <div className="pet-name">{companion?.name ?? 'Загрузка...'}</div>
        <div className="pet-meta">
          Уровень {companion?.level ?? '—'} · {moodLabel[companion?.mood ?? ''] ?? ''}
        </div>
      </div>

      <div className="stat-chip-row">
        <div className="stat-chip">
          <div className="value streak">{summary?.current_streak_days ?? '—'}</div>
          <div className="label">Дней подряд</div>
        </div>
        <div className="stat-chip">
          <div className="value calm">{summary?.total_workouts ?? '—'}</div>
          <div className="label">Тренировок всего</div>
        </div>
      </div>

      <button className="primary" onClick={handleInteract}>Погладить питомца</button>
      <p className="muted" style={{ textAlign: 'center', marginTop: 12 }}>
        Энергия растёт, когда ты завершаешь тренировки во вкладке «Тренировки»
      </p>
    </div>
  )
}
