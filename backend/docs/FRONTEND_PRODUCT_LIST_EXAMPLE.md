# Example Complet - Liste Produits avec Publication

## 📦 Composant Liste de Produits avec Actions

### `src/app/dashboard/products/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { PublishDialog } from '@/components/marketplaces/PublishDialog';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Upload } from 'lucide-react';

interface Product {
  id: number;
  sku: string;
  title: string;
  price: number;
  brand: string;
  category: string;
  status: 'DRAFT' | 'PUBLISHED' | 'SOLD' | 'ARCHIVED';
  stock_quantity: number;
  created_at: string;
}

interface ProductsResponse {
  products: Product[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function ProductsPage() {
  const [page, setPage] = useState(1);
  const [publishDialogOpen, setPublishDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Fetch products
  const { data, isLoading, error } = useQuery<ProductsResponse>({
    queryKey: ['products', page],
    queryFn: async () => {
      const { data } = await api.get(`/products/?skip=${(page - 1) * 10}&limit=10`);
      return data;
    },
  });

  const handlePublish = (product: Product) => {
    setSelectedProduct(product);
    setPublishDialogOpen(true);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <p className="text-red-600">Erreur de chargement des produits</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Produits</h1>
          <p className="text-muted-foreground">
            {data?.total || 0} produits au total
          </p>
        </div>
        <Button>
          <Upload className="mr-2 h-4 w-4" />
          Ajouter un produit
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Liste des produits</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>SKU</TableHead>
                <TableHead>Titre</TableHead>
                <TableHead>Marque</TableHead>
                <TableHead>Prix</TableHead>
                <TableHead>Stock</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.products.map((product) => (
                <TableRow key={product.id}>
                  <TableCell className="font-mono text-sm">
                    {product.sku}
                  </TableCell>
                  <TableCell className="font-medium">
                    {product.title}
                  </TableCell>
                  <TableCell>{product.brand}</TableCell>
                  <TableCell>{product.price.toFixed(2)} €</TableCell>
                  <TableCell>{product.stock_quantity}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        product.status === 'PUBLISHED'
                          ? 'default'
                          : product.status === 'SOLD'
                          ? 'secondary'
                          : 'outline'
                      }
                    >
                      {product.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button
                      size="sm"
                      onClick={() => handlePublish(product)}
                      disabled={product.status === 'SOLD'}
                    >
                      Publier
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-4">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                Précédent
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {page} sur {data.total_pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
              >
                Suivant
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Publish Dialog */}
      {selectedProduct && (
        <PublishDialog
          open={publishDialogOpen}
          onOpenChange={setPublishDialogOpen}
          productId={selectedProduct.id}
          productTitle={selectedProduct.title}
        />
      )}
    </div>
  );
}
```

---

## 🎯 Composant Détails Produit avec Multi-Marketplace

### `src/app/dashboard/products/[id]/page.tsx`

```typescript
'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { ebayApi } from '@/services/marketplaces/ebay';
import { etsyApi } from '@/services/marketplaces/etsy';

interface Product {
  id: number;
  sku: string;
  title: string;
  description: string;
  price: number;
  brand: string;
  category: string;
  condition: string;
  status: string;
  product_images: Array<{ id: number; image_path: string; display_order: number }>;
}

interface MarketplacePublication {
  platform: 'ebay' | 'etsy';
  listing_id: string;
  status: string;
  url: string;
  published_at: string;
}

export default function ProductDetailPage() {
  const params = useParams();
  const productId = parseInt(params.id as string);
  const queryClient = useQueryClient();

  const [ebayMarketplace, setEbayMarketplace] = useState('EBAY_FR');
  const [etsyTaxonomy, setEtsyTaxonomy] = useState('');

  // Fetch product
  const { data: product, isLoading } = useQuery<Product>({
    queryKey: ['product', productId],
    queryFn: async () => {
      const { data } = await api.get(`/products/${productId}`);
      return data;
    },
  });

  // Fetch marketplace publications (custom endpoint à créer si besoin)
  const { data: publications } = useQuery<MarketplacePublication[]>({
    queryKey: ['product', productId, 'publications'],
    queryFn: async () => {
      const { data } = await api.get(`/products/${productId}/publications`);
      return data;
    },
    enabled: !!product,
  });

  // Publish to eBay
  const publishEbay = useMutation({
    mutationFn: () =>
      ebayApi.publishProduct({
        product_id: productId,
        marketplace_id: ebayMarketplace,
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['product', productId, 'publications'] });
      toast.success(`✅ Publié sur eBay! Listing: ${data.listing_id}`);
    },
    onError: (error: any) => {
      toast.error(`Erreur eBay: ${error.response?.data?.detail || error.message}`);
    },
  });

  // Publish to Etsy
  const publishEtsy = useMutation({
    mutationFn: () =>
      etsyApi.publishProduct({
        product_id: productId,
        taxonomy_id: parseInt(etsyTaxonomy),
        state: 'active',
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['product', productId, 'publications'] });
      toast.success(`✅ Publié sur Etsy!`);
    },
    onError: (error: any) => {
      toast.error(`Erreur Etsy: ${error.response?.data?.detail || error.message}`);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!product) {
    return <div>Produit non trouvé</div>;
  }

  const isPublishedOnEbay = publications?.some((p) => p.platform === 'ebay');
  const isPublishedOnEtsy = publications?.some((p) => p.platform === 'etsy');

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{product.title}</h1>
        <p className="text-muted-foreground">SKU: {product.sku}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Product Info */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Informations Produit</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Prix</p>
                <p className="text-2xl font-bold">{product.price.toFixed(2)} €</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <Badge>{product.status}</Badge>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Marque</p>
                <p className="font-medium">{product.brand}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Catégorie</p>
                <p className="font-medium">{product.category}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Condition</p>
                <p className="font-medium">{product.condition}</p>
              </div>
            </div>

            <div>
              <p className="text-sm text-muted-foreground mb-2">Description</p>
              <p className="text-sm">{product.description}</p>
            </div>

            {/* Images */}
            {product.product_images.length > 0 && (
              <div>
                <p className="text-sm text-muted-foreground mb-2">Images</p>
                <div className="grid grid-cols-4 gap-2">
                  {product.product_images.map((img) => (
                    <img
                      key={img.id}
                      src={`/${img.image_path}`}
                      alt=""
                      className="w-full h-24 object-cover rounded border"
                    />
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Marketplace Publications */}
        <Card>
          <CardHeader>
            <CardTitle>Marketplaces</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="ebay">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="ebay">
                  eBay {isPublishedOnEbay && '✅'}
                </TabsTrigger>
                <TabsTrigger value="etsy">
                  Etsy {isPublishedOnEtsy && '✅'}
                </TabsTrigger>
              </TabsList>

              <TabsContent value="ebay" className="space-y-4">
                {isPublishedOnEbay ? (
                  <div className="space-y-2">
                    <Badge variant="default">Publié</Badge>
                    {publications
                      ?.filter((p) => p.platform === 'ebay')
                      .map((pub) => (
                        <div key={pub.listing_id} className="text-sm">
                          <p className="font-medium">Listing: {pub.listing_id}</p>
                          <a
                            href={pub.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline"
                          >
                            Voir sur eBay →
                          </a>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Marketplace</label>
                      <select
                        className="w-full mt-1 px-3 py-2 border rounded"
                        value={ebayMarketplace}
                        onChange={(e) => setEbayMarketplace(e.target.value)}
                      >
                        <option value="EBAY_FR">eBay France</option>
                        <option value="EBAY_US">eBay USA</option>
                        <option value="EBAY_UK">eBay UK</option>
                      </select>
                    </div>

                    <Button
                      className="w-full"
                      onClick={() => publishEbay.mutate()}
                      disabled={publishEbay.isPending}
                    >
                      {publishEbay.isPending ? 'Publication...' : 'Publier sur eBay'}
                    </Button>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="etsy" className="space-y-4">
                {isPublishedOnEtsy ? (
                  <div className="space-y-2">
                    <Badge variant="default">Publié</Badge>
                    {publications
                      ?.filter((p) => p.platform === 'etsy')
                      .map((pub) => (
                        <div key={pub.listing_id} className="text-sm">
                          <p className="font-medium">Listing: {pub.listing_id}</p>
                          <a
                            href={pub.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-orange-600 hover:underline"
                          >
                            Voir sur Etsy →
                          </a>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">Taxonomy ID</label>
                      <input
                        type="number"
                        className="w-full mt-1 px-3 py-2 border rounded"
                        placeholder="Ex: 1234"
                        value={etsyTaxonomy}
                        onChange={(e) => setEtsyTaxonomy(e.target.value)}
                      />
                    </div>

                    <Button
                      className="w-full bg-orange-600 hover:bg-orange-700"
                      onClick={() => publishEtsy.mutate()}
                      disabled={publishEtsy.isPending || !etsyTaxonomy}
                    >
                      {publishEtsy.isPending ? 'Publication...' : 'Publier sur Etsy'}
                    </Button>
                  </div>
                )}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

## 📊 Dashboard avec Statistiques

### `src/app/dashboard/page.tsx`

```typescript
'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useEbayStatus } from '@/hooks/useEbay';
import { useEtsyStatus } from '@/hooks/useEtsy';
import { Package, ShoppingCart, TrendingUp, DollarSign } from 'lucide-react';

interface DashboardStats {
  total_products: number;
  published_products: number;
  sold_products: number;
  total_revenue: number;
  ebay_listings: number;
  etsy_listings: number;
  pending_orders: number;
}

export default function DashboardPage() {
  const { data: ebayStatus } = useEbayStatus();
  const { data: etsyStatus } = useEtsyStatus();

  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ['dashboard', 'stats'],
    queryFn: async () => {
      const { data } = await api.get('/dashboard/stats');
      return data;
    },
  });

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Tableau de Bord</h1>
        <p className="text-muted-foreground">
          Vue d'ensemble de votre activité Stoflow
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Produits</CardTitle>
            <Package className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_products || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.published_products || 0} publiés
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Commandes</CardTitle>
            <ShoppingCart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending_orders || 0}</div>
            <p className="text-xs text-muted-foreground">En attente</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Vendus</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.sold_products || 0}</div>
            <p className="text-xs text-muted-foreground">Ce mois</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Revenu</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats?.total_revenue.toFixed(2) || '0.00'} €
            </div>
            <p className="text-xs text-muted-foreground">Total</p>
          </CardContent>
        </Card>
      </div>

      {/* Marketplace Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>eBay</CardTitle>
          </CardHeader>
          <CardContent>
            {ebayStatus?.connected ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full" />
                  <span className="text-sm font-medium">Connecté</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {stats?.ebay_listings || 0} listings actifs
                </p>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-gray-300 rounded-full" />
                <span className="text-sm text-muted-foreground">Non connecté</span>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Etsy</CardTitle>
          </CardHeader>
          <CardContent>
            {etsyStatus?.connected ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full" />
                  <span className="text-sm font-medium">Connecté</span>
                </div>
                <p className="text-sm text-muted-foreground">
                  {stats?.etsy_listings || 0} listings actifs
                </p>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 bg-gray-300 rounded-full" />
                <span className="text-sm text-muted-foreground">Non connecté</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

---

## ✅ Backend Endpoint Manquant (à créer)

### `api/dashboard.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.dependencies import get_current_user, get_db
from models.public.user import User
from models.user.product import Product, ProductStatus
from decimal import Decimal

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Récupère les statistiques du dashboard."""

    # Total products
    total_products = db.query(Product).filter(
        Product.deleted_at.is_(None)
    ).count()

    # Published products
    published_products = db.query(Product).filter(
        Product.status == ProductStatus.PUBLISHED,
        Product.deleted_at.is_(None)
    ).count()

    # Sold products
    sold_products = db.query(Product).filter(
        Product.status == ProductStatus.SOLD,
        Product.deleted_at.is_(None)
    ).count()

    # Total revenue (from sold products)
    sold_items = db.query(Product).filter(
        Product.status == ProductStatus.SOLD,
        Product.deleted_at.is_(None)
    ).all()

    total_revenue = sum(p.price for p in sold_items)

    return {
        "total_products": total_products,
        "published_products": published_products,
        "sold_products": sold_products,
        "total_revenue": float(total_revenue),
        "ebay_listings": 0,  # TODO: Count from publications table
        "etsy_listings": 0,  # TODO: Count from publications table
        "pending_orders": 0,  # TODO: Count from orders
    }
```

Puis dans `main.py`:

```python
from api.dashboard import router as dashboard_router

app.include_router(dashboard_router, prefix="/api")
```

---

Voilà ! Tu as maintenant **tous les éléments** pour connecter le frontend aux endpoints eBay et Etsy ! 🚀

**Résumé des fichiers créés:**
1. ✅ Guide d'intégration complet
2. ✅ Exemples de code copy-paste ready
3. ✅ Exemple de liste produits
4. ✅ Exemple de dashboard

Tout est prêt pour être utilisé côté frontend ! 💪
