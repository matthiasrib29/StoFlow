# Documentation Stoflow Backend

**Version:** 1.0
**Dernière mise à jour:** 2025-12-08

---

## 📚 Documentation Principale

### 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md)
Architecture technique complète du système Stoflow.

**Contenu:**
- Vue d'ensemble de la plateforme
- Stratégie multi-tenant (schema PostgreSQL par client)
- Structure complète du projet
- Authentification & autorisation JWT
- Cycle de vie des produits
- Modèle de données (public & tenant schemas)
- Intégrations plateformes (Vinted, eBay, Etsy)
- Déploiement & infrastructure
- Sécurité & monitoring
- Tests & coverage

**Quand le lire:** Pour comprendre l'architecture globale du système.

---

### 🚀 [README.md](./README.md)
Guide de démarrage rapide et overview du projet.

**Contenu:**
- Présentation de Stoflow
- Stack technique
- Installation en 5 étapes
- Configuration base de données
- Premiers pas avec l'API
- Structure du projet
- Tests & commandes utiles
- Variables d'environnement
- Support & contribution

**Quand le lire:** Pour démarrer avec le projet (installation, premier lancement).

---

### 💼 [BUSINESS_LOGIC.md](./BUSINESS_LOGIC.md)
Règles métier, validations et contraintes business critiques.

**Contenu:**
- Cycle de vie des produits (DRAFT → PUBLISHED → SOLD → ARCHIVED)
- Soft delete & produits supprimés
- Gestion des images (display_order, cascade)
- Catégories hiérarchiques (max 3 niveaux, circularité interdite)
- Gestion des prix & stock
- SKU unique par tenant
- Validation des attributs (brands, colors, sizes, etc.)
- Historique des publications
- Checklist business logic
- Erreurs critiques P0 et P1 à éviter

**Quand le lire:** Avant d'implémenter ou modifier de la logique métier.

---

### 📅 [MVP_ROADMAP.md](./MVP_ROADMAP.md)
Roadmap détaillée du MVP (8 semaines).

**Contenu:**
- Planning complet semaine par semaine
- Week 0: Setup & Infrastructure ✅
- Week 1: Authentification & Onboarding ✅
- Week 2-8: Features principales (CRUD, catégories, images, plugin, Vinted)
- Livrables détaillés pour chaque semaine
- Validation & tests par semaine
- Métriques de succès MVP
- Post-MVP features

**Quand le lire:** Pour suivre l'avancement du projet et les priorités.

---

### 🔌 [PLUGIN_INTEGRATION.md](./PLUGIN_INTEGRATION.md)
Guide complet d'intégration du plugin Firefox/Chrome.

**Contenu:**
- Architecture globale (Backend → API Bridge → Page HTML → Plugin → Vinted API)
- Composants du plugin (manifest, background.js, content.js, popup)
- Système de polling (plugin interroge backend toutes les 5s)
- Actions disponibles (get_user_data, get_all_products, create_product, etc.)
- Debug & troubleshooting
- Logs et problèmes courants

**Quand le lire:** Pour travailler sur l'intégration Vinted via le plugin navigateur.

---

### ⚙️ [PLUGIN_CONFIG.md](./PLUGIN_CONFIG.md)
Configuration rapide du plugin (URL backend, endpoints, checklist).

**Contenu:**
- URL Backend configurée : `http://localhost:8000`
- Fichiers à configurer (background.js, popup.js)
- Endpoints backend disponibles
- Checklist configuration complète
- Vérifications et tests
- Problèmes courants et solutions

**Quand le lire:** Pour configurer rapidement le plugin ou résoudre des problèmes de connexion.

---

## 📂 Autres Documents

### 📋 [PRODUCT_API.md](./PRODUCT_API.md)
Documentation API des endpoints produits.

### 📝 [PRODUCT_IMPLEMENTATION_SUMMARY.md](./PRODUCT_IMPLEMENTATION_SUMMARY.md)
Résumé de l'implémentation des produits.

---

## 🗂️ Archives

Les anciens fichiers de documentation ont été archivés dans:
```
docs/archive_old_docs/
```

**Fichiers archivés:**
- AUTHENTICATION_UNIFIED.md
- BACKEND_TO_PLUGIN.md
- BUSINESS_LOGIC_ANALYSIS.md
- BUSINESS_PLAN.md
- CRITICAL_FIXES_CHECKLIST.md
- ONBOARDING_IMPLEMENTATION.md
- PLUGIN_POLLING_API.md
- QUICK_REFERENCE.md
- WEEK0_SETUP.md
- WEEK1_MULTITENANT.md
- etc.

Ces fichiers ont été consolidés dans les 5 documents principaux ci-dessus.

---

## 🎯 Guide de Navigation Rapide

### Je veux...

**Installer et lancer le projet**
→ Lire [README.md](./README.md)

**Comprendre l'architecture multi-tenant**
→ Lire [ARCHITECTURE.md](./ARCHITECTURE.md) - Section "Stratégie Multi-Tenant"

**Implémenter une nouvelle feature**
→ Lire [BUSINESS_LOGIC.md](./BUSINESS_LOGIC.md) pour comprendre les règles métier

**Suivre l'avancement du MVP**
→ Lire [MVP_ROADMAP.md](./MVP_ROADMAP.md)

**Intégrer le plugin Vinted**
→ Lire [PLUGIN_INTEGRATION.md](./PLUGIN_INTEGRATION.md)

**Comprendre les règles de statut produit**
→ Lire [BUSINESS_LOGIC.md](./BUSINESS_LOGIC.md) - Section "Cycle de Vie d'un Produit"

**Voir les tests à lancer**
→ Lire [README.md](./README.md) - Section "Tests"

**Configurer les variables d'environnement**
→ Lire [README.md](./README.md) - Section "Configuration"

---

## 📞 Support

Si tu as des questions:
1. Consulte d'abord la documentation appropriée ci-dessus
2. Vérifie les archives si besoin (`docs/archive_old_docs/`)
3. Contacte l'équipe de développement

---

**Dernière mise à jour:** 2025-12-08
