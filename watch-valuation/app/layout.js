export const metadata = {
  title: 'Valorador de Relojes',
  description: 'Encuentra el valor de mercado de relojes usados basado en ventas reales',
}

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body style={{ margin: 0, padding: 0 }}>{children}</body>
    </html>
  )
}
