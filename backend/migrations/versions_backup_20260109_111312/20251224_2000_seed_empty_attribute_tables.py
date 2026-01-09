"""Seed empty product attribute tables

Revision ID: 20251224_2000
Revises: 20251224_1900
Create Date: 2024-12-24 20:00:00

This migration seeds the 8 empty attribute tables with data from ALL_PRODUCT_ATTRIBUTES.txt:
1. closures (7 values)
2. condition_sup (33 values)
3. decades (10 values)
4. origins (48 values)
5. rises (6 values)
6. sleeve_lengths (4 values)
7. trends (22 values)
8. unique_features (66 values)

Total: 196 values

Author: Claude
Date: 2025-12-24
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = "20251224_2000"
down_revision = "20251224_1900"
branch_labels = None
depends_on = None


# ===== DATA =====

CLOSURES_DATA = [
    ("button fly", "Braguette à boutons"),
    ("buttons", "Boutons"),
    ("elastic", "Élastique"),
    ("laces", "Lacets"),
    ("pull-on", "Enfilable"),
    ("zip fly", "Braguette zippée"),
    ("zipper", "Fermeture éclair"),
]

CONDITION_SUP_DATA = [
    ("acceptable condition", "État acceptable"),
    ("damaged button", "Bouton endommagé"),
    ("damaged patch", "Patch endommagé"),
    ("excellent condition", "Excellent état"),
    ("faded", "Délavé"),
    ("frayed hems", "Ourlets effilochés"),
    ("general wear", "Usure générale"),
    ("good condition", "Bon état"),
    ("hem undone", "Ourlet défait"),
    ("hemmed/shortened", "Ourlé/Raccourci"),
    ("knee wear", "Usure aux genoux"),
    ("light discoloration", "Légère décoloration"),
    ("like new", "Comme neuf"),
    ("marked discoloration", "Décoloration marquée"),
    ("missing button", "Bouton manquant"),
    ("missing patch", "Patch manquant"),
    ("multiple holes", "Plusieurs trous"),
    ("multiple stains", "Plusieurs taches"),
    ("pilling", "Boulochage"),
    ("resewn", "Recousu"),
    ("seam to fix", "Couture à réparer"),
    ("single stain", "Tache unique"),
    ("small hole", "Petit trou"),
    ("snag", "Accroc"),
    ("stretched", "Étiré"),
    ("tapered", "Ajusté"),
    ("torn", "Déchiré"),
    ("very good condition", "Très bon état"),
    ("vintage patina", "Patine vintage"),
    ("vintage wear", "Usure vintage"),
    ("waist altered", "Taille modifiée"),
    ("worn", "Usé"),
    ("zipper to replace", "Fermeture à remplacer"),
]

DECADES_DATA = [
    ("50s", "Années 50"),
    ("60s", "Années 60"),
    ("70s", "Années 70"),
    ("80s", "Années 80"),
    ("90s", "Années 90"),
    ("2000s", "Années 2000"),
    ("2010s", "Années 2010"),
    ("2020s", "Années 2020"),
    ("vintage", "Vintage"),
    ("modern", "Moderne"),
]

ORIGINS_DATA = [
    ("australia", "Australie"),
    ("bahrain", "Bahreïn"),
    ("bangladesh", "Bangladesh"),
    ("belgium", "Belgique"),
    ("brazil", "Brésil"),
    ("brunei", "Brunei"),
    ("cambodia", "Cambodge"),
    ("canada", "Canada"),
    ("china", "Chine"),
    ("colombia", "Colombie"),
    ("costa rica", "Costa Rica"),
    ("dominican republic", "République Dominicaine"),
    ("egypt", "Égypte"),
    ("el salvador", "El Salvador"),
    ("france", "France"),
    ("germany", "Allemagne"),
    ("guatemala", "Guatemala"),
    ("haiti", "Haïti"),
    ("honduras", "Honduras"),
    ("hong kong", "Hong Kong"),
    ("india", "Inde"),
    ("indonesia", "Indonésie"),
    ("italy", "Italie"),
    ("japan", "Japon"),
    ("jordan", "Jordanie"),
    ("kenya", "Kenya"),
    ("malaysia", "Malaisie"),
    ("malta", "Malte"),
    ("mauritius", "Maurice"),
    ("mexico", "Mexique"),
    ("morocco", "Maroc"),
    ("netherlands", "Pays-Bas"),
    ("nicaragua", "Nicaragua"),
    ("norway", "Norvège"),
    ("pakistan", "Pakistan"),
    ("philippines", "Philippines"),
    ("poland", "Pologne"),
    ("portugal", "Portugal"),
    ("slovakia", "Slovaquie"),
    ("south korea", "Corée du Sud"),
    ("spain", "Espagne"),
    ("taiwan", "Taïwan"),
    ("tunisia", "Tunisie"),
    ("turkey", "Turquie"),
    ("turkmenistan", "Turkménistan"),
    ("united kingdom", "Royaume-Uni"),
    ("usa", "États-Unis"),
    ("vietnam", "Vietnam"),
]

RISES_DATA = [
    ("super low-rise", "Taille très basse"),
    ("low-rise", "Taille basse"),
    ("mid-rise", "Taille mi-haute"),
    ("regular rise", "Taille normale"),
    ("high-rise", "Taille haute"),
    ("ultra high-rise", "Taille très haute"),
]

SLEEVE_LENGTHS_DATA = [
    ("sleeveless", "Sans manches"),
    ("short sleeve", "Manches courtes"),
    ("3/4 sleeve", "Manches 3/4"),
    ("long sleeve", "Manches longues"),
]

TRENDS_DATA = [
    ("athleisure", "Athleisure"),
    ("bohemian", "Bohème"),
    ("cottagecore", "Cottagecore"),
    ("dark academia", "Dark Academia"),
    ("geek chic", "Geek Chic"),
    ("gothic", "Gothique"),
    ("grunge", "Grunge"),
    ("japanese streetwear", "Streetwear Japonais"),
    ("minimalist", "Minimaliste"),
    ("modern", "Moderne"),
    ("normcore", "Normcore"),
    ("preppy", "Preppy"),
    ("punk", "Punk"),
    ("retro", "Rétro"),
    ("skater", "Skater"),
    ("sportswear", "Sportswear"),
    ("streetwear", "Streetwear"),
    ("techwear", "Techwear"),
    ("vintage", "Vintage"),
    ("western", "Western"),
    ("workwear", "Workwear"),
    ("y2k", "Y2K"),
]

UNIQUE_FEATURES_DATA = [
    ("acid wash", "Délavage acide"),
    ("appliqué", "Appliqué"),
    ("bar tacks", "Points d'arrêt"),
    ("beaded", "Perlé"),
    ("belt loops", "Passants de ceinture"),
    ("bleached", "Blanchi"),
    ("brass rivets", "Rivets en laiton"),
    ("button detail", "Détail boutonné"),
    ("chain detail", "Détail chaîne"),
    ("chain stitching", "Couture chaînette"),
    ("coin pocket", "Poche à monnaie"),
    ("contrast stitching", "Coutures contrastées"),
    ("copper rivets", "Rivets en cuivre"),
    ("cuffed", "Revers"),
    ("custom design", "Design personnalisé"),
    ("darted", "Pinces"),
    ("deadstock fabric", "Tissu deadstock"),
    ("decorative pockets", "Poches décoratives"),
    ("distressed", "Vieilli"),
    ("double stitch", "Double couture"),
    ("embossed buttons", "Boutons embossés"),
    ("embroidered", "Brodé"),
    ("fading", "Décoloration"),
    ("flat felled seams", "Coutures rabattues"),
    ("fly", "Braguette"),
    ("frayed", "Effiloché"),
    ("garment dyed", "Teinture pièce"),
    ("gradient", "Dégradé"),
    ("hand embroidered", "Brodé main"),
    ("hand painted", "Peint main"),
    ("hidden rivets", "Rivets cachés"),
    ("jacron patch", "Patch jacron"),
    ("lace detail", "Détail dentelle"),
    ("leather label", "Étiquette cuir"),
    ("leather patch", "Patch cuir"),
    ("lined", "Doublé"),
    ("original buttons", "Boutons d'origine"),
    ("padded", "Rembourré"),
    ("painted", "Peint"),
    ("paneled", "Panneaux"),
    ("paper patch", "Patch papier"),
    ("patchwork", "Patchwork"),
    ("pleated", "Plissé"),
    ("printed", "Imprimé"),
    ("raw denim", "Denim brut"),
    ("raw hem", "Ourlet brut"),
    ("reinforced seams", "Coutures renforcées"),
    ("ripped", "Déchiré"),
    ("rope dyed", "Teinture corde"),
    ("sanforized", "Sanforisé"),
    ("selvage denim", "Denim selvedge"),
    ("selvedge", "Selvedge"),
    ("sequined", "Pailleté"),
    ("shuttle loom", "Métier navette"),
    ("single stitch", "Simple couture"),
    ("stone washed", "Délavé pierre"),
    ("studded", "Clouté"),
    ("triple stitch", "Triple couture"),
    ("unsanforized", "Non sanforisé"),
    ("vintage hardware", "Quincaillerie vintage"),
    ("vintage wash", "Lavage vintage"),
    ("waistband", "Ceinture"),
    ("whiskering", "Moustaches"),
    ("woven label", "Étiquette tissée"),
    ("yoke", "Empiècement"),
    ("zipper detail", "Détail zip"),
]


def upgrade() -> None:
    """Seed the 8 empty attribute tables."""
    connection = op.get_bind()

    # ===== 1. CLOSURES =====
    print("  📦 Seeding closures...")
    for name_en, name_fr in CLOSURES_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.closures (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(CLOSURES_DATA)} closures")

    # ===== 2. CONDITION_SUP =====
    print("  📦 Seeding condition_sup...")
    for name_en, name_fr in CONDITION_SUP_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.condition_sup (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(CONDITION_SUP_DATA)} condition_sup values")

    # ===== 3. DECADES =====
    print("  📦 Seeding decades...")
    for name_en, name_fr in DECADES_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.decades (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(DECADES_DATA)} decades")

    # ===== 4. ORIGINS =====
    print("  📦 Seeding origins...")
    for name_en, name_fr in ORIGINS_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.origins (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(ORIGINS_DATA)} origins")

    # ===== 5. RISES =====
    print("  📦 Seeding rises...")
    for name_en, name_fr in RISES_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.rises (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(RISES_DATA)} rises")

    # ===== 6. SLEEVE_LENGTHS =====
    print("  📦 Seeding sleeve_lengths...")
    for name_en, name_fr in SLEEVE_LENGTHS_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.sleeve_lengths (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(SLEEVE_LENGTHS_DATA)} sleeve_lengths")

    # ===== 7. TRENDS =====
    print("  📦 Seeding trends...")
    for name_en, name_fr in TRENDS_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.trends (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(TRENDS_DATA)} trends")

    # ===== 8. UNIQUE_FEATURES =====
    print("  📦 Seeding unique_features...")
    for name_en, name_fr in UNIQUE_FEATURES_DATA:
        connection.execute(
            sa.text("""
                INSERT INTO product_attributes.unique_features (name_en, name_fr)
                VALUES (:name_en, :name_fr)
                ON CONFLICT (name_en) DO NOTHING
            """),
            {"name_en": name_en, "name_fr": name_fr}
        )
    print(f"  ✅ Seeded {len(UNIQUE_FEATURES_DATA)} unique_features")

    # Summary
    total = (
        len(CLOSURES_DATA) + len(CONDITION_SUP_DATA) + len(DECADES_DATA) +
        len(ORIGINS_DATA) + len(RISES_DATA) + len(SLEEVE_LENGTHS_DATA) +
        len(TRENDS_DATA) + len(UNIQUE_FEATURES_DATA)
    )
    print(f"\n  🎉 Total: {total} values seeded across 8 tables")


def downgrade() -> None:
    """Remove seeded data from the 8 tables."""
    connection = op.get_bind()

    tables = [
        "closures", "condition_sup", "decades", "origins",
        "rises", "sleeve_lengths", "trends", "unique_features"
    ]

    for table in tables:
        connection.execute(sa.text(f"DELETE FROM product_attributes.{table}"))
        print(f"  🗑️  Cleared {table}")

    print("  ✅ All seeded data removed")
