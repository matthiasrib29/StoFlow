# Claude Code Guidelines - Stoflow Project

## 🎯 Règle Principale

**TOUJOURS POSER DES QUESTIONS avant d'implémenter de la logique métier.**

En cas de doute sur une règle business, un calcul, un comportement → **STOP → DEMANDER**.

## 📋 Quand Poser des Questions

### ✅ Obligatoire de demander pour :

- **Logique métier** : Calculs (prix, commissions, arrondis), règles de validation, limites
- **Comportements** : Gestion d'erreurs, retry, fallback, cas limites
- **Intégrations externes** : APIs tierces (Vinted, eBay, Etsy), format des données, mapping
- **Règles business** : Permissions, quotas, rate limiting, abonnements
- **UX/UI** : Comportements utilisateur, messages d'erreur, workflows
- **Workflows** : États, transitions, conditions, validations

### ❌ Pas besoin de demander pour :

- Code technique standard (CRUD, utils, helpers)
- Patterns établis (composants, services, repositories)
- Configuration technique de base
- Formatting et style de code

## 💻 Standards de Code Généraux

### Qualité
- **Type safety** : Utiliser les types (TypeScript, Python type hints)
- **Documentation** : Docstrings/JSDoc pour fonctions publiques
- **Nommage clair** : Variables et fonctions explicites
- **DRY** : Ne pas répéter le code, extraire en fonctions réutilisables

### Sécurité
- **Jamais** de secrets en dur dans le code
- Validation de toutes les entrées utilisateur
- Sanitization des données avant affichage
- HTTPS pour toutes les requêtes externes

### Gestion d'Erreurs
- Try/catch appropriés avec messages clairs
- Logs des erreurs avec contexte
- Messages d'erreur utilisateur compréhensibles
- Ne jamais exposer d'infos techniques sensibles à l'utilisateur

### Tests
- Coverage minimum 80%
- Tests unitaires pour la logique métier
- Tests d'intégration pour les APIs
- Tests E2E pour les parcours critiques

## 🏗️ Architecture Projet Stoflow

### Convention de Nommage des Composants (Nuxt Auto-Import)

Le projet utilise l'auto-import Nuxt avec `pathPrefix: true` (par défaut).
Les composants sont nommés automatiquement en combinant le chemin du dossier + nom du fichier.

**Règle : `components/<folder>/<File>.vue` → `<FolderFile>`**

#### Exemples :
| Fichier | Composant auto-importé |
|---------|------------------------|
| `components/sidebar/MenuItem.vue` | `<SidebarMenuItem>` |
| `components/vinted/StatsCards.vue` | `<VintedStatsCards>` |
| `components/layout/DashboardSidebar.vue` | `<LayoutDashboardSidebar>` |
| `components/ui/InfoBox.vue` | `<UiInfoBox>` |
| `components/platform/HeaderActions.vue` | `<PlatformHeaderActions>` |

#### Règles importantes :
- **Ne pas répéter** le préfixe dans le nom du fichier (éviter `vinted/VintedStatsCards.vue`)
- **Ne pas utiliser d'imports explicites** pour les composants locaux - laisser Nuxt auto-importer
- **Organiser par domaine** : `vinted/`, `ebay/`, `etsy/`, `sidebar/`, `ui/`, etc.

### Multi-Tenant
- Isolation des données par client (tenant)
- Jamais mélanger les données de différents tenants
- Authentification JWT avec tenant_id

### API Communication
- Backend : FastAPI REST API sur `/api/*`
- Frontend : Appels API via composables/services
- Authentification : Bearer token JWT
- Validation : Pydantic (backend) / Zod (frontend)

## 📚 Documentation des Décisions

Quand une règle métier est validée :

1. **Documenter dans le code** avec commentaire explicite
2. **Référencer** : Date et validation (@utilisateur)
3. **Créer des tests** basés sur la règle validée
4. **Mettre à jour** la documentation si nécessaire

### Exemple :
```python
def calculate_price(base: float) -> float:
    """
    Calcule le prix final.

    Business rule (validé avec @maribeiro le 2024-12-04):
    - Commission : 5% du prix de base
    - Arrondi au centime supérieur
    """
    commission = base * 0.05
    return math.ceil((base + commission) * 100) / 100
```

## 🚫 Ne Jamais / ✅ Toujours

### ❌ Ne JAMAIS :
- Inventer des règles métier ou supposer un comportement
- Commiter du code avec des TODO sans ticket associé
- Pusher du code qui ne compile/build pas
- Ignorer les warnings du linter
- Commenter du code "pour plus tard" (supprimer au lieu)

### ✅ TOUJOURS :
- Poser des questions en cas de doute
- Tester le code avant de commiter
- Faire des commits atomiques avec messages clairs
- Relire son code avant de demander une review
- Mettre à jour la documentation si changement d'API

## 📝 Convention Commits

Format : `type(scope): description`

### Types :
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation uniquement
- `style`: Formatage (pas de changement de code)
- `refactor`: Refactoring (pas de feat ni fix)
- `test`: Ajout/modification de tests
- `chore`: Tâches de maintenance (deps, config)

### Exemples :
```
feat(auth): add JWT authentication
fix(products): correct price calculation
docs(api): update endpoints documentation
refactor(services): extract duplicate logic
test(auth): add login edge cases
chore(deps): update fastapi to 0.115.0
```

## 🎯 Workflow de Développement

1. **Comprendre** le besoin (lire le ticket, poser des questions)
2. **Planifier** l'implémentation (architecture, patterns)
3. **Coder** avec les standards (tests, doc, types)
4. **Tester** localement (unit, integration, manuel)
5. **Review** son code (relecture, lint, format)
6. **Commiter** avec message clair
7. **Documenter** si nécessaire

## 📞 Communication

### Poser une Question
```
🤔 QUESTION - [Sujet]

Contexte : [Ce que tu veux faire]

Questions :
1. [Question précise]
2. [Question suivante]

Options possibles :
- Option A : [Description] - Avantages/Inconvénients
- Option B : [Description] - Avantages/Inconvénients

Impact : [Pourquoi c'est important]
```

### Demander une Clarification
```
⚠️ BESOIN DE CLARIFICATION

Je dois implémenter [X] mais :
- Point flou 1
- Point flou 2

Pourrais-tu préciser ?
```

---

**Version :** 1.1
**Dernière mise à jour :** 2026-01-05
**Applicable à :** Backend (Python/FastAPI) et Frontend (Vue/Nuxt)
