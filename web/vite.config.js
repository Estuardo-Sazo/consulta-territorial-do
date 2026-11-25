// Configuración de Vite. https://vite.dev/config/
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5180,
    strictPort: true,
    // Proxy de desarrollo: "/api/..." se reenvía a FastAPI. El código usa rutas
    // relativas que funcionan igual en desarrollo y en Docker (allí lo hace nginx).
    proxy: { '/api': process.env.API_URL ?? 'http://localhost:8010' },
  },
})
