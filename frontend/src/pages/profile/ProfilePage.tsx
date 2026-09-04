import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bell, ChevronRight, CreditCard } from 'lucide-react'
import { api } from '../../api/client'
import { useAuth } from '../../context/AuthContext'
import ScreenHeader from '../../components/ScreenHeader'

/**
 * Модуль 4 (платежи/подписка) + вход в уведомления + выход из аккаунта.
 * Реальная Stripe test-интеграция вызывается из handleSubscribe — нужны
 * заполненные STRIPE_* переменные в backend/.env (см. docs/PLAN.md).
 */

interface Subscription {
  plan: string
  status: string
}

export default function ProfilePage() {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadingCheckout, setLoadingCheckout] = useState(false)

  useEffect(() => {
    api.get<Subscription>('/payments/subscription').then((r) => setSubscription(r.data))
  }, [])

  async function handleSubscribe() {
    setError(null)
    setLoadingCheckout(true)
    try {
      const { data } = await api.post<{ checkout_url: string }>('/payments/create-checkout-session')
      window.location.href = data.checkout_url
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Ошибка при создании checkout-сессии')
    } finally {
      setLoadingCheckout(false)
    }
  }

  return (
    <div>
      <ScreenHeader title="Профиль" />

      <div className="card">
        <h2><CreditCard size={16} style={{ verticalAlign: -2, marginRight: 6 }} />Подписка</h2>
        <p className="muted" style={{ marginBottom: 12 }}>
          План: <strong style={{ color: 'var(--text)' }}>{subscription?.plan ?? '...'}</strong>
          {' · '}Статус: <strong style={{ color: 'var(--text)' }}>{subscription?.status ?? '...'}</strong>
        </p>
        {error && <div className="error">{error}</div>}
        {subscription?.plan !== 'pro' && (
          <button className="primary" onClick={handleSubscribe} disabled={loadingCheckout}>
            {loadingCheckout ? 'Открываем Stripe...' : 'Оформить Pro (тестовая оплата)'}
          </button>
        )}
        <p className="muted" style={{ marginTop: 10 }}>
          Тестовая карта Stripe: 4242 4242 4242 4242, любая будущая дата, любой CVC.
        </p>
      </div>

      <div className="card">
        <div className="chevron-row" onClick={() => navigate('/notifications')}>
          <span className="label"><Bell size={18} /> Уведомления</span>
          <ChevronRight size={18} color="var(--text-faint)" />
        </div>
      </div>

      <button className="danger" onClick={logout}>Выйти из аккаунта</button>
    </div>
  )
}
