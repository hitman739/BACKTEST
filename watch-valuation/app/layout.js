import './globals.css'
import { Providers } from './providers'

export const metadata = {
  title: 'LAPOMETRO - Valorador de Relojes',
  description: 'Encuentra el valor de mercado de relojes usados basado en ventas reales',
}

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>
        <div className="animated-bg"></div>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
