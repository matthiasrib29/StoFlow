# Guide de Configuration Stripe pour Stoflow

Ce guide vous explique comment configurer Stripe pour activer les paiements dans Stoflow.

## 📋 Prérequis

- Un compte Stripe (créer un compte sur https://stripe.com)
- Accès au Dashboard Stripe (https://dashboard.stripe.com)

## 🔑 Étape 1: Récupérer les Clés API

### Mode Test (Développement)

1. Connectez-vous au [Dashboard Stripe](https://dashboard.stripe.com)
2. Activez le **mode Test** (toggle en haut à droite)
3. Allez dans **Developers** → **API keys**
4. Copiez les clés suivantes:
   - **Publishable key** (commence par `pk_test_`)
   - **Secret key** (commence par `sk_test_`)

### Mode Production

⚠️ **Attention**: N'utilisez les clés de production QUE sur un serveur sécurisé (HTTPS)

1. Désactivez le **mode Test**
2. Allez dans **Developers** → **API keys**
3. Copiez les clés suivantes:
   - **Publishable key** (commence par `pk_live_`)
   - **Secret key** (commence par `sk_live_`)

## ⚙️ Étape 2: Configurer les Variables d'Environnement

Éditez votre fichier `.env` (backend):

```bash
# Mode Test
STRIPE_SECRET_KEY=sk_test_VOTRE_CLE_SECRETE
STRIPE_PUBLISHABLE_KEY=pk_test_VOTRE_CLE_PUBLIQUE
STRIPE_WEBHOOK_SECRET=whsec_VOTRE_WEBHOOK_SECRET  # Voir étape 3

# URL Frontend pour les redirections
FRONTEND_BASE_URL=http://localhost:3000  # ou votre domaine en production
```

⚠️ **Sécurité**:
- **JAMAIS** commiter les clés de production dans Git
- Utilisez des variables d'environnement ou un gestionnaire de secrets
- Les clés secrètes doivent rester côté backend uniquement

## 🔔 Étape 3: Configurer les Webhooks

Les webhooks permettent à Stripe de notifier votre backend des événements (paiement réussi, échec, etc.).

### En Développement (avec Stripe CLI)

1. Installez [Stripe CLI](https://stripe.com/docs/stripe-cli)

2. Authentifiez-vous:
   ```bash
   stripe login
   ```

3. Écoutez les événements localement:
   ```bash
   stripe listen --forward-to http://localhost:8000/api/stripe/webhook
   ```

4. Stripe CLI vous donnera un **webhook secret** (commence par `whsec_`)
   Copiez-le dans votre `.env`:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_xxx
   ```

### En Production

1. Allez dans **Developers** → **Webhooks**
2. Cliquez sur **Add endpoint**
3. Configurez:
   - **Endpoint URL**: `https://votredomaine.com/api/stripe/webhook`
   - **Events to send**: Sélectionnez:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

4. Cliquez sur **Add endpoint**
5. Dans la page de l'endpoint, révélez le **Signing secret** (commence par `whsec_`)
6. Copiez-le dans votre `.env` de production

## 📦 Étape 4: Configurer le Customer Portal

Le Customer Portal permet aux clients de gérer leur abonnement (annulation, mise à jour du moyen de paiement, etc.).

1. Allez dans **Settings** → **Billing** → **Customer portal**
2. Cliquez sur **Activate test link** (mode Test) ou **Activate** (mode Production)
3. Configurez les options:
   - **Allow customers to**:
     - ✅ Update payment methods
     - ✅ Cancel subscriptions
     - ✅ View invoices
   - **After canceling**:
     - Choisissez "Cancel immediately" ou "Cancel at end of billing period"

4. Cliquez sur **Save**

## 🧪 Étape 5: Tester en Mode Test

### Cartes de Test

Utilisez ces numéros de carte pour tester:

| Carte | Numéro | Résultat |
|-------|--------|----------|
| Visa réussie | `4242 4242 4242 4242` | Paiement réussi |
| Visa déclinée | `4000 0000 0000 0002` | Paiement refusé |
| 3D Secure requis | `4000 0027 6000 3184` | Authentification SCA |

**Autres informations de test**:
- **Date d'expiration**: N'importe quelle date future (ex: 12/34)
- **CVV**: N'importe quel code 3 chiffres (ex: 123)
- **Code postal**: N'importe lequel (ex: 75001)

### Tester le Flow Complet

1. Démarrez le backend: `python3 -m uvicorn main:app --reload`
2. Démarrez le frontend: `npm run dev`
3. Démarrez Stripe CLI: `stripe listen --forward-to http://localhost:8000/api/stripe/webhook`
4. Connectez-vous et testez un paiement

## 🚀 Étape 6: Passage en Production

### Checklist avant Production

- [ ] Toutes les clés Test sont remplacées par les clés Production
- [ ] Le webhook de production est configuré et testé
- [ ] Le Customer Portal est activé en production
- [ ] HTTPS est activé sur votre domaine
- [ ] Les variables d'environnement sont dans un gestionnaire de secrets
- [ ] Les logs Stripe sont monitorés

### Activer le Mode Production

1. Dans le Dashboard Stripe, désactivez le **mode Test**
2. Vérifiez que votre compte est **activé** (Settings → Account)
3. Configurez les **paramètres fiscaux** si nécessaire (pour la TVA)
4. Testez un paiement réel avec une vraie carte

## 🛠️ Dépannage

### Webhook ne fonctionne pas

- Vérifiez que le `STRIPE_WEBHOOK_SECRET` est correct
- Vérifiez que l'URL du webhook est accessible publiquement (en production)
- Regardez les logs dans **Developers** → **Webhooks** → votre endpoint

### Erreur "Invalid API Key"

- Vérifiez que vous utilisez les bonnes clés (Test vs Production)
- Vérifiez que `STRIPE_SECRET_KEY` est bien configurée
- Vérifiez qu'il n'y a pas d'espaces ou de caractères invisibles

### Paiement refusé

- En test: Utilisez les [cartes de test Stripe](https://stripe.com/docs/testing)
- En production: Le paiement peut être refusé par la banque du client

### Session Checkout expire

- Les sessions Checkout expirent après 24h
- Le client doit recommencer le processus de paiement

## 📚 Ressources

- [Documentation Stripe](https://stripe.com/docs)
- [Stripe Checkout Guide](https://stripe.com/docs/payments/checkout)
- [Webhooks Guide](https://stripe.com/docs/webhooks)
- [API Reference](https://stripe.com/docs/api)
- [Test Cards](https://stripe.com/docs/testing)

## 🔒 Sécurité

- ✅ Toujours vérifier la signature des webhooks
- ✅ Utiliser HTTPS en production
- ✅ Ne jamais exposer les clés secrètes côté client
- ✅ Logger tous les événements de paiement
- ✅ Monitorer les tentatives de fraude dans le Dashboard Stripe

## 💡 Notes Importantes

### Prix et Devises

Les prix configurés dans votre backend sont en **EUR** (euros). Si vous souhaitez supporter d'autres devises:
1. Modifiez `shared/stripe_config.py`
2. Changez `currency: "eur"` en `currency: "usd"` (par exemple)
3. Adaptez les prix dans `models/public/subscription_quota.py`

### Abonnements Récurrents

- Les abonnements sont renouvelés automatiquement par Stripe
- Un webhook `invoice.payment_succeeded` est envoyé à chaque renouvellement
- Un webhook `invoice.payment_failed` est envoyé en cas d'échec
- Grace period de **3 jours** configuré pour les échecs de paiement

### Crédits IA

- Les crédits IA sont des **paiements one-time** (pas récurrents)
- Les crédits achetés ne s'épuisent jamais
- Les crédits mensuels (de l'abonnement) se renouvellent chaque mois

---

**Besoin d'aide ?** Contactez le support Stripe ou consultez la [documentation officielle](https://stripe.com/docs).
