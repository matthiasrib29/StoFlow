# Guide d'Intégration Frontend - eBay & Etsy

## 📋 Vue d'ensemble

Ce guide explique comment connecter le frontend React/TypeScript aux endpoints eBay et Etsy du backend.

---

## 🔧 Configuration Initiale

### 1. Variables d'environnement Frontend

Créer `.env.local` dans le projet frontend:

```env
# API Backend
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# eBay Callback URL (doit matcher .env backend)
NEXT_PUBLIC_EBAY_CALLBACK_URL=http://localhost:3000/ebay/callback

# Etsy Callback URL (doit matcher .env backend)
NEXT_PUBLIC_ETSY_CALLBACK_URL=http://localhost:3000/etsy/callback
```

### 2. Installation des dépendances

```bash
npm install axios react-query zustand
# ou
yarn add axios react-query zustand
```

---

## 🔐 Service API - Configuration de base

### `src/services/api.ts`

```typescript
import axios, { AxiosInstance, AxiosError } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// Créer instance Axios
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token JWT
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Intercepteur pour gérer les erreurs
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expiré, rediriger vers login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## 🛍️ Service eBay

### `src/services/ebay.service.ts`

```typescript
import apiClient from './api';

export interface EbayConnectionStatus {
  connected: boolean;
  user_id: string | null;
  access_token_expires_at: string | null;
  refresh_token_expires_at: string | null;
}

export interface EbayMarketplace {
  marketplace_id: string;
  country_code: string;
  site_id: number;
  currency: string;
  is_active: boolean;
  language: string;
  content_language: string;
}

export interface PublishProductRequest {
  product_id: number;
  marketplace_id: string;
  category_id?: string;
}

export interface PublishProductResponse {
  success: boolean;
  sku_derived: string;
  offer_id: string;
  listing_id: string;
  marketplace_id: string;
  message: string;
}

class EbayService {
  /**
   * Démarre le flow OAuth2 eBay
   */
  async connect(): Promise<{ authorization_url: string; state: string }> {
    const response = await apiClient.get('/ebay/oauth/connect');
    return response.data;
  }

  /**
   * Vérifie le statut de connexion eBay
   */
  async getConnectionStatus(): Promise<EbayConnectionStatus> {
    const response = await apiClient.get('/ebay/connection/status');
    return response.data;
  }

  /**
   * Déconnecte le compte eBay
   */
  async disconnect(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/ebay/oauth/disconnect');
    return response.data;
  }

  /**
   * Récupère les marketplaces eBay disponibles
   */
  async getMarketplaces(): Promise<EbayMarketplace[]> {
    const response = await apiClient.get('/ebay/marketplaces');
    return response.data;
  }

  /**
   * Publie un produit sur eBay
   */
  async publishProduct(data: PublishProductRequest): Promise<PublishProductResponse> {
    const response = await apiClient.post('/ebay/products/publish', data);
    return response.data;
  }

  /**
   * Dépublie un produit d'eBay
   */
  async unpublishProduct(productId: number, marketplaceId: string): Promise<any> {
    const response = await apiClient.post('/ebay/products/unpublish', {
      product_id: productId,
      marketplace_id: marketplaceId,
    });
    return response.data;
  }

  /**
   * Récupère les commandes eBay
   */
  async getOrders(status?: string, limit: number = 50): Promise<any> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('limit', limit.toString());

    const response = await apiClient.get(`/ebay/orders?${params.toString()}`);
    return response.data;
  }
}

export default new EbayService();
```

---

## 🎨 Service Etsy

### `src/services/etsy.service.ts`

```typescript
import apiClient from './api';

export interface EtsyConnectionStatus {
  connected: boolean;
  shop_id: string | null;
  shop_name: string | null;
  access_token_expires_at: string | null;
  refresh_token_expires_at: string | null;
}

export interface EtsyShopInfo {
  shop_id: number;
  shop_name: string;
  title: string;
  url: string;
  listing_active_count: number;
  currency_code: string;
}

export interface PublishEtsyProductRequest {
  product_id: number;
  taxonomy_id: number;
  shipping_profile_id?: number;
  return_policy_id?: number;
  shop_section_id?: number;
  state?: 'active' | 'draft';
}

export interface PublishEtsyProductResponse {
  success: boolean;
  listing_id: number;
  listing_url: string;
  state: string;
  error: string | null;
}

export interface EtsyListing {
  listing_id: number;
  title: string;
  state: string;
  price: any;
  quantity: number;
  url?: string;
  created_timestamp?: number;
  updated_timestamp?: number;
}

export interface EtsyTaxonomyNode {
  id: number;
  level: number;
  name: string;
  parent_id: number | null;
  children: number[];
  full_path_taxonomy_ids?: number[];
}

class EtsyService {
  /**
   * Démarre le flow OAuth2 Etsy (avec PKCE)
   */
  async connect(): Promise<{ authorization_url: string; state: string }> {
    const response = await apiClient.get('/etsy/oauth/connect');
    return response.data;
  }

  /**
   * Vérifie le statut de connexion Etsy
   */
  async getConnectionStatus(): Promise<EtsyConnectionStatus> {
    const response = await apiClient.get('/etsy/connection/status');
    return response.data;
  }

  /**
   * Déconnecte le compte Etsy
   */
  async disconnect(): Promise<{ success: boolean; message: string }> {
    const response = await apiClient.post('/etsy/oauth/disconnect');
    return response.data;
  }

  /**
   * Récupère les infos du shop Etsy
   */
  async getShopInfo(): Promise<EtsyShopInfo> {
    const response = await apiClient.get('/etsy/shop');
    return response.data;
  }

  /**
   * Publie un produit sur Etsy
   */
  async publishProduct(data: PublishEtsyProductRequest): Promise<PublishEtsyProductResponse> {
    const response = await apiClient.post('/etsy/products/publish', data);
    return response.data;
  }

  /**
   * Met à jour un listing Etsy
   */
  async updateProduct(listingId: number, productId: number): Promise<any> {
    const response = await apiClient.put('/etsy/products/update', {
      listing_id: listingId,
      product_id: productId,
    });
    return response.data;
  }

  /**
   * Supprime un listing Etsy
   */
  async deleteProduct(listingId: number): Promise<any> {
    const response = await apiClient.delete('/etsy/products/delete', {
      data: { listing_id: listingId },
    });
    return response.data;
  }

  /**
   * Récupère les listings actifs
   */
  async getActiveListings(limit: number = 25, offset: number = 0): Promise<EtsyListing[]> {
    const response = await apiClient.get(`/etsy/listings/active?limit=${limit}&offset=${offset}`);
    return response.data;
  }

  /**
   * Récupère les détails d'un listing
   */
  async getListingDetails(listingId: number): Promise<any> {
    const response = await apiClient.get(`/etsy/listings/${listingId}`);
    return response.data;
  }

  /**
   * Récupère les commandes Etsy
   */
  async getOrders(statusFilter?: string, limit: number = 25, offset: number = 0): Promise<any[]> {
    const params = new URLSearchParams();
    if (statusFilter) params.append('status_filter', statusFilter);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const response = await apiClient.get(`/etsy/orders?${params.toString()}`);
    return response.data;
  }

  /**
   * Récupère les catégories Etsy (taxonomy)
   */
  async getTaxonomyNodes(search?: string): Promise<EtsyTaxonomyNode[]> {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    const response = await apiClient.get(`/etsy/taxonomy/nodes${params}`);
    return response.data;
  }

  /**
   * Récupère les propriétés requises pour une catégorie
   */
  async getTaxonomyProperties(taxonomyId: number): Promise<any[]> {
    const response = await apiClient.get(`/etsy/taxonomy/nodes/${taxonomyId}/properties`);
    return response.data;
  }

  /**
   * Récupère les shipping profiles
   */
  async getShippingProfiles(): Promise<any[]> {
    const response = await apiClient.get('/etsy/shipping/profiles');
    return response.data;
  }

  /**
   * Déclenche un cycle de polling Etsy
   */
  async triggerPolling(
    checkOrders: boolean = true,
    checkListings: boolean = true,
    checkStock: boolean = true
  ): Promise<any> {
    const params = new URLSearchParams();
    params.append('check_orders', checkOrders.toString());
    params.append('check_listings', checkListings.toString());
    params.append('check_stock', checkStock.toString());

    const response = await apiClient.get(`/etsy/polling/status?${params.toString()}`);
    return response.data;
  }
}

export default new EtsyService();
```

---

## 🎯 Composants React

### Connexion eBay - `src/components/EbayConnect.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import ebayService, { EbayConnectionStatus } from '@/services/ebay.service';
import { Button, Card, Badge, Spinner } from '@/components/ui';

export const EbayConnect: React.FC = () => {
  const [status, setStatus] = useState<EbayConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    loadConnectionStatus();
  }, []);

  const loadConnectionStatus = async () => {
    try {
      setLoading(true);
      const data = await ebayService.getConnectionStatus();
      setStatus(data);
    } catch (error) {
      console.error('Error loading eBay status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      const { authorization_url } = await ebayService.connect();

      // Rediriger vers eBay OAuth
      window.location.href = authorization_url;
    } catch (error) {
      console.error('Error connecting to eBay:', error);
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Êtes-vous sûr de vouloir déconnecter votre compte eBay ?')) {
      return;
    }

    try {
      await ebayService.disconnect();
      await loadConnectionStatus();
    } catch (error) {
      console.error('Error disconnecting eBay:', error);
    }
  };

  if (loading) {
    return <Spinner />;
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">eBay</h2>
        {status?.connected ? (
          <Badge variant="success">Connecté</Badge>
        ) : (
          <Badge variant="secondary">Non connecté</Badge>
        )}
      </div>

      {status?.connected ? (
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-500">User ID</p>
            <p className="font-medium">{status.user_id}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Token expire le</p>
            <p className="font-medium">
              {new Date(status.access_token_expires_at!).toLocaleString('fr-FR')}
            </p>
          </div>

          <Button onClick={handleDisconnect} variant="destructive">
            Déconnecter
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-gray-600">
            Connectez votre compte eBay pour publier vos produits
          </p>
          <Button onClick={handleConnect} disabled={connecting}>
            {connecting ? 'Redirection...' : 'Connecter eBay'}
          </Button>
        </div>
      )}
    </Card>
  );
};
```

### Connexion Etsy - `src/components/EtsyConnect.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import etsyService, { EtsyConnectionStatus } from '@/services/etsy.service';
import { Button, Card, Badge, Spinner } from '@/components/ui';

export const EtsyConnect: React.FC = () => {
  const [status, setStatus] = useState<EtsyConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    loadConnectionStatus();
  }, []);

  const loadConnectionStatus = async () => {
    try {
      setLoading(true);
      const data = await etsyService.getConnectionStatus();
      setStatus(data);
    } catch (error) {
      console.error('Error loading Etsy status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      const { authorization_url } = await etsyService.connect();

      // Rediriger vers Etsy OAuth
      window.location.href = authorization_url;
    } catch (error) {
      console.error('Error connecting to Etsy:', error);
      setConnecting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Êtes-vous sûr de vouloir déconnecter votre compte Etsy ?')) {
      return;
    }

    try {
      await etsyService.disconnect();
      await loadConnectionStatus();
    } catch (error) {
      console.error('Error disconnecting Etsy:', error);
    }
  };

  if (loading) {
    return <Spinner />;
  }

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold">Etsy</h2>
        {status?.connected ? (
          <Badge variant="success">Connecté</Badge>
        ) : (
          <Badge variant="secondary">Non connecté</Badge>
        )}
      </div>

      {status?.connected ? (
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-500">Shop Name</p>
            <p className="font-medium">{status.shop_name}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Shop ID</p>
            <p className="font-medium">{status.shop_id}</p>
          </div>

          <div>
            <p className="text-sm text-gray-500">Token expire le</p>
            <p className="font-medium">
              {new Date(status.access_token_expires_at!).toLocaleString('fr-FR')}
            </p>
          </div>

          <Button onClick={handleDisconnect} variant="destructive">
            Déconnecter
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-gray-600">
            Connectez votre boutique Etsy pour publier vos produits
          </p>
          <Button onClick={handleConnect} disabled={connecting}>
            {connecting ? 'Redirection...' : 'Connecter Etsy'}
          </Button>
        </div>
      )}
    </Card>
  );
};
```

### Publication Produit - `src/components/PublishProduct.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import ebayService from '@/services/ebay.service';
import etsyService from '@/services/etsy.service';
import { Button, Select, Modal } from '@/components/ui';

interface PublishProductProps {
  productId: number;
  productTitle: string;
}

export const PublishProduct: React.FC<PublishProductProps> = ({ productId, productTitle }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [platform, setPlatform] = useState<'ebay' | 'etsy'>('ebay');
  const [publishing, setPublishing] = useState(false);

  // eBay
  const [ebayMarketplace, setEbayMarketplace] = useState('EBAY_FR');
  const [ebayCategory, setEbayCategory] = useState('');

  // Etsy
  const [etsyTaxonomy, setEtsyTaxonomy] = useState<number | null>(null);
  const [etsyState, setEtsyState] = useState<'active' | 'draft'>('draft');

  const handlePublish = async () => {
    try {
      setPublishing(true);

      if (platform === 'ebay') {
        const result = await ebayService.publishProduct({
          product_id: productId,
          marketplace_id: ebayMarketplace,
          category_id: ebayCategory,
        });

        alert(`✅ Produit publié sur eBay!\nListing ID: ${result.listing_id}`);
      } else {
        if (!etsyTaxonomy) {
          alert('Veuillez sélectionner une catégorie Etsy');
          return;
        }

        const result = await etsyService.publishProduct({
          product_id: productId,
          taxonomy_id: etsyTaxonomy,
          state: etsyState,
        });

        alert(`✅ Produit publié sur Etsy!\nURL: ${result.listing_url}`);
      }

      setIsOpen(false);
    } catch (error: any) {
      console.error('Error publishing product:', error);
      alert(`❌ Erreur: ${error.response?.data?.detail || error.message}`);
    } finally {
      setPublishing(false);
    }
  };

  return (
    <>
      <Button onClick={() => setIsOpen(true)}>Publier sur Marketplace</Button>

      <Modal open={isOpen} onClose={() => setIsOpen(false)}>
        <div className="p-6 space-y-4">
          <h2 className="text-xl font-bold">Publier "{productTitle}"</h2>

          {/* Sélection plateforme */}
          <div>
            <label className="block text-sm font-medium mb-2">Plateforme</label>
            <Select value={platform} onChange={(e) => setPlatform(e.target.value as any)}>
              <option value="ebay">eBay</option>
              <option value="etsy">Etsy</option>
            </Select>
          </div>

          {/* Options eBay */}
          {platform === 'ebay' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">Marketplace</label>
                <Select value={ebayMarketplace} onChange={(e) => setEbayMarketplace(e.target.value)}>
                  <option value="EBAY_FR">eBay France</option>
                  <option value="EBAY_US">eBay USA</option>
                  <option value="EBAY_UK">eBay UK</option>
                  <option value="EBAY_DE">eBay Allemagne</option>
                </Select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Catégorie eBay</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border rounded"
                  placeholder="Ex: 11450 (T-shirts)"
                  value={ebayCategory}
                  onChange={(e) => setEbayCategory(e.target.value)}
                />
              </div>
            </>
          )}

          {/* Options Etsy */}
          {platform === 'etsy' && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">Catégorie Etsy (Taxonomy ID)</label>
                <input
                  type="number"
                  className="w-full px-3 py-2 border rounded"
                  placeholder="Ex: 1234"
                  value={etsyTaxonomy || ''}
                  onChange={(e) => setEtsyTaxonomy(parseInt(e.target.value) || null)}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">État du listing</label>
                <Select value={etsyState} onChange={(e) => setEtsyState(e.target.value as any)}>
                  <option value="draft">Brouillon</option>
                  <option value="active">Actif</option>
                </Select>
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button onClick={handlePublish} disabled={publishing}>
              {publishing ? 'Publication...' : 'Publier'}
            </Button>
            <Button onClick={() => setIsOpen(false)} variant="secondary">
              Annuler
            </Button>
          </div>
        </div>
      </Modal>
    </>
  );
};
```

---

## 🔄 Pages Callback OAuth

### eBay Callback - `src/pages/ebay/callback.tsx`

```typescript
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import apiClient from '@/services/api';

export default function EbayCallback() {
  const router = useRouter();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Connexion à eBay en cours...');

  useEffect(() => {
    const handleCallback = async () => {
      const { code, state } = router.query;

      if (!code || !state) {
        setStatus('error');
        setMessage('Paramètres manquants');
        return;
      }

      try {
        const response = await apiClient.get(
          `/ebay/oauth/callback?code=${code}&state=${state}`
        );

        if (response.data.success) {
          setStatus('success');
          setMessage('✅ Compte eBay connecté avec succès!');

          setTimeout(() => {
            router.push('/dashboard/integrations');
          }, 2000);
        } else {
          throw new Error(response.data.error || 'Erreur inconnue');
        }
      } catch (error: any) {
        setStatus('error');
        setMessage(`❌ Erreur: ${error.response?.data?.detail || error.message}`);
      }
    };

    if (router.isReady) {
      handleCallback();
    }
  }, [router.isReady, router.query]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        {status === 'processing' && (
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        )}

        {status === 'success' && (
          <div className="text-6xl mb-4">✅</div>
        )}

        {status === 'error' && (
          <div className="text-6xl mb-4">❌</div>
        )}

        <p className="text-xl">{message}</p>

        {status === 'success' && (
          <p className="text-sm text-gray-500 mt-2">Redirection...</p>
        )}

        {status === 'error' && (
          <button
            onClick={() => router.push('/dashboard/integrations')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retour au tableau de bord
          </button>
        )}
      </div>
    </div>
  );
}
```

### Etsy Callback - `src/pages/etsy/callback.tsx`

```typescript
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import apiClient from '@/services/api';

export default function EtsyCallback() {
  const router = useRouter();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Connexion à Etsy en cours...');

  useEffect(() => {
    const handleCallback = async () => {
      const { code, state } = router.query;

      if (!code || !state) {
        setStatus('error');
        setMessage('Paramètres manquants');
        return;
      }

      try {
        const response = await apiClient.get(
          `/etsy/oauth/callback?code=${code}&state=${state}`
        );

        if (response.data.success) {
          setStatus('success');
          setMessage(`✅ Boutique Etsy "${response.data.shop_name}" connectée avec succès!`);

          setTimeout(() => {
            router.push('/dashboard/integrations');
          }, 2000);
        } else {
          throw new Error(response.data.error || 'Erreur inconnue');
        }
      } catch (error: any) {
        setStatus('error');
        setMessage(`❌ Erreur: ${error.response?.data?.detail || error.message}`);
      }
    };

    if (router.isReady) {
      handleCallback();
    }
  }, [router.isReady, router.query]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        {status === 'processing' && (
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto mb-4"></div>
        )}

        {status === 'success' && (
          <div className="text-6xl mb-4">✅</div>
        )}

        {status === 'error' && (
          <div className="text-6xl mb-4">❌</div>
        )}

        <p className="text-xl">{message}</p>

        {status === 'success' && (
          <p className="text-sm text-gray-500 mt-2">Redirection...</p>
        )}

        {status === 'error' && (
          <button
            onClick={() => router.push('/dashboard/integrations')}
            className="mt-4 px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700"
          >
            Retour au tableau de bord
          </button>
        )}
      </div>
    </div>
  );
}
```

---

## 📊 Page Dashboard Intégrations

### `src/pages/dashboard/integrations.tsx`

```typescript
import React from 'react';
import { EbayConnect } from '@/components/EbayConnect';
import { EtsyConnect } from '@/components/EtsyConnect';

export default function IntegrationsPage() {
  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Intégrations Marketplaces</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <EbayConnect />
        <EtsyConnect />
      </div>

      <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded">
        <h3 className="font-semibold mb-2">ℹ️ Informations</h3>
        <ul className="text-sm space-y-1 text-gray-700">
          <li>• Les tokens eBay expirent après 2 heures (refresh automatique)</li>
          <li>• Les tokens Etsy expirent après 1 heure (refresh automatique)</li>
          <li>• Etsy n'a pas de webhooks natifs, le polling s'exécute toutes les 5-15 minutes</li>
          <li>• Vos credentials sont stockés de manière sécurisée</li>
        </ul>
      </div>
    </div>
  );
}
```

---

## 🎯 React Query Hooks (Optionnel)

Pour une meilleure gestion du cache et des requêtes:

### `src/hooks/useEbay.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from 'react-query';
import ebayService from '@/services/ebay.service';

export const useEbayConnection = () => {
  return useQuery('ebayConnection', () => ebayService.getConnectionStatus(), {
    refetchInterval: 60000, // Refetch toutes les 60 secondes
  });
};

export const useEbayMarketplaces = () => {
  return useQuery('ebayMarketplaces', () => ebayService.getMarketplaces());
};

export const usePublishToEbay = () => {
  const queryClient = useQueryClient();

  return useMutation(ebayService.publishProduct, {
    onSuccess: () => {
      queryClient.invalidateQueries('products');
    },
  });
};
```

### `src/hooks/useEtsy.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from 'react-query';
import etsyService from '@/services/etsy.service';

export const useEtsyConnection = () => {
  return useQuery('etsyConnection', () => etsyService.getConnectionStatus(), {
    refetchInterval: 60000,
  });
};

export const useEtsyShopInfo = () => {
  return useQuery('etsyShopInfo', () => etsyService.getShopInfo());
};

export const usePublishToEtsy = () => {
  const queryClient = useQueryClient();

  return useMutation(etsyService.publishProduct, {
    onSuccess: () => {
      queryClient.invalidateQueries('products');
    },
  });
};
```

---

## ✅ Checklist d'Intégration

- [ ] Configurer `.env.local` avec `NEXT_PUBLIC_API_URL`
- [ ] Créer `src/services/api.ts` (client Axios)
- [ ] Créer `src/services/ebay.service.ts`
- [ ] Créer `src/services/etsy.service.ts`
- [ ] Créer composants `EbayConnect.tsx` et `EtsyConnect.tsx`
- [ ] Créer pages callback `/ebay/callback` et `/etsy/callback`
- [ ] Créer page `/dashboard/integrations`
- [ ] Tester connexion eBay
- [ ] Tester connexion Etsy
- [ ] Tester publication produit eBay
- [ ] Tester publication produit Etsy

---

## 🔧 Troubleshooting

### CORS Errors

Si vous obtenez des erreurs CORS, vérifiez `.env` backend:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Token Expired

Les tokens sont refreshés automatiquement par le backend. Si vous obtenez 401:
- Vérifiez que le backend tourne
- Vérifiez que le token JWT est valide
- Reconnectez-vous

### Redirect URI Mismatch

Assurez-vous que les redirect URIs correspondent:
- Backend `.env`: `EBAY_REDIRECT_URI`, `ETSY_REDIRECT_URI`
- Frontend `.env.local`: URLs des pages callback
- Configuration eBay/Etsy Developer Portal

---

**Auteur:** Claude
**Date:** 2025-12-10
