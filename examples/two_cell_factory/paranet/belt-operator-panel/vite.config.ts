import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3001, // Set the server to use port 3001
  },
  base: "./",
  build: {
    outDir: 'dist',
  },
});
