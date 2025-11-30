/// <reference types="vitest" />
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/setupTests.ts',
    css: true,
  },
  server: {
    host: '0.0.0.0', // Allow external connections (for Docker)
    port: 5173,
    strictPort: true,
    watch: {
      usePolling: true, // Required for Docker volume mounts
    },
  },
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
});
