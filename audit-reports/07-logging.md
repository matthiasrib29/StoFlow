# Rapport d'Audit - Pratiques de Logging

**Projet**: StoFlow (Backend + Frontend + Plugin)
**Date d'analyse**: 2026-01-27
**Score Global**: 7.5/10

---

## État Général

Le projet dispose d'un **système de logging globalement bien structuré** avec :
- Logging centralisé avec formatage cohérent (`shared/logging.py`)
- Redaction automatique des données sensibles (RGPD compliant)
- Structured logging avec `StructuredLogger`
- Frontend avec logger sécurisé (`utils/logger.ts`)

---

## 1. Print Statements

### État : ✅ BON

Aucun `print()` trouvé dans les services de production. Les occurrences (147) sont dans `/tests/` (scripts de diagnostic), ce qui est acceptable.

**Verdict**: Aucune action requise

---

## 2. Niveaux de Log

### Problèmes

#### a) Manque `exc_info=True` dans les logs d'erreur

**Statistique**: 39 occurrences seulement avec `exc_info=True` sur ~868 logs

**Exemple** (`services/ebay/ebay_importer.py:109`):
```python
# ❌ Stack trace perdue
except Exception as e:
    logger.error(f"Error fetching inventory items at offset {offset}: {e}")
    break

# ✅ Correct
except Exception as e:
    logger.error(f"Error fetching inventory items: offset={offset}", exc_info=True)
    break
```

#### b) Niveaux globalement corrects
- ERROR pour opérations échouées ✅
- WARNING pour situations gérées ✅
- INFO pour événements normaux ✅

---

## 3. Logging dans Chemins Critiques

### a) Authentification - Score: 10/10

`services/auth_service.py` : logging complet avec contexte (login échoué, compte inactif, verrouillé, tentatives, succès avec user_id/schema/source).

### b) Paiements Stripe - Score: 7/10

`services/stripe/webhook_handlers.py` : Pas de log d'entrée dans les handlers. Manque de contexte.

### c) APIs Marketplace - Score: 8/10

`services/vinted/vinted_sync_service.py` : Bon logging des étapes, mais trop verbeux (voir section 7).

---

## 4. Données Sensibles dans les Logs

### État : ✅ EXCELLENT

**Backend** (`shared/logging.py`):
- `redact_email()` - Masque emails en production
- `redact_password()` - Masque mots de passe
- `sanitize_for_log()` - Sanitize automatique des champs sensibles

**Frontend** (`utils/logger.ts`):
- Patterns regex pour JWT tokens, API keys, emails, cartes de crédit
- Logs DEBUG/INFO supprimés en production

**Aucune fuite identifiée** ✅

---

## 5. Configuration du Logging

### État : ✅ BON

- RotatingFileHandler configuré
- Format détaillé disponible
- Logger racine `stoflow` avec propagation désactivée
- Validation secrets au startup

**Recommandation**: Ajouter handler vers monitoring externe (Sentry)

---

## 6. Contexte Manquant

### Problèmes

Certains logs manquent de contexte (`user_id`, `product_id`, `marketplace_id`):

```python
# ❌ Pas assez de contexte
logger.info(f"Total inventory items fetched: {len(all_items)}")

# ✅ Avec contexte
logger.info(
    f"Total inventory items fetched: count={len(all_items)}, "
    f"user_id={self.user_id}, marketplace_id={self.marketplace_id}"
)
```

### F-strings vs paramètres formatés

~360 logs avec f-strings vs ~26 avec paramètres. Les paramètres sont plus performants (lazy evaluation).

```python
# ❌ F-string (interpolation même si log désactivé)
logger.info(f"User authenticated: user_id={user.id}")

# ✅ Paramètres (lazy evaluation)
logger.info("User authenticated: user_id=%s", user.id)
```

---

## 7. Logs Trop Verbeux

**Fichier** : `services/vinted/vinted_sync_service.py:117-189`

Trop de logs INFO dans une seule opération :
```python
logger.info(f"  Produit: {product.title[:50]}...")
logger.info(f"  Validation...")
logger.info(f"  Mapping attributs...")
logger.info(f"  Calcul prix...")
logger.info(f"  Upload photos...")
```

**Fix**: DEBUG pour étapes intermédiaires, INFO uniquement pour le résultat final.

---

## 8. Blocs except silencieux

### État : ✅ BON

0 occurrences de `except: pass` dans les services.

---

## 9. Frontend Console.log

### État : ✅ BON

9 occurrences au total, dont 2 à corriger :
- `composables/usePendingActions.ts:72,92` - `console.error` direct au lieu du logger sécurisé

---

## 10. Structured Logging

### État : ⚠️ Sous-utilisé

`StructuredLogger` existe dans `shared/logging.py:259-321` mais n'est utilisé que dans quelques endroits.

**Recommandation**: Généraliser dans tous les services critiques.

---

## Résumé par Priorité

### Important (à corriger rapidement)
1. **Ajouter `exc_info=True`** dans les logs d'erreur (effort: faible)
2. **Remplacer `console.error`** direct par logger dans `usePendingActions.ts` (effort: faible)

### Moyen (amélioration recommandée)
3. **Réduire verbosité** dans `vinted_sync_service.py` (DEBUG au lieu d'INFO)
4. **Ajouter contexte** manquant (user_id, product_id)
5. **F-strings → paramètres** formatés (performance)

### Optionnel
6. **Généraliser StructuredLogger** dans tous les services
7. **Intégrer monitoring externe** (Sentry)

---

## Checklist

- ✅ Pas de `print()` en production
- ✅ Pas de `except: pass` silencieux
- ✅ Redaction données sensibles
- ✅ Logger configuré avec rotation
- ✅ Frontend avec logger sécurisé
- ⚠️ `exc_info=True` manquant dans certains logs d'erreur
- ⚠️ 2 `console.error` directs à remplacer
- ⚠️ Logs trop verbeux dans certains services
- ℹ️ F-strings au lieu de paramètres
- ℹ️ StructuredLogger sous-utilisé

---

**Rapport généré le**: 2026-01-27
**Analyste**: Claude Code (Log Optimizer)
