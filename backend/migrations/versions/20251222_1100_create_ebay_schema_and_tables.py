"""create_ebay_schema_and_tables

Creates the 'ebay' schema and migrates/creates all eBay-related tables.

This migration:
1. Creates the 'ebay' schema
2. Moves existing eBay tables from 'public' to 'ebay' schema
3. Creates aspect value tables for multilingual support

Tables moved:
- public.marketplace_config → ebay.marketplace_config
- public.aspect_mappings → ebay.aspect_name_mapping (renamed)
- public.ebay_category_mapping → ebay.category_mapping
- public.exchange_rate_config → ebay.exchange_rate

Tables created:
- ebay.aspect_colour (color translations)
- ebay.aspect_size (size translations)
- ebay.aspect_material (material translations)
- ebay.aspect_fit (fit translations)
- ebay.aspect_closure (closure translations)
- ebay.aspect_rise (rise translations)
- ebay.aspect_waist_size (waist size translations)
- ebay.aspect_inside_leg (inside leg translations)
- ebay.aspect_department (department translations)
- ebay.aspect_type (type translations)
- ebay.aspect_style (style translations)
- ebay.aspect_pattern (pattern translations)
- ebay.aspect_neckline (neckline translations)
- ebay.aspect_sleeve_length (sleeve length translations)
- ebay.aspect_occasion (occasion translations)
- ebay.aspect_features (features translations)

Revision ID: c7a9b3d8e5f2
Revises: b58854908d67
Create Date: 2025-12-22 11:00:00.000000+01:00

Author: Claude
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7a9b3d8e5f2'
down_revision: Union[str, None] = 'b58854908d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# List of all aspect value tables to create
ASPECT_TABLES = [
    'aspect_colour',
    'aspect_size',
    'aspect_material',
    'aspect_fit',
    'aspect_closure',
    'aspect_rise',
    'aspect_waist_size',
    'aspect_inside_leg',
    'aspect_department',
    'aspect_type',
    'aspect_style',
    'aspect_pattern',
    'aspect_neckline',
    'aspect_sleeve_length',
    'aspect_occasion',
    'aspect_features',
]


def upgrade() -> None:
    """Create ebay schema and migrate/create tables."""

    # ========================================
    # 1. CREATE EBAY SCHEMA
    # ========================================
    op.execute("CREATE SCHEMA IF NOT EXISTS ebay")

    # ========================================
    # 2. MOVE EXISTING TABLES TO EBAY SCHEMA
    # ========================================

    # 2a. Move marketplace_config
    op.execute("ALTER TABLE public.marketplace_config SET SCHEMA ebay")

    # 2b. Move and rename aspect_mappings → aspect_name_mapping
    op.execute("ALTER TABLE public.aspect_mappings SET SCHEMA ebay")
    op.execute("ALTER TABLE ebay.aspect_mappings RENAME TO aspect_name_mapping")

    # 2c. Move and rename ebay_category_mapping → category_mapping
    op.execute("ALTER TABLE public.ebay_category_mapping SET SCHEMA ebay")
    op.execute("ALTER TABLE ebay.ebay_category_mapping RENAME TO category_mapping")

    # 2d. Move and rename exchange_rate_config → exchange_rate
    op.execute("ALTER TABLE public.exchange_rate_config SET SCHEMA ebay")
    op.execute("ALTER TABLE ebay.exchange_rate_config RENAME TO exchange_rate")

    # ========================================
    # 3. CREATE ASPECT VALUE TABLES
    # ========================================
    # Each table has:
    # - ebay_gb (PK): English/GB value (reference)
    # - ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl: translations

    for table_name in ASPECT_TABLES:
        op.create_table(
            table_name,
            sa.Column('ebay_gb', sa.String(100), primary_key=True,
                      comment='English/GB value (reference key)'),
            sa.Column('ebay_fr', sa.String(100), nullable=True,
                      comment='French translation'),
            sa.Column('ebay_de', sa.String(100), nullable=True,
                      comment='German translation'),
            sa.Column('ebay_es', sa.String(100), nullable=True,
                      comment='Spanish translation'),
            sa.Column('ebay_it', sa.String(100), nullable=True,
                      comment='Italian translation'),
            sa.Column('ebay_nl', sa.String(100), nullable=True,
                      comment='Dutch translation'),
            sa.Column('ebay_be', sa.String(100), nullable=True,
                      comment='Belgian French translation'),
            sa.Column('ebay_pl', sa.String(100), nullable=True,
                      comment='Polish translation'),
            schema='ebay'
        )

    # ========================================
    # 4. INSERT INITIAL DATA - COLOURS
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_colour (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Black', 'Noir', 'Schwarz', 'Negro', 'Nero', 'Zwart', 'Noir', 'Czarny'),
        ('White', 'Blanc', 'Weiß', 'Blanco', 'Bianco', 'Wit', 'Blanc', 'Biały'),
        ('Blue', 'Bleu', 'Blau', 'Azul', 'Blu', 'Blauw', 'Bleu', 'Niebieski'),
        ('Red', 'Rouge', 'Rot', 'Rojo', 'Rosso', 'Rood', 'Rouge', 'Czerwony'),
        ('Green', 'Vert', 'Grün', 'Verde', 'Verde', 'Groen', 'Vert', 'Zielony'),
        ('Yellow', 'Jaune', 'Gelb', 'Amarillo', 'Giallo', 'Geel', 'Jaune', 'Żółty'),
        ('Orange', 'Orange', 'Orange', 'Naranja', 'Arancione', 'Oranje', 'Orange', 'Pomarańczowy'),
        ('Pink', 'Rose', 'Rosa', 'Rosa', 'Rosa', 'Roze', 'Rose', 'Różowy'),
        ('Purple', 'Violet', 'Lila', 'Púrpura', 'Viola', 'Paars', 'Violet', 'Fioletowy'),
        ('Brown', 'Marron', 'Braun', 'Marrón', 'Marrone', 'Bruin', 'Marron', 'Brązowy'),
        ('Grey', 'Gris', 'Grau', 'Gris', 'Grigio', 'Grijs', 'Gris', 'Szary'),
        ('Beige', 'Beige', 'Beige', 'Beige', 'Beige', 'Beige', 'Beige', 'Beżowy'),
        ('Navy', 'Bleu Marine', 'Marineblau', 'Azul Marino', 'Blu Navy', 'Marineblauw', 'Bleu Marine', 'Granatowy'),
        ('Cream', 'Crème', 'Creme', 'Crema', 'Crema', 'Crème', 'Crème', 'Kremowy'),
        ('Multicoloured', 'Multicolore', 'Mehrfarbig', 'Multicolor', 'Multicolore', 'Meerkleurig', 'Multicolore', 'Wielokolorowy'),
        ('Khaki', 'Kaki', 'Khaki', 'Caqui', 'Cachi', 'Kaki', 'Kaki', 'Khaki'),
        ('Gold', 'Or', 'Gold', 'Dorado', 'Oro', 'Goud', 'Or', 'Złoty'),
        ('Silver', 'Argent', 'Silber', 'Plateado', 'Argento', 'Zilver', 'Argent', 'Srebrny'),
        ('Burgundy', 'Bordeaux', 'Burgund', 'Burdeos', 'Bordeaux', 'Bordeauxrood', 'Bordeaux', 'Bordowy'),
        ('Turquoise', 'Turquoise', 'Türkis', 'Turquesa', 'Turchese', 'Turquoise', 'Turquoise', 'Turkusowy')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 5. INSERT INITIAL DATA - DEPARTMENTS
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_department (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Men', 'Homme', 'Herren', 'Hombre', 'Uomo', 'Heren', 'Homme', 'Mężczyźni'),
        ('Women', 'Femme', 'Damen', 'Mujer', 'Donna', 'Dames', 'Femme', 'Kobiety'),
        ('Unisex Adults', 'Adulte unisexe', 'Unisex Erwachsene', 'Adultos unisex', 'Adulto unisex', 'Unisex volwassenen', 'Adulte unisexe', 'Dorośli unisex'),
        ('Boys', 'Garçon', 'Jungen', 'Niños', 'Bambino', 'Jongens', 'Garçon', 'Chłopcy'),
        ('Girls', 'Fille', 'Mädchen', 'Niñas', 'Bambina', 'Meisjes', 'Fille', 'Dziewczynki')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 6. INSERT INITIAL DATA - MATERIALS
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_material (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Cotton', 'Coton', 'Baumwolle', 'Algodón', 'Cotone', 'Katoen', 'Coton', 'Bawełna'),
        ('Polyester', 'Polyester', 'Polyester', 'Poliéster', 'Poliestere', 'Polyester', 'Polyester', 'Poliester'),
        ('Denim', 'Jean', 'Denim', 'Mezclilla', 'Denim', 'Denim', 'Jean', 'Dżins'),
        ('Leather', 'Cuir', 'Leder', 'Cuero', 'Pelle', 'Leer', 'Cuir', 'Skóra'),
        ('Wool', 'Laine', 'Wolle', 'Lana', 'Lana', 'Wol', 'Laine', 'Wełna'),
        ('Silk', 'Soie', 'Seide', 'Seda', 'Seta', 'Zijde', 'Soie', 'Jedwab'),
        ('Linen', 'Lin', 'Leinen', 'Lino', 'Lino', 'Linnen', 'Lin', 'Len'),
        ('Nylon', 'Nylon', 'Nylon', 'Nailon', 'Nylon', 'Nylon', 'Nylon', 'Nylon'),
        ('Viscose', 'Viscose', 'Viskose', 'Viscosa', 'Viscosa', 'Viscose', 'Viscose', 'Wiskoza'),
        ('Cashmere', 'Cachemire', 'Kaschmir', 'Cachemir', 'Cashmere', 'Kasjmier', 'Cachemire', 'Kaszmir'),
        ('Velvet', 'Velours', 'Samt', 'Terciopelo', 'Velluto', 'Fluweel', 'Velours', 'Aksamit'),
        ('Suede', 'Daim', 'Wildleder', 'Ante', 'Camoscio', 'Suède', 'Daim', 'Zamsz'),
        ('Fleece', 'Polaire', 'Fleece', 'Forro polar', 'Pile', 'Fleece', 'Polaire', 'Polar'),
        ('Elastane', 'Élasthanne', 'Elasthan', 'Elastano', 'Elastan', 'Elastaan', 'Élasthanne', 'Elastan'),
        ('Synthetic', 'Synthétique', 'Synthetik', 'Sintético', 'Sintetico', 'Synthetisch', 'Synthétique', 'Syntetyczny')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 7. INSERT INITIAL DATA - FIT
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_fit (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Regular', 'Regular', 'Regular', 'Regular', 'Regular', 'Normaal', 'Regular', 'Regularny'),
        ('Slim', 'Slim', 'Slim', 'Ajustado', 'Slim', 'Slim', 'Slim', 'Slim'),
        ('Skinny', 'Skinny', 'Skinny', 'Pitillo', 'Skinny', 'Skinny', 'Skinny', 'Skinny'),
        ('Loose', 'Ample', 'Weit', 'Ancho', 'Largo', 'Ruim', 'Ample', 'Luźny'),
        ('Relaxed', 'Relaxed', 'Relaxed', 'Relajado', 'Rilassato', 'Relaxed', 'Relaxed', 'Swobodny'),
        ('Oversized', 'Oversize', 'Oversized', 'Oversize', 'Oversize', 'Oversized', 'Oversize', 'Oversize'),
        ('Bootcut', 'Bootcut', 'Bootcut', 'Bootcut', 'Bootcut', 'Bootcut', 'Bootcut', 'Bootcut'),
        ('Straight', 'Droit', 'Gerade', 'Recto', 'Dritto', 'Recht', 'Droit', 'Prosty'),
        ('Wide Leg', 'Jambe large', 'Weites Bein', 'Pierna ancha', 'Gamba larga', 'Wijde pijp', 'Jambe large', 'Szeroka nogawka'),
        ('Tapered', 'Fuselé', 'Konisch', 'Estrecho', 'Affusolato', 'Taps toelopend', 'Fuselé', 'Zwężany'),
        ('Athletic', 'Athlétique', 'Athletisch', 'Atlético', 'Atletico', 'Athletic', 'Athlétique', 'Atletyczny')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 8. INSERT INITIAL DATA - CLOSURE
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_closure (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Zip', 'Fermeture éclair', 'Reißverschluss', 'Cremallera', 'Cerniera', 'Rits', 'Fermeture éclair', 'Zamek błyskawiczny'),
        ('Button', 'Bouton', 'Knopf', 'Botón', 'Bottone', 'Knoop', 'Bouton', 'Guzik'),
        ('Buckle', 'Boucle', 'Schnalle', 'Hebilla', 'Fibbia', 'Gesp', 'Boucle', 'Klamra'),
        ('Hook & Eye', 'Agrafe', 'Haken & Öse', 'Corchete', 'Gancio', 'Haak en oog', 'Agrafe', 'Haczyk'),
        ('Drawstring', 'Cordon', 'Kordelzug', 'Cordón', 'Coulisse', 'Trekkoord', 'Cordon', 'Sznurek'),
        ('Velcro', 'Velcro', 'Klett', 'Velcro', 'Velcro', 'Klittenband', 'Velcro', 'Rzep'),
        ('Pull On', 'Enfiler', 'Schlupf', 'Sin cierre', 'Senza chiusura', 'Geen', 'Enfiler', 'Bez zapięcia'),
        ('Snap', 'Pression', 'Druckknopf', 'Corchete', 'Bottone a pressione', 'Drukknoop', 'Pression', 'Zatrzask')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 9. INSERT INITIAL DATA - SIZE (basic)
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_size (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('XS', 'XS', 'XS', 'XS', 'XS', 'XS', 'XS', 'XS'),
        ('S', 'S', 'S', 'S', 'S', 'S', 'S', 'S'),
        ('M', 'M', 'M', 'M', 'M', 'M', 'M', 'M'),
        ('L', 'L', 'L', 'L', 'L', 'L', 'L', 'L'),
        ('XL', 'XL', 'XL', 'XL', 'XL', 'XL', 'XL', 'XL'),
        ('XXL', 'XXL', 'XXL', 'XXL', 'XXL', 'XXL', 'XXL', 'XXL'),
        ('One Size', 'Taille unique', 'Einheitsgröße', 'Talla única', 'Taglia unica', 'One size', 'Taille unique', 'Jeden rozmiar')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 10. INSERT INITIAL DATA - STYLE
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_style (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Casual', 'Décontracté', 'Casual', 'Casual', 'Casual', 'Casual', 'Décontracté', 'Casualowy'),
        ('Formal', 'Habillé', 'Formal', 'Formal', 'Formale', 'Formeel', 'Habillé', 'Formalny'),
        ('Sporty', 'Sportif', 'Sportlich', 'Deportivo', 'Sportivo', 'Sportief', 'Sportif', 'Sportowy'),
        ('Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage', 'Vintage'),
        ('Streetwear', 'Streetwear', 'Streetwear', 'Streetwear', 'Streetwear', 'Streetwear', 'Streetwear', 'Streetwear'),
        ('Basic', 'Basique', 'Basic', 'Básico', 'Basic', 'Basic', 'Basique', 'Podstawowy'),
        ('Designer', 'Designer', 'Designer', 'Diseñador', 'Designer', 'Designer', 'Designer', 'Designerski')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 11. INSERT INITIAL DATA - TYPE (product type)
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_type (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Jeans', 'Jean', 'Jeans', 'Vaqueros', 'Jeans', 'Jeans', 'Jean', 'Dżinsy'),
        ('T-Shirt', 'T-shirt', 'T-Shirt', 'Camiseta', 'T-shirt', 'T-shirt', 'T-shirt', 'T-shirt'),
        ('Shirt', 'Chemise', 'Hemd', 'Camisa', 'Camicia', 'Overhemd', 'Chemise', 'Koszula'),
        ('Jacket', 'Veste', 'Jacke', 'Chaqueta', 'Giacca', 'Jas', 'Veste', 'Kurtka'),
        ('Coat', 'Manteau', 'Mantel', 'Abrigo', 'Cappotto', 'Jas', 'Manteau', 'Płaszcz'),
        ('Dress', 'Robe', 'Kleid', 'Vestido', 'Vestito', 'Jurk', 'Robe', 'Sukienka'),
        ('Skirt', 'Jupe', 'Rock', 'Falda', 'Gonna', 'Rok', 'Jupe', 'Spódnica'),
        ('Trousers', 'Pantalon', 'Hose', 'Pantalón', 'Pantaloni', 'Broek', 'Pantalon', 'Spodnie'),
        ('Shorts', 'Short', 'Shorts', 'Pantalón corto', 'Pantaloncini', 'Korte broek', 'Short', 'Szorty'),
        ('Sweater', 'Pull', 'Pullover', 'Jersey', 'Maglione', 'Trui', 'Pull', 'Sweter'),
        ('Hoodie', 'Sweat à capuche', 'Kapuzenpullover', 'Sudadera con capucha', 'Felpa con cappuccio', 'Hoodie', 'Sweat à capuche', 'Bluza z kapturem'),
        ('Blazer', 'Blazer', 'Blazer', 'Blazer', 'Blazer', 'Blazer', 'Blazer', 'Marynarka'),
        ('Polo', 'Polo', 'Poloshirt', 'Polo', 'Polo', 'Poloshirt', 'Polo', 'Polo')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 12. INSERT INITIAL DATA - RISE
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_rise (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Low', 'Taille basse', 'Niedrig', 'Tiro bajo', 'Bassa', 'Laag', 'Taille basse', 'Niski'),
        ('Mid', 'Taille moyenne', 'Mittel', 'Tiro medio', 'Media', 'Midden', 'Taille moyenne', 'Średni'),
        ('High', 'Taille haute', 'Hoch', 'Tiro alto', 'Alta', 'Hoog', 'Taille haute', 'Wysoki')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 13. INSERT INITIAL DATA - NECKLINE
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_neckline (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Crew Neck', 'Col rond', 'Rundhals', 'Cuello redondo', 'Girocollo', 'Ronde hals', 'Col rond', 'Okrągły'),
        ('V-Neck', 'Col en V', 'V-Ausschnitt', 'Cuello en V', 'Scollo a V', 'V-hals', 'Col en V', 'Dekolt w serek'),
        ('Collared', 'Col', 'Kragen', 'Con cuello', 'Con colletto', 'Kraag', 'Col', 'Z kołnierzem'),
        ('Hooded', 'À capuche', 'Mit Kapuze', 'Con capucha', 'Con cappuccio', 'Met capuchon', 'À capuche', 'Z kapturem'),
        ('Polo', 'Col polo', 'Polokragen', 'Cuello polo', 'Collo polo', 'Polokraag', 'Col polo', 'Polo'),
        ('Turtleneck', 'Col roulé', 'Rollkragen', 'Cuello alto', 'Collo alto', 'Coltrui', 'Col roulé', 'Golf'),
        ('Scoop Neck', 'Col dégagé', 'Rundausschnitt', 'Cuello redondo', 'Scollo tondo', 'Ronde hals', 'Col dégagé', 'Okrągły')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 14. INSERT INITIAL DATA - SLEEVE LENGTH
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_sleeve_length (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Short Sleeve', 'Manches courtes', 'Kurzarm', 'Manga corta', 'Manica corta', 'Korte mouw', 'Manches courtes', 'Krótki rękaw'),
        ('Long Sleeve', 'Manches longues', 'Langarm', 'Manga larga', 'Manica lunga', 'Lange mouw', 'Manches longues', 'Długi rękaw'),
        ('3/4 Sleeve', 'Manches 3/4', '3/4-Arm', 'Manga 3/4', 'Manica 3/4', '3/4 mouw', 'Manches 3/4', 'Rękaw 3/4'),
        ('Sleeveless', 'Sans manches', 'Ärmellos', 'Sin mangas', 'Senza maniche', 'Mouwloos', 'Sans manches', 'Bez rękawów')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 15. INSERT INITIAL DATA - OCCASION
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_occasion (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Casual', 'Décontracté', 'Freizeit', 'Casual', 'Casual', 'Casual', 'Décontracté', 'Codzienny'),
        ('Formal', 'Formel', 'Formell', 'Formal', 'Formale', 'Formeel', 'Formel', 'Formalny'),
        ('Party', 'Soirée', 'Party', 'Fiesta', 'Festa', 'Feest', 'Soirée', 'Imprezowy'),
        ('Sport', 'Sport', 'Sport', 'Deporte', 'Sport', 'Sport', 'Sport', 'Sportowy'),
        ('Work', 'Travail', 'Arbeit', 'Trabajo', 'Lavoro', 'Werk', 'Travail', 'Do pracy'),
        ('Holiday', 'Vacances', 'Urlaub', 'Vacaciones', 'Vacanza', 'Vakantie', 'Vacances', 'Wakacyjny')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 16. INSERT INITIAL DATA - PATTERN
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_pattern (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Solid', 'Uni', 'Uni', 'Liso', 'Tinta unita', 'Effen', 'Uni', 'Jednolity'),
        ('Striped', 'Rayé', 'Gestreift', 'Rayas', 'Righe', 'Gestreept', 'Rayé', 'W paski'),
        ('Checked', 'À carreaux', 'Kariert', 'Cuadros', 'A quadri', 'Geruit', 'À carreaux', 'W kratę'),
        ('Floral', 'Fleuri', 'Geblümt', 'Floral', 'Floreale', 'Bloemen', 'Fleuri', 'W kwiaty'),
        ('Animal Print', 'Imprimé animal', 'Tiermuster', 'Estampado animal', 'Animalier', 'Dierenprint', 'Imprimé animal', 'Zwierzęcy'),
        ('Camouflage', 'Camouflage', 'Camouflage', 'Camuflaje', 'Mimetico', 'Camouflage', 'Camouflage', 'Moro'),
        ('Paisley', 'Paisley', 'Paisley', 'Cachemir', 'Paisley', 'Paisley', 'Paisley', 'Paisley'),
        ('Polka Dot', 'À pois', 'Gepunktet', 'Lunares', 'A pois', 'Stippen', 'À pois', 'W groszki'),
        ('Graphic', 'Graphique', 'Grafik', 'Gráfico', 'Grafico', 'Grafisch', 'Graphique', 'Graficzny'),
        ('Logo', 'Logo', 'Logo', 'Logotipo', 'Logo', 'Logo', 'Logo', 'Logo')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)

    # ========================================
    # 17. INSERT INITIAL DATA - FEATURES
    # ========================================
    op.execute("""
        INSERT INTO ebay.aspect_features (ebay_gb, ebay_fr, ebay_de, ebay_es, ebay_it, ebay_nl, ebay_be, ebay_pl) VALUES
        ('Pockets', 'Poches', 'Taschen', 'Bolsillos', 'Tasche', 'Zakken', 'Poches', 'Kieszenie'),
        ('Stretch', 'Stretch', 'Stretch', 'Elástico', 'Elasticizzato', 'Stretch', 'Stretch', 'Rozciągliwy'),
        ('Lined', 'Doublé', 'Gefüttert', 'Forrado', 'Foderato', 'Gevoerd', 'Doublé', 'Podszewka'),
        ('Hooded', 'Capuche', 'Kapuze', 'Capucha', 'Cappuccio', 'Capuchon', 'Capuche', 'Kaptur'),
        ('Machine Washable', 'Lavable en machine', 'Maschinenwaschbar', 'Lavable a máquina', 'Lavabile in lavatrice', 'Machine wasbaar', 'Lavable en machine', 'Nadaje się do prania w pralce'),
        ('Breathable', 'Respirant', 'Atmungsaktiv', 'Transpirable', 'Traspirante', 'Ademend', 'Respirant', 'Oddychający'),
        ('Waterproof', 'Imperméable', 'Wasserdicht', 'Impermeable', 'Impermeabile', 'Waterdicht', 'Imperméable', 'Wodoodporny'),
        ('Lightweight', 'Léger', 'Leicht', 'Ligero', 'Leggero', 'Lichtgewicht', 'Léger', 'Lekki')
        ON CONFLICT (ebay_gb) DO NOTHING
    """)


def downgrade() -> None:
    """Reverse the migration."""

    # 1. Drop aspect value tables
    for table_name in ASPECT_TABLES:
        op.drop_table(table_name, schema='ebay')

    # 2. Move tables back to public and restore original names
    op.execute("ALTER TABLE ebay.exchange_rate RENAME TO exchange_rate_config")
    op.execute("ALTER TABLE ebay.exchange_rate_config SET SCHEMA public")

    op.execute("ALTER TABLE ebay.category_mapping RENAME TO ebay_category_mapping")
    op.execute("ALTER TABLE ebay.ebay_category_mapping SET SCHEMA public")

    op.execute("ALTER TABLE ebay.aspect_name_mapping RENAME TO aspect_mappings")
    op.execute("ALTER TABLE ebay.aspect_mappings SET SCHEMA public")

    op.execute("ALTER TABLE ebay.marketplace_config SET SCHEMA public")

    # 3. Drop ebay schema
    op.execute("DROP SCHEMA IF EXISTS ebay CASCADE")
