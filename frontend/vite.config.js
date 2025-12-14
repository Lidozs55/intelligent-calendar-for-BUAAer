import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  base: './', // 使用相对路径构建
  plugins: [vue()],
  server: {
    port: 3000,
    host: '0.0.0.0', // 允许外部访问开发服务器
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
