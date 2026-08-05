import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

const BACKEND = process.env.VITE_BACKEND ?? 'http://127.0.0.1:8000'

const proxyTargets = [
  '/auth',
  '/organizations',
  '/persons',
  '/resource',
  '/resource-warehouse',
  '/assets',
  '/warehouse',
  '/warehouses',
  '/transactions',
  '/transaction',
  '/party',
  '/person',
  '/personnel',
  '/summary',
  '/chat',
  '/seller',
  '/campaigns',
  '/spaces',
  '/health',
]

const proxies = Object.fromEntries(
  proxyTargets.map((path) => [
    path,
    { target: BACKEND, changeOrigin: true, secure: false },
  ]),
)

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    proxy: proxies,
  },
  test: {
    environment: 'jsdom',
    globals: true,
    css: false,
  },
})
