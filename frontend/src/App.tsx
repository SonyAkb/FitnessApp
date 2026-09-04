import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import PhoneShell from './components/PhoneShell'

import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import HomePage from './pages/home/HomePage'
import SchedulePage from './pages/schedule/SchedulePage'
import TrainingPage from './pages/training/TrainingPage'
import ProgressPage from './pages/progress/ProgressPage'
import ProfilePage from './pages/profile/ProfilePage'
import NotificationsPage from './pages/notifications/NotificationsPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        {/* Единая "рамка телефона" на всё приложение — и для auth-экранов, и для основных */}
        <PhoneShell>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route element={<ProtectedRoute />}>
              {/* Экраны с нижним таб-баром (5 вкладок) */}
              <Route element={<Layout />}>
                <Route path="/home" element={<HomePage />} />
                <Route path="/schedule" element={<SchedulePage />} />
                <Route path="/training" element={<TrainingPage />} />
                <Route path="/progress" element={<ProgressPage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Route>

              {/* Экран без таб-бара — открывается "поверх", с кнопкой "назад" */}
              <Route
                path="/notifications"
                element={
                  <div className="screen-content">
                    <NotificationsPage />
                  </div>
                }
              />

              <Route path="/" element={<Navigate to="/home" replace />} />
            </Route>

            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        </PhoneShell>
      </AuthProvider>
    </BrowserRouter>
  )
}
