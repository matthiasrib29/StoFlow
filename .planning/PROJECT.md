# AI Product Generation - Titre & Description

## Vision

Générateur automatique de **titres SEO** et **descriptions dynamiques** pour produits vestimentaires secondhand, basé sur les attributs produit. Les phrases/segments avec attributs manquants sont automatiquement supprimés.

**One-liner**: Templates Python déterministes pour générer titres et descriptions optimisés SEO, configurables par l'utilisateur.

---

## Requirements

### Validated (Existing Capabilities)

- ✓ **Product model with 30+ attributes** - brand, category, materials, condition, etc.
- ✓ **Product attributes tables** - All values in `product_attributes` schema
- ✓ **FastAPI service architecture** - Clean Architecture with services/repositories
- ✓ **Nuxt frontend with composables** - Vue 3 Composition API
- ✓ **User settings system** - Pour stocker les préférences utilisateur

### Active (To Be Built)

#### Backend - Service de Génération

- [ ] **Créer `ProductTextGeneratorService`** - Service principal de génération
  - Méthode `generate_title(product, format)` → str
  - Méthode `generate_description(product, style)` → str
  - Méthode `generate_all(product)` → dict avec tous les formats/styles
  - Gestion intelligente des attributs manquants (skip silencieux)

- [ ] **Implémenter 3 formats de TITRE**
  - Format 1: Ultra Complet `{brand} {category} {gender} {size} {color} {material} {fit} {condition} {decade}`
  - Format 2: Détails Techniques `{brand} {category} {size} {color} {material} {fit} {rise} {closure} {unique_feature} {condition}`
  - Format 3: Style & Tendance `{brand} {category} {gender} {size} {color} {pattern} {material} {fit} {trend} {season} {origin} {condition}`

- [ ] **Implémenter 3 styles de DESCRIPTION**
  - Style 1: Professionnel / E-commerce (phrases fluides, ton commercial)
  - Style 2: Storytelling / Lifestyle (narratif, émotionnel, paragraphes)
  - Style 3: Minimaliste / Fiche Technique (liste structurée, scan rapide)

- [ ] **Mapping condition score → texte français**
  - 10: "Neuf", 9: "Comme neuf", 8: "Excellent état", 7: "Très bon état"
  - 6: "Bon état", 5: "État correct", 4: "État acceptable"
  - 3: "État passable", 2: "Mauvais état", 1: "Pour pièces", 0: "Défauts majeurs"

- [ ] **Créer endpoint API** - `POST /api/products/{id}/generate-text`
  - Input: `product_id`, `title_format` (optionnel), `description_style` (optionnel)
  - Output: `{ title: str, description: str, all_titles: dict, all_descriptions: dict }`
  - Utilise les préférences user si format/style non spécifiés

- [ ] **Créer endpoint preview** - `POST /api/products/preview-text`
  - Input: Attributs produit (pas besoin d'ID, pour preview avant save)
  - Output: Même format que ci-dessus
  - Pour générer en temps réel pendant l'édition du formulaire

#### Backend - User Settings

- [ ] **Ajouter préférences génération dans user settings**
  - `preferred_title_format`: 1, 2, ou 3 (défaut: 1)
  - `preferred_description_style`: 1, 2, ou 3 (défaut: 1)
  - Stocké dans `public.users` ou table `user_settings`

#### Frontend - Composable

- [ ] **Créer `useProductTextGenerator.ts`**
  - `generateTitle(productId)` - Génère avec préférences user
  - `generateDescription(productId)` - Génère avec préférences user
  - `generatePreview(attributes)` - Preview temps réel
  - `generateAll(productId)` - Tous les formats/styles
  - State: `loading`, `error`, `generatedTitle`, `generatedDescription`

#### Frontend - UI Components

- [ ] **Créer `TextGeneratorButton.vue`**
  - Bouton "Générer" avec icône magic wand
  - Loading state pendant génération
  - Placement: À côté des champs title et description dans le formulaire

- [ ] **Créer `TextPreviewModal.vue`**
  - Modal affichant les 3 formats de titre + 3 styles de description
  - User peut cliquer pour sélectionner celui qu'il préfère
  - Bouton "Appliquer" pour copier dans le formulaire

- [ ] **Intégrer dans formulaire produit**
  - Page create: `pages/dashboard/products/create.vue`
  - Page edit: `pages/dashboard/products/[id]/edit.vue`
  - Boutons à côté de title et description

#### Frontend - Settings UI

- [ ] **Ajouter section "Génération de texte" dans settings**
  - Dropdown pour choisir format titre par défaut (1, 2, 3)
  - Dropdown pour choisir style description par défaut (1, 2, 3)
  - Preview en temps réel avec un produit exemple

### Out of Scope (v1)

- **Génération par LLM (Gemini)** - Templates Python uniquement pour v1
- **Génération batch** - Un produit à la fois
- **Personnalisation des templates** - Templates fixes, pas éditables par user
- **Multi-langue** - Français uniquement pour v1
- **A/B testing des descriptions** - Pas de tracking de performance

---

## Context

### Attributs Obligatoires (pour PUBLISH)

| Attribut | Type | Description |
|----------|------|-------------|
| `brand` | str | Marque ("Unbranded" accepté) |
| `category` | str | Type de vêtement |
| `gender` | str | Men, Women, Unisex |
| `size_normalized` | str | Taille standardisée |
| `colors` | list[str] | Au moins 1 couleur |
| `condition` | int | 0-10 |

### Attributs Optionnels

| Attribut | Type | Utilisé dans |
|----------|------|--------------|
| `material` | str | Titre + Description |
| `fit` | str | Titre + Description |
| `rise` | str | Titre Format 2, Description |
| `closure` | str | Titre Format 2, Description |
| `stretch` | str | Description |
| `length` | str | Description |
| `neckline` | str | Description |
| `sleeve_length` | str | Description |
| `lining` | str | Description |
| `unique_feature` | list[str] | Titre Format 2, Description |
| `trend` | str | Titre Format 3, Description |
| `season` | str | Titre Format 3, Description |
| `origin` | str | Titre Format 3, Description |
| `decade` | str | Titre Format 1, Description |
| `condition_sup` | list[str] | Description |
| `pattern` | str | Titre Format 3, Description |
| `sport` | str | Description |

### Condition Mapping

```python
CONDITION_MAP = {
    10: "Neuf",
    9: "Comme neuf",
    8: "Excellent état",
    7: "Très bon état",
    6: "Bon état",
    5: "État correct avec usure visible",
    4: "État acceptable",
    3: "État passable",
    2: "Mauvais état",
    1: "Pour pièces uniquement",
    0: "Défauts majeurs"
}
```

---

## Constraints

### Technical

- **Templates Python uniquement** - Pas de LLM, déterministe et rapide
- **Gestion attributs manquants** - Skip silencieux, pas d'erreur
- **Limite longueur titre** - Max 80 caractères (Vinted/eBay)
- **Limite longueur description** - Max 5000 caractères
- **Endpoint rapide** - < 100ms response time (pas d'I/O externe)

### Business

- **Ordre SEO respecté** - Brand > Category > Gender > Size > Color > Material > ...
- **Texte propre** - Pas de doubles espaces, pas de virgules orphelines
- **Français correct** - Accords, conjugaisons

### UX

- **Preview temps réel** - Génération pendant l'édition du formulaire
- **Tous les styles accessibles** - Modal pour voir/comparer les 3 options
- **Settings persistants** - Préférences sauvegardées par utilisateur

---

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Templates Python vs LLM | Déterministe, rapide, gratuit, prévisible | Templates uniquement pour v1 |
| 3 formats titre + 3 styles description | Flexibilité sans complexité | User choisit son préféré |
| Settings par user | Chaque vendeur a son style | Préférences persistantes |
| Génération à la demande | Pas d'auto-génération intempestive | Bouton explicite |
| Preview sans save | Voir avant de valider | Endpoint séparé |

---

## Implementation Summary

### Files to Create

**Backend:**
- `backend/services/product_text_generator.py` - Service principal
- `backend/api/products/text_generation.py` - Endpoints API
- `backend/schemas/text_generation_schemas.py` - Pydantic schemas

**Frontend:**
- `frontend/composables/useProductTextGenerator.ts` - Composable
- `frontend/components/products/TextGeneratorButton.vue` - Bouton
- `frontend/components/products/TextPreviewModal.vue` - Modal preview

**Database:**
- Migration pour ajouter `preferred_title_format` et `preferred_description_style` à users

---

## Success Criteria

- [ ] User peut générer titre + description en 1 clic
- [ ] Les 3 formats de titre fonctionnent correctement
- [ ] Les 3 styles de description fonctionnent correctement
- [ ] Attributs manquants = segments supprimés proprement
- [ ] Préférences user sauvegardées et respectées
- [ ] Preview temps réel dans le formulaire
- [ ] Response time < 100ms

---

*Last updated: 2026-01-13 after project initialization*
