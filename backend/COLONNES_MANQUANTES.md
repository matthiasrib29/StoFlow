# Rapport : Colonnes Manquantes dans la Base de Test

Analyse comparative entre les modèles SQLAlchemy et le schéma de la base de test.

## 🔴 Table `public.users`

### Colonnes MANQUANTES (attendues par le modèle mais absentes en BDD):

| Colonne | Type | Nullable | Default | Commentaire |
|---------|------|----------|---------|-------------|
| `current_products_count` | INTEGER | NOT NULL | 0 | Nombre actuel de produits actifs |
| `current_platforms_count` | INTEGER | NOT NULL | 0 | Nombre actuel de plateformes connectées |
| `last_failed_login` | TIMESTAMP WITH TIME ZONE | NULL | NULL | Date de la dernière tentative échouée |
| `password_changed_at` | TIMESTAMP WITH TIME ZONE | NULL | NULL | Date du dernier changement de mot de passe |
| `email_verification_expires` | TIMESTAMP WITH TIME ZONE | NULL | NULL | Date d'expiration du token de vérification |

### Colonnes PRÉSENTES mais avec nom différent:
- BDD a `email_verification_sent_at`
- Modèle attend `email_verification_expires`

**Action requise :** Migration pour ajouter 4 colonnes + renommer 1 colonne.

---

## ✅ Table `public.subscription_quotas`

### Colonnes MANQUANTES (DÉJÀ CORRIGÉES par migration 303159a94619):

| Colonne | Type | Nullable | Default | Commentaire |
|---------|------|----------|---------|-------------|
| `price` | DECIMAL(10,2) | NOT NULL | 0.00 | Prix mensuel de l'abonnement |
| `display_name` | VARCHAR(50) | NOT NULL | '' | Nom d'affichage (Gratuit, Pro, etc.) |
| `description` | VARCHAR(200) | NULL | NULL | Description courte |
| `annual_discount_percent` | INTEGER | NOT NULL | 20 | Pourcentage de réduction annuelle |
| `is_popular` | BOOLEAN | NOT NULL | false | Badge "Populaire" |
| `cta_text` | VARCHAR(100) | NULL | NULL | Texte du bouton CTA |
| `display_order` | INTEGER | NOT NULL | 0 | Ordre d'affichage |

**Statut :** ✅ CORRIGÉ (migration 20260107_1051 appliquée)

---

## ✅ Table `template_tenant.batch_jobs`

**Statut :** ✅ COMPLET - Toutes les colonnes présentes

---

## 🔴 Table `template_tenant.marketplace_jobs`

### Colonnes MANQUANTES:

| Colonne | Type | Nullable | Default | Commentaire |
|---------|------|----------|---------|-------------|
| `input_data` | JSONB | NULL | NULL | Job input parameters |
| `max_retries` | INTEGER | NOT NULL | 3 | Maximum retry attempts |

**Action requise :** Migration pour ajouter 2 colonnes.

---

## ✅ Table `template_tenant.marketplace_tasks`

**Statut :** ✅ COMPLET - Toutes les colonnes présentes

---

## 📋 Tables à Vérifier Ensuite

1. `public.ai_credits` - relation avec users
2. `public.admin_audit_logs` - audit logs
3. `public.doc_categories` et `doc_articles` - documentation
4. `template_tenant.*` - toutes les tables tenant

---

## 🎯 Plan d'Action - Migrations à Créer

### Priorité 1 - CRITIQUE (bloque tests d'intégration)

#### Migration 1: Compléter `public.users`
```sql
-- Ajouter colonnes manquantes
ALTER TABLE public.users ADD COLUMN current_products_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.users ADD COLUMN current_platforms_count INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.users ADD COLUMN last_failed_login TIMESTAMP WITH TIME ZONE NULL;
ALTER TABLE public.users ADD COLUMN password_changed_at TIMESTAMP WITH TIME ZONE NULL;

-- Renommer colonne existante
ALTER TABLE public.users RENAME COLUMN email_verification_sent_at TO email_verification_expires;
```

**Impact :** Critique - Bloque création d'utilisateurs de test

---

#### Migration 2: Compléter `template_tenant.marketplace_jobs`
```sql
-- Ajouter colonnes manquantes
ALTER TABLE template_tenant.marketplace_jobs ADD COLUMN input_data JSONB NULL;
ALTER TABLE template_tenant.marketplace_jobs ADD COLUMN max_retries INTEGER NOT NULL DEFAULT 3;

-- Appliquer sur tous les schemas user_X existants
DO $$
DECLARE
    schema_name text;
BEGIN
    FOR schema_name IN SELECT nspname FROM pg_namespace WHERE nspname LIKE 'user_%' LOOP
        EXECUTE format('ALTER TABLE %I.marketplace_jobs ADD COLUMN IF NOT EXISTS input_data JSONB NULL', schema_name);
        EXECUTE format('ALTER TABLE %I.marketplace_jobs ADD COLUMN IF NOT EXISTS max_retries INTEGER NOT NULL DEFAULT 3', schema_name);
    END LOOP;
END $$;
```

**Impact :** Important - Nécessaire pour création de MarketplaceJob avec tous les champs

---

### ✅ Migrations Déjà Appliquées
- [x] **subscription_quotas** : Migration 303159a94619 appliquée

### ✅ Tables Complètes (pas de migration nécessaire)
- [x] **batch_jobs** : Toutes les colonnes présentes
- [x] **marketplace_tasks** : Toutes les colonnes présentes

---

## 📊 Résumé

| Table | Colonnes manquantes | Statut | Priorité |
|-------|---------------------|--------|----------|
| `public.subscription_quotas` | 7 | ✅ CORRIGÉ | - |
| `public.users` | 5 | 🔴 À CORRIGER | **P1 - CRITIQUE** |
| `template_tenant.marketplace_jobs` | 2 | 🔴 À CORRIGER | **P1 - CRITIQUE** |
| `template_tenant.batch_jobs` | 0 | ✅ OK | - |
| `template_tenant.marketplace_tasks` | 0 | ✅ OK | - |

**Total migrations nécessaires :** 2 migrations critiques

---

**Date d'analyse :** 2026-01-07
**Base de test :** postgresql://stoflow_test@localhost:5434/stoflow_test
