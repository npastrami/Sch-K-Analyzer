import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/upload': 'http://localhost:5000',
      '/extract_k1_1065': 'http://localhost:5000',
      '/refresh': 'http://localhost:5000',
      '/get_client_data': 'http://localhost:5000',
      '/download_csv': 'http://localhost:5000',
      '/download_all_documents': 'http://localhost:5000',
    },
  },
});