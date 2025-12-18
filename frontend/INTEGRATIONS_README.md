# Intégrations eBay & Etsy - Frontend

## ✅ Ce qui a été implémenté

### Composables (API Services)
1. **`composables/useEbay.ts`** - Service eBay complet
   - `connect()` - Démarre OAuth2
   - `getConnectionStatus()` - Vérifie le statut
   - `disconnect()` - Déconnexion
   - `getMarketplaces()` - Liste des marketplaces
   - `publishProduct()` - Publication produit
   - `unpublishProduct()` - Dépublication
   - `getOrders()` - Récupération commandes

2. **`composables/useEtsy.ts`** - Service Etsy complet
   - `connect()` - Démarre OAuth2 avec PKCE
   - `getConnectionStatus()` - Vérifie le statut
   - `disconnect()` - Déconnexion
   - `getShopInfo()` - Infos boutique
   - `publishProduct()` - Publication produit
   - `updateProduct()` - Mise à jour listing
   - `deleteProduct()` - Suppression listing
   - `getActiveListings()` - Liste listings actifs
   - `getOrders()` - Récupération commandes
   - `getTaxonomyNodes()` - Catégories Etsy
   - `getShippingProfiles()` - Profils expédition
   - `triggerPolling()` - Déclencher polling manuel

### Pages
1. **`pages/ebay/callback.vue`** - Page callback OAuth2 eBay
   - Gère le retour OAuth
   - Affiche status (processing/success/error)
   - Redirige vers `/dashboard/integrations`

2. **`pages/etsy/callback.vue`** - Page callback OAuth2 Etsy
   - Gère le retour OAuth (PKCE)
   - Affiche nom boutique
   - Redirige vers `/dashboard/integrations`

3. **`pages/dashboard/integrations.vue`** - Page principale intégrations
   - Affiche status eBay et Etsy
   - Boutons connexion/déconnexion
   - Infos tokens et expiration
   - Toasts pour notifications

### Composants
1. **`components/integrations/MarketplaceCard.vue`** - Card pour marketplace
   - Props: platform, connected, loading, shopName, userId, expiresAt
   - Emit: connect, disconnect
   - Affichage différencié eBay/Etsy
   - Tags status
   - Formatage dates

2. **`components/integrations/PublishDialog.vue`** - Dialog publication
   - Sélection plateforme (eBay/Etsy)
   - Options eBay: marketplace, catégorie
   - Options Etsy: taxonomy ID, état listing
   - Validation formulaire
   - Gestion erreurs

### Configuration
- **`.env`** - Variables environnement
  ```env
  NUXT_PUBLIC_API_URL=http://localhost:8000
  NUXT_PUBLIC_EBAY_CALLBACK_URL=http://localhost:3000/ebay/callback
  NUXT_PUBLIC_ETSY_CALLBACK_URL=http://localhost:3000/etsy/callback
  ```

---

## 🚀 Utilisation

### 1. Accéder à la page intégrations
```
http://localhost:3000/dashboard/integrations
```

### 2. Connecter eBay
1. Cliquer sur "Connecter eBay"
2. Vous serez redirigé vers eBay OAuth2
3. Autorisez l'application
4. Retour automatique vers `/ebay/callback`
5. Redirection vers `/dashboard/integrations`

### 3. Connecter Etsy
1. Cliquer sur "Connecter Etsy"
2. Vous serez redirigé vers Etsy OAuth2 (PKCE)
3. Autorisez l'application
4. Retour automatique vers `/etsy/callback`
5. Redirection vers `/dashboard/integrations`

### 4. Publier un produit
Dans n'importe quelle page produit, utilisez le composant:

```vue
<PublishDialog
  v-model="showDialog"
  :product-id="product.id"
  :product-title="product.title"
  @published="handlePublished"
/>
```

---

## 📋 Checklist Intégration

- [x] Composables eBay créé
- [x] Composables Etsy créé
- [x] Pages callback OAuth créées
- [x] Page intégrations créée
- [x] Composant MarketplaceCard créé
- [x] Composant PublishDialog créé
- [x] Variables .env configurées
- [ ] Tester connexion eBay
- [ ] Tester connexion Etsy
- [ ] Tester publication eBay
- [ ] Tester publication Etsy

---

## 🔧 Configuration Backend Requise

Assurez-vous que le backend est configuré dans `.env`:

```env
# eBay
EBAY_APP_ID=your_app_id
EBAY_CERT_ID=your_cert_id
EBAY_DEV_ID=your_dev_id
EBAY_REDIRECT_URI=http://localhost:3000/ebay/callback

# Etsy
ETSY_API_KEY=your_client_id
ETSY_API_SECRET=your_client_secret
ETSY_REDIRECT_URI=http://localhost:3000/etsy/callback

# CORS
CORS_ORIGINS=http://localhost:3000
```

---

## 🎨 Styles PrimeVue

Les composants utilisent PrimeVue:
- Card
- Button
- Tag
- Dialog
- Dropdown
- SelectButton
- InputText
- InputNumber
- Toast
- ProgressSpinner

Tous les composants sont déjà stylés et responsive.

---

## 📱 Responsive

Tous les composants sont responsive:
- Grid 1 colonne sur mobile
- Grid 2 colonnes sur desktop (>768px)
- Dialogs adaptés mobile

---

## 🔐 Sécurité

- JWT automatique via `useApi()`
- Tokens stockés dans le store auth
- Redirect auto si 401 (token expiré)
- CSRF protection via state parameter OAuth

---

## 🎯 Prochaines Étapes

1. **Intégrer dans liste produits**
   - Ajouter bouton "Publier" sur chaque produit
   - Ouvrir PublishDialog au clic

2. **Dashboard statistiques**
   - Nombre de listings actifs par marketplace
   - Commandes en attente
   - Graphiques ventes

3. **Gestion listings**
   - Page liste des listings actifs
   - Bouton dépublier
   - Sync automatique

4. **Gestion commandes**
   - Page liste commandes eBay/Etsy
   - Statuts commandes
   - Tracking

---

**Tout est prêt !** 🚀

Le frontend est maintenant complètement intégré avec le backend eBay et Etsy.
