# eBay OAuth - Flow Manuel (URLs par défaut)

## 📋 Vue d'ensemble

Comme tu utilises les **URLs par défaut eBay** pour le redirect URI, le flow OAuth nécessite une étape manuelle pour copier le code d'autorisation.

## 🔄 Flow complet

### 1️⃣ Obtenir l'URL d'autorisation

Dans ton frontend, clique sur **"Synchroniser"** pour eBay. Cela va :
- Appeler `GET /api/integrations/ebay/connect`
- Recevoir une `auth_url` et un `state`
- Ouvrir une popup vers eBay

### 2️⃣ Autoriser sur eBay

Tu seras redirigé vers la page d'autorisation eBay :
```
https://auth.ebay.com/oauth2/authorize?
  client_id=YOUR_EBAY_CLIENT_ID&
  redirect_uri=YOUR_EBAY_RUNAME&
  response_type=code&
  scope=...&
  state=2:xxx
```

Connecte-toi avec ton compte eBay et clique sur **"Autoriser"**.

### 3️⃣ eBay te redirige vers sa page par défaut

Après autorisation, eBay te redirige vers :
```
https://signin.ebay.com/ws/eBayISAPI.dll?ThirdPartyAuthSucessFailure&isAuthSuccessful=true&code=v^1.1#...&expires_in=299
```

**IMPORTANT** : Cette URL contient le **code d'autorisation** dans le paramètre `code`.

### 4️⃣ Copier le code

Dans la barre d'adresse, tu verras une URL qui ressemble à :
```
https://signin.ebay.com/ws/eBayISAPI.dll?ThirdPartyAuthSucessFailure&isAuthSuccessful=true&code=v^1.1#i^1#p^3#...&expires_in=299
```

Le code commence par `v^1.1#i^1#p^3#...` et dure **299 secondes** (environ 5 minutes).

### 5️⃣ Soumettre le code au backend

**Option A : Via l'API directement**

```bash
curl -X POST "http://localhost:8000/api/integrations/ebay/submit-code" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "v^1.1#i^1#p^3#...",
    "state": "2:xxxxx",
    "sandbox": false
  }'
```

**Option B : Via le frontend (recommandé)**

Le frontend devrait afficher un champ de texte où tu peux coller :
- Soit **juste le code** : `v^1.1#i^1#p^3#...`
- Soit **l'URL complète** (le frontend extraira le code)

Le `state` est stocké dans le localStorage du frontend après l'étape 1.

### 6️⃣ Tokens sauvegardés

Une fois le code soumis, le backend :
- Échange le code contre des tokens OAuth2
- Sauvegarde les tokens dans `user_{id}.ebay_credentials`
- Retourne une confirmation

## 🎯 Endpoints disponibles

### `GET /api/integrations/ebay/connect`
Génère l'URL d'autorisation eBay.

**Response:**
```json
{
  "auth_url": "https://auth.ebay.com/oauth2/authorize?...",
  "state": "2:xxxxx"
}
```

### `POST /api/integrations/ebay/submit-code`
Soumet manuellement le code d'autorisation.

**Request:**
```json
{
  "code": "v^1.1#i^1#p^3#...",
  "state": "2:xxxxx",
  "sandbox": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "eBay account connected successfully",
  "access_token_expires_at": "2025-12-11T14:35:00Z",
  "refresh_token_expires_at": "2026-06-11T12:35:00Z"
}
```

### `GET /api/integrations/ebay/status`
Vérifie si le compte eBay est connecté.

**Response:**
```json
{
  "connected": true,
  "access_token_valid": true,
  "refresh_token_valid": true,
  "access_token_expires_at": "2025-12-11T14:35:00Z",
  "refresh_token_expires_at": "2026-06-11T12:35:00Z"
}
```

## 🔧 Configuration actuelle

### Backend `.env`
```env
EBAY_CLIENT_ID=your-ebay-client-id
EBAY_CLIENT_SECRET=your-ebay-client-secret
EBAY_REDIRECT_URI=your-ebay-runame
EBAY_API_ENV=production
```

### eBay Developer Portal
- **RuName**: `your-ebay-runame`
- **Auth Accepted URL**: Page par défaut eBay (https://signin.ebay.com/ws/eBayISAPI.dll?ThirdPartyAuthSucessFailure&isAuthSuccessful=true)
- **Auth Declined URL**: Page par défaut eBay

## 💡 Amélioration future (optionnelle)

Pour éviter l'étape manuelle, tu pourras plus tard :

1. **Utiliser ngrok** pour exposer ton localhost en HTTPS
2. **Modifier le RuName** sur eBay Developer Portal avec :
   - Auth Accepted URL: `https://xxx.ngrok.io/api/integrations/ebay/callback`
3. Le flow deviendra automatique (pas besoin de copier le code)

## 🐛 Dépannage

### Le code expire trop vite
Le code d'autorisation expire après **299 secondes** (5 minutes). Si tu mets trop de temps à le copier, recommence le flow depuis l'étape 1.

### Erreur "Invalid state parameter"
Assure-toi d'utiliser le même `state` que celui reçu à l'étape 1. Le frontend doit le stocker en localStorage.

### Erreur "Token exchange failed"
Vérifie que :
- Le code commence bien par `v^1.1#`
- Le code n'a pas expiré
- Les credentials eBay sont corrects dans `.env`

---

**Date**: 2025-12-11
**Auteur**: Claude
**Configuration**: Production eBay avec URLs par défaut
