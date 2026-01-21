import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { crx } from '@crxjs/vite-plugin';

// Use manifest.dev.json for development, manifest.json for production
// This allows localhost origins in dev while keeping the production manifest clean for Chrome Web Store
const isDev = process.env.NODE_ENV !== 'production';
const manifest = isDev
  ? require('./manifest.dev.json')
  : require('./manifest.json');

export default defineConfig({
  plugins: [
    vue(),
    crx({ manifest })
  ],
  build: {
    rollupOptions: {
      input: {
        popup: 'src/popup/index.html',
        options: 'src/options/index.html'
      }
    }
  }
});
