import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const proxy = {
  '/api': {
    target: 'http://127.0.0.1:8000',
    changeOrigin: true,
  },
}

export default defineConfig({
  plugins: [react()],
  server: {
    // Fail clearly if an older server is still using the expected address.
    port: 5173,
    strictPort: true,
    proxy,
  },
  preview: {
    port: 5174,
    strictPort: true,
    proxy,
  },
})
