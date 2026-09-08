import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// UI on 8026, api one above it. Proxying keeps the browser same-origin, so there is no CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8026,
    strictPort: true,
    proxy: { '/api': { target: 'http://127.0.0.1:8027', changeOrigin: true } },
  },
})
