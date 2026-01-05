/**
 * Composable for intelligent breadcrumb generation.
 * Generates breadcrumbs based on current route path.
 */

interface BreadcrumbItem {
  label: string
  path?: string
}

export function useBreadcrumbs() {
  const route = useRoute()

  const breadcrumbs = computed<BreadcrumbItem[]>(() => {
    const path = route.path
    const crumbs: BreadcrumbItem[] = []

    // Subscription pages
    if (path.startsWith('/dashboard/subscription')) {
      crumbs.push({ label: 'Abonnement', path: '/dashboard/subscription' })

      // Credits details page
      if (path.match(/\/subscription\/credits\/(\d+)/)) {
        const credits = route.params.credits
        crumbs.push({ label: `Pack ${credits} crédits` })
      }
      // Upgrade details page
      else if (path.match(/\/subscription\/upgrade\/([^/]+)/)) {
        const tier = route.params.tier as string
        crumbs.push({ label: `Abonnement ${tier.toUpperCase()}` })
      }
      // Payment page
      else if (path.includes('/payment')) {
        const type = route.query.type as string
        if (type === 'credits') {
          const credits = route.query.credits
          crumbs.push({ label: `Pack ${credits} crédits`, path: `/dashboard/subscription/credits/${credits}` })
        } else if (type === 'upgrade') {
          const tier = route.query.tier as string
          crumbs.push({ label: `Abonnement ${tier?.toUpperCase()}`, path: `/dashboard/subscription/upgrade/${tier}` })
        }
        crumbs.push({ label: 'Paiement' })
      }
    }
    // Products pages
    else if (path.startsWith('/dashboard/products')) {
      crumbs.push({ label: 'Produits', path: '/dashboard/products' })

      if (path.includes('/create')) {
        crumbs.push({ label: 'Créer un produit' })
      } else if (route.params.sku) {
        crumbs.push({ label: `Produit ${route.params.sku}` })
      }
    }
    // Platforms pages
    else if (path.startsWith('/dashboard/platforms')) {
      crumbs.push({ label: 'Plateformes', path: '/dashboard/platforms' })

      const subSectionLabels: Record<string, string> = {
        'publications': 'Publications',
        'products': 'Annonces',
        'sales': 'Ventes',
        'shipments': 'Expéditions',
        'analytics': 'Analytiques',
        'settings': 'Paramètres',
        'messages': 'Messages'
      }

      if (path.includes('/vinted')) {
        crumbs.push({ label: 'Vinted', path: '/dashboard/platforms/vinted' })
        const subSection = path.split('/vinted/')[1]
        if (subSection && subSectionLabels[subSection]) {
          crumbs.push({ label: subSectionLabels[subSection] })
        }
      } else if (path.includes('/ebay')) {
        crumbs.push({ label: 'eBay', path: '/dashboard/platforms/ebay' })
        const subSection = path.split('/ebay/')[1]
        if (subSection && subSectionLabels[subSection]) {
          crumbs.push({ label: subSectionLabels[subSection] })
        }
      } else if (path.includes('/etsy')) {
        crumbs.push({ label: 'Etsy', path: '/dashboard/platforms/etsy' })
        const subSection = path.split('/etsy/')[1]
        if (subSection && subSectionLabels[subSection]) {
          crumbs.push({ label: subSectionLabels[subSection] })
        }
      }
    }
    // Admin pages
    else if (path.startsWith('/dashboard/admin')) {
      crumbs.push({ label: 'Administration', path: '/dashboard/admin' })

      const adminLabels: Record<string, string> = {
        'users': 'Utilisateurs',
        'attributes': 'Données de référence',
        'audit-logs': 'Logs d\'audit'
      }

      const segments = path.split('/').filter(Boolean)
      const lastSegment = segments[segments.length - 1]
      if (lastSegment && lastSegment !== 'admin' && adminLabels[lastSegment]) {
        crumbs.push({ label: adminLabels[lastSegment] })
      }
    }
    // Settings pages
    else if (path.startsWith('/dashboard/settings')) {
      crumbs.push({ label: 'Paramètres', path: '/dashboard/settings' })

      const settingsLabels: Record<string, string> = {
        'security': 'Sécurité',
        'notifications': 'Notifications',
        'integrations': 'Intégrations'
      }

      const segments = path.split('/').filter(Boolean)
      const lastSegment = segments[segments.length - 1]
      if (lastSegment && lastSegment !== 'settings' && settingsLabels[lastSegment]) {
        crumbs.push({ label: settingsLabels[lastSegment] })
      }
    }
    // Other pages
    else if (path.startsWith('/dashboard/')) {
      const segments = path.split('/').filter(Boolean)
      if (segments.length > 1) {
        const pageName = segments[segments.length - 1]
        if (pageName) {
          const labels: Record<string, string> = {
            'publications': 'Publications',
            'stats': 'Statistiques',
            'settings': 'Paramètres'
          }
          crumbs.push({ label: labels[pageName] || pageName })
        }
      }
    }

    return crumbs
  })

  return {
    breadcrumbs
  }
}
