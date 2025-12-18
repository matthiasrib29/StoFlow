# Etsy Polling Service - Guide de Configuration

## 📋 Vue d'ensemble

Etsy n'a **PAS de webhooks natifs**, contrairement à eBay. Pour recevoir les mises à jour en temps quasi-réel, nous utilisons un **système de polling** qui interroge régulièrement l'API Etsy.

Ce service poll automatiquement:
- ✅ **Nouvelles commandes** (toutes les 5 minutes)
- ✅ **Listings mis à jour** (toutes les 15 minutes)
- ✅ **Stock faible** (toutes les 15 minutes)

---

## 🔧 Installation

### 1. Installer APScheduler

```bash
pip install apscheduler
```

Ou si déjà dans `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Configuration (.env)

Ajouter les variables de configuration dans `.env`:

```env
# Polling Intervals (en minutes)
ETSY_POLLING_INTERVAL_ORDERS=5
ETSY_POLLING_INTERVAL_LISTINGS=15
ETSY_POLLING_LOW_STOCK_THRESHOLD=5
```

### 3. Vérifier les credentials Etsy

Assurez-vous que les credentials Etsy sont configurés:

```env
ETSY_API_KEY=your-etsy-client-id
ETSY_API_SECRET=your-etsy-client-secret
ETSY_REDIRECT_URI=http://localhost:3000/etsy/callback
```

---

## 🚀 Démarrage

### Option 1: Démarrage Manuel (Développement)

```bash
# En foreground (voir les logs en direct)
./scripts/start_etsy_polling.sh

# En background (daemon mode)
./scripts/start_etsy_polling.sh --daemon
```

### Option 2: Python Direct

```bash
source venv/bin/activate
python -m services.etsy_polling_cron
```

### Option 3: Systemd Service (Production)

#### Installation du service systemd:

```bash
# 1. Copier le fichier service
sudo cp scripts/etsy-polling.service /etc/systemd/system/

# 2. Recharger systemd
sudo systemctl daemon-reload

# 3. Activer le service (démarrage automatique au boot)
sudo systemctl enable etsy-polling

# 4. Démarrer le service
sudo systemctl start etsy-polling

# 5. Vérifier le status
sudo systemctl status etsy-polling
```

#### Commandes de gestion:

```bash
# Démarrer
sudo systemctl start etsy-polling

# Arrêter
sudo systemctl stop etsy-polling

# Redémarrer
sudo systemctl restart etsy-polling

# Voir les logs
sudo journalctl -u etsy-polling -f

# Voir les logs dans le fichier
tail -f logs/etsy_polling.log
```

---

## 📊 Monitoring

### Vérifier que le service tourne

```bash
# Via systemd
sudo systemctl status etsy-polling

# Via ps
ps aux | grep etsy_polling

# Via PID file
cat logs/etsy_polling.pid
```

### Voir les logs

```bash
# Logs du service
tail -f logs/etsy_polling.log

# Logs d'erreurs
tail -f logs/etsy_polling_error.log

# Logs systemd
sudo journalctl -u etsy-polling -f --since "10 minutes ago"
```

### Logs attendus

Quand le service démarre:

```
✅ Etsy polling scheduler started
📋 Jobs configured:
  - New Orders: every 5 minutes
  - Updated Listings: every 15 minutes
  - Low Stock: every 15 minutes
🚀 Etsy polling service is running.
```

Quand il poll:

```
🔄 Starting Etsy polling: NEW ORDERS
Found 3 Etsy-connected users
✅ User 123 (shop: MyEtsyShop): 2 new orders
✅ Etsy order polling completed: 2 total new orders
```

---

## 🔍 Que fait le polling ?

### 1. Nouvelles Commandes (toutes les 5 min)

- Interroge l'API Etsy `/shop/receipts`
- Filtre les commandes créées depuis le dernier poll
- Log les nouvelles commandes trouvées
- **TODO**: Envoyer notifications email/push

### 2. Listings Mis à Jour (toutes les 15 min)

- Interroge l'API Etsy `/listings/active`
- Compare `updated_timestamp` avec le dernier poll
- Détecte les changements de prix, stock, etc.
- **TODO**: Synchroniser en DB locale

### 3. Stock Faible (toutes les 15 min)

- Interroge l'API Etsy `/listings/active`
- Filtre `quantity < threshold` (défaut: 5)
- Log les listings avec stock faible
- **TODO**: Envoyer alertes email

---

## ⚙️ Configuration Avancée

### Changer les intervalles de polling

Dans `.env`:

```env
# Poll orders toutes les 3 minutes (au lieu de 5)
ETSY_POLLING_INTERVAL_ORDERS=3

# Poll listings toutes les 30 minutes (au lieu de 15)
ETSY_POLLING_INTERVAL_LISTINGS=30

# Seuil de stock faible = 10 (au lieu de 5)
ETSY_POLLING_LOW_STOCK_THRESHOLD=10
```

Puis redémarrer le service:

```bash
sudo systemctl restart etsy-polling
```

### Désactiver certains types de polling

Modifier `services/etsy_polling_cron.py` et commenter les jobs non désirés:

```python
# Ne pas poll les listings
# scheduler.add_job(
#     func=poll_updated_listings_for_all_users,
#     ...
# )
```

---

## 🛠️ Troubleshooting

### Le service ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u etsy-polling -n 50

# Vérifier que l'env virtuel existe
ls -la /home/maribeiro/Stoflow/Stoflow_BackEnd/venv

# Vérifier que APScheduler est installé
source venv/bin/activate
python -c "import apscheduler"
```

### Pas de nouvelles commandes détectées

- Vérifier que des utilisateurs sont connectés à Etsy:

```sql
SELECT user_id, shop_name, access_token_expires_at
FROM platform_mappings
WHERE platform = 'etsy';
```

- Vérifier que les tokens ne sont pas expirés
- Vérifier les logs d'erreurs API

### Rate Limiting Etsy

Etsy limite à **10 requêtes/seconde** et **10,000 requêtes/jour**.

Si vous avez beaucoup d'utilisateurs (>100), ajustez les intervalles:

```env
# Poll moins souvent pour éviter rate limits
ETSY_POLLING_INTERVAL_ORDERS=10
ETSY_POLLING_INTERVAL_LISTINGS=30
```

---

## 📈 Performance

### Charge système

Pour **100 utilisateurs connectés à Etsy**:

- Orders poll (5 min): ~100 requêtes API toutes les 5 min
- Listings poll (15 min): ~100 requêtes API toutes les 15 min

**Total**: ~1,300 requêtes API/heure (bien en dessous de la limite de 10,000/jour)

### Optimisations possibles

1. **Batching**: Grouper plusieurs utilisateurs par requête (si API le supporte)
2. **Priorité**: Poll les utilisateurs actifs plus fréquemment
3. **Caching**: Cacher les résultats temporairement
4. **Queue**: Utiliser Redis Queue pour distribuer la charge

---

## 🔐 Sécurité

- ✅ Tokens stockés chiffrés en DB
- ✅ Refresh automatique des access tokens
- ✅ Isolation par utilisateur
- ✅ Rate limiting respecté
- ✅ Logs sans données sensibles

---

## 📝 TODOs

Fonctionnalités à implémenter:

- [ ] Envoyer notifications email pour nouvelles commandes
- [ ] Synchroniser listings en DB locale
- [ ] Envoyer alertes stock faible
- [ ] Dashboard de monitoring (Grafana)
- [ ] Webhooks vers frontend
- [ ] Support multi-shop par utilisateur
- [ ] Retry automatique en cas d'erreur API

---

## 📚 Références

- [Etsy API v3 Documentation](https://developer.etsy.com/documentation/reference)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [Systemd Service Documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)

---

**Auteur**: Claude
**Date**: 2025-12-10
**Version**: 1.0.0
