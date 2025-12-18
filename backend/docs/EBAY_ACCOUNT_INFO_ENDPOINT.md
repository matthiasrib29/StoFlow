# eBay Account Information Endpoint

## Overview

Le endpoint `/api/integrations/ebay/account-info` permet de récupérer les informations du compte eBay connecté. Cela affiche des détails sur le compte eBay du seller, y compris les programmes auxquels il est inscrit et le nombre de politiques configurées.

## Endpoint

```
GET /api/integrations/ebay/account-info
```

## Authentication

**Required**: JWT Bearer token dans le header `Authorization`

```
Authorization: Bearer <your_jwt_token>
```

## Response

### Success Response (200 OK)

```json
{
  "success": true,
  "ebay_user_id": null,
  "sandbox_mode": false,
  "programs": [
    {
      "programType": "SELLING_POLICY_MANAGEMENT"
    }
  ],
  "fulfillment_policies_count": 2,
  "access_token_expires_at": "2025-12-11T16:58:09.601088+00:00"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Indique si la requête a réussi |
| `ebay_user_id` | string\|null | ID utilisateur eBay (peut être null) |
| `sandbox_mode` | boolean | `true` si en mode sandbox, `false` pour production |
| `programs` | array | Liste des programmes eBay auxquels le seller est inscrit |
| `programs[].programType` | string | Type de programme (ex: "SELLING_POLICY_MANAGEMENT") |
| `fulfillment_policies_count` | number\|null | Nombre de politiques de livraison configurées |
| `access_token_expires_at` | string | Date d'expiration du token d'accès (ISO 8601) |

### Error Responses

#### 404 - Not Connected
```json
{
  "detail": "eBay account not connected. Please connect first."
}
```

**Raison**: L'utilisateur n'a pas encore connecté son compte eBay via le flow OAuth.

#### 401 - Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

**Raison**: Le token JWT est invalide, expiré, ou manquant.

#### 401 - Token Expired
```json
{
  "detail": "eBay access token expired. Please reconnect your account."
}
```

**Raison**: Le token d'accès eBay a expiré. L'utilisateur doit se reconnecter.

#### 500 - Internal Server Error
```json
{
  "detail": "Failed to fetch eBay account info: <error_message>"
}
```

**Raison**: Erreur lors de l'appel à l'API eBay (credentials invalides, API eBay indisponible, etc.)

## Frontend Integration Example

### Vue 3 / Nuxt 3

```typescript
// Dans votre store ou composable
export const fetchEbayAccountInfo = async () => {
  try {
    const response = await $fetch('/api/integrations/ebay/account-info', {
      headers: {
        Authorization: `Bearer ${getAccessToken()}`
      }
    })

    return response
  } catch (error) {
    if (error.statusCode === 404) {
      console.error('Compte eBay non connecté')
    } else if (error.statusCode === 401) {
      console.error('Token expiré ou invalide')
    } else {
      console.error('Erreur lors de la récupération des infos eBay:', error)
    }
    throw error
  }
}
```

### Usage dans un composant

```vue
<script setup>
const ebayInfo = ref(null)
const loading = ref(false)
const error = ref(null)

const loadEbayInfo = async () => {
  loading.value = true
  error.value = null

  try {
    ebayInfo.value = await fetchEbayAccountInfo()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadEbayInfo()
})
</script>

<template>
  <div v-if="loading">Chargement...</div>
  <div v-else-if="error">Erreur: {{ error }}</div>
  <div v-else-if="ebayInfo">
    <h3>Compte eBay</h3>
    <p>Mode: {{ ebayInfo.sandbox_mode ? 'Sandbox' : 'Production' }}</p>
    <p>Token expire le: {{ new Date(ebayInfo.access_token_expires_at).toLocaleString() }}</p>

    <h4>Programmes inscrits:</h4>
    <ul>
      <li v-for="program in ebayInfo.programs" :key="program.programType">
        {{ program.programType }}
      </li>
    </ul>

    <p>Politiques de livraison: {{ ebayInfo.fulfillment_policies_count || 0 }}</p>
  </div>
</template>
```

## Use Cases

1. **Afficher le statut de connexion eBay**: Vérifier que le compte est bien connecté et afficher les informations de base
2. **Vérifier l'expiration du token**: Avertir l'utilisateur si le token expire bientôt
3. **Afficher les programmes actifs**: Montrer à l'utilisateur les fonctionnalités eBay auxquelles il a accès
4. **Validation du compte**: S'assurer que le compte est correctement configuré avant de publier des produits

## Notes

- **Performance**: L'endpoint fait 2 appels à l'API eBay (programmes + politiques), donc il peut prendre 2-3 secondes à répondre
- **Rate Limiting**: eBay limite le nombre d'appels API. Évitez d'appeler cet endpoint trop fréquemment
- **Caching**: Considérez de mettre en cache ces informations côté frontend (ex: 5-10 minutes)
- **Refresh Token**: Le backend gère automatiquement le refresh du token d'accès si nécessaire

## Endpoints Associés

- `GET /api/integrations/ebay/status` - Vérifier la connexion eBay (plus rapide, pas d'appel API eBay)
- `GET /api/integrations/ebay/connect` - Générer l'URL d'autorisation OAuth
- `POST /api/integrations/ebay/disconnect` - Déconnecter le compte eBay
