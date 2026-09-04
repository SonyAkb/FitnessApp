import { Outlet } from 'react-router-dom'
import BottomTabBar from './BottomTabBar'

/**
 * Оболочка защищённых экранов: скроллящийся контент + фиксированный
 * нижний таб-бар. Общая рамка телефона задаётся выше, в PhoneShell (App.tsx).
 */
export default function Layout() {
  return (
    <>
      <div className="screen-content with-tabbar">
        <Outlet />
      </div>
      <BottomTabBar />
    </>
  )
}
