import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev-only: proxy /api to a locally running backend (docker compose uses nginx).
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
