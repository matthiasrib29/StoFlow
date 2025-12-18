# Plan d'Action Refactoring - StoFlow Plugin

**Date de début**: 2025-12-09 (suggéré)
**Durée estimée**: 5 jours (40h)
**Fichiers générés**:
- `REFACTORING_ANALYSIS.md` - Analyse détaillée
- `REFACTORING_EXAMPLES.md` - Exemples code AVANT/APRÈS
- `REFACTORING_ACTION_PLAN.md` - Ce fichier

---

## 🎯 Objectifs Globaux

**Phase 1 (Critique)**: Stabiliser le code
**Phase 2 (Majeur)**: Améliorer l'architecture
**Phase 3 (Optimisation)**: Polish et qualité
**Phase 4 (Validation)**: Tests et déploiement

---

## 📅 Planning Détaillé

### Jour 1 - Lundi (8h)

#### Matin (4h) : Préparation + Logs
- ✅ **[30min]** Backup + Branche
  ```bash
  git checkout -b refactor/plugin-cleanup
  git push -u origin refactor/plugin-cleanup
  ```

- ✅ **[30min]** Setup environnement test
  ```bash
  npm install
  npm run test
  npm run build
  ```

- ✅ **[3h]** P0.1 - Migration console.log → Logger
  - Exécuter `scripts/migrate-logs.js`
  - Vérifier compilation
  - Tester manuellement
  - Commit: `refactor: migrate console.log to Logger system`

#### Après-midi (4h) : BackgroundService
- ✅ **[2h]** P0.2 - Refactorer BackgroundService
  - Extraire `findVintedTab()`
  - Extraire `sendMessageToTab()`
  - Simplifier `handleFetchVintedData()`
  - Commit: `refactor: extract reusable methods in BackgroundService`

- ✅ **[2h]** P0.3 - Éliminer duplication
  - Centraliser recherche onglet Vinted
  - Créer `utils/tab-manager.ts`
  - Remplacer 6 occurrences
  - Commit: `refactor: centralize Vinted tab search logic`

**Livrables Jour 1**:
- ✅ 426 console.log → Logger (0 console.log)
- ✅ 50+ lignes dupliquées supprimées
- ✅ 3 commits propres

---

### Jour 2 - Mardi (8h)

#### Matin (4h) : Gestion d'erreurs
- ✅ **[2h]** P0.4 - Standardiser error handling
  - Utiliser classes d'erreur partout
  - Wrapper try/catch unifié
  - Tester avec erreurs simulées
  - Commit: `refactor: standardize error handling with StoflowError`

- ✅ **[2h]** P0.5 (Partie 1) - Préparer extraction Vinted
  - Analyser `extractVintedDataFromPage()`
  - Créer squelette `VintedPageParser` class
  - Écrire tests unitaires (TDD)
  - Commit: `test: add unit tests for VintedPageParser`

#### Après-midi (4h) : Extraction Vinted
- ✅ **[4h]** P0.5 (Partie 2) - Refactorer extraction
  - Implémenter `VintedPageParser`
  - Séparer extraction CSRF / currentUser
  - Ajouter caching (5 min)
  - Migrer code existant
  - Commit: `refactor: extract VintedPageParser with caching`

**Livrables Jour 2**:
- ✅ Gestion d'erreurs unifiée
- ✅ Extraction Vinted refactorisée (280L → ~80L)
- ✅ Tests unitaires VintedPageParser
- ✅ 3 commits propres

---

### Jour 3 - Mercredi (8h)

#### Matin (4h) : Type Safety
- ✅ **[3h]** P1.1 - Type safety messages Chrome
  - Créer `types/messages.ts`
  - Définir union types discriminés
  - Migrer tous les listeners
  - Commit: `refactor: add type safety to Chrome messages`

- ✅ **[1h]** P1.3 - Unifier getProducts()
  - Fusionner `getMyProducts()` et `getAllProducts()`
  - Ajouter options pagination
  - Commit: `refactor: unify product fetching logic`

#### Après-midi (4h) : Rate Limiting + Timeout
- ✅ **[1h]** P1.4 - Activer rate limiting
  - Utiliser `RateLimiter` existant
  - Appliquer sur toutes requêtes Vinted
  - Tester avec boucle rapide
  - Commit: `feat: add rate limiting to Vinted API calls`

- ✅ **[2h]** P1.6 - Timeout messages
  - Créer `sendMessageWithTimeout()`
  - Migrer tous les `sendMessage()`
  - Tester timeout simulation
  - Commit: `feat: add timeout to content script messages`

- ✅ **[1h]** P1.5 - Résoudre TODOs
  - Décider quoi garder/supprimer
  - Implémenter ou supprimer
  - Commit: `chore: resolve pending TODOs`

**Livrables Jour 3**:
- ✅ Messages Chrome 100% typés
- ✅ Rate limiting actif
- ✅ Timeout protection
- ✅ TODOs résolus
- ✅ 5 commits propres

---

### Jour 4 - Jeudi (8h)

#### Matin (4h) : Injection de Dépendances
- ✅ **[4h]** P1.2 - Injection de dépendances
  - Créer interfaces (`ITabManager`, `IStorageManager`, etc.)
  - Implémenter `ChromeTabManager`, `ChromeStorageManager`
  - Refactorer `BackgroundService` avec DI
  - Créer mocks pour tests
  - Commit: `refactor: implement dependency injection in BackgroundService`

#### Après-midi (4h) : Optimisations
- ✅ **[1h]** P2.1 - Storage typé
  - Créer `TypedStorage` class
  - Migrer tous les usages
  - Commit: `refactor: add type safety to Chrome storage`

- ✅ **[1h]** P2.2 - Props Vue typés
  - Ajouter types aux composants Vue
  - Tester autocomplete
  - Commit: `refactor: add typed props to Vue components`

- ✅ **[2h]** P2.3 - Validation réponses API
  - Installer Zod ou créer validateurs manuels
  - Valider réponses Vinted
  - Commit: `feat: add API response validation`

**Livrables Jour 4**:
- ✅ DI complète (100% testable)
- ✅ Storage typé
- ✅ Vue props typés
- ✅ Validation API
- ✅ 4 commits propres

---

### Jour 5 - Vendredi (8h)

#### Matin (4h) : Tests + Polish
- ✅ **[1h]** P2.4 - Constantes magic numbers
  - Extraire toutes constantes
  - Documenter
  - Commit: `refactor: extract magic numbers to constants`

- ✅ **[2h]** P2.5 - Compléter useSync
  - Centraliser logique sync
  - État réactif global
  - Commit: `refactor: centralize sync logic in useSync composable`

- ✅ **[1h]** Tests unitaires manquants
  - Atteindre >80% coverage
  - Commit: `test: add missing unit tests for 80% coverage`

#### Après-midi (4h) : CI/CD + Documentation
- ✅ **[2h]** Setup CI/CD
  - GitHub Actions workflow
  - Lint + type check + tests
  - Build Chrome + Firefox
  - Commit: `ci: setup GitHub Actions workflow`

- ✅ **[1h]** Pre-commit hooks
  - Husky + lint-staged
  - Commit: `chore: setup pre-commit hooks`

- ✅ **[1h]** Documentation
  - Mettre à jour README
  - Documentation API
  - Commit: `docs: update documentation`

**Livrables Jour 5**:
- ✅ Tests coverage >80%
- ✅ CI/CD fonctionnel
- ✅ Pre-commit hooks
- ✅ Documentation à jour
- ✅ 4 commits propres

---

## 📋 Checklist Quotidienne

Avant de commit chaque soir :

```bash
# 1. Vérifier compilation
npm run build

# 2. Lancer tests
npm run test

# 3. Vérifier types
npx vue-tsc --noEmit

# 4. Linter
npx eslint src/

# 5. Test manuel
# - Charger extension Chrome
# - Tester login
# - Tester import Vinted
# - Vérifier logs

# 6. Commit propre
git add .
git commit -m "refactor: [description]"
git push
```

---

## 🎯 Commits Recommandés

**Format**: `type(scope): description`

**Types**:
- `refactor`: Refactoring sans changement fonctionnel
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction bug
- `test`: Ajout tests
- `docs`: Documentation
- `chore`: Tâches maintenance (deps, config)
- `ci`: Configuration CI/CD

**Exemples**:
```
refactor(background): migrate console.log to Logger system
refactor(content): extract VintedPageParser class
feat(utils): add timeout to content script messages
test(parser): add unit tests for VintedPageParser
ci: setup GitHub Actions workflow
docs: update README with refactoring notes
```

---

## 🔍 Tests de Non-Régression

Après chaque phase, tester manuellement :

### Scénario 1 : Login
1. Ouvrir popup
2. Se connecter avec email/password
3. ✅ Token sauvegardé
4. ✅ Polling démarré
5. ✅ UI mise à jour

### Scénario 2 : Import Vinted
1. Ouvrir vinted.fr
2. Se connecter sur Vinted
3. Cliquer "Synchroniser Vinted"
4. ✅ Produits récupérés
5. ✅ Logs visibles en console dev
6. ✅ Notification affichée

### Scénario 3 : Gestion d'erreurs
1. Fermer tous onglets Vinted
2. Cliquer "Synchroniser"
3. ✅ Erreur user-friendly
4. ✅ Pas de crash
5. ✅ Log technique en console

### Scénario 4 : Polling
1. Login
2. Backend crée tâche
3. ✅ Plugin récupère tâche
4. ✅ Exécute requête
5. ✅ Renvoie résultat

---

## 📊 Métriques de Succès

**Mesurer avant/après** :

| Métrique | Avant | Cible | Mesure |
|----------|-------|-------|--------|
| **Code** |
| Lignes de code | 7730 | <6500 | `cloc src/` |
| console.log | 426 | 0 | `grep -r "console.log" src/ \| wc -l` |
| Duplication | ~15% | <5% | `jscpd src/` |
| **Qualité** |
| Tests coverage | 30% | >80% | `npm run test:coverage` |
| Type errors | ? | 0 | `npx vue-tsc --noEmit` |
| ESLint warnings | ? | 0 | `npx eslint src/` |
| **Performance** |
| Temps chargement | ? | -20% | Chrome DevTools |
| Taille bundle | ? | <500KB | `ls -lh dist/` |

---

## 🐛 Debugging

Si problème durant refactoring :

### Erreur TypeScript
```bash
# Voir tous les types inférés
npx vue-tsc --noEmit --pretty

# Mode watch
npx vue-tsc --watch --noEmit
```

### Tests échouent
```bash
# Mode watch
npm run test -- --watch

# Avec UI
npm run test:ui

# Coverage
npm run test:coverage
```

### Extension ne charge pas
```bash
# Vérifier build
npm run build

# Vérifier manifest
cat dist/manifest.json

# Logs Chrome
chrome://extensions > Errors
```

---

## 🚀 Après le Refactoring

Une fois terminé :

### 1. Code Review
- [ ] Créer PR vers `main`
- [ ] Review par pair
- [ ] Résoudre commentaires

### 2. Merge
```bash
git checkout main
git merge refactor/plugin-cleanup
git push
```

### 3. Release
```bash
# Tag version
git tag v1.1.0-refactored
git push --tags

# Build production
npm run build

# Publish Chrome
# Upload dist/ vers Chrome Web Store

# Publish Firefox
# Upload dist/ vers Firefox Add-ons
```

### 4. Documentation
- [ ] Mettre à jour CHANGELOG.md
- [ ] Archiver anciens docs
- [ ] Partager learnings avec équipe

---

## 📚 Ressources Utiles

### Documentation
- [Chrome Extensions Manifest V3](https://developer.chrome.com/docs/extensions/mv3/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vue 3 Guide](https://vuejs.org/guide/)
- [Vitest](https://vitest.dev/)

### Outils
- [cloc](https://github.com/AlDanial/cloc) - Comptage lignes
- [jscpd](https://github.com/kucherenko/jscpd) - Détection duplication
- [madge](https://github.com/pahen/madge) - Analyse dépendances

### Commandes Pratiques

```bash
# Compter lignes de code
npx cloc src/

# Détecter duplication
npx jscpd src/

# Analyser dépendances
npx madge --circular --extensions ts src/

# Analyser bundle size
npx vite-bundle-visualizer

# Formater code
npx prettier --write "src/**/*.{ts,vue}"

# Vérifier imports inutilisés
npx depcheck
```

---

## ✅ Validation Finale

Avant de merger :

### Code Quality
- [ ] `npm run build` → ✅ Success
- [ ] `npm run test` → ✅ All pass
- [ ] `npx vue-tsc --noEmit` → ✅ No errors
- [ ] `npx eslint src/` → ✅ No warnings
- [ ] Coverage >80%

### Fonctionnel
- [ ] Login fonctionne
- [ ] Import Vinted fonctionne
- [ ] Polling backend fonctionne
- [ ] Gestion erreurs OK
- [ ] Logs production désactivés

### Performance
- [ ] Temps chargement ≤ avant
- [ ] Memory usage ≤ avant
- [ ] Bundle size ≤ avant

### Documentation
- [ ] README à jour
- [ ] CHANGELOG rempli
- [ ] JSDoc sur fonctions publiques

---

## 🎉 Célébrer le Succès !

Après 5 jours de refactoring intensif :

**Avant** :
- ❌ 426 console.log
- ❌ Code dupliqué
- ❌ Fonctions 100+ lignes
- ❌ 30% tests coverage

**Après** :
- ✅ 0 console.log (Logger structuré)
- ✅ <5% duplication
- ✅ Fonctions <50 lignes
- ✅ >80% tests coverage
- ✅ 100% type safety
- ✅ Architecture testable

**Impact** :
- 🚀 Code 2x plus maintenable
- 🐛 -80% bugs potentiels
- ⚡ -20% temps debugging
- 📚 Onboarding nouveau dev -70%

---

**Bon courage ! 💪**
