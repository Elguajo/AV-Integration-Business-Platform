import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

// The shell is served on /av (ADR-006). The build writes assets to av_platform/public/frontend
// and the page template, with the boot data placeholder, to av_platform/www/av.html.
export default defineConfig({
  plugins: [
    frappeui({
      frontendRoute: '/av',
      // The prototype bench runs in Docker, so there is no local bench to proxy to.
      frappeProxy: false,
      buildConfig: {
        outDir: '../av_platform/public/frontend',
        baseUrl: '/assets/av_platform/frontend/',
        indexHtmlPath: '../av_platform/www/av.html',
      },
    }),
    vue(),
  ],
})
