import { defineConfig } from 'vite';

export default defineConfig({
  // relative base so the build works on GitHub Pages under /<repo>/
  base: './',
  build: {
    target: 'es2022',
    chunkSizeWarningLimit: 1200,
  },
});
