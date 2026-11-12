import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'

// The site serves the app on /av; the build writes assets to av_platform/public/frontend
// and the page template to av_platform/www/av.html.
export default defineConfig({
  plugins: [
    frappeui({
      frontendRoute: '/av',
      // The prototype bench runs in Docker, so there is no local bench to proxy to.
      frappeProxy: false,
      buildConfig: { indexHtmlPath: '../av_platform/www/av.html' },
    }),
    vue(),
  ],
})
