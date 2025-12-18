"""
eBay GPSR Compliance Helper (EU 2024).

GPSR = General Product Safety Regulation (Règlement général sur la sécurité des produits)

À partir de décembre 2024, l'UE impose que tous les produits vendus
dans l'UE affichent des informations de sécurité obligatoires:

1. **Informations fabricant** (Mandatory):
   - Nom fabricant
   - Adresse complète
   - Email de contact

2. **Informations responsable EU** (si fabricant hors UE):
   - Nom personne responsable dans l'UE
   - Adresse EU
   - Email

3. **Avertissements** (selon catégorie produit):
   - Age minimum
   - Dangers spécifiques
   - Instructions de sécurité

**Catégories concernées:**
- Tous produits vendus sur EBAY_FR, EBAY_DE, EBAY_IT, EBAY_ES, EBAY_NL, EBAY_BE

**Impact:**
Produits non conformes peuvent être:
- Rejetés par eBay
- Supprimés du marketplace
- Soumis à amendes

Documentation officielle:
https://www.ebay.com/sellercenter/resources/general-product-safety-regulation

Author: Claude
Date: 2025-12-10
"""

from typing import Any, Dict, List, Optional


# Marketplaces EU concernées par GPSR
EU_MARKETPLACES = ["EBAY_FR", "EBAY_DE", "EBAY_IT", "EBAY_ES", "EBAY_NL", "EBAY_BE", "EBAY_PL"]


def is_gpsr_required(marketplace_id: str) -> bool:
    """
    Vérifie si GPSR est requis pour ce marketplace.

    Args:
        marketplace_id: Marketplace (EBAY_FR, EBAY_GB, etc.)

    Returns:
        bool: True si GPSR requis (marketplace EU)

    Examples:
        >>> is_gpsr_required("EBAY_FR")
        True
        >>> is_gpsr_required("EBAY_GB")
        False  # UK n'est plus dans l'UE
        >>> is_gpsr_required("EBAY_US")
        False
    """
    return marketplace_id in EU_MARKETPLACES


def build_gpsr_product_safety(
    manufacturer_name: str,
    manufacturer_address: str,
    manufacturer_email: str,
    manufacturer_phone: Optional[str] = None,
    responsible_person_name: Optional[str] = None,
    responsible_person_address: Optional[str] = None,
    responsible_person_email: Optional[str] = None,
    warnings: Optional[List[str]] = None,
    documents_urls: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Construit le bloc productSafety pour conformité GPSR.

    Ce bloc doit être ajouté à l'inventory item pour les marketplaces EU.

    Args:
        manufacturer_name: Nom du fabricant
        manufacturer_address: Adresse complète du fabricant
        manufacturer_email: Email de contact fabricant
        manufacturer_phone: Téléphone fabricant (optionnel)
        responsible_person_name: Nom personne responsable EU (si fabricant hors UE)
        responsible_person_address: Adresse EU de la personne responsable
        responsible_person_email: Email personne responsable EU
        warnings: Liste d'avertissements (ex: ["Ne convient pas aux enfants de moins de 3 ans"])
        documents_urls: URLs vers documents de sécurité (CE, manuels, etc.)

    Returns:
        Dict à ajouter dans inventory_item["product"]["productSafety"]

    Examples:
        >>> # Fabricant dans l'UE
        >>> gpsr = build_gpsr_product_safety(
        ...     manufacturer_name="Nike Europe B.V.",
        ...     manufacturer_address="Colosseum 1, 1213 NL Hilversum, Netherlands",
        ...     manufacturer_email="contact@nike.com",
        ...     manufacturer_phone="+31 20 123 4567",
        ...     warnings=["Ne pas repasser les motifs imprimés"]
        ... )
        >>>
        >>> # Fabricant hors UE (Chine) avec responsable EU
        >>> gpsr_china = build_gpsr_product_safety(
        ...     manufacturer_name="Shenzhen Factory Ltd",
        ...     manufacturer_address="Building 3, Shenzhen, China",
        ...     manufacturer_email="factory@example.cn",
        ...     responsible_person_name="EU Import SAS",
        ...     responsible_person_address="12 Rue de la Paix, 75001 Paris, France",
        ...     responsible_person_email="compliance@euimport.fr",
        ...     warnings=["Attention: petites pièces - risque d'étouffement"],
        ...     documents_urls=["https://example.com/ce-certificate.pdf"]
        ... )
    """
    product_safety = {
        "manufacturer": {
            "companyName": manufacturer_name,
            "companyAddress": manufacturer_address,
            "email": manufacturer_email,
        }
    }

    # Téléphone optionnel
    if manufacturer_phone:
        product_safety["manufacturer"]["phone"] = manufacturer_phone

    # Personne responsable EU (obligatoire si fabricant hors UE)
    if responsible_person_name:
        product_safety["responsiblePerson"] = {
            "companyName": responsible_person_name,
            "companyAddress": responsible_person_address,
            "email": responsible_person_email,
        }

    # Avertissements
    if warnings:
        product_safety["warnings"] = warnings

    # Documents
    if documents_urls:
        product_safety["documentUrls"] = documents_urls

    return product_safety


def add_gpsr_to_inventory_item(
    inventory_item: Dict[str, Any],
    marketplace_id: str,
    manufacturer_name: str,
    manufacturer_address: str,
    manufacturer_email: str,
    **kwargs,
) -> Dict[str, Any]:
    """
    Ajoute GPSR compliance à un inventory item existant.

    Modifie l'inventory_item en place en ajoutant le bloc productSafety.

    Args:
        inventory_item: Dict inventory item à modifier
        marketplace_id: Marketplace (pour vérifier si GPSR requis)
        manufacturer_name: Nom fabricant
        manufacturer_address: Adresse fabricant
        manufacturer_email: Email fabricant
        **kwargs: Arguments optionnels pour build_gpsr_product_safety()

    Returns:
        inventory_item modifié avec GPSR

    Examples:
        >>> # Après avoir construit inventory_item
        >>> inventory_item = service.convert_to_inventory_item(
        ...     product, sku, marketplace_id="EBAY_FR"
        ... )
        >>>
        >>> # Ajouter GPSR compliance
        >>> inventory_item = add_gpsr_to_inventory_item(
        ...     inventory_item,
        ...     marketplace_id="EBAY_FR",
        ...     manufacturer_name="Nike Europe",
        ...     manufacturer_address="Colosseum 1, Hilversum, NL",
        ...     manufacturer_email="contact@nike.com"
        ... )
        >>>
        >>> # Publier sur eBay
        >>> client.create_or_replace_inventory_item(sku, inventory_item)
    """
    # Vérifier si GPSR requis
    if not is_gpsr_required(marketplace_id):
        return inventory_item

    # Construire productSafety
    product_safety = build_gpsr_product_safety(
        manufacturer_name=manufacturer_name,
        manufacturer_address=manufacturer_address,
        manufacturer_email=manufacturer_email,
        **kwargs,
    )

    # Ajouter à inventory_item
    if "product" not in inventory_item:
        inventory_item["product"] = {}

    inventory_item["product"]["productSafety"] = product_safety

    return inventory_item


def validate_gpsr_compliance(
    inventory_item: Dict[str, Any],
    marketplace_id: str,
) -> tuple[bool, Optional[str]]:
    """
    Valide qu'un inventory item est conforme GPSR.

    Args:
        inventory_item: Inventory item à valider
        marketplace_id: Marketplace

    Returns:
        tuple (is_valid, error_message)
        - is_valid: True si conforme
        - error_message: Message d'erreur si non conforme

    Examples:
        >>> is_valid, error = validate_gpsr_compliance(inventory_item, "EBAY_FR")
        >>> if not is_valid:
        ...     print(f"❌ GPSR non conforme: {error}")
        ...     # Corriger avant publication
    """
    # Si pas marketplace EU, pas de validation requise
    if not is_gpsr_required(marketplace_id):
        return True, None

    # Vérifier présence productSafety
    product_safety = inventory_item.get("product", {}).get("productSafety")

    if not product_safety:
        return False, "productSafety manquant - requis pour marketplaces EU (GPSR)"

    # Vérifier manufacturer
    manufacturer = product_safety.get("manufacturer", {})
    if not manufacturer.get("companyName"):
        return False, "manufacturer.companyName requis (GPSR)"
    if not manufacturer.get("companyAddress"):
        return False, "manufacturer.companyAddress requis (GPSR)"
    if not manufacturer.get("email"):
        return False, "manufacturer.email requis (GPSR)"

    # Si fabricant hors UE, vérifier personne responsable EU
    # (Simplifié: on ne vérifie pas l'origine géographique ici)

    return True, None


def get_gpsr_warning_templates() -> Dict[str, List[str]]:
    """
    Retourne des templates d'avertissements GPSR par catégorie.

    Returns:
        Dict {category: [warnings]}

    Examples:
        >>> templates = get_gpsr_warning_templates()
        >>> toys_warnings = templates["toys"]
        >>> print(toys_warnings[0])
        "Attention: Ne convient pas aux enfants de moins de 3 ans - Risque d'étouffement"
    """
    return {
        "toys": [
            "Attention: Ne convient pas aux enfants de moins de 3 ans - Risque d'étouffement (petites pièces)",
            "À utiliser sous la surveillance d'un adulte",
        ],
        "electronics": [
            "Lire les instructions avant utilisation",
            "Ne pas exposer à l'eau",
            "Risque de choc électrique - ne pas ouvrir",
        ],
        "clothing": [
            "Laver avant première utilisation",
            "Ne pas repasser les motifs imprimés",
            "Tenir éloigné du feu",
        ],
        "cosmetics": [
            "Usage externe uniquement",
            "En cas de contact avec les yeux, rincer abondamment",
            "Tenir hors de portée des enfants",
        ],
    }
