import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    build: {
        outDir: 'dist',
        sourcemap: false,
    },
    server: {
        headers: {
            'Content-Security-Policy': "script-src 'self' 'unsafe-inline' 'unsafe-eval';",
            'Cache-Control': 'no-cache, no-store, must-revalidate', // отключаем кэш
            'Pragma': 'no-cache',
            'Expires': '0'
        },
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
})