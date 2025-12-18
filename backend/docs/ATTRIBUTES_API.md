# API Attributs - Documentation

## Vue d'ensemble

L'API Attributs fournit un système générique pour récupérer tous les types d'attributs de produits sans avoir besoin de créer de nouvelles routes pour chaque nouvel attribut.

## Route Générique

### GET `/api/attributes/{attribute_type}`

Récupère n'importe quel type d'attribut de manière dynamique.

**Paramètres de chemin :**
- `attribute_type` : Type d'attribut à récupérer

**Paramètres de requête :**
- `lang` : Code langue ISO 639-1 (défaut: `en`)
  - Valeurs supportées : `en`, `fr`, `de`, `it`, `es`, `nl`, `pl`
- `search` : Terme de recherche (minimum 2 caractères, si supporté)
- `limit` : Nombre max de résultats (défaut: 100, max: 500)

## Types d'attributs disponibles

| Type | Description | Supporte recherche | Champs extras |
|------|-------------|-------------------|---------------|
| `categories` | Catégories de produits | ❌ | `parent_category`, `default_gender` |
| `conditions` | États des produits | ❌ | `coefficient`, `vinted_id`, `ebay_condition` |
| `genders` | Genres | ❌ | - |
| `seasons` | Saisons | ❌ | - |
| `brands` | Marques | ✅ | - |
| `colors` | Couleurs | ❌ | - |
| `materials` | Matériaux | ❌ | - |
| `fits` | Coupes | ❌ | - |
| `sizes` | Tailles | ❌ | `category`, `sort_order` |

## Exemples d'utilisation

### Récupérer les catégories en français
```bash
GET /api/attributes/categories?lang=fr
```

**Réponse :**
```json
[
  {
    "value": "Jeans",
    "label": "Jeans",
    "parent_category": "Clothing",
    "default_gender": "unisex"
  },
  {
    "value": "Jackets",
    "label": "Vestes",
    "parent_category": "Clothing",
    "default_gender": "unisex"
  }
]
```

### Rechercher des marques
```bash
GET /api/attributes/brands?search=nike&limit=10
```

**Réponse :**
```json
[
  {
    "value": "Nike",
    "label": "Nike"
  },
  {
    "value": "Nike SB",
    "label": "Nike SB"
  }
]
```

### Récupérer les conditions en anglais
```bash
GET /api/attributes/conditions?lang=en
```

**Réponse :**
```json
[
  {
    "value": "NEW",
    "label": "Brand new",
    "coefficient": 1.0,
    "vinted_id": 6,
    "ebay_condition": "NEW"
  },
  {
    "value": "EXCELLENT",
    "label": "Excellent",
    "coefficient": 0.95,
    "vinted_id": 1,
    "ebay_condition": "PRE_OWNED_EXCELLENT"
  }
]
```

### Lister tous les types disponibles
```bash
GET /api/attributes/
```

**Réponse :**
```json
{
  "available_types": [
    "categories",
    "conditions",
    "genders",
    "seasons",
    "brands",
    "colors",
    "materials",
    "fits",
    "sizes"
  ],
  "usage": "Use GET /api/attributes/{attribute_type} to fetch specific attributes",
  "example": "/api/attributes/categories?lang=fr"
}
```

## Ajouter un nouvel attribut

Pour ajouter un nouveau type d'attribut (ex: `patterns`), suivez ces étapes :

### 1. Créer le modèle SQLAlchemy

Créez `/models/public/pattern.py` :
```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from shared.database import Base

class Pattern(Base):
    __tablename__ = "patterns"
    __table_args__ = {"schema": "product_attributes"}

    name_en: Mapped[str] = mapped_column(String(100), primary_key=True)
    name_fr: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # ... autres langues
```

### 2. Ajouter au mapping dans `api/attributes.py`

```python
from models.public.pattern import Pattern

ATTRIBUTE_MODELS = {
    # ... existants
    "patterns": Pattern,
}

ATTRIBUTE_CONFIG = {
    # ... existants
    "patterns": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es"],
        "supports_search": False,
    },
}
```

### 3. C'est tout !

Le nouvel attribut est maintenant disponible automatiquement :
```bash
GET /api/attributes/patterns?lang=fr
```

## Utilisation côté Frontend

### Méthodes spécifiques (déjà disponibles)
```typescript
const {
  fetchCategories,
  fetchConditions,
  fetchGenders,
  fetchSeasons,
  fetchBrands
} = useAttributes()

// Utilisation
await fetchCategories('fr')
await fetchBrands('nike', 50)
```

### Méthode générique (pour nouveaux attributs)
```typescript
const { fetchAttribute } = useAttributes()

// Récupérer un nouvel attribut (ex: patterns)
const patterns = await fetchAttribute('patterns', 'fr')

// Récupérer les couleurs
const colors = await fetchAttribute('colors', 'en')

// Récupérer les matériaux en français
const materials = await fetchAttribute('materials', 'fr')
```

## Gestion du cache

Les données sont automatiquement mises en cache côté client pour éviter des appels répétés.

**Vider le cache :**
```typescript
const { clearCache } = useAttributes()
clearCache()
```

## Format de réponse standard

Toutes les réponses suivent le même format :

```typescript
interface AttributeOption {
  value: string        // Valeur technique (toujours en anglais)
  label: string        // Label traduit selon la langue
  [key: string]: any   // Champs supplémentaires selon le type
}
```

## Gestion des erreurs

### Erreur 404 - Type d'attribut inconnu
```json
{
  "detail": "Attribute type 'unknown' not found. Available types: categories, conditions, genders, seasons, brands, colors, materials, fits, sizes"
}
```

### Erreur 422 - Paramètres invalides
```json
{
  "detail": [
    {
      "loc": ["query", "search"],
      "msg": "ensure this value has at least 2 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

## Support multilingue

Le système supporte actuellement 7 langues :
- 🇬🇧 **en** - Anglais (par défaut)
- 🇫🇷 **fr** - Français
- 🇩🇪 **de** - Allemand
- 🇮🇹 **it** - Italien
- 🇪🇸 **es** - Espagnol
- 🇳🇱 **nl** - Néerlandais
- 🇵🇱 **pl** - Polonais

**Fallback automatique :**
Si une traduction n'existe pas pour la langue demandée, le système retourne automatiquement la valeur en anglais.

## Performance

- **Cache côté client** : Les données sont cachées dans le composable Vue
- **Limite par défaut** : 100 résultats max par requête
- **Pagination** : Non implémentée (tous les résultats retournés dans la limite)
- **Indexes database** : Tous les champs `value` sont indexés

## Sécurité

- **Endpoints publics** : Pas d'authentification requise (lecture seule)
- **Rate limiting** : Activé globalement sur l'API
- **SQL Injection** : Protection via SQLAlchemy ORM
- **XSS** : Headers de sécurité activés

---

**Version :** 1.0
**Dernière mise à jour :** 2025-12-09
**Auteur :** Claude Code
