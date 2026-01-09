"""populate_colors_translations

Revision ID: 93a8fb1b3d42
Revises: 22bb182e5129
Create Date: 2026-01-08 17:02:42.123456+01:00

Business Rules (2026-01-08):
- Add/update translations (DE, IT, ES, NL, PL) to colors table
- FR translations kept as-is (already complete at 97%)
- 66 colors total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '93a8fb1b3d42'
down_revision: Union[str, None] = '22bb182e5129'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Klein blue': ('Klein-Blau', 'Blu Klein', 'Azul Klein', 'Klein blauw', 'Błękit Klein'),
    'Vanilla yellow': ('Vanillegelb', 'Giallo vaniglia', 'Amarillo vainilla', 'Vanillegeel', 'Waniliowy'),
    'Charcoal': ('Anthrazit', 'Antracite', 'Gris marengo', 'Antraciet', 'Antracytowy'),
    'Silver': ('Silber', 'Argento', 'Plata', 'Zilver', 'Srebrny'),
    'Tan': ('Hellbraun', 'Cuoio', 'Bronceado', 'Lichtbruin', 'Jasnobrązowy'),
    'Camel': ('Camel', 'Cammello', 'Camello', 'Camel', 'Camelowy'),
    'Cognac': ('Cognac', 'Cognac', 'Coñac', 'Cognac', 'Koniakowy'),
    'Burgundy': ('Burgund', 'Borgogna', 'Burdeos', 'Bordeaux', 'Bordowy'),
    'Coral': ('Koralle', 'Corallo', 'Coral', 'Koraal', 'Koralowy'),
    'Mustard': ('Senfgelb', 'Senape', 'Mostaza', 'Mosterd', 'Musztardowy'),
    'Gold': ('Gold', 'Oro', 'Dorado', 'Goud', 'Złoty'),
    'Olive': ('Oliv', 'Verde oliva', 'Oliva', 'Olijfgroen', 'Oliwkowy'),
    'Khaki': ('Khaki', 'Kaki', 'Caqui', 'Kaki', 'Khaki'),
    'Mint': ('Mint', 'Menta', 'Menta', 'Mint', 'Miętowy'),
    'Navy': ('Marineblau', 'Blu navy', 'Azul marino', 'Marineblauw', 'Granatowy'),
    'Light-blue': ('Hellblau', 'Azzurro', 'Azul claro', 'Lichtblauw', 'Jasnoniebieski'),
    'Teal': ('Petrol', 'Verde petrolio', 'Verde azulado', 'Teal', 'Morski'),
    'Turquoise': ('Türkis', 'Turchese', 'Turquesa', 'Turquoise', 'Turkusowy'),
    'Lavender': ('Lavendel', 'Lavanda', 'Lavanda', 'Lavendel', 'Lawendowy'),
    'Fuchsia': ('Fuchsia', 'Fucsia', 'Fucsia', 'Fuchsia', 'Fuksjowy'),
    'Metallic': ('Metallic', 'Metallizzato', 'Metálico', 'Metallic', 'Metaliczny'),
    'Beige': ('Beige', 'Beige', 'Beige', 'Beige', 'Beżowy'),
    'Black': ('Schwarz', 'Nero', 'Negro', 'Zwart', 'Czarny'),
    'Blue': ('Blau', 'Blu', 'Azul', 'Blauw', 'Niebieski'),
    'Brown': ('Braun', 'Marrone', 'Marrón', 'Bruin', 'Brązowy'),
    'Cream': ('Creme', 'Crema', 'Crema', 'Crème', 'Kremowy'),
    'Gray': ('Grau', 'Grigio', 'Gris', 'Grijs', 'Szary'),
    'Green': ('Grün', 'Verde', 'Verde', 'Groen', 'Zielony'),
    'Multicolor': ('Mehrfarbig', 'Multicolore', 'Multicolor', 'Meerkleurig', 'Wielokolorowy'),
    'Orange': ('Orange', 'Arancione', 'Naranja', 'Oranje', 'Pomarańczowy'),
    'Pink': ('Rosa', 'Rosa', 'Rosa', 'Roze', 'Różowy'),
    'Purple': ('Lila', 'Viola', 'Morado', 'Paars', 'Fioletowy'),
    'Red': ('Rot', 'Rosso', 'Rojo', 'Rood', 'Czerwony'),
    'White': ('Weiß', 'Bianco', 'Blanco', 'Wit', 'Biały'),
    'Yellow': ('Gelb', 'Giallo', 'Amarillo', 'Geel', 'Żółty'),
    'Off-white': ('Offwhite', 'Bianco sporco', 'Blanco roto', 'Gebroken wit', 'Złamana biel'),
    'Ivory': ('Elfenbein', 'Avorio', 'Marfil', 'Ivoorwit', 'Kość słoniowa'),
    'Sand': ('Sand', 'Sabbia', 'Arena', 'Zand', 'Piaskowy'),
    'Nude': ('Nude', 'Nude', 'Nude', 'Nude', 'Nude'),
    'Slate': ('Schiefergrau', 'Ardesia', 'Pizarra', 'Leisteen', 'Łupkowy'),
    'Taupe': ('Taupe', 'Tortora', 'Topo', 'Taupe', 'Taupe'),
    'Mocha': ('Mokka', 'Moka', 'Moca', 'Mokka', 'Mokka'),
    'Chocolate': ('Schokobraun', 'Cioccolato', 'Chocolate', 'Chocolade', 'Czekoladowy'),
    'Espresso': ('Espresso', 'Espresso', 'Expreso', 'Espresso', 'Espresso'),
    'Cinnamon': ('Zimt', 'Cannella', 'Canela', 'Kaneel', 'Cynamonowy'),
    'Wine': ('Weinrot', 'Vinaccia', 'Vino', 'Wijnrood', 'Wino'),
    'Cherry red': ('Kirschrot', 'Rosso ciliegia', 'Rojo cereza', 'Kersenrood', 'Wiśniowy'),
    'Rust': ('Rostbraun', 'Ruggine', 'Óxido', 'Roest', 'Rdzawy'),
    'Terracotta': ('Terrakotta', 'Terracotta', 'Terracota', 'Terracotta', 'Terakota'),
    'Burnt orange': ('Gebranntes Orange', 'Arancione bruciato', 'Naranja quemado', 'Verbrand oranje', 'Spalona pomarańcz'),
    'Peach': ('Pfirsich', 'Pesca', 'Melocotón', 'Perzik', 'Brzoskwiniowy'),
    'Butter yellow': ('Buttergelb', 'Giallo burro', 'Amarillo mantequilla', 'Botergeel', 'Maślany'),
    'Sage': ('Salbei', 'Salvia', 'Salvia', 'Salie', 'Szałwiowy'),
    'Emerald': ('Smaragd', 'Smeraldo', 'Esmeralda', 'Smaragd', 'Szmaragdowy'),
    'Forest green': ('Waldgrün', 'Verde foresta', 'Verde bosque', 'Bosgroen', 'Leśna zieleń'),
    'Cobalt': ('Kobaltblau', 'Blu cobalto', 'Azul cobalto', 'Kobaltblauw', 'Kobaltowy'),
    'Powder blue': ('Puderblau', 'Blu polvere', 'Azul empolvado', 'Poederblauw', 'Pudrowy błękit'),
    'Lilac': ('Flieder', 'Lilla', 'Lila', 'Lila', 'Liliowy'),
    'Plum': ('Pflaume', 'Prugna', 'Ciruela', 'Pruim', 'Śliwkowy'),
    'Eggplant': ('Aubergine', 'Melanzana', 'Berenjena', 'Aubergine', 'Bakłażanowy'),
    'Mauve': ('Malve', 'Malva', 'Malva', 'Mauve', 'Różowofioletowy'),
    'Blush': ('Altrosa', 'Rosa cipria', 'Rosa empolvado', 'Blush', 'Pudrowy róż'),
    'Dusty pink': ('Altrosa', 'Rosa antico', 'Rosa empolvado', 'Oudroze', 'Brudny róż'),
    'Hot pink': ('Pink', 'Rosa acceso', 'Rosa intenso', 'Felroze', 'Intensywny róż'),
    'Rose gold': ('Roségold', 'Oro rosa', 'Oro rosa', 'Roségoud', 'Różowe złoto'),
    'Bronze': ('Bronze', 'Bronzo', 'Bronce', 'Brons', 'Brązowy'),
}


def upgrade() -> None:
    """Add/update translations (DE, IT, ES, NL, PL) to colors."""
    conn = op.get_bind()

    for name_en, (name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.colors
                SET name_de = :name_de,
                    name_it = :name_it,
                    name_es = :name_es,
                    name_nl = :name_nl,
                    name_pl = :name_pl
                WHERE name_en = :name_en
            """),
            {
                'name_en': name_en,
                'name_de': name_de,
                'name_it': name_it,
                'name_es': name_es,
                'name_nl': name_nl,
                'name_pl': name_pl,
            }
        )


def downgrade() -> None:
    """Remove translations (DE, IT, ES, NL, PL) from colors."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.colors
                SET name_de = NULL,
                    name_it = NULL,
                    name_es = NULL,
                    name_nl = NULL,
                    name_pl = NULL
                WHERE name_en = :name_en
            """),
            {'name_en': name_en}
        )
