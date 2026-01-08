"""populate_condition_sups_translations

Revision ID: d7e1b5c4f6a3
Revises: c6d0a4b3e5f2
Create Date: 2026-01-08 17:08:45.123456+01:00

Business Rules (2026-01-08):
- Add missing translations (DE, IT, ES, NL, PL) to condition_sups table
- FR translations already complete, not modified
- 38 condition supplements total
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'd7e1b5c4f6a3'
down_revision: Union[str, None] = 'c6d0a4b3e5f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Faded': ('Ausgeblichen', 'Sbiadito', 'Desteñido', 'Vervaagd', 'Wyblakły'),
    'Resewn': ('Neu genäht', 'Ricucito', 'Recosido', 'Opnieuw genaaid', 'Przeszyty'),
    'Stretched': ('Ausgeleiert', 'Sformato', 'Estirado', 'Uitgerekt', 'Rozciągnięty'),
    'Worn': ('Abgetragen', 'Usurato', 'Desgastado', 'Versleten', 'Zużyty'),
    'Damaged button': ('Beschädigter Knopf', 'Bottone danneggiato', 'Botón dañado', 'Beschadigde knoop', 'Uszkodzony guzik'),
    'Damaged patch': ('Beschädigter Aufnäher', 'Toppa danneggiata', 'Parche dañado', 'Beschadigde patch', 'Uszkodzona łata'),
    'Frayed hems': ('Ausgefranste Säume', 'Orli sfilacciati', 'Dobladillos deshilachados', 'Gerafelde zomen', 'Postrzępione brzegi'),
    'General wear': ('Allgemeine Abnutzung', 'Usura generale', 'Desgaste general', 'Algemene slijtage', 'Ogólne zużycie'),
    'Hem undone': ('Saum aufgegangen', 'Orlo scucito', 'Dobladillo descosido', 'Losgekomen zoom', 'Odpruty rąbek'),
    'Hemmed/shortened': ('Gesäumt/gekürzt', 'Orlo/accorciato', 'Dobladillo/acortado', 'Gezoomd/ingekort', 'Obszyte/skrócone'),
    'Knee wear': ('Knieabnutzung', 'Usura alle ginocchia', 'Desgaste en rodillas', 'Knieslijtage', 'Zużycie na kolanach'),
    'Light discoloration': ('Leichte Verfärbung', 'Leggero scolorimento', 'Ligera decoloración', 'Lichte verkleuring', 'Lekkie odbarwienie'),
    'Marked discoloration': ('Deutliche Verfärbung', 'Scolorimento marcato', 'Decoloración marcada', 'Duidelijke verkleuring', 'Wyraźne odbarwienie'),
    'Missing button': ('Fehlender Knopf', 'Bottone mancante', 'Botón faltante', 'Ontbrekende knoop', 'Brakujący guzik'),
    'Missing patch': ('Fehlender Aufnäher', 'Toppa mancante', 'Parche faltante', 'Ontbrekende patch', 'Brakująca łata'),
    'Multiple holes': ('Mehrere Löcher', 'Diversi buchi', 'Varios agujeros', 'Meerdere gaten', 'Wiele dziur'),
    'Multiple stains': ('Mehrere Flecken', 'Diverse macchie', 'Varias manchas', 'Meerdere vlekken', 'Wiele plam'),
    'Pilling': ('Pilling', 'Pilling', 'Bolitas', 'Pilling', 'Mechacenie'),
    'Seam to fix': ('Naht zu reparieren', 'Cucitura da riparare', 'Costura a reparar', 'Naad te repareren', 'Szew do naprawy'),
    'Single stain': ('Einzelner Fleck', 'Macchia singola', 'Mancha única', 'Enkele vlek', 'Pojedyncza plama'),
    'Small hole': ('Kleines Loch', 'Piccolo buco', 'Pequeño agujero', 'Klein gaatje', 'Mała dziura'),
    'Snag': ('Ziehfaden', 'Smagliatura', 'Enganchón', 'Haakje', 'Zaciągnięcie'),
    'Tapered': ('Verjüngt', 'Rastremato', 'Estrechado', 'Getailleerd', 'Zwężony'),
    'Torn': ('Gerissen', 'Strappato', 'Rasgado', 'Gescheurd', 'Rozdarty'),
    'Vintage patina': ('Vintage-Patina', 'Patina vintage', 'Pátina vintage', 'Vintage patina', 'Patyna vintage'),
    'Vintage wear': ('Vintage-Abnutzung', 'Usura vintage', 'Desgaste vintage', 'Vintage slijtage', 'Zużycie vintage'),
    'Waist altered': ('Taille geändert', 'Vita modificata', 'Cintura ajustada', 'Taille aangepast', 'Zmieniony pas'),
    'Zipper to replace': ('Reißverschluss zu ersetzen', 'Cerniera da sostituire', 'Cremallera a reemplazar', 'Rits te vervangen', 'Zamek do wymiany'),
    'New With Tags (NWT)': ('Neu mit Etikett (NWT)', 'Nuovo con cartellino (NWT)', 'Nuevo con etiquetas (NWT)', 'Nieuw met labels (NWT)', 'Nowy z metkami (NWT)'),
    'New Without Tags (NWOT)': ('Neu ohne Etikett (NWOT)', 'Nuovo senza cartellino (NWOT)', 'Nuevo sin etiquetas (NWOT)', 'Nieuw zonder labels (NWOT)', 'Nowy bez metek (NWOT)'),
    'Deadstock (NOS)': ('Deadstock (NOS)', 'Deadstock (NOS)', 'Stock antiguo nuevo (NOS)', 'Deadstock (NOS)', 'Deadstock (NOS)'),
    'Color bleeding': ('Farbübertragung', 'Sanguinamento colore', 'Sangrado de color', 'Kleurafgifte', 'Farbowanie'),
    'Sun fading': ('Sonnenverfärbung', 'Scolorimento solare', 'Decoloración solar', 'Zonverkleuring', 'Wyblakłe od słońca'),
    'Moth holes': ('Mottenlöcher', 'Buchi di tarme', 'Agujeros de polilla', 'Motgaatjes', 'Dziury od moli'),
    'Odor': ('Geruch', 'Odore', 'Olor', 'Geur', 'Zapach'),
    'Elastic worn': ('Gummi ausgeleiert', 'Elastico usurato', 'Elástico gastado', 'Elastiek versleten', 'Zużyta guma'),
    'Lining damaged': ('Futter beschädigt', 'Fodera danneggiata', 'Forro dañado', 'Voering beschadigd', 'Uszkodzona podszewka'),
}


def upgrade() -> None:
    """Add missing translations (DE, IT, ES, NL, PL) to condition_sups."""
    conn = op.get_bind()

    for name_en, (name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.condition_sups
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
    """Remove translations (DE, IT, ES, NL, PL) from condition_sups."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.condition_sups
                SET name_de = NULL,
                    name_it = NULL,
                    name_es = NULL,
                    name_nl = NULL,
                    name_pl = NULL
                WHERE name_en = :name_en
            """),
            {'name_en': name_en}
        )
