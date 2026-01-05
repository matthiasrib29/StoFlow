import { defineStore } from 'pinia'

interface Publication {
  id: number
  product_id: number
  product_title: string
  platform: 'vinted' | 'ebay' | 'etsy'
  status: 'draft' | 'published' | 'sold' | 'archived'
  platform_url?: string
  published_at?: string
  sold_at?: string
  price: number
  views?: number
  likes?: number
}

interface Integration {
  platform: 'vinted' | 'ebay' | 'etsy'
  name: string
  is_connected: boolean
  last_sync?: string
  total_publications?: number
  active_publications?: number
  views?: number
  sales?: number
}

interface Activity {
  id: number
  type: 'product_created' | 'product_updated' | 'product_published' | 'product_sold'
  title: string
  description: string
  timestamp: string
  icon: string
  color: string
}

export const usePublicationsStore = defineStore('publications', {
  state: () => ({
    publications: [] as Publication[],
    integrations: [
      {
        platform: 'vinted' as const,
        name: 'Vinted',
        is_connected: false,
        total_publications: 0,
        active_publications: 0
      },
      {
        platform: 'ebay' as const,
        name: 'eBay',
        is_connected: false,
        total_publications: 0,
        active_publications: 0
      },
      {
        platform: 'etsy' as const,
        name: 'Etsy',
        is_connected: false,
        total_publications: 0,
        active_publications: 0
      }
    ] as Integration[],
    recentActivity: [] as Activity[],
    isLoading: false,
    error: null as string | null
  }),

  getters: {
    connectedIntegrations: (state) => state.integrations.filter(i => i.is_connected),
    totalPublications: (state) => state.publications.length,
    activePublications: (state) => state.publications.filter(p => p.status === 'published').length,
    soldPublications: (state) => state.publications.filter(p => p.status === 'sold').length
  },

  actions: {
    /**
     * Charger le statut des intégrations depuis les APIs individuelles
     */
    async fetchIntegrationsStatus() {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()

        // Fetch Vinted status
        try {
          const vintedStatus = await api.get<{
            is_connected: boolean
            last_sync?: string
          }>('/api/vinted/status')

          const vintedIntegration = this.integrations.find(i => i.platform === 'vinted')
          if (vintedIntegration) {
            vintedIntegration.is_connected = vintedStatus.is_connected
            vintedIntegration.last_sync = vintedStatus.last_sync
          }
        } catch (e) {
          console.warn('Vinted status fetch failed:', e)
        }

        // Fetch eBay status
        try {
          const ebayStatus = await api.get<{
            connected: boolean
          }>('/api/ebay/status')

          const ebayIntegration = this.integrations.find(i => i.platform === 'ebay')
          if (ebayIntegration) {
            ebayIntegration.is_connected = ebayStatus.connected
          }
        } catch (e) {
          console.warn('eBay status fetch failed:', e)
        }

        // Etsy is disabled for now
        const etsyIntegration = this.integrations.find(i => i.platform === 'etsy')
        if (etsyIntegration) {
          etsyIntegration.is_connected = false
        }

        return { integrations: this.integrations }
      } catch (error: any) {
        console.error('Erreur chargement statut intégrations:', error)
        this.error = error.message
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Charger les publications depuis les APIs des plateformes
     */
    async fetchPublications() {
      this.isLoading = true
      this.error = null

      try {
        const api = useApi()
        const allPublications: Publication[] = []

        // Récupérer les produits Vinted
        try {
          const vintedResponse = await api.get<{
            products: any[]
            total: number
          }>('/api/vinted/products?limit=100')

          if (vintedResponse?.products) {
            const vintedPublications = vintedResponse.products.map((p: any) => ({
              id: p.id,
              product_id: p.id,
              product_title: p.title || 'Sans titre',
              platform: 'vinted' as const,
              status: p.status === 'sold' ? 'sold' as const : 'published' as const,
              platform_url: p.url,
              published_at: p.date,
              price: p.price || 0,
              views: p.view_count || 0,
              likes: p.favourite_count || 0
            }))
            allPublications.push(...vintedPublications)
          }
        } catch (error) {
          console.warn('Erreur récupération produits Vinted:', error)
        }

        // TODO: Ajouter récupération eBay et Etsy quand implémentés

        this.publications = allPublications
      } catch (error: any) {
        this.error = error.message
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Charger l'activité récente
     * TODO: Implémenter route backend /api/activity quand disponible
     */
    async fetchRecentActivity() {
      this.isLoading = true

      try {
        // TODO: Remplacer par appel API quand route disponible
        // const api = useApi()
        // const response = await api.get('/api/activity?limit=10')
        // this.recentActivity = response.activities

        // Pour l'instant, générer activité depuis les publications
        const activities: Activity[] = []

        this.publications.slice(0, 5).forEach((pub, index) => {
          activities.push({
            id: index + 1,
            type: pub.status === 'sold' ? 'product_sold' : 'product_published',
            title: pub.status === 'sold' ? 'Produit vendu' : 'Produit publié',
            description: `${pub.product_title} sur ${pub.platform}`,
            timestamp: pub.published_at || new Date().toISOString(),
            icon: pub.status === 'sold' ? 'pi-check-circle' : 'pi-send',
            color: pub.status === 'sold' ? 'primary' : 'blue'
          })
        })

        this.recentActivity = activities
      } catch (error: any) {
        this.error = error.message
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Vérifier/Rafraîchir le statut de connexion d'une intégration
     * Note: La connexion réelle est gérée par le plugin browser
     */
    async connectIntegration(platform: Integration['platform']) {
      const integration = this.integrations.find(i => i.platform === platform)
      if (!integration) return

      this.isLoading = true

      try {
        const api = useApi()

        if (platform === 'vinted') {
          // Vérifier le statut de connexion Vinted
          const status = await api.get<{
            is_connected: boolean
            vinted_user_id?: number
            login?: string
            last_sync?: string
          }>('/api/vinted/status')

          integration.is_connected = status.is_connected
          integration.last_sync = status.last_sync

          if (!status.is_connected) {
            throw new Error('Vinted non connecté. Ouvrez le plugin browser et connectez-vous à Vinted.')
          }
        } else if (platform === 'ebay') {
          // Vérifier via OAuth - redirige vers flow OAuth si pas connecté
          const status = await api.get<{ is_connected: boolean }>('/api/ebay/status')
          integration.is_connected = status.is_connected
        } else if (platform === 'etsy') {
          const status = await api.get<{ is_connected: boolean }>('/api/etsy/status')
          integration.is_connected = status.is_connected
        }

        return { success: integration.is_connected }
      } catch (error: any) {
        this.error = error.message
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Déconnecter une intégration
     */
    async disconnectIntegration(platform: Integration['platform']) {
      const integration = this.integrations.find(i => i.platform === platform)
      if (!integration) return

      this.isLoading = true

      try {
        const api = useApi()

        if (platform === 'vinted') {
          // Pour Vinted, on supprime juste la connexion côté backend
          await api.delete('/api/vinted/disconnect')
        } else if (platform === 'ebay') {
          await api.delete('/api/ebay/disconnect')
        } else if (platform === 'etsy') {
          await api.delete('/api/etsy/disconnect')
        }

        // Reset local state
        integration.is_connected = false
        integration.last_sync = undefined
        integration.total_publications = 0
        integration.active_publications = 0

        return { success: true }
      } catch (error: any) {
        // Même si l'API échoue, reset le state local
        integration.is_connected = false
        integration.last_sync = undefined
        console.warn(`Erreur déconnexion ${platform}:`, error.message)
        return { success: true }
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Mettre à jour manuellement le statut d'une intégration (appelé depuis les pages)
     */
    updateIntegrationStatus(platform: Integration['platform'], status: Partial<Integration>) {
      const integration = this.integrations.find(i => i.platform === platform)
      if (integration) {
        Object.assign(integration, status)
      }
    }
  }
})
