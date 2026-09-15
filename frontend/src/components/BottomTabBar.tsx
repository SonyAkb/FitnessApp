import { NavLink } from 'react-router-dom'
import { PawPrint, CalendarDays, Dumbbell, LineChart, User } from 'lucide-react'

/**
 * Нижний таб-бар вместо бокового/выпадающего меню — привычный паттерн
 * мобильных приложений (Apple Fitness, Genopets и т.п.). 5 вкладок —
 * жёсткий потолок для мобильного таб-бара, чтобы иконки не теснились.
 */
const tabs = [
  { to: '/home', label: 'Питомец', icon: PawPrint },
  { to: '/schedule', label: 'План', icon: CalendarDays },
  { to: '/training', label: 'Тренировки', icon: Dumbbell },
  { to: '/progress', label: 'Прогресс', icon: LineChart },
  { to: '/profile', label: 'Профиль', icon: User },
]

export default function BottomTabBar() {
  return (
    <nav className="tab-bar">
      {tabs.map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} className={({ isActive }) => `tab-item ${isActive ? 'active' : ''}`}>
          <Icon strokeWidth={2.2} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
