/**
 * Plugin to set dev environment indicator (favicon + title)
 * Only runs in client mode to avoid SSR issues
 */
import { createLogger } from '~/utils/logger'

const devLogger = createLogger({ prefix: 'DevEnv' })

export default defineNuxtPlugin(() => {
  const config = useRuntimeConfig()
  const devEnv = config.public.devEnv

  if (devEnv) {
    // Update favicon
    const faviconPath = `/favicon-dev${devEnv}.svg`

    // Remove existing favicon links
    const existingFavicons = document.querySelectorAll('link[rel="icon"]')
    existingFavicons.forEach(link => link.remove())

    // Add new favicon link
    const link = document.createElement('link')
    link.rel = 'icon'
    link.type = 'image/svg+xml'
    link.href = faviconPath
    document.head.appendChild(link)

    // Update page title to include dev environment number
    const originalTitle = document.title
    document.title = `[DEV ${devEnv}] ${originalTitle}`

    devLogger.info(`Running in dev environment ${devEnv}`)
  }
})
