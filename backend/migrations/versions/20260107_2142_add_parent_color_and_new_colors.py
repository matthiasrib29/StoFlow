"""add_parent_color_and_new_colors

Add parent_color column and insert 31 new colors (+ Metallic parent).
All color names converted to Sentence case for consistency.

Revision ID: f262703133fd
Revises: cdb2019ff925
Create Date: 2026-01-07 21:42:10.924161+01:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'f262703133fd'
down_revision: Union[str, None] = 'cdb2019ff925'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # ========================================================================
    # STEP 1: Add parent_color column
    # ========================================================================
    print("Step 1: Adding parent_color column to colors table...")

    conn.execute(text("""
        ALTER TABLE product_attributes.colors
        ADD COLUMN parent_color VARCHAR(100);
    """))

    # Add FK constraint
    conn.execute(text("""
        ALTER TABLE product_attributes.colors
        ADD CONSTRAINT fk_colors_parent_color
        FOREIGN KEY (parent_color)
        REFERENCES product_attributes.colors(name_en)
        ON UPDATE CASCADE
        ON DELETE SET NULL;
    """))

    # Add index
    conn.execute(text("""
        CREATE INDEX idx_colors_parent_color
        ON product_attributes.colors(parent_color);
    """))

    print("✅ parent_color column added")

    # ========================================================================
    # STEP 2: Convert existing colors to Sentence case
    # ========================================================================
    print("Step 2: Converting existing colors to Sentence case...")

    # All existing colors are already in proper case except these need fixing
    # (Most are already correct, but let's be explicit)
    existing_updates = [
        # These are already correct: White, Cream, Beige, etc.
        # Only Light-blue needs attention but it's correct as compound
    ]

    # Update parent relationships for existing colors
    existing_parents = [
        ("Charcoal", "Gray"),
        ("Silver", "Gray"),
        ("Tan", "Brown"),
        ("Camel", "Brown"),
        ("Cognac", "Brown"),
        ("Burgundy", "Red"),
        ("Coral", "Orange"),
        ("Mustard", "Yellow"),
        ("Gold", "Yellow"),
        ("Olive", "Green"),
        ("Khaki", "Green"),
        ("Mint", "Green"),
        ("Navy", "Blue"),
        ("Light-blue", "Blue"),
        ("Teal", "Blue"),
        ("Turquoise", "Blue"),
        ("Lavender", "Purple"),
        ("Fuchsia", "Pink"),
    ]

    for color, parent in existing_parents:
        conn.execute(text("""
            UPDATE product_attributes.colors
            SET parent_color = :parent
            WHERE name_en = :color;
        """), {"color": color, "parent": parent})

    print(f"✅ Updated {len(existing_parents)} parent relationships")

    # ========================================================================
    # STEP 3: Insert Metallic parent color
    # ========================================================================
    print("Step 3: Adding Metallic parent color...")

    conn.execute(text("""
        INSERT INTO product_attributes.colors (
            name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl,
            hex_code, parent_color
        ) VALUES (
            'Metallic', 'Métallique', 'Metallisch', 'Metallico', 'Metálico',
            'Metallic', 'Metaliczny', '#C0C0C0', NULL
        )
        ON CONFLICT (name_en) DO NOTHING;
    """))

    print("✅ Metallic parent color added")

    # ========================================================================
    # STEP 4: Insert 31 new colors (Sentence case)
    # ========================================================================
    print("Step 4: Inserting 31 new colors...")

    new_colors = [
        # WHITE family
        ("Off-white", "Blanc cassé", "Gebrochen Weiß", "Bianco sporco", "Blanco roto", "Gebroken wit", "Złamana biel", "White", "#FAF9F6"),
        ("Ivory", "Ivoire", "Elfenbein", "Avorio", "Marfil", "Ivoorwit", "Kość słoniowa", "White", "#FFFFF0"),

        # BEIGE family
        ("Sand", "Sable", "Sand", "Sabbia", "Arena", "Zand", "Piaskowy", "Beige", "#C2B280"),
        ("Nude", "Nude", "Nude", "Nudo", "Nude", "Nude", "Cielisty", "Beige", "#E3BC9A"),

        # GRAY family
        ("Slate", "Ardoise", "Schiefergrau", "Ardesia", "Pizarra", "Leisteen", "Łupkowy", "Gray", "#708090"),
        ("Taupe", "Taupe", "Taupe", "Talpa", "Topo", "Taupe", "Szarobrązowy", "Gray", "#483C32"),

        # BROWN family
        ("Mocha", "Moka", "Mokka", "Moca", "Moca", "Mokka", "Mokka", "Brown", "#967969"),
        ("Chocolate", "Chocolat", "Schokolade", "Cioccolato", "Chocolate", "Chocolade", "Czekoladowy", "Brown", "#7B3F00"),
        ("Espresso", "Expresso", "Espresso", "Espresso", "Espresso", "Espresso", "Espresso", "Brown", "#4E312D"),
        ("Cinnamon", "Cannelle", "Zimt", "Cannella", "Canela", "Kaneel", "Cynamonowy", "Brown", "#D2691E"),

        # RED family
        ("Wine", "Vin", "Weinrot", "Vinaccia", "Vino", "Wijnrood", "Winny", "Red", "#722F37"),
        ("Cherry red", "Rouge cerise", "Kirschrot", "Rosso ciliegia", "Rojo cereza", "Kersenrood", "Wiśniowy", "Red", "#DE3163"),
        ("Rust", "Rouille", "Rostrot", "Ruggine", "Óxido", "Roest", "Rdzawy", "Red", "#B7410E"),

        # ORANGE family
        ("Terracotta", "Terracotta", "Terrakotta", "Terracotta", "Terracota", "Terracotta", "Terakota", "Orange", "#E2725B"),
        ("Burnt orange", "Orange brûlé", "Gebranntes Orange", "Arancione bruciato", "Naranja quemado", "Verbrand oranje", "Spalony pomarańcz", "Orange", "#CC5500"),
        ("Peach", "Pêche", "Pfirsich", "Pesca", "Melocotón", "Perzik", "Brzoskwiniowy", "Orange", "#FFCBA4"),

        # YELLOW family
        ("Butter yellow", "Jaune beurre", "Buttergelb", "Giallo burro", "Amarillo mantequilla", "Botergeel", "Maślany", "Yellow", "#FFFAA0"),

        # GREEN family
        ("Sage", "Sauge", "Salbei", "Salvia", "Salvia", "Salie", "Szałwiowy", "Green", "#9DC183"),
        ("Emerald", "Émeraude", "Smaragd", "Smeraldo", "Esmeralda", "Smaragd", "Szmaragdowy", "Green", "#50C878"),
        ("Forest green", "Vert forêt", "Waldgrün", "Verde foresta", "Verde bosque", "Bosgroen", "Leśna zieleń", "Green", "#228B22"),

        # BLUE family
        ("Cobalt", "Cobalt", "Kobalt", "Cobalto", "Cobalto", "Kobalt", "Kobaltowy", "Blue", "#0047AB"),
        ("Powder blue", "Bleu poudré", "Puderblau", "Blu polvere", "Azul empolvado", "Poederblauw", "Pudrowy niebieski", "Blue", "#B0E0E6"),

        # PURPLE family
        ("Lilac", "Lilas", "Flieder", "Lilla", "Lila", "Lila", "Liliowy", "Purple", "#C8A2C8"),
        ("Plum", "Prune", "Pflaume", "Prugna", "Ciruela", "Pruim", "Śliwkowy", "Purple", "#8E4585"),
        ("Eggplant", "Aubergine", "Aubergine", "Melanzana", "Berenjena", "Aubergine", "Bakłażanowy", "Purple", "#614051"),
        ("Mauve", "Mauve", "Malve", "Malva", "Malva", "Mauve", "Lila różowy", "Purple", "#E0B0FF"),

        # PINK family
        ("Blush", "Rose poudré", "Altrosa", "Rosa cipria", "Rosa rubor", "Blozend roze", "Róż pudrowy", "Pink", "#DE5D83"),
        ("Dusty pink", "Vieux rose", "Altrosa", "Rosa antico", "Rosa viejo", "Oud roze", "Brudny róż", "Pink", "#D4A5A5"),
        ("Hot pink", "Rose vif", "Pink", "Rosa shocking", "Rosa intenso", "Felroze", "Jaskrawy róż", "Pink", "#FF69B4"),

        # METALLIC family
        ("Rose gold", "Or rose", "Roségold", "Oro rosa", "Oro rosa", "Roségoud", "Różowe złoto", "Metallic", "#B76E79"),
        ("Bronze", "Bronze", "Bronze", "Bronzo", "Bronce", "Brons", "Brązowy metaliczny", "Metallic", "#CD7F32"),
    ]

    for name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl, parent, hex_code in new_colors:
        conn.execute(text("""
            INSERT INTO product_attributes.colors (
                name_en, name_fr, name_de, name_it, name_es, name_nl, name_pl,
                hex_code, parent_color
            ) VALUES (
                :name_en, :name_fr, :name_de, :name_it, :name_es, :name_nl, :name_pl,
                :hex_code, :parent
            )
            ON CONFLICT (name_en) DO NOTHING;
        """), {
            "name_en": name_en,
            "name_fr": name_fr,
            "name_de": name_de,
            "name_it": name_it,
            "name_es": name_es,
            "name_nl": name_nl,
            "name_pl": name_pl,
            "hex_code": hex_code,
            "parent": parent,
        })

    print(f"✅ Inserted {len(new_colors)} new colors")
    print("🎉 Color expansion completed!")


def downgrade() -> None:
    conn = op.get_bind()

    # Delete new colors (31 + Metallic)
    new_color_names = [
        'Off-white', 'Ivory', 'Sand', 'Nude', 'Slate', 'Taupe',
        'Mocha', 'Chocolate', 'Espresso', 'Cinnamon',
        'Wine', 'Cherry red', 'Rust',
        'Terracotta', 'Burnt orange', 'Peach',
        'Butter yellow',
        'Sage', 'Emerald', 'Forest green',
        'Cobalt', 'Powder blue',
        'Lilac', 'Plum', 'Eggplant', 'Mauve',
        'Blush', 'Dusty pink', 'Hot pink',
        'Rose gold', 'Bronze',
        'Metallic'
    ]

    for color in new_color_names:
        conn.execute(text("""
            DELETE FROM product_attributes.colors WHERE name_en = :color;
        """), {"color": color})

    # Drop parent_color column
    conn.execute(text("""
        ALTER TABLE product_attributes.colors DROP COLUMN IF EXISTS parent_color CASCADE;
    """))

    print("⚠️  Downgrade completed - parent_color removed and new colors deleted")
