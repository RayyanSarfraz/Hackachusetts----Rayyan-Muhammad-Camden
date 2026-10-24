import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Bind to all interfaces so the dev server is reachable from outside the
    // container, and poll for changes (needed for file watching in Docker).
    host: true,
    port: 5173,
    watch: {
      usePolling: true,
    },
    // Proxy API calls to the Django backend during development.
    proxy: {
      '/api': {
        target: process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
