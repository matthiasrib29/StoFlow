"""
Seed Product Attributes

Script pour peupler les tables d'attributs produits avec des données de base.

Usage:
    python scripts/seed_product_attributes.py

Business Rules (2025-12-04):
- Tables à peupler: brands, colors, conditions, sizes, materials, fits, genders, seasons, categories
- Données basées sur les standards Vinted/eBay/Etsy
- Exécuter APRÈS la migration Alembic
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.fit import Fit
from models.public.gender import Gender
from models.public.material import Material
from models.public.season import Season
from models.public.size import Size
from shared.config import settings


def seed_conditions(session):
    """Seed les conditions standards."""
    conditions = [
        Condition(
            name="NEW",
            description_en="New with tags",
            description_fr="Neuf avec étiquettes"
        ),
        Condition(
            name="EXCELLENT",
            description_en="Excellent condition - like new",
            description_fr="Excellent état - comme neuf"
        ),
        Condition(
            name="GOOD",
            description_en="Good condition - minor signs of wear",
            description_fr="Bon état - signes d'usure mineurs"
        ),
        Condition(
            name="SATISFACTORY",
            description_en="Satisfactory - visible signs of wear",
            description_fr="Satisfaisant - signes d'usure visibles"
        ),
    ]

    for condition in conditions:
        existing = session.query(Condition).filter(Condition.name == condition.name).first()
        if not existing:
            session.add(condition)

    session.commit()
    print(f"✓ Seeded {len(conditions)} conditions")


def seed_brands(session):
    """Seed les marques populaires."""
    brands = [
        ("Levi's", "Iconic American denim brand"),
        ("Nike", "Athletic wear and sportswear"),
        ("Adidas", "Sports apparel and footwear"),
        ("Zara", "Spanish fast fashion retailer"),
        ("H&M", "Swedish fashion retailer"),
        ("Uniqlo", "Japanese casual wear"),
        ("Gap", "American clothing brand"),
        ("Mango", "Spanish fashion brand"),
        ("Pull & Bear", "Fashion brand"),
        ("Bershka", "Fashion brand"),
        ("Stradivarius", "Fashion brand"),
        ("Reserved", "Fashion brand"),
        ("New Look", "UK fashion retailer"),
        ("Topshop", "British fashion retailer"),
        ("Urban Outfitters", "Lifestyle brand"),
        ("American Eagle", "Casual clothing"),
        ("Hollister", "Casual wear"),
        ("Abercrombie & Fitch", "Casual luxury"),
        ("Tommy Hilfiger", "American premium brand"),
        ("Calvin Klein", "American fashion house"),
        ("Ralph Lauren", "American luxury brand"),
        ("Lacoste", "French clothing company"),
        ("Guess", "American clothing brand"),
        ("Diesel", "Italian retail clothing"),
        ("G-Star Raw", "Dutch designer brand"),
    ]

    count = 0
    for name, desc in brands:
        existing = session.query(Brand).filter(Brand.name == name).first()
        if not existing:
            session.add(Brand(name=name, description=desc))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} brands")


def seed_colors(session):
    """Seed les couleurs standards."""
    colors = [
        ("Black", "Noir"),
        ("White", "Blanc"),
        ("Grey", "Gris"),
        ("Blue", "Bleu"),
        ("Navy", "Bleu marine"),
        ("Red", "Rouge"),
        ("Pink", "Rose"),
        ("Green", "Vert"),
        ("Yellow", "Jaune"),
        ("Orange", "Orange"),
        ("Purple", "Violet"),
        ("Brown", "Marron"),
        ("Beige", "Beige"),
        ("Khaki", "Kaki"),
        ("Multicolor", "Multicolore"),
    ]

    count = 0
    for name_en, name_fr in colors:
        existing = session.query(Color).filter(Color.name_en == name_en).first()
        if not existing:
            session.add(Color(name_en=name_en, name_fr=name_fr))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} colors")


def seed_sizes(session):
    """Seed les tailles standards."""
    sizes = [
        # Tailles génériques
        "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL",
        # Tailles numériques femmes
        "34", "36", "38", "40", "42", "44", "46", "48",
        # Tailles jeans
        "W26", "W27", "W28", "W29", "W30", "W31", "W32", "W33", "W34", "W36", "W38",
        "W26L30", "W28L30", "W30L30", "W32L30", "W34L30",
        "W26L32", "W28L32", "W30L32", "W32L32", "W34L32",
        "W26L34", "W28L34", "W30L34", "W32L34", "W34L34",
        # Chaussures EU
        "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46",
    ]

    count = 0
    for size in sizes:
        existing = session.query(Size).filter(Size.name == size).first()
        if not existing:
            session.add(Size(name=size))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} sizes")


def seed_materials(session):
    """Seed les matières standards."""
    materials = [
        ("Cotton", "Coton"),
        ("Polyester", "Polyester"),
        ("Denim", "Denim"),
        ("Wool", "Laine"),
        ("Silk", "Soie"),
        ("Linen", "Lin"),
        ("Leather", "Cuir"),
        ("Suede", "Daim"),
        ("Viscose", "Viscose"),
        ("Elastane", "Élasthanne"),
        ("Nylon", "Nylon"),
        ("Acrylic", "Acrylique"),
    ]

    count = 0
    for name_en, name_fr in materials:
        existing = session.query(Material).filter(Material.name_en == name_en).first()
        if not existing:
            session.add(Material(name_en=name_en, name_fr=name_fr))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} materials")


def seed_fits(session):
    """Seed les coupes standards."""
    fits = [
        ("Slim", "Ajusté"),
        ("Regular", "Regular"),
        ("Relaxed", "Décontracté"),
        ("Oversized", "Oversize"),
        ("Tight", "Moulant"),
        ("Loose", "Ample"),
    ]

    count = 0
    for name_en, name_fr in fits:
        existing = session.query(Fit).filter(Fit.name_en == name_en).first()
        if not existing:
            session.add(Fit(name_en=name_en, name_fr=name_fr))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} fits")


def seed_genders(session):
    """Seed les genres standards."""
    genders = [
        ("Men", "Homme"),
        ("Women", "Femme"),
        ("Unisex", "Unisexe"),
        ("Kids", "Enfant"),
    ]

    count = 0
    for name_en, name_fr in genders:
        existing = session.query(Gender).filter(Gender.name_en == name_en).first()
        if not existing:
            session.add(Gender(name_en=name_en, name_fr=name_fr))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} genders")


def seed_seasons(session):
    """Seed les saisons standards."""
    seasons = [
        ("Spring", "Printemps"),
        ("Summer", "Été"),
        ("Fall", "Automne"),
        ("Winter", "Hiver"),
        ("All-Season", "Toute saison"),
    ]

    count = 0
    for name_en, name_fr in seasons:
        existing = session.query(Season).filter(Season.name_en == name_en).first()
        if not existing:
            session.add(Season(name_en=name_en, name_fr=name_fr))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} seasons")


def seed_categories(session):
    """Seed les catégories avec hiérarchie."""
    # Catégories parentes
    parent_categories = [
        ("Clothing", "Vêtements"),
        ("Shoes", "Chaussures"),
        ("Accessories", "Accessoires"),
        ("Bags", "Sacs"),
    ]

    count = 0
    for name_en, name_fr in parent_categories:
        existing = session.query(Category).filter(Category.name_en == name_en).first()
        if not existing:
            session.add(Category(name_en=name_en, name_fr=name_fr))
            count += 1

    session.commit()

    # Catégories enfants (sous-catégories)
    child_categories = [
        # Clothing children
        ("Jeans", "Jeans", "Clothing"),
        ("T-Shirts", "T-Shirts", "Clothing"),
        ("Shirts", "Chemises", "Clothing"),
        ("Sweaters", "Pulls", "Clothing"),
        ("Jackets", "Vestes", "Clothing"),
        ("Coats", "Manteaux", "Clothing"),
        ("Dresses", "Robes", "Clothing"),
        ("Skirts", "Jupes", "Clothing"),
        ("Shorts", "Shorts", "Clothing"),
        ("Pants", "Pantalons", "Clothing"),
        # Shoes children
        ("Sneakers", "Baskets", "Shoes"),
        ("Boots", "Bottes", "Shoes"),
        ("Sandals", "Sandales", "Shoes"),
        ("Heels", "Talons", "Shoes"),
        # Accessories children
        ("Belts", "Ceintures", "Accessories"),
        ("Hats", "Chapeaux", "Accessories"),
        ("Scarves", "Écharpes", "Accessories"),
        ("Jewelry", "Bijoux", "Accessories"),
        # Bags children
        ("Backpacks", "Sacs à dos", "Bags"),
        ("Handbags", "Sacs à main", "Bags"),
        ("Crossbody", "Bandoulière", "Bags"),
    ]

    for name_en, name_fr, parent_name in child_categories:
        existing = session.query(Category).filter(Category.name_en == name_en).first()
        if not existing:
            session.add(Category(
                name_en=name_en,
                name_fr=name_fr,
                parent_category=parent_name
            ))
            count += 1

    session.commit()
    print(f"✓ Seeded {count} categories")


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("Seeding Product Attributes")
    print("=" * 60)

    # Créer engine et session
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Seed dans l'ordre (dépendances)
        seed_conditions(session)
        seed_brands(session)
        seed_colors(session)
        seed_sizes(session)
        seed_materials(session)
        seed_fits(session)
        seed_genders(session)
        seed_seasons(session)
        seed_categories(session)  # En dernier (self-FK)

        print("\n" + "=" * 60)
        print("✅ Seeding completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
