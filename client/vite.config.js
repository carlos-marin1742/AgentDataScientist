import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/run-analysis": "http://localhost:8000",
      "/upload": "http://localhost:8000",
      "/generate-insights": "http://localhost:8000",
      "/generate-analysis": "http://localhost:8000",
    },
  },
})
