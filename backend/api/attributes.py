"""
Attributes Routes

Route API générique pour récupérer tous les attributs de produits.

Business Rules (Updated 2025-12-09):
- Route générique: /api/attributes/{attribute_type}
- Endpoints publics (pas d'authentification requise pour lecture)
- Données partagées entre tous les tenants (schema product_attributes)
- Support multilingue (EN par défaut, FR disponible)
- Extensible: nouveaux attributs automatiquement disponibles
- Données en cache côté client recommandé
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.category import Category
from models.public.closure import Closure
from models.public.color import Color
from models.public.condition import Condition
from models.public.decade import Decade
from models.public.fit import Fit
from models.public.gender import Gender
from models.public.length import Length
from models.public.material import Material
from models.public.neckline import Neckline
from models.public.origin import Origin
from models.public.pattern import Pattern
from models.public.rise import Rise
from models.public.season import Season
from models.public.size_normalized import SizeNormalized
from models.public.sleeve_length import SleeveLength
from models.public.sport import Sport
from models.public.trend import Trend
from shared.database import get_db

router = APIRouter(prefix="/attributes", tags=["Attributes"])

# Mapping des types d'attributs vers leurs modèles SQLAlchemy
ATTRIBUTE_MODELS = {
    "categories": Category,
    "conditions": Condition,
    "genders": Gender,
    "seasons": Season,
    "brands": Brand,
    "colors": Color,
    "materials": Material,
    "fits": Fit,
    "sizes": SizeNormalized,
    # Clothing attributes
    "sports": Sport,
    "necklines": Neckline,
    "lengths": Length,
    "patterns": Pattern,
    "rises": Rise,
    "closures": Closure,
    "sleeve_lengths": SleeveLength,
    # Vintage attributes
    "origins": Origin,
    "decades": Decade,
    "trends": Trend,
}

# Configuration pour chaque type d'attribut
ATTRIBUTE_CONFIG = {
    "categories": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es"],
        "extra_fields": ["parent_category", "genders"],
        "supports_search": False,
    },
    "conditions": {
        "value_field": "note",
        "label_method": "get_name",  # Méthode spéciale du modèle
        "extra_fields": ["coefficient", "vinted_id", "ebay_condition"],
        "supports_search": False,
    },
    "genders": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "seasons": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "brands": {
        "value_field": "name",
        "label_fields": ["name"],
        "supports_search": True,
        "search_field": "name",
    },
    "colors": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "extra_fields": ["hex_code"],
        "supports_search": False,
    },
    "materials": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es"],
        "supports_search": False,
    },
    "fits": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es"],
        "supports_search": False,
    },
    "sizes": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "extra_fields": ["vinted_id", "ebay_size", "etsy_size"],
        "supports_search": False,
    },
    # Clothing attributes
    "sports": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr"],
        "supports_search": False,
    },
    "necklines": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "lengths": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "patterns": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "rises": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "closures": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "sleeve_lengths": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    # Vintage attributes
    "origins": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "decades": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
    "trends": {
        "value_field": "name_en",
        "label_fields": ["name_en", "name_fr", "name_de", "name_it", "name_es", "name_nl", "name_pl"],
        "supports_search": False,
    },
}


def _get_label_for_item(item, config: dict, lang: str) -> str:
    """
    Récupère le label d'un item selon la langue et la configuration.

    Args:
        item: L'objet modèle SQLAlchemy
        config: Configuration de l'attribut
        lang: Code langue (en, fr, de, etc.)

    Returns:
        Le label traduit ou le label par défaut
    """
    # Si méthode spéciale (ex: Condition.get_description)
    if "label_method" in config:
        method = getattr(item, config["label_method"], None)
        if method and callable(method):
            return method(lang)

    # Sinon, utiliser les champs de label
    label_fields = config.get("label_fields", [])

    # Essayer avec la langue demandée
    if label_fields:
        # Construire le nom du champ selon la langue (ex: name_fr)
        for field_base in label_fields:
            if "_" in field_base:  # Champ déjà avec langue (name_en, name_fr...)
                if field_base.endswith(f"_{lang}"):
                    value = getattr(item, field_base, None)
                    if value:
                        return value
            else:  # Champ sans langue, retourner tel quel
                value = getattr(item, field_base, None)
                if value:
                    return value

        # Fallback sur la première langue disponible
        for field in label_fields:
            value = getattr(item, field, None)
            if value:
                return value

    # Dernier recours: utiliser le value_field
    return str(getattr(item, config["value_field"], ""))


@router.get("/{attribute_type}")
def get_attributes(
    attribute_type: str = Path(..., description="Type d'attribut (categories, conditions, genders, etc.)"),
    lang: str = Query("en", description="Langue (en, fr, de, it, es, nl, pl)"),
    search: str | None = Query(None, min_length=1, description="Terme de recherche (si supporté)"),
    limit: int = Query(100, ge=1, le=500, description="Nombre max de résultats"),
    db: Session = Depends(get_db),
):
    """
    Route générique pour récupérer tous les types d'attributs.

    Cette route permet de récupérer dynamiquement n'importe quel type d'attribut
    sans avoir besoin d'ajouter de nouvelles routes.

    Path Parameters:
        - attribute_type: Type d'attribut (categories, conditions, genders, seasons,
                         brands, colors, materials, fits, sizes)

    Query Parameters:
        - lang: Code langue ISO 639-1 (défaut: en)
        - search: Terme de recherche (minimum 2 caractères, si supporté par l'attribut)
        - limit: Nombre max de résultats (défaut: 100, max: 500)

    Returns:
        Liste des attributs avec leurs valeurs et labels traduits

    Raises:
        404: Si le type d'attribut n'existe pas

    Examples:
        GET /api/attributes/categories?lang=fr
        GET /api/attributes/brands?search=nike&limit=50
        GET /api/attributes/conditions?lang=en
    """
    # Vérifier que le type d'attribut existe
    if attribute_type not in ATTRIBUTE_MODELS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attribute type '{attribute_type}' not found. Available types: {', '.join(ATTRIBUTE_MODELS.keys())}"
        )

    model = ATTRIBUTE_MODELS[attribute_type]
    config = ATTRIBUTE_CONFIG[attribute_type]

    # Construire la requête
    query = db.query(model)

    # Appliquer la recherche si supportée et fournie
    if search and config.get("supports_search", False):
        search_field = config.get("search_field", "name")
        field_attr = getattr(model, search_field)
        query = query.filter(field_attr.ilike(f"%{search}%"))

    # Appliquer la limite
    items = query.limit(limit).all()

    # Construire les résultats
    result = []
    for item in items:
        # Construire l'objet de base
        item_data = {
            "value": getattr(item, config["value_field"]),
            "label": _get_label_for_item(item, config, lang)
        }

        # Ajouter les champs extras si configurés
        if "extra_fields" in config:
            for field in config["extra_fields"]:
                value = getattr(item, field, None)
                # Gérer les enums
                if hasattr(value, 'value'):
                    value = value.value
                item_data[field] = value

        result.append(item_data)

    return result


# Route de compatibilité pour lister tous les types d'attributs disponibles
@router.get("/")
def list_attribute_types():
    """
    Liste tous les types d'attributs disponibles.

    Returns:
        Liste des types d'attributs avec leur configuration
    """
    return {
        "available_types": list(ATTRIBUTE_MODELS.keys()),
        "usage": "Use GET /api/attributes/{attribute_type} to fetch specific attributes",
        "example": "/api/attributes/categories?lang=fr"
    }
