# 🧹 Audit de Nettoyage du Plugin Stoflow

## ✅ Code Actif et Nécessaire

### Content Scripts
- **vinted.ts** (utilisé) : Script principal Vinted, gère messages et extraction userId/login
- **vinted-detector.ts** (utilisé) : Extrait userId + login depuis HTML
- **vinted-api-bridge.ts** (utilisé) : Hook Webpack pour accès API Vinted avancé
- **stoflow-web.ts** (utilisé) : Gère SSO sur localhost:3000
- **ebay.ts, etsy.ts** (conservés) : Placeholders pour futures intégrations

### API Helpers
- **StoflowAPI.ts** (utilisé) : Tous les endpoints backend actifs
- **VintedAPI.ts** (utilisé) : API Vinted avec cookies, 4/5 méthodes utilisées

### Background
- **background/index.ts** (utilisé) : Service worker principal
- **background/PollingManager.ts** (utilisé) : Système de tâches actif

### Composants Vue
- **Popup.vue** (utilisé) : Interface popup principale
- **VintedSessionInfo.vue** (utilisé) : Affiche userId + login
- **LoginForm.vue** (utilisé) : Formulaire de connexion Stoflow
- **DevModeBanner.vue** (utilisé) : Bannière mode développement
- **Options.vue** (utilisé) : Page de paramètres

---

## 🗑️ Code Obsolète à Supprimer

### 1. Dossier adapters/ (SUPPRIMÉ ✅)
- Dupliquait vinted-api-bridge.ts
- Utilisait ancien système fetch() au lieu de Webpack hook

### 2. Composants Vue non utilisés
```bash
# À supprimer
src/components/HttpProxyTest.vue    # Composant de test, jamais importé
src/components/UserDataCard.vue     # Composant de démo, jamais importé
```

### 3. Méthode VintedAPI inutilisée
**Fichier** : `src/api/VintedAPI.ts`
```typescript
// Ligne 140-154 : getProductDetails() jamais appelée
// À supprimer si on ne prévoit pas de l'utiliser
```

### 4. Méthode StoflowAPI potentiellement inutilisée
**Fichier** : `src/api/StoflowAPI.ts`
```typescript
// Ligne 83-115 : syncVintedUser() pas clairement utilisée
// À vérifier dans le backend si nécessaire
```

### 5. Code mort dans background/index.ts

#### injectSSOScript() (lignes 449-528)
```typescript
// 80 lignes jamais appelées
// L'injection dynamique est commentée ligne 66-73
// Remplacé par content script déclaratif stoflow-web.ts
```

#### handlePublishProduct() (lignes 341-345)
```typescript
// Placeholder TODO jamais implémenté
private async handlePublishProduct(productId: string, platforms: string[]): Promise<any> {
  BackgroundLogger.debug('Publishing product:', productId, 'to', platforms);
  // TODO: Implémenter la publication
  return { success: true };
}
```

#### Chrome Alarms Sync (incomplet)
**Lignes** : 347-402
```typescript
// startSync(), stopSync(), updateSyncInterval()
// handleAlarm(), checkForSales()
// checkForSales() est juste un TODO placeholder
// Options.vue utilise UPDATE_SYNC_INTERVAL mais l'alarme ne fait rien
// PollingManager fait déjà le même job (et fonctionne réellement)
```

#### startLocalhostTokenPolling() simplifié
**Ligne** : 533-551
```typescript
// Corps commenté, appelle juste checkAndRefreshTokenOnStartup()
// Peut être simplifié pour appeler directement la méthode
```

---

## 📝 Résumé des Actions

### Suppression immédiate recommandée
1. ✅ `src/adapters/` (déjà supprimé)
2. ⏳ `src/components/HttpProxyTest.vue`
3. ⏳ `src/components/UserDataCard.vue`
4. ⏳ `background/index.ts` : méthode `injectSSOScript()` (lignes 449-528)
5. ⏳ `background/index.ts` : méthode `handlePublishProduct()` (lignes 341-345)

### À décider avec l'utilisateur
6. ⏳ Chrome Alarms Sync (lignes 347-402) : Supprimer ou implémenter ?
7. ⏳ `VintedAPI.ts::getProductDetails()` : Supprimer ou conserver pour usage futur ?
8. ⏳ `StoflowAPI.ts::syncVintedUser()` : Vérifier utilisation backend

### Simplification recommandée
9. ⏳ `startLocalhostTokenPolling()` : Appel direct sans méthode wrapper

---

## 💾 Gain estimé
- **~150 lignes** de code mort supprimées
- **2 composants** Vue inutilisés retirés
- **1 dossier** adapters/ déjà supprimé
- **Code simplifié** et plus maintenable
