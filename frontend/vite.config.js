import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/ui/',
  server: {
    port: 5173,
    proxy: {
      '/send_message': 'http://localhost:8000',
      '/detect_emotion': 'http://localhost:8000',
      '/voice_command': 'http://localhost:8000',
      '/speak': 'http://localhost:8000',
      '/test_tts': 'http://localhost:8000',
      '/test_audio': 'http://localhost:8000',
      '/tts': 'http://localhost:8000',
      '/test_microphone': 'http://localhost:8000',
      '/emotion_detector': 'http://localhost:8000',
      '/conversation': 'http://localhost:8000',
      '/memory': 'http://localhost:8000',
      '/generate_report': 'http://localhost:8000',
      '/reports': 'http://localhost:8000',
      '/language': 'http://localhost:8000',
    },
  },
})
