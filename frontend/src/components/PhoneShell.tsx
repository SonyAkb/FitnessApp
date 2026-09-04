import { ReactNode } from 'react'

/**
 * Внешняя "рамка телефона". На реальном мобильном устройстве max-width
 * превышает ширину экрана, поэтому рамка растягивается на весь экран —
 * приложение выглядит нативно. На десктопе (разработка/демо) появляется
 * бесель, чтобы сразу считывалось как мобильное приложение.
 */
export default function PhoneShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-outer">
      <div className="phone-frame">{children}</div>
    </div>
  )
}
