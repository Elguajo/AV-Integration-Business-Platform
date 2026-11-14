import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

// The role screens run inside Frappe Desk (ADR-004). The build writes one JavaScript entry
// and its chunks to av_platform/public/frontend; av_platform.desk reads the Vite manifest at
// boot so Desk pages can load the current hashed files.
export default defineConfig({
  plugins: [
    frappeui({
      // There is no standalone page and no local bench to proxy to (the bench runs in Docker).
      frappeProxy: false,
      jinjaBootData: false,
      buildConfig: false,
    }),
    vue(),
  ],
  base: '/assets/av_platform/frontend/',
  build: {
    outDir: '../av_platform/public/frontend',
    emptyOutDir: true,
    manifest: true,
    sourcemap: false,
    rollupOptions: { input: 'src/desk.ts' },
  },
})
