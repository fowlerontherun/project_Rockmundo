import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: './setup.ts',
    include: ['**/*.{test,spec}.{js,ts,jsx,tsx}', '**/test_*.js']
  }
});
