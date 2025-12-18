# Code Examples Frontend - Copy-Paste Ready

## 📦 Installation Dépendances

```bash
npm install axios @tanstack/react-query zustand
# ou
yarn add axios @tanstack/react-query zustand
```

---

## 🔧 Configuration React Query

### `src/app/providers.tsx` (Next.js 13+ App Router)

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### `src/app/layout.tsx`

```typescript
import { Providers } from './providers';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

---

## 🎨 Store Zustand pour Auth

### `src/store/authStore.ts`

```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: any | null;
  setToken: (token: string) => void;
  setUser: (user: any) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setToken: (token) => set({ token }),
      setUser: (user) => set({ user }),
      logout: () => set({ token: null, user: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

---

## 🌐 API Client avec Zustand

### `src/lib/api.ts`

```typescript
import axios, { AxiosError } from 'axios';
import { useAuthStore } from '@/store/authStore';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const { token } = useAuthStore.getState();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token expiré
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

---

## 🛍️ Services API Complets

### `src/services/marketplaces/ebay.ts`

```typescript
import { api } from '@/lib/api';

export const ebayApi = {
  // Connection
  connect: async () => {
    const { data } = await api.get('/ebay/oauth/connect');
    return data;
  },

  getStatus: async () => {
    const { data } = await api.get('/ebay/connection/status');
    return data;
  },

  disconnect: async () => {
    const { data } = await api.post('/ebay/oauth/disconnect');
    return data;
  },

  // Marketplaces
  getMarketplaces: async () => {
    const { data } = await api.get('/ebay/marketplaces');
    return data;
  },

  // Products
  publishProduct: async (payload: {
    product_id: number;
    marketplace_id: string;
    category_id?: string;
  }) => {
    const { data } = await api.post('/ebay/products/publish', payload);
    return data;
  },

  unpublishProduct: async (productId: number, marketplaceId: string) => {
    const { data } = await api.post('/ebay/products/unpublish', {
      product_id: productId,
      marketplace_id: marketplaceId,
    });
    return data;
  },

  // Orders
  getOrders: async (params?: { status?: string; limit?: number }) => {
    const { data } = await api.get('/ebay/orders', { params });
    return data;
  },

  getOrder: async (orderId: string) => {
    const { data } = await api.get(`/ebay/orders/${orderId}`);
    return data;
  },
};
```

### `src/services/marketplaces/etsy.ts`

```typescript
import { api } from '@/lib/api';

export const etsyApi = {
  // Connection
  connect: async () => {
    const { data } = await api.get('/etsy/oauth/connect');
    return data;
  },

  getStatus: async () => {
    const { data } = await api.get('/etsy/connection/status');
    return data;
  },

  disconnect: async () => {
    const { data } = await api.post('/etsy/oauth/disconnect');
    return data;
  },

  // Shop
  getShop: async () => {
    const { data } = await api.get('/etsy/shop');
    return data;
  },

  getSections: async () => {
    const { data } = await api.get('/etsy/shop/sections');
    return data;
  },

  // Products
  publishProduct: async (payload: {
    product_id: number;
    taxonomy_id: number;
    shipping_profile_id?: number;
    state?: 'active' | 'draft';
  }) => {
    const { data } = await api.post('/etsy/products/publish', payload);
    return data;
  },

  updateProduct: async (listingId: number, productId: number) => {
    const { data } = await api.put('/etsy/products/update', {
      listing_id: listingId,
      product_id: productId,
    });
    return data;
  },

  deleteProduct: async (listingId: number) => {
    const { data } = await api.delete('/etsy/products/delete', {
      data: { listing_id: listingId },
    });
    return data;
  },

  // Listings
  getActiveListings: async (params?: { limit?: number; offset?: number }) => {
    const { data } = await api.get('/etsy/listings/active', { params });
    return data;
  },

  getListingDetails: async (listingId: number) => {
    const { data } = await api.get(`/etsy/listings/${listingId}`);
    return data;
  },

  // Orders
  getOrders: async (params?: { status_filter?: string; limit?: number; offset?: number }) => {
    const { data } = await api.get('/etsy/orders', { params });
    return data;
  },

  getOrder: async (receiptId: number) => {
    const { data } = await api.get(`/etsy/orders/${receiptId}`);
    return data;
  },

  // Taxonomy
  getTaxonomy: async (search?: string) => {
    const { data } = await api.get('/etsy/taxonomy/nodes', {
      params: search ? { search } : undefined,
    });
    return data;
  },

  getTaxonomyProperties: async (taxonomyId: number) => {
    const { data } = await api.get(`/etsy/taxonomy/nodes/${taxonomyId}/properties`);
    return data;
  },

  // Shipping
  getShippingProfiles: async () => {
    const { data } = await api.get('/etsy/shipping/profiles');
    return data;
  },

  // Polling
  triggerPolling: async () => {
    const { data } = await api.get('/etsy/polling/status');
    return data;
  },
};
```

---

## 🪝 React Query Hooks

### `src/hooks/useEbay.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ebayApi } from '@/services/marketplaces/ebay';
import { toast } from 'sonner'; // ou react-hot-toast

export const useEbayStatus = () => {
  return useQuery({
    queryKey: ['ebay', 'status'],
    queryFn: ebayApi.getStatus,
    refetchInterval: 60000, // Refetch every minute
  });
};

export const useEbayMarketplaces = () => {
  return useQuery({
    queryKey: ['ebay', 'marketplaces'],
    queryFn: ebayApi.getMarketplaces,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};

export const useEbayConnect = () => {
  return useMutation({
    mutationFn: ebayApi.connect,
    onSuccess: (data) => {
      window.location.href = data.authorization_url;
    },
    onError: (error: any) => {
      toast.error(`Erreur: ${error.response?.data?.detail || error.message}`);
    },
  });
};

export const useEbayDisconnect = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ebayApi.disconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ebay', 'status'] });
      toast.success('Compte eBay déconnecté');
    },
    onError: (error: any) => {
      toast.error(`Erreur: ${error.response?.data?.detail || error.message}`);
    },
  });
};

export const usePublishToEbay = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ebayApi.publishProduct,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`✅ Produit publié! Listing ID: ${data.listing_id}`);
    },
    onError: (error: any) => {
      toast.error(`Erreur: ${error.response?.data?.detail || error.message}`);
    },
  });
};

export const useEbayOrders = (params?: { status?: string; limit?: number }) => {
  return useQuery({
    queryKey: ['ebay', 'orders', params],
    queryFn: () => ebayApi.getOrders(params),
    enabled: !!params, // Only fetch if params provided
  });
};
```

### `src/hooks/useEtsy.ts`

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { etsyApi } from '@/services/marketplaces/etsy';
import { toast } from 'sonner';

export const useEtsyStatus = () => {
  return useQuery({
    queryKey: ['etsy', 'status'],
    queryFn: etsyApi.getStatus,
    refetchInterval: 60000,
  });
};

export const useEtsyShop = () => {
  return useQuery({
    queryKey: ['etsy', 'shop'],
    queryFn: etsyApi.getShop,
  });
};

export const useEtsyConnect = () => {
  return useMutation({
    mutationFn: etsyApi.connect,
    onSuccess: (data) => {
      window.location.href = data.authorization_url;
    },
    onError: (error: any) => {
      toast.error(`Erreur: ${error.response?.data?.detail || error.message}`);
    },
  });
};

export const useEtsyDisconnect = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: etsyApi.disconnect,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etsy', 'status'] });
      toast.success('Boutique Etsy déconnectée');
    },
    onError: (error: any) => {
      toast.error(`Erreur: ${error.response?.data?.detail || error.message}`);
    },
  });
};

export const usePublishToEtsy = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: etsyApi.publishProduct,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success(`✅ Produit publié sur Etsy!`);
    },
    onError: (error: any) => {
      toast.error(`Erreur: ${error.response?.data?.detail || error.message}`);
    },
  });
};

export const useEtsyListings = (params?: { limit?: number; offset?: number }) => {
  return useQuery({
    queryKey: ['etsy', 'listings', params],
    queryFn: () => etsyApi.getActiveListings(params),
  });
};

export const useEtsyTaxonomy = (search?: string) => {
  return useQuery({
    queryKey: ['etsy', 'taxonomy', search],
    queryFn: () => etsyApi.getTaxonomy(search),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useEtsyOrders = (params?: {
  status_filter?: string;
  limit?: number;
  offset?: number;
}) => {
  return useQuery({
    queryKey: ['etsy', 'orders', params],
    queryFn: () => etsyApi.getOrders(params),
  });
};
```

---

## 🎨 Composants UI Complets

### `src/components/marketplaces/MarketplaceCard.tsx`

```typescript
'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';

interface MarketplaceCardProps {
  platform: 'ebay' | 'etsy';
  connected: boolean;
  loading: boolean;
  shopName?: string;
  userId?: string;
  expiresAt?: string;
  onConnect: () => void;
  onDisconnect: () => void;
}

export function MarketplaceCard({
  platform,
  connected,
  loading,
  shopName,
  userId,
  expiresAt,
  onConnect,
  onDisconnect,
}: MarketplaceCardProps) {
  const platformConfig = {
    ebay: {
      name: 'eBay',
      color: 'bg-blue-600',
      logo: '🏪',
    },
    etsy: {
      name: 'Etsy',
      color: 'bg-orange-600',
      logo: '🎨',
    },
  };

  const config = platformConfig[platform];

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-4xl">{config.logo}</span>
            <div>
              <CardTitle>{config.name}</CardTitle>
              <CardDescription>
                {connected ? 'Compte connecté' : 'Non connecté'}
              </CardDescription>
            </div>
          </div>
          <Badge variant={connected ? 'default' : 'secondary'}>
            {connected ? 'Connecté' : 'Non connecté'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {connected ? (
          <>
            {shopName && (
              <div>
                <p className="text-sm text-muted-foreground">Boutique</p>
                <p className="font-medium">{shopName}</p>
              </div>
            )}

            {userId && (
              <div>
                <p className="text-sm text-muted-foreground">User ID</p>
                <p className="font-medium">{userId}</p>
              </div>
            )}

            {expiresAt && (
              <div>
                <p className="text-sm text-muted-foreground">Token expire le</p>
                <p className="font-medium">
                  {new Date(expiresAt).toLocaleString('fr-FR')}
                </p>
              </div>
            )}

            <Button onClick={onDisconnect} variant="destructive" className="w-full">
              Déconnecter
            </Button>
          </>
        ) : (
          <>
            <p className="text-sm text-muted-foreground">
              Connectez votre compte {config.name} pour publier vos produits
            </p>
            <Button onClick={onConnect} className={`w-full ${config.color}`}>
              Connecter {config.name}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
```

### `src/components/marketplaces/PublishDialog.tsx`

```typescript
'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { usePublishToEbay } from '@/hooks/useEbay';
import { usePublishToEtsy } from '@/hooks/useEtsy';

interface PublishDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  productId: number;
  productTitle: string;
}

export function PublishDialog({ open, onOpenChange, productId, productTitle }: PublishDialogProps) {
  const [platform, setPlatform] = useState<'ebay' | 'etsy'>('ebay');

  // eBay state
  const [ebayMarketplace, setEbayMarketplace] = useState('EBAY_FR');
  const [ebayCategory, setEbayCategory] = useState('');

  // Etsy state
  const [etsyTaxonomy, setEtsyTaxonomy] = useState('');
  const [etsyState, setEtsyState] = useState<'active' | 'draft'>('draft');

  const publishToEbay = usePublishToEbay();
  const publishToEtsy = usePublishToEtsy();

  const handlePublish = () => {
    if (platform === 'ebay') {
      publishToEbay.mutate(
        {
          product_id: productId,
          marketplace_id: ebayMarketplace,
          category_id: ebayCategory || undefined,
        },
        {
          onSuccess: () => onOpenChange(false),
        }
      );
    } else {
      if (!etsyTaxonomy) {
        alert('Veuillez sélectionner une catégorie Etsy');
        return;
      }

      publishToEtsy.mutate(
        {
          product_id: productId,
          taxonomy_id: parseInt(etsyTaxonomy),
          state: etsyState,
        },
        {
          onSuccess: () => onOpenChange(false),
        }
      );
    }
  };

  const isLoading = publishToEbay.isPending || publishToEtsy.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[525px]">
        <DialogHeader>
          <DialogTitle>Publier sur Marketplace</DialogTitle>
          <DialogDescription>
            Publier "{productTitle}" sur eBay ou Etsy
          </DialogDescription>
        </DialogHeader>

        <Tabs value={platform} onValueChange={(v) => setPlatform(v as any)}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="ebay">eBay</TabsTrigger>
            <TabsTrigger value="etsy">Etsy</TabsTrigger>
          </TabsList>

          <TabsContent value="ebay" className="space-y-4">
            <div>
              <Label htmlFor="marketplace">Marketplace</Label>
              <Select value={ebayMarketplace} onValueChange={setEbayMarketplace}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="EBAY_FR">eBay France</SelectItem>
                  <SelectItem value="EBAY_US">eBay USA</SelectItem>
                  <SelectItem value="EBAY_UK">eBay UK</SelectItem>
                  <SelectItem value="EBAY_DE">eBay Allemagne</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="category">Catégorie eBay (optionnel)</Label>
              <Input
                id="category"
                placeholder="Ex: 11450 (T-shirts)"
                value={ebayCategory}
                onChange={(e) => setEbayCategory(e.target.value)}
              />
            </div>
          </TabsContent>

          <TabsContent value="etsy" className="space-y-4">
            <div>
              <Label htmlFor="taxonomy">Taxonomy ID *</Label>
              <Input
                id="taxonomy"
                type="number"
                placeholder="Ex: 1234"
                value={etsyTaxonomy}
                onChange={(e) => setEtsyTaxonomy(e.target.value)}
              />
            </div>

            <div>
              <Label htmlFor="state">État du listing</Label>
              <Select value={etsyState} onValueChange={(v) => setEtsyState(v as any)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Brouillon</SelectItem>
                  <SelectItem value="active">Actif</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </TabsContent>
        </Tabs>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Annuler
          </Button>
          <Button onClick={handlePublish} disabled={isLoading}>
            {isLoading ? 'Publication...' : 'Publier'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

---

## 📄 Page Complète - Intégrations

### `src/app/dashboard/integrations/page.tsx`

```typescript
'use client';

import { MarketplaceCard } from '@/components/marketplaces/MarketplaceCard';
import { useEbayStatus, useEbayConnect, useEbayDisconnect } from '@/hooks/useEbay';
import { useEtsyStatus, useEtsyConnect, useEtsyDisconnect } from '@/hooks/useEtsy';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { InfoIcon } from 'lucide-react';

export default function IntegrationsPage() {
  // eBay
  const { data: ebayStatus, isLoading: ebayLoading } = useEbayStatus();
  const ebayConnect = useEbayConnect();
  const ebayDisconnect = useEbayDisconnect();

  // Etsy
  const { data: etsyStatus, isLoading: etsyLoading } = useEtsyStatus();
  const etsyConnect = useEtsyConnect();
  const etsyDisconnect = useEtsyDisconnect();

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Intégrations Marketplaces</h1>
        <p className="text-muted-foreground">
          Connectez vos comptes eBay et Etsy pour publier vos produits
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <MarketplaceCard
          platform="ebay"
          connected={ebayStatus?.connected ?? false}
          loading={ebayLoading}
          userId={ebayStatus?.user_id}
          expiresAt={ebayStatus?.access_token_expires_at}
          onConnect={() => ebayConnect.mutate()}
          onDisconnect={() => ebayDisconnect.mutate()}
        />

        <MarketplaceCard
          platform="etsy"
          connected={etsyStatus?.connected ?? false}
          loading={etsyLoading}
          shopName={etsyStatus?.shop_name}
          userId={etsyStatus?.shop_id}
          expiresAt={etsyStatus?.access_token_expires_at}
          onConnect={() => etsyConnect.mutate()}
          onDisconnect={() => etsyDisconnect.mutate()}
        />
      </div>

      <Alert>
        <InfoIcon className="h-4 w-4" />
        <AlertDescription>
          <ul className="list-disc list-inside space-y-1 text-sm">
            <li>Les tokens eBay expirent après 2 heures (refresh automatique)</li>
            <li>Les tokens Etsy expirent après 1 heure (refresh automatique)</li>
            <li>Etsy utilise un système de polling toutes les 5-15 minutes</li>
            <li>Vos credentials sont stockés de manière sécurisée</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  );
}
```

---

## ✅ Checklist Finale

- [ ] Installer dépendances: `npm install axios @tanstack/react-query zustand sonner`
- [ ] Créer `src/lib/api.ts`
- [ ] Créer `src/store/authStore.ts`
- [ ] Créer `src/services/marketplaces/ebay.ts`
- [ ] Créer `src/services/marketplaces/etsy.ts`
- [ ] Créer `src/hooks/useEbay.ts`
- [ ] Créer `src/hooks/useEtsy.ts`
- [ ] Créer `src/components/marketplaces/MarketplaceCard.tsx`
- [ ] Créer `src/components/marketplaces/PublishDialog.tsx`
- [ ] Créer `src/app/dashboard/integrations/page.tsx`
- [ ] Créer `src/app/ebay/callback/page.tsx`
- [ ] Créer `src/app/etsy/callback/page.tsx`
- [ ] Tester connexion eBay
- [ ] Tester connexion Etsy
- [ ] Tester publication

---

**Prêt à copier-coller!** 🚀
