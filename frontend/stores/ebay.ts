import { defineStore } from 'pinia'

/**
 * Types pour l'intégration eBay
 */
export interface EbayAccount {
  userId: string
  username: string
  email: string
  accountType: 'individual' | 'business'
  registrationDate: string
  sellerLevel: 'top_rated' | 'above_standard' | 'standard' | 'below_standard'
  feedbackScore: number
  feedbackPercentage: number
  storeName?: string
  storeUrl?: string
  // Nouvelles infos depuis l'API Commerce Identity
  firstName?: string
  lastName?: string
  businessName?: string
  phone?: string
  address?: string
  marketplace?: string
  programs?: Array<{ programType: string }>
  fulfillmentPoliciesCount?: number
  accessTokenExpiresAt?: string
  sandboxMode?: boolean
}

export interface EbayTokens {
  accessToken: string
  refreshToken: string
  expiresAt: string
  scope: string[]
}

export interface EbayShippingPolicy {
  id: string
  name: string
  description?: string
  type: 'flat_rate' | 'calculated' | 'free_shipping'
  domesticShipping: {
    service: string
    cost: number
    additionalCost?: number
    handlingTime: number
  }
  internationalShipping?: {
    enabled: boolean
    service?: string
    cost?: number
    countries?: string[]
  }
  isDefault: boolean
}

export interface EbayReturnPolicy {
  id: string
  name: string
  description?: string
  returnsAccepted: boolean
  returnPeriod: number // jours
  refundMethod: 'money_back' | 'exchange' | 'store_credit'
  shippingCostPaidBy: 'buyer' | 'seller'
  isDefault: boolean
}

export interface EbayPaymentPolicy {
  id: string
  name: string
  description?: string
  paymentMethods: ('paypal' | 'credit_card' | 'bank_transfer')[]
  immediatePay: boolean
  isDefault: boolean
}

export interface EbayCategory {
  id: string
  name: string
  parentId?: string
  level: number
  leafCategory: boolean
  children?: EbayCategory[]
}

export interface EbaySyncSettings {
  autoSync: boolean
  syncInterval: number // en minutes
  syncStock: boolean
  syncPrices: boolean
  syncDescriptions: boolean
  lastSyncAt?: string
  nextSyncAt?: string
}

export interface EbayStats {
  activeLis: number
  totalViews: number
  totalWatchers: number
  totalSales: number
  totalRevenue: number
  averagePrice: number
  conversionRate: number
  impressions: number
}

export const useEbayStore = defineStore('ebay', {
  state: () => ({
    // Connexion
    isConnected: false,
    isConnecting: false,
    connectionError: null as string | null,

    // Compte
    account: null as EbayAccount | null,
    tokens: null as EbayTokens | null,

    // Politiques
    shippingPolicies: [] as EbayShippingPolicy[],
    returnPolicies: [] as EbayReturnPolicy[],
    paymentPolicies: [] as EbayPaymentPolicy[],

    // Catégories
    categories: [] as EbayCategory[],
    selectedCategories: [] as string[],

    // Paramètres de sync
    syncSettings: {
      autoSync: true,
      syncInterval: 30,
      syncStock: true,
      syncPrices: true,
      syncDescriptions: false,
      lastSyncAt: undefined,
      nextSyncAt: undefined
    } as EbaySyncSettings,

    // Stats
    stats: {
      activeLis: 0,
      totalViews: 0,
      totalWatchers: 0,
      totalSales: 0,
      totalRevenue: 0,
      averagePrice: 0,
      conversionRate: 0,
      impressions: 0
    } as EbayStats,

    // Loading states
    isLoading: false,
    isLoadingPolicies: false,
    isLoadingCategories: false,
    isSyncing: false
  }),

  getters: {
    hasValidTokens(): boolean {
      if (!this.tokens) return false
      return new Date(this.tokens.expiresAt) > new Date()
    },

    defaultShippingPolicy(): EbayShippingPolicy | undefined {
      return this.shippingPolicies.find(p => p.isDefault)
    },

    defaultReturnPolicy(): EbayReturnPolicy | undefined {
      return this.returnPolicies.find(p => p.isDefault)
    },

    defaultPaymentPolicy(): EbayPaymentPolicy | undefined {
      return this.paymentPolicies.find(p => p.isDefault)
    },

    sellerLevelLabel(): string {
      if (!this.account) return 'Non connecté'
      const labels: Record<string, string> = {
        top_rated: 'Vendeur Top Fiabilité',
        above_standard: 'Au-dessus des standards',
        standard: 'Standard',
        below_standard: 'En dessous des standards'
      }
      return labels[this.account.sellerLevel] || this.account.sellerLevel
    }
  },

  actions: {
    /**
     * Initialiser l'URL OAuth eBay
     */
    getOAuthUrl(): string {
      const config = useRuntimeConfig()
      const baseUrl = 'https://auth.ebay.com/oauth2/authorize'
      const params = new URLSearchParams({
        client_id: config.public.ebayClientId || 'YOUR_EBAY_CLIENT_ID',
        response_type: 'code',
        redirect_uri: config.public.ebayRedirectUri || `${window.location.origin}/dashboard/platforms/ebay/callback`,
        scope: [
          'https://api.ebay.com/oauth/api_scope',
          'https://api.ebay.com/oauth/api_scope/sell.marketing.readonly',
          'https://api.ebay.com/oauth/api_scope/sell.marketing',
          'https://api.ebay.com/oauth/api_scope/sell.inventory.readonly',
          'https://api.ebay.com/oauth/api_scope/sell.inventory',
          'https://api.ebay.com/oauth/api_scope/sell.account.readonly',
          'https://api.ebay.com/oauth/api_scope/sell.account',
          'https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly',
          'https://api.ebay.com/oauth/api_scope/sell.fulfillment'
        ].join(' ')
      })

      return `${baseUrl}?${params.toString()}`
    },

    /**
     * Initier la connexion OAuth
     */
    async initiateOAuth() {
      this.isConnecting = true
      this.connectionError = null

      try {
        // Appeler le backend pour obtenir l'URL OAuth
        const api = useApi()
        const { auth_url } = await api.get('/api/integrations/ebay/connect')

        // Ouvrir popup OAuth eBay
        const popup = window.open(auth_url, 'ebay_oauth', 'width=600,height=700,scrollbars=yes')

        if (!popup) {
          throw new Error('Popup bloquée. Veuillez autoriser les popups pour ce site.')
        }

        // Attendre le callback (sera géré par la page callback)
        return new Promise((resolve, reject) => {
          const checkClosed = setInterval(() => {
            if (popup.closed) {
              clearInterval(checkClosed)
              if (this.isConnected) {
                resolve(true)
              } else {
                reject(new Error('Connexion annulée'))
              }
            }
          }, 500)

          // Timeout après 5 minutes
          setTimeout(() => {
            clearInterval(checkClosed)
            if (!this.isConnected) {
              popup.close()
              reject(new Error('Délai d\'authentification expiré'))
            }
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
     * Échanger le code OAuth contre des tokens
     */
    async exchangeCodeForTokens(code: string) {
      this.isConnecting = true

      try {
        const api = useApi()

        // Appel backend pour échanger le code
        const response = await api.post('/api/integrations/ebay/callback', { code })

        this.tokens = response.tokens
        this.account = response.account
        this.isConnected = true

        // Charger les données
        await Promise.all([
          this.fetchPolicies(),
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
     * Vérifier le statut de connexion eBay
     */
    async checkConnectionStatus() {
      try {
        const api = useApi()
        const status = await api.get('/api/integrations/ebay/status')

        if (status.connected) {
          this.isConnected = true

          // Extraire les informations du compte depuis account_info (DB)
          if (status.account_info) {
            const info = status.account_info

            this.account = {
              userId: info.userId || '',
              username: info.username || '',
              email: info.email || '',
              accountType: info.accountType?.toLowerCase() || 'individual',
              registrationDate: info.registrationDate || '',
              sellerLevel: info.sellerLevel || 'standard',
              feedbackScore: info.feedbackScore || 0,
              feedbackPercentage: info.feedbackPercentage || 0,
              // Nouvelles données
              businessName: info.businessName,
              firstName: info.firstName,
              lastName: info.lastName,
              phone: info.phone,
              address: info.address,
              marketplace: info.marketplace,
              sandboxMode: status.sandbox_mode,
              accessTokenExpiresAt: status.access_token_expires_at
              // Note: programs et fulfillmentPoliciesCount sont chargés via fetchAccountInfo()
            }
          }
        } else {
          this.isConnected = false
        }

        return status
      } catch (error) {
        console.error('Erreur vérification statut eBay:', error)
        this.isConnected = false
        throw error
      }
    },

    /**
     * MOCK: Connecter (simulation)
     */
    async connectMock() {
      this.isConnecting = true
      this.connectionError = null

      try {
        await new Promise(resolve => setTimeout(resolve, 1500))

        // Mock account
        this.account = {
          userId: 'ebay_user_123',
          username: 'stoflow_seller',
          email: 'seller@stoflow.com',
          accountType: 'business',
          registrationDate: '2020-03-15',
          sellerLevel: 'top_rated',
          feedbackScore: 2847,
          feedbackPercentage: 99.8,
          storeName: 'Stoflow Fashion Store',
          storeUrl: 'https://www.ebay.fr/str/stoflowfashion'
        }

        this.tokens = {
          accessToken: 'mock_access_token',
          refreshToken: 'mock_refresh_token',
          expiresAt: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(),
          scope: ['sell.inventory', 'sell.account', 'sell.fulfillment']
        }

        this.isConnected = true

        // Charger les données mock
        await Promise.all([
          this.fetchPoliciesMock(),
          this.fetchStatsMock()
        ])

      } catch (error: any) {
        this.connectionError = error.message
        throw error
      } finally {
        this.isConnecting = false
      }
    },

    /**
     * Déconnecter le compte eBay
     */
    async disconnect() {
      this.isLoading = true

      try {
        const api = useApi()
        await api.post('/api/integrations/ebay/disconnect')

        this.$reset()

      } finally {
        this.isLoading = false
      }
    },

    /**
     * Charger les politiques eBay
     */
    async fetchPolicies() {
      this.isLoadingPolicies = true

      try {
        const api = useApi()

        const [shipping, returns, payment] = await Promise.all([
          api.get('/api/integrations/ebay/policies/shipping'),
          api.get('/api/integrations/ebay/policies/return'),
          api.get('/api/integrations/ebay/policies/payment')
        ])

        this.shippingPolicies = shipping
        this.returnPolicies = returns
        this.paymentPolicies = payment

      } catch (error) {
        console.error('Erreur chargement politiques:', error)
      } finally {
        this.isLoadingPolicies = false
      }
    },

    /**
     * MOCK: Charger les politiques
     */
    async fetchPoliciesMock() {
      this.isLoadingPolicies = true

      try {
        await new Promise(resolve => setTimeout(resolve, 800))

        this.shippingPolicies = [
          {
            id: 'ship_1',
            name: 'Livraison Standard France',
            description: 'Colissimo sous 3-5 jours',
            type: 'flat_rate',
            domesticShipping: {
              service: 'FR_ColipostColissimo',
              cost: 5.99,
              additionalCost: 1.50,
              handlingTime: 1
            },
            internationalShipping: {
              enabled: true,
              service: 'FR_ColipostInternational',
              cost: 12.99,
              countries: ['BE', 'DE', 'ES', 'IT', 'NL']
            },
            isDefault: true
          },
          {
            id: 'ship_2',
            name: 'Livraison Express',
            description: 'Chronopost 24h',
            type: 'flat_rate',
            domesticShipping: {
              service: 'FR_Chronopost',
              cost: 9.99,
              handlingTime: 0
            },
            isDefault: false
          },
          {
            id: 'ship_3',
            name: 'Livraison Gratuite',
            description: 'Pour commandes > 50€',
            type: 'free_shipping',
            domesticShipping: {
              service: 'FR_ColipostColissimo',
              cost: 0,
              handlingTime: 2
            },
            isDefault: false
          }
        ]

        this.returnPolicies = [
          {
            id: 'ret_1',
            name: 'Retours 30 jours',
            description: 'Remboursement complet sous 30 jours',
            returnsAccepted: true,
            returnPeriod: 30,
            refundMethod: 'money_back',
            shippingCostPaidBy: 'buyer',
            isDefault: true
          },
          {
            id: 'ret_2',
            name: 'Retours 14 jours',
            description: 'Conforme à la loi EU',
            returnsAccepted: true,
            returnPeriod: 14,
            refundMethod: 'money_back',
            shippingCostPaidBy: 'seller',
            isDefault: false
          },
          {
            id: 'ret_3',
            name: 'Pas de retours',
            description: 'Ventes finales uniquement',
            returnsAccepted: false,
            returnPeriod: 0,
            refundMethod: 'money_back',
            shippingCostPaidBy: 'buyer',
            isDefault: false
          }
        ]

        this.paymentPolicies = [
          {
            id: 'pay_1',
            name: 'Paiement Immédiat PayPal',
            description: 'PayPal avec paiement immédiat requis',
            paymentMethods: ['paypal', 'credit_card'],
            immediatePay: true,
            isDefault: true
          },
          {
            id: 'pay_2',
            name: 'Paiement Flexible',
            description: 'Plusieurs méthodes acceptées',
            paymentMethods: ['paypal', 'credit_card', 'bank_transfer'],
            immediatePay: false,
            isDefault: false
          }
        ]

      } finally {
        this.isLoadingPolicies = false
      }
    },

    /**
     * Charger les statistiques
     */
    async fetchStats() {
      try {
        const api = useApi()
        const stats = await api.get('/api/integrations/ebay/stats')
        this.stats = stats
      } catch (error) {
        console.error('Erreur chargement stats:', error)
      }
    },

    /**
     * Charger les informations du compte eBay
     */
    async fetchAccountInfo() {
      try {
        const api = useApi()
        const response = await api.get('/api/integrations/ebay/account-info')

        console.log('eBay account-info response:', response)

        if (response.success) {
          // Créer le compte si inexistant
          if (!this.account) {
            this.account = {
              userId: '',
              username: '',
              email: '',
              accountType: 'individual',
              registrationDate: '',
              sellerLevel: 'standard',
              feedbackScore: 0,
              feedbackPercentage: 0
            }
          }

          // Enrichir avec seller_info si disponible
          if (response.seller_info) {
            // Données de base depuis Commerce Identity
            this.account.userId = response.seller_info.userId || this.account.userId
            this.account.username = response.seller_info.username || this.account.username
            this.account.accountType = response.seller_info.accountType || this.account.accountType
            this.account.marketplace = response.seller_info.registrationMarketplaceId

            // Business Account (BUSINESS)
            if (response.seller_info.businessAccount) {
              const business = response.seller_info.businessAccount
              this.account.businessName = business.name
              this.account.email = business.email

              // Téléphone
              if (business.primaryPhone) {
                this.account.phone = `+${business.primaryPhone.countryCode} ${business.primaryPhone.number}`
              }

              // Adresse
              if (business.address) {
                const addr = business.address
                this.account.address = [
                  addr.addressLine1,
                  addr.addressLine2,
                  `${addr.postalCode} ${addr.city}`,
                  addr.country
                ].filter(Boolean).join(', ')
              }

              // Contact principal
              if (business.primaryContact) {
                this.account.firstName = business.primaryContact.firstName
                this.account.lastName = business.primaryContact.lastName
              }
            }
            // Individual Account (INDIVIDUAL)
            else if (response.seller_info.individualAccount) {
              const individual = response.seller_info.individualAccount
              this.account.firstName = individual.firstName
              this.account.lastName = individual.lastName
              this.account.email = individual.email

              // Téléphone
              if (individual.primaryPhone) {
                this.account.phone = `+${individual.primaryPhone.countryCode} ${individual.primaryPhone.number}`
              }

              // Adresse
              if (individual.registrationAddress) {
                const addr = individual.registrationAddress
                this.account.address = [
                  addr.addressLine1,
                  addr.addressLine2,
                  `${addr.postalCode} ${addr.city}`,
                  addr.country
                ].filter(Boolean).join(', ')
              }
            }

            // Données depuis Trading API (si présentes aussi)
            if (response.seller_info.feedback_score !== undefined) {
              this.account.feedbackScore = response.seller_info.feedback_score
              this.account.feedbackPercentage = response.seller_info.positive_feedback_percent || 0
            }
            if (response.seller_info.registration_date) {
              this.account.registrationDate = response.seller_info.registration_date
            }
            if (response.seller_info.seller_level) {
              this.account.sellerLevel = response.seller_info.top_rated_seller ? 'top_rated' : response.seller_info.seller_level
            }
          } else {
            console.warn('seller_info is null - API failed')
          }

          // Toujours ajouter les programmes et policies count
          this.account.programs = response.programs
          this.account.fulfillmentPoliciesCount = response.fulfillment_policies_count
          this.account.accessTokenExpiresAt = response.access_token_expires_at
          this.account.sandboxMode = response.sandbox_mode
        }

        return response
      } catch (error) {
        console.error('Erreur chargement infos compte eBay:', error)
        throw error
      }
    },

    /**
     * MOCK: Charger les statistiques
     */
    async fetchStatsMock() {
      await new Promise(resolve => setTimeout(resolve, 500))

      this.stats = {
        activeLis: 47,
        totalViews: 12847,
        totalWatchers: 234,
        totalSales: 156,
        totalRevenue: 8947.50,
        averagePrice: 57.35,
        conversionRate: 3.2,
        impressions: 45680
      }
    },

    /**
     * Créer une politique d'expédition
     */
    async createShippingPolicy(policy: Omit<EbayShippingPolicy, 'id'>) {
      this.isLoading = true

      try {
        // TODO: Appel API
        await new Promise(resolve => setTimeout(resolve, 500))

        const newPolicy: EbayShippingPolicy = {
          ...policy,
          id: `ship_${Date.now()}`
        }

        if (policy.isDefault) {
          this.shippingPolicies.forEach(p => p.isDefault = false)
        }

        this.shippingPolicies.push(newPolicy)
        return newPolicy

      } finally {
        this.isLoading = false
      }
    },

    /**
     * Créer une politique de retour
     */
    async createReturnPolicy(policy: Omit<EbayReturnPolicy, 'id'>) {
      this.isLoading = true

      try {
        await new Promise(resolve => setTimeout(resolve, 500))

        const newPolicy: EbayReturnPolicy = {
          ...policy,
          id: `ret_${Date.now()}`
        }

        if (policy.isDefault) {
          this.returnPolicies.forEach(p => p.isDefault = false)
        }

        this.returnPolicies.push(newPolicy)
        return newPolicy

      } finally {
        this.isLoading = false
      }
    },

    /**
     * Supprimer une politique
     */
    async deletePolicy(type: 'shipping' | 'return' | 'payment', policyId: string) {
      this.isLoading = true

      try {
        await new Promise(resolve => setTimeout(resolve, 300))

        switch (type) {
          case 'shipping':
            this.shippingPolicies = this.shippingPolicies.filter(p => p.id !== policyId)
            break
          case 'return':
            this.returnPolicies = this.returnPolicies.filter(p => p.id !== policyId)
            break
          case 'payment':
            this.paymentPolicies = this.paymentPolicies.filter(p => p.id !== policyId)
            break
        }

      } finally {
        this.isLoading = false
      }
    },

    /**
     * Synchroniser les données
     */
    async syncData() {
      this.isSyncing = true

      try {
        await new Promise(resolve => setTimeout(resolve, 2000))

        this.syncSettings.lastSyncAt = new Date().toISOString()
        this.syncSettings.nextSyncAt = new Date(Date.now() + this.syncSettings.syncInterval * 60 * 1000).toISOString()

        // Recharger les stats
        await this.fetchStatsMock()

      } finally {
        this.isSyncing = false
      }
    },

    /**
     * Sauvegarder les paramètres de sync
     */
    async saveSyncSettings(settings: Partial<EbaySyncSettings>) {
      this.syncSettings = { ...this.syncSettings, ...settings }

      // TODO: Appel API pour sauvegarder
      await new Promise(resolve => setTimeout(resolve, 300))
    },

    /**
     * Charger les catégories eBay
     */
    async fetchCategoriesMock() {
      this.isLoadingCategories = true

      try {
        await new Promise(resolve => setTimeout(resolve, 600))

        this.categories = [
          {
            id: '11450',
            name: 'Vêtements, accessoires',
            level: 1,
            leafCategory: false,
            children: [
              {
                id: '11483',
                name: 'Vêtements homme',
                parentId: '11450',
                level: 2,
                leafCategory: false,
                children: [
                  { id: '57988', name: 'T-shirts', parentId: '11483', level: 3, leafCategory: true },
                  { id: '57989', name: 'Chemises', parentId: '11483', level: 3, leafCategory: true },
                  { id: '57990', name: 'Jeans', parentId: '11483', level: 3, leafCategory: true },
                  { id: '57991', name: 'Vestes & Manteaux', parentId: '11483', level: 3, leafCategory: true },
                  { id: '57992', name: 'Pulls & Sweats', parentId: '11483', level: 3, leafCategory: true }
                ]
              },
              {
                id: '11484',
                name: 'Vêtements femme',
                parentId: '11450',
                level: 2,
                leafCategory: false,
                children: [
                  { id: '63861', name: 'Robes', parentId: '11484', level: 3, leafCategory: true },
                  { id: '63862', name: 'Tops & T-shirts', parentId: '11484', level: 3, leafCategory: true },
                  { id: '63863', name: 'Jupes', parentId: '11484', level: 3, leafCategory: true },
                  { id: '63864', name: 'Pantalons', parentId: '11484', level: 3, leafCategory: true }
                ]
              },
              {
                id: '11485',
                name: 'Chaussures',
                parentId: '11450',
                level: 2,
                leafCategory: false,
                children: [
                  { id: '93427', name: 'Baskets', parentId: '11485', level: 3, leafCategory: true },
                  { id: '93428', name: 'Chaussures de ville', parentId: '11485', level: 3, leafCategory: true },
                  { id: '93429', name: 'Bottes', parentId: '11485', level: 3, leafCategory: true }
                ]
              }
            ]
          },
          {
            id: '26395',
            name: 'Maison, jardin',
            level: 1,
            leafCategory: false,
            children: [
              { id: '38227', name: 'Décoration', parentId: '26395', level: 2, leafCategory: true },
              { id: '38228', name: 'Mobilier', parentId: '26395', level: 2, leafCategory: true }
            ]
          }
        ]

      } finally {
        this.isLoadingCategories = false
      }
    }
  },

  // Persist to localStorage
  persist: {
    key: 'stoflow-ebay',
    pick: ['isConnected', 'account', 'syncSettings', 'selectedCategories']
  }
})
