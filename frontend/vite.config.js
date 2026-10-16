import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// In development, forward /api calls to the local FastAPI server so the
// frontend can use the same relative URLs it uses behind Nginx and Ingress.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
