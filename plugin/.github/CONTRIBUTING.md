# 🤝 Guide de Contribution

Merci de votre intérêt pour contribuer à Stoflow Plugin !

## 🚀 Comment Contribuer

### 1. Fork & Clone

```bash
# Fork le repo sur GitHub, puis :
git clone https://github.com/VOTRE-USERNAME/Stoflow_Plugin.git
cd Stoflow_Plugin
npm install
```

### 2. Créer une Branche

```bash
git checkout -b feature/ma-super-fonctionnalite
```

### 3. Développer

```bash
# Lancer en mode dev
npm run dev

# Faire vos modifications dans src/
```

### 4. Tester

- Charger l'extension dans Firefox/Chrome
- Tester manuellement les changements
- Vérifier qu'aucune régression n'a été introduite

### 5. Commit

```bash
git add .
git commit -m "feat(vinted): add product image optimization"
```

**Format des commits :**

```
type(scope): message

feat: nouvelle fonctionnalité
fix: correction de bug
docs: documentation
refactor: refactoring
test: ajout de tests
chore: tâches diverses
```

### 6. Push & Pull Request

```bash
git push origin feature/ma-super-fonctionnalite
```

Puis créer une Pull Request sur GitHub.

## 📝 Standards de Code

### TypeScript

- Utiliser les types explicites
- Éviter `any`
- Documenter les fonctions publiques

```typescript
/**
 * Importe tous les produits depuis Vinted
 * @returns Liste des produits importés
 */
async function importVintedProducts(): Promise<VintedProduct[]> {
  // ...
}
```

### Vue 3

- Utiliser Composition API
- Extraire la logique dans des composables
- Props typés avec TypeScript

```vue
<script setup lang="ts">
import { ref } from 'vue';

interface Props {
  title: string;
  count?: number;
}

const props = defineProps<Props>();
</script>
```

### Nommage

- **Fichiers** : camelCase (`useAuth.ts`)
- **Composants** : PascalCase (`LoginForm.vue`)
- **Variables** : camelCase (`isLoading`)
- **Constantes** : UPPER_SNAKE_CASE (`API_URL`)

## 🧪 Tests

Avant de soumettre une PR :

1. ✅ Le build réussit : `npm run build`
2. ✅ Pas d'erreurs TypeScript : `npm run build:check`
3. ✅ L'extension se charge correctement
4. ✅ Les fonctionnalités existantes fonctionnent toujours

## 📖 Documentation

- Mettre à jour le README si nécessaire
- Ajouter des commentaires pour le code complexe
- Documenter les nouvelles APIs

## 🐛 Rapporter un Bug

Créer une issue avec :

1. **Description** : Que s'est-il passé ?
2. **Reproduction** : Comment reproduire le bug ?
3. **Environnement** : OS, navigateur, version
4. **Logs** : Copier les logs de la console

## 💡 Proposer une Fonctionnalité

Créer une issue avec :

1. **Problème** : Quel problème résout-elle ?
2. **Solution** : Comment fonctionne-t-elle ?
3. **Alternatives** : Autres approches considérées ?

## 📋 Checklist PR

Avant de soumettre :

- [ ] Le code build sans erreurs
- [ ] Les changements sont testés manuellement
- [ ] Le code suit les conventions du projet
- [ ] La documentation est à jour
- [ ] Les commits suivent le format standard
- [ ] La PR a une description claire

## 🎯 Priorités

### High Priority

- [ ] Tests unitaires
- [ ] Tests E2E
- [ ] Support eBay complet
- [ ] Support Etsy complet

### Medium Priority

- [ ] Amélioration UI/UX
- [ ] Gestion d'erreurs robuste
- [ ] Cache des requêtes
- [ ] Retry automatique

### Low Priority

- [ ] Templates de description
- [ ] Statistiques
- [ ] Export CSV
- [ ] Multi-comptes

## ❓ Questions

Des questions ? Créer une issue ou contacter l'équipe !

---

**Merci pour votre contribution ! 🙏**
