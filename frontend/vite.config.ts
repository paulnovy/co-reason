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
      '/experiments': 'http://localhost:8000',
      '/runs': 'http://localhost:8000',
    },
  },
  build: {
    // Keep chunks smaller (Vite warns when a single chunk > 500kB minified)
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined;

          // NOTE: keep react/react-dom in vendor to avoid circular chunks
          if (id.includes('/@tanstack/react-query/')) return 'react-query';
          if (id.includes('/@xyflow/react/')) return 'xyflow';
          if (id.includes('/framer-motion/')) return 'framer-motion';
          if (id.includes('/lucide-react/')) return 'icons';
          if (id.includes('/zustand/')) return 'zustand';

          return 'vendor';
        },
      },
    },
  },
})
