"""
Script pour peupler la table des catégories avec les catégories de vêtements.

Usage:
    python scripts/seed_categories.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from shared.database import SessionLocal
from models.public.category import Category


def seed_categories(db: Session):
    """Peuple la base de données avec toutes les catégories de vêtements."""

    categories_data = [
        # Root category
        ("clothing", "Clothing", "Vêtements", None, "unisex"),

        # Main categories (depth 1)
        ("tops", "Tops", "Hauts", "clothing", "unisex"),
        ("bottoms", "Bottoms", "Bas", "clothing", "unisex"),
        ("outerwear", "Outerwear", "Vêtements d'extérieur", "clothing", "unisex"),
        ("dresses-jumpsuits", "Dresses & Jumpsuits", "Robes et combinaisons", "clothing", "female"),
        ("formalwear", "Formalwear", "Costumes et tenues habillées", "clothing", "unisex"),
        ("sportswear", "Sportswear", "Vêtements de sport", "clothing", "unisex"),

        # Tops subcategories
        ("t-shirt", "T-shirt", "T-shirt", "tops", "unisex"),
        ("tank-top", "Tank top", "Débardeur", "tops", "unisex"),
        ("shirt", "Shirt", "Chemise", "tops", "unisex"),
        ("blouse", "Blouse", "Blouse", "tops", "female"),
        ("top", "Top", "Top", "tops", "female"),
        ("bodysuit", "Bodysuit", "Body", "tops", "female"),
        ("corset", "Corset", "Corset", "tops", "female"),
        ("bustier", "Bustier", "Bustier", "tops", "female"),
        ("camisole", "Camisole", "Caraco", "tops", "female"),
        ("crop-top", "Crop top", "Crop top", "tops", "female"),
        ("polo", "Polo", "Polo", "tops", "unisex"),
        ("sweater", "Sweater", "Pull", "tops", "unisex"),
        ("cardigan", "Cardigan", "Cardigan", "tops", "unisex"),
        ("sweatshirt", "Sweatshirt", "Sweat", "tops", "unisex"),
        ("hoodie", "Hoodie", "Hoodie", "tops", "unisex"),
        ("sports-jersey", "Sports jersey", "Maillot de sport", "tops", "unisex"),
        ("fleece", "Fleece", "Polaire", "tops", "unisex"),
        ("overshirt", "Overshirt", "Surchemise", "tops", "unisex"),

        # Bottoms subcategories
        ("pants", "Pants", "Pantalon", "bottoms", "unisex"),
        ("jeans", "Jeans", "Jean", "bottoms", "unisex"),
        ("chinos", "Chinos", "Chino", "bottoms", "unisex"),
        ("joggers", "Joggers", "Jogging", "bottoms", "unisex"),
        ("cargo-pants", "Cargo pants", "Pantalon cargo", "bottoms", "unisex"),
        ("dress-pants", "Dress pants", "Pantalon habillé", "bottoms", "unisex"),
        ("shorts", "Shorts", "Short", "bottoms", "unisex"),
        ("bermuda", "Bermuda", "Bermuda", "bottoms", "unisex"),
        ("skirt", "Skirt", "Jupe", "bottoms", "female"),
        ("leggings", "Leggings", "Legging", "bottoms", "female"),
        ("culottes", "Culottes", "Jupe-culotte", "bottoms", "female"),

        # Outerwear subcategories
        ("jacket", "Jacket", "Veste", "outerwear", "unisex"),
        ("bomber", "Bomber", "Blouson", "outerwear", "unisex"),
        ("puffer", "Puffer", "Doudoune", "outerwear", "unisex"),
        ("coat", "Coat", "Manteau", "outerwear", "unisex"),
        ("trench", "Trench", "Trench", "outerwear", "unisex"),
        ("parka", "Parka", "Parka", "outerwear", "unisex"),
        ("raincoat", "Raincoat", "Imperméable", "outerwear", "unisex"),
        ("windbreaker", "Windbreaker", "Coupe-vent", "outerwear", "unisex"),
        ("blazer", "Blazer", "Blazer", "outerwear", "unisex"),
        ("vest", "Vest", "Gilet", "outerwear", "unisex"),
        ("half-zip", "Half-zip", "Demi-zip", "outerwear", "unisex"),
        ("cape", "Cape", "Cape", "outerwear", "female"),
        ("poncho", "Poncho", "Poncho", "outerwear", "unisex"),
        ("kimono", "Kimono", "Kimono", "outerwear", "female"),

        # Dresses & Jumpsuits subcategories
        ("dress", "Dress", "Robe", "dresses-jumpsuits", "female"),
        ("jumpsuit", "Jumpsuit", "Combinaison", "dresses-jumpsuits", "unisex"),
        ("romper", "Romper", "Combishort", "dresses-jumpsuits", "female"),
        ("overalls", "Overalls", "Salopette", "dresses-jumpsuits", "unisex"),

        # Formalwear subcategories
        ("suit", "Suit", "Costume", "formalwear", "unisex"),
        ("tuxedo", "Tuxedo", "Smoking", "formalwear", "male"),
        ("womens-suit", "Women's suit", "Tailleur", "formalwear", "female"),
        ("suit-vest", "Suit vest", "Gilet de costume", "formalwear", "male"),

        # Sportswear subcategories
        ("sports-bra", "Sports bra", "Brassière de sport", "sportswear", "female"),
        ("sports-top", "Sports top", "T-shirt de sport", "sportswear", "unisex"),
        ("sports-shorts", "Sports shorts", "Short de sport", "sportswear", "unisex"),
        ("sports-leggings", "Sports leggings", "Legging de sport", "sportswear", "female"),
        ("tracksuit", "Tracksuit", "Survêtement", "sportswear", "unisex"),
        ("swimsuit", "Swimsuit", "Maillot de bain", "sportswear", "unisex"),
        ("bikini", "Bikini", "Bikini", "sportswear", "female"),
    ]

    # Supprimer les catégories existantes (ATTENTION: cascade delete)
    print("Suppression des catégories existantes...")
    db.query(Category).delete()
    db.commit()

    # Créer les catégories
    created_count = 0
    for id_slug, name_en, name_fr, parent, gender in categories_data:
        category = Category(
            name_en=id_slug,  # Utiliser l'id comme clé primaire
            parent_category=parent,
            name_fr=name_fr,
            default_gender=gender  # Valeur string directe (unisex, male, female)
        )
        db.add(category)
        created_count += 1

        if created_count % 10 == 0:
            print(f"Créé {created_count} catégories...")

    db.commit()
    print(f"\n✅ {created_count} catégories créées avec succès!")

    # Afficher un résumé
    print("\n📊 Résumé de la hiérarchie:")
    root_categories = db.query(Category).filter(Category.parent_category == None).all()
    for root in root_categories:
        print(f"\n{root.name_en} ({root.name_fr})")
        children = db.query(Category).filter(Category.parent_category == root.name_en).all()
        for child in children:
            subcats = db.query(Category).filter(Category.parent_category == child.name_en).count()
            print(f"  ├── {child.name_en} ({child.name_fr}) - {subcats} sous-catégories")


def main():
    """Point d'entrée du script."""
    print("🌱 Seed des catégories de vêtements\n")

    db = SessionLocal()
    try:
        seed_categories(db)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
