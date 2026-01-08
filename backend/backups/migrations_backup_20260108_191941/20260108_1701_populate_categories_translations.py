"""populate_categories_translations

Revision ID: 22bb182e5129
Revises: 3b9cddbe6380
Create Date: 2026-01-08 17:01:24.605551+01:00

Business Rules (2026-01-08):
- Add missing translations (DE, IT, ES, NL, PL) to categories table
- FR translations already complete, not modified
- 64 categories total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '22bb182e5129'
down_revision: Union[str, None] = '3b9cddbe6380'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'other': ('Sonstiges', 'Altro', 'Otro', 'Overig', 'Inne'),
    'body suit': ('Body', 'Body', 'Body', 'Body', 'Body'),
    'fleece jacket': ('Fleecejacke', 'Giacca in pile', 'Chaqueta polar', 'Fleecevest', 'Bluza polarowa'),
    'clothing': ('Kleidung', 'Abbigliamento', 'Ropa', 'Kleding', 'Odzież'),
    'tops': ('Oberteile', 'Top', 'Tops', 'Tops', 'Góry'),
    't-shirt': ('T-Shirt', 'T-shirt', 'Camiseta', 'T-shirt', 'T-shirt'),
    'tank-top': ('Tanktop', 'Canotta', 'Camiseta de tirantes', 'Tanktop', 'Top na ramiączkach'),
    'shirt': ('Hemd', 'Camicia', 'Camisa', 'Overhemd', 'Koszula'),
    'blouse': ('Bluse', 'Blusa', 'Blusa', 'Blouse', 'Bluzka'),
    'top': ('Top', 'Top', 'Top', 'Top', 'Top'),
    'corset': ('Korsett', 'Corsetto', 'Corsé', 'Korset', 'Gorset'),
    'bustier': ('Bustier', 'Bustier', 'Bustier', 'Bustier', 'Bustier'),
    'camisole': ('Unterhemd', 'Canottiera', 'Camisola', 'Hemdje', 'Koszulka na ramiączkach'),
    'crop-top': ('Crop-Top', 'Crop top', 'Crop top', 'Crop top', 'Crop top'),
    'polo': ('Polo', 'Polo', 'Polo', 'Polo', 'Polo'),
    'sweater': ('Pullover', 'Maglione', 'Jersey', 'Trui', 'Sweter'),
    'cardigan': ('Cardigan', 'Cardigan', 'Cárdigan', 'Vest', 'Kardigan'),
    'sweatshirt': ('Sweatshirt', 'Felpa', 'Sudadera', 'Sweater', 'Bluza'),
    'hoodie': ('Hoodie', 'Felpa con cappuccio', 'Sudadera con capucha', 'Hoodie', 'Bluza z kapturem'),
    'overshirt': ('Überhemd', 'Sovracamicia', 'Sobrecamisa', 'Overshirt', 'Koszula wierzchnia'),
    'bottoms': ('Unterteile', 'Pantaloni', 'Partes de abajo', 'Broeken', 'Doły'),
    'pants': ('Hose', 'Pantaloni', 'Pantalones', 'Broek', 'Spodnie'),
    'jeans': ('Jeans', 'Jeans', 'Vaqueros', 'Jeans', 'Jeansy'),
    'chinos': ('Chinos', 'Chinos', 'Chinos', 'Chino', 'Chinosy'),
    'joggers': ('Jogginghose', 'Pantaloni sportivi', 'Pantalones jogger', 'Joggingbroek', 'Spodnie dresowe'),
    'cargo-pants': ('Cargohose', 'Pantaloni cargo', 'Pantalones cargo', 'Cargobroek', 'Spodnie cargo'),
    'dress-pants': ('Stoffhose', 'Pantaloni eleganti', 'Pantalones de vestir', 'Nette broek', 'Spodnie wizytowe'),
    'shorts': ('Shorts', 'Shorts', 'Pantalones cortos', 'Shorts', 'Szorty'),
    'bermuda': ('Bermuda', 'Bermuda', 'Bermudas', 'Bermuda', 'Bermudy'),
    'skirt': ('Rock', 'Gonna', 'Falda', 'Rok', 'Spódnica'),
    'leggings': ('Leggings', 'Leggings', 'Leggings', 'Legging', 'Legginsy'),
    'culottes': ('Hosenrock', 'Gonna pantalone', 'Falda pantalón', 'Culotte', 'Spódnico-spodnie'),
    'outerwear': ('Oberbekleidung', 'Capispalla', 'Ropa de abrigo', 'Bovenkleding', 'Odzież wierzchnia'),
    'jacket': ('Jacke', 'Giacca', 'Chaqueta', 'Jas', 'Kurtka'),
    'bomber': ('Bomberjacke', 'Bomber', 'Bomber', 'Bomberjas', 'Bomber'),
    'puffer': ('Pufferjacke', 'Piumino', 'Abrigo acolchado', 'Pufferjack', 'Kurtka puchowa'),
    'coat': ('Mantel', 'Cappotto', 'Abrigo', 'Jas', 'Płaszcz'),
    'trench': ('Trenchcoat', 'Trench', 'Gabardina', 'Trenchcoat', 'Trencz'),
    'parka': ('Parka', 'Parka', 'Parka', 'Parka', 'Parka'),
    'raincoat': ('Regenmantel', 'Impermeabile', 'Impermeable', 'Regenjas', 'Płaszcz przeciwdeszczowy'),
    'windbreaker': ('Windbreaker', 'Giacca a vento', 'Cortavientos', 'Windbreaker', 'Wiatrówka'),
    'blazer': ('Blazer', 'Blazer', 'Blazer', 'Blazer', 'Blezer'),
    'vest': ('Weste', 'Gilet', 'Chaleco', 'Bodywarmer', 'Kamizelka'),
    'half-zip': ('Halfzip', 'Mezza zip', 'Media cremallera', 'Halfzip', 'Półzamek'),
    'cape': ('Cape', 'Mantella', 'Capa', 'Cape', 'Peleryna'),
    'poncho': ('Poncho', 'Poncho', 'Poncho', 'Poncho', 'Ponczo'),
    'kimono': ('Kimono', 'Kimono', 'Kimono', 'Kimono', 'Kimono'),
    'formalwear': ('Festliche Kleidung', 'Abbigliamento formale', 'Ropa formal', 'Formele kleding', 'Strój formalny'),
    'suit': ('Anzug', 'Abito', 'Traje', 'Pak', 'Garnitur'),
    'tuxedo': ('Smoking', 'Smoking', 'Esmoquin', 'Smoking', 'Smoking'),
    'sportswear': ('Sportbekleidung', 'Abbigliamento sportivo', 'Ropa deportiva', 'Sportkleding', 'Odzież sportowa'),
    'sports-bra': ('Sport-BH', 'Reggiseno sportivo', 'Sujetador deportivo', 'Sportbeha', 'Biustonosz sportowy'),
    'sports-top': ('Sport-Top', 'Top sportivo', 'Top deportivo', 'Sporttop', 'Top sportowy'),
    'sports-jersey': ('Sporttrikot', 'Maglia sportiva', 'Camiseta deportiva', 'Sportshirt', 'Koszulka sportowa'),
    'sports-shorts': ('Sporthose', 'Shorts sportivi', 'Pantalones cortos deportivos', 'Sportshorts', 'Spodenki sportowe'),
    'sports-leggings': ('Sportleggings', 'Leggings sportivi', 'Leggings deportivos', 'Sportlegging', 'Legginsy sportowe'),
    'bikini': ('Bikini', 'Bikini', 'Bikini', 'Bikini', 'Bikini'),
    'dress': ('Kleid', 'Vestito', 'Vestido', 'Jurk', 'Sukienka'),
    'romper': ('Playsuit', 'Tutina', 'Mono corto', 'Playsuit', 'Kombinezon krótki'),
    'overalls': ('Latzhose', 'Salopette', 'Peto', 'Tuinbroek', 'Ogrodniczki'),
    'swim suit': ('Badeanzug', 'Costume da bagno', 'Bañador', 'Badpak', 'Kostium kąpielowy'),
    'track suit': ('Trainingsanzug', 'Tuta', 'Chándal', 'Trainingspak', 'Dres'),
    'jump suit': ('Jumpsuit', 'Tuta intera', 'Mono', 'Jumpsuit', 'Kombinezon'),
    'waistcoat': ('Weste', 'Gilet', 'Chaleco de traje', 'Gilet', 'Kamizelka do garnituru'),
}


def upgrade() -> None:
    """Add missing translations (DE, IT, ES, NL, PL) to categories."""
    conn = op.get_bind()

    for name_en, (name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.categories
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
    """Remove translations (DE, IT, ES, NL, PL) from categories."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.categories
                SET name_de = NULL,
                    name_it = NULL,
                    name_es = NULL,
                    name_nl = NULL,
                    name_pl = NULL
                WHERE name_en = :name_en
            """),
            {'name_en': name_en}
        )
