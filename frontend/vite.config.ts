import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/variables': 'http://localhost:8000',
      '/relationships': 'http://localhost:8000',
    },
  },
})
