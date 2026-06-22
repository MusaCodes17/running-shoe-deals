import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    // Proxy API requests to the FastAPI backend during development so the
    // frontend can call relative `/api/...` paths without CORS concerns.
    proxy: {
      // Use 127.0.0.1 (not localhost) so Node 18 doesn't resolve to IPv6 ::1,
      // which the IPv4-only backend refuses.
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
