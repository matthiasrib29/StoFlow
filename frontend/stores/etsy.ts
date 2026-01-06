import { defineStore } from 'pinia'
import { etsyLogger } from '~/utils/logger'

interface EtsyTokens {
  access_token: string
  refresh_token: string
  expires_at: string
}

interface EtsyShop {
  shop_id: number
  shop_name: string
  url: string
  currency_code: string
}

interface EtsyAccount {
  user_id: number
  email: string
  first_name?: string
  last_name?: string
}

interface EtsyListing {
  listing_id: number
  title: string
  price: {
    amount: number
    divisor: number
    currency_code: string
  }
  quantity: number
  state: string
  url: string
}

interface EtsyStats {
  total_listings: number
  active_listings: number
  sold_listings: number
  shop_rating?: number
  total_sales?: number
}

interface EtsyState {
  isConnected: boolean
  isConnecting: boolean
  isLoading: boolean
  isLoadingListings: boolean
  tokens: EtsyTokens | null
  account: EtsyAccount | null
  shop: EtsyShop | null
  listings: EtsyListing[]
  stats: EtsyStats | null
  connectionError: string | null
}

export const useEtsyStore = defineStore('etsy', {
  state: (): EtsyState => ({
    isConnected: false,
    isConnecting: false,
    isLoading: false,
    isLoadingListings: false,
    tokens: null,
    account: null,
    shop: null,
    listings: [],
    stats: null,
    connectionError: null
  }),

  getters: {
    hasActiveListings: (state) => (state.stats?.active_listings ?? 0) > 0,
    totalListings: (state) => state.stats?.total_listings ?? 0,
    shopUrl: (state) => state.shop?.url ?? null
  },

  actions: {
    /**
     * Vérifie le statut de connexion depuis l'API
     */
    async checkConnectionStatus() {
      try {
        const api = useApi()
        const status = await api.get<{
          connected: boolean
          account?: EtsyAccount
          shop?: EtsyShop
          tokens?: EtsyTokens
        }>('/api/etsy/status')

        if (status.connected) {
          this.isConnected = true
          this.account = status.account ?? null
          this.shop = status.shop ?? null
          this.tokens = status.tokens ?? null
        } else {
          this.isConnected = false
        }

        return status
      } catch (error) {
        etsyLogger.error('Erreur vérification statut Etsy', { error })
        this.isConnected = false
        throw error
      }
    },

    /**
     * Initie le processus OAuth avec popup
     */
    async initiateOAuth() {
      this.isConnecting = true
      this.connectionError = null

      try {
        const api = useApi()
        const { authorization_url } = await api.get<{ authorization_url: string }>('/api/etsy/authorize')

        // Ouvrir popup OAuth
        const width = 600
        const height = 700
        const left = window.screen.width / 2 - width / 2
        const top = window.screen.height / 2 - height / 2

        const popup = window.open(
          authorization_url,
          'EtsyOAuth',
          `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no`
        )

        if (!popup) {
          throw new Error('Impossible d\'ouvrir la fenêtre d\'authentification. Veuillez autoriser les popups.')
        }

        // Écouter le message du callback
        return new Promise((resolve, reject) => {
          const messageHandler = async (event: MessageEvent) => {
            if (event.origin !== window.location.origin) return

            if (event.data.type === 'etsy-oauth-success') {
              window.removeEventListener('message', messageHandler)
              popup.close()

              try {
                await this.exchangeCodeForTokens(event.data.code)
                resolve(true)
              } catch (error) {
                reject(error)
              }
            } else if (event.data.type === 'etsy-oauth-error') {
              window.removeEventListener('message', messageHandler)
              popup.close()
              reject(new Error(event.data.error || 'Échec de l\'authentification'))
            }
          }

          window.addEventListener('message', messageHandler)

          // Timeout après 5 minutes
          setTimeout(() => {
            window.removeEventListener('message', messageHandler)
            if (!popup.closed) {
              popup.close()
            }
            reject(new Error('Délai d\'authentification expiré'))
          }, 5 * 60 * 1000)
        })
      } catch (error: any) {
        this.connectionError = error.message
        throw error
      } finally {
        this.isConnecting = false
      }
    },

    /**
     * Échange le code OAuth contre les tokens
     */
    async exchangeCodeForTokens(code: string) {
      this.isConnecting = true

      try {
        const api = useApi()
        const response = await api.post<{
          tokens: EtsyTokens
          account: EtsyAccount
          shop: EtsyShop
        }>('/api/etsy/callback', { code })

        this.tokens = response.tokens
        this.account = response.account
        this.shop = response.shop
        this.isConnected = true

        // Charger les données supplémentaires
        await Promise.all([
          this.fetchListings(),
          this.fetchStats()
        ])

        return response
      } catch (error: any) {
        this.connectionError = error.message
        throw error
      } finally {
        this.isConnecting = false
      }
    },

    /**
     * Déconnecte le compte Etsy
     */
    async disconnect() {
      this.isLoading = true

      try {
        const api = useApi()
        await api.post('/api/etsy/disconnect')

        // Réinitialiser le state
        this.$reset()
      } catch (error: any) {
        etsyLogger.error('Erreur déconnexion Etsy', { error })
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Récupère les listings de la boutique
     */
    async fetchListings() {
      this.isLoadingListings = true

      try {
        const api = useApi()
        const listings = await api.get<EtsyListing[]>('/api/etsy/listings')
        this.listings = listings ?? []
      } catch (error) {
        etsyLogger.error('Erreur chargement listings Etsy', { error })
        throw error
      } finally {
        this.isLoadingListings = false
      }
    },

    /**
     * Récupère les statistiques de la boutique
     */
    async fetchStats() {
      try {
        const api = useApi()
        const stats = await api.get<EtsyStats>('/api/etsy/stats')
        this.stats = stats
      } catch (error) {
        etsyLogger.error('Erreur chargement stats Etsy', { error })
        throw error
      }
    },

    /**
     * Crée un listing sur Etsy
     */
    async createListing(listingData: any) {
      this.isLoading = true

      try {
        const api = useApi()
        const newListing = await api.post('/api/etsy/listings', listingData)

        // Recharger les listings et stats
        await Promise.all([
          this.fetchListings(),
          this.fetchStats()
        ])

        return newListing
      } catch (error: any) {
        etsyLogger.error('Erreur création listing Etsy', { error })
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Met à jour un listing existant
     */
    async updateListing(listingId: number, updates: Partial<EtsyListing>) {
      this.isLoading = true

      try {
        const api = useApi()
        const updatedListing = await api.put<EtsyListing>(`/api/etsy/listings/${listingId}`, updates)

        // Mettre à jour localement
        const index = this.listings.findIndex(l => l.listing_id === listingId)
        if (index !== -1 && updatedListing) {
          this.listings[index] = updatedListing
        }

        return updatedListing
      } catch (error: any) {
        etsyLogger.error('Erreur mise à jour listing Etsy', { error })
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Supprime un listing
     */
    async deleteListing(listingId: number) {
      this.isLoading = true

      try {
        const api = useApi()
        await api.delete(`/api/etsy/listings/${listingId}`)

        // Retirer localement
        this.listings = this.listings.filter(l => l.listing_id !== listingId)

        // Recharger les stats
        await this.fetchStats()
      } catch (error: any) {
        etsyLogger.error('Erreur suppression listing Etsy', { error })
        throw error
      } finally {
        this.isLoading = false
      }
    }
  }
})
