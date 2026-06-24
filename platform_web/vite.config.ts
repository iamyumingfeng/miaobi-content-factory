import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import { readFileSync } from 'node:fs'

// Read frontend version from VERSION file
function getFrontendVersion(): string {
  try {
    const versionPath = resolve(__dirname, 'VERSION')
    const version = readFileSync(versionPath, 'utf-8').trim()
    if (version) {
      return version
    }
  } catch (error) {
    console.error('Failed to read frontend version:', error)
  }
  return '1.0.0'
}

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory
  const env = loadEnv(mode, process.cwd(), '')

  const frontendVersion = getFrontendVersion()

  return {
    plugins: [vue()],
    define: {
      // Inject version into client-side code
      __FRONTEND_VERSION__: JSON.stringify(frontendVersion)
    },
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src')
      }
    },
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler',
          silenceDeprecations: ['legacy-js-api', 'import']
        }
      }
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      open: false,
      proxy: {
        '/api': {
          target: 'http://api:8000',
          changeOrigin: true,
          secure: false,
          configure: (proxy, options) => {
            proxy.on('proxyRes', (proxyRes, req, res) => {
              // 重写重定向响应中的 Location 头
              const location = proxyRes.headers['location']
              if (location && typeof location === 'string') {
                proxyRes.headers['location'] = location.replace('http://api:8000', '')
              }
            })
          }
        },
        '/cos': {
          target: 'http://api:8000',
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})
