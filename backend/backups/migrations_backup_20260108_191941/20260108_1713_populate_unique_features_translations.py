"""populate_unique_features_translations

Revision ID: f9g3d7e6b8c5
Revises: e8f2c6d5a7b4
Create Date: 2026-01-08 17:13:12.123456+01:00

Business Rules (2026-01-08):
- Add/update translations (FR, DE, IT, ES, NL, PL) to unique_features table
- 65 unique features total
- Some FR translations were missing, now completed
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'f9g3d7e6b8c5'
down_revision: Union[str, None] = 'e8f2c6d5a7b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Translation data: name_en -> (name_fr, name_de, name_it, name_es, name_nl, name_pl)
TRANSLATIONS = {
    'Cutouts': ('Découpes', 'Cutouts', 'Tagli', 'Aberturas', 'Cutouts', 'Wycięcia'),
    'Fringe': ('Franges', 'Fransen', 'Frange', 'Flecos', 'Franjes', 'Frędzle'),
    'Tiered': ('Volants superposés', 'Gestuft', 'A balze', 'Escalonado', 'Gelaagd', 'Warstwowy'),
    'Distressed': ('Vieilli', 'Distressed', 'Effetto vissuto', 'Desgastado', 'Distressed', 'Postarzany'),
    'Acid wash': ('Délavage acide', 'Acid Wash', 'Lavaggio acido', 'Lavado ácido', 'Acid wash', 'Sprany kwasem'),
    'Appliqué': ('Appliqué', 'Applikation', 'Applicazione', 'Aplique', 'Applicatie', 'Aplikacja'),
    'Bar tacks': ('Points d\'arrêt', 'Riegelstiche', 'Punti di rinforzo', 'Presillas', 'Bartacks', 'Rygle'),
    'Beaded': ('Perlé', 'Perlenbesetzt', 'Con perline', 'Con cuentas', 'Met kralen', 'Zdobiony koralikami'),
    'Belt loops': ('Passants de ceinture', 'Gürtelschlaufen', 'Passanti', 'Trabillas', 'Riemlussen', 'Szlufki'),
    'Bleached': ('Blanchi', 'Gebleicht', 'Sbiancato', 'Blanqueado', 'Gebleekt', 'Wybielany'),
    'Brass rivets': ('Rivets en laiton', 'Messingnieten', 'Rivetti in ottone', 'Remaches de latón', 'Messing klinknagels', 'Nity mosiężne'),
    'Button detail': ('Détail boutons', 'Knopfdetail', 'Dettaglio bottoni', 'Detalle de botones', 'Knoopdetail', 'Detal guzikowy'),
    'Chain detail': ('Détail chaîne', 'Kettendetail', 'Dettaglio catena', 'Detalle de cadena', 'Kettingdetail', 'Detal łańcuszkowy'),
    'Chain stitching': ('Couture chaînette', 'Kettenstich', 'Cucitura a catenella', 'Puntada de cadena', 'Kettingsteek', 'Ścieg łańcuszkowy'),
    'Coin pocket': ('Poche à monnaie', 'Münztasche', 'Taschino portamonete', 'Bolsillo monedero', 'Muntzakje', 'Kieszonka na monety'),
    'Contrast stitching': ('Surpiqûres contrastées', 'Kontrastnähte', 'Cuciture a contrasto', 'Costuras en contraste', 'Contrasterende stiksels', 'Kontrastowe przeszycia'),
    'Copper rivets': ('Rivets en cuivre', 'Kupfernieten', 'Rivetti in rame', 'Remaches de cobre', 'Koperen klinknagels', 'Nity miedziane'),
    'Cuffed': ('Revers', 'Mit Umschlag', 'Con risvolto', 'Con dobladillo', 'Met omslag', 'Z mankietem'),
    'Custom design': ('Design personnalisé', 'Individuelles Design', 'Design personalizzato', 'Diseño personalizado', 'Custom design', 'Własny design'),
    'Darted': ('Pinces', 'Mit Abnähern', 'Con pince', 'Con pinzas', 'Met figuurnaad', 'Z zaszewkami'),
    'Deadstock fabric': ('Tissu deadstock', 'Deadstock-Stoff', 'Tessuto deadstock', 'Tejido deadstock', 'Deadstock stof', 'Tkanina deadstock'),
    'Decorative pockets': ('Poches décoratives', 'Ziertaschen', 'Tasche decorative', 'Bolsillos decorativos', 'Decoratieve zakken', 'Kieszenie dekoracyjne'),
    'Double stitch': ('Double couture', 'Doppelnaht', 'Doppia cucitura', 'Doble puntada', 'Dubbele steek', 'Podwójny szew'),
    'Embossed buttons': ('Boutons embossés', 'Geprägte Knöpfe', 'Bottoni in rilievo', 'Botones en relieve', 'Reliëfknopen', 'Guziki tłoczone'),
    'Embroidered': ('Brodé', 'Bestickt', 'Ricamato', 'Bordado', 'Geborduurd', 'Haftowany'),
    'Fading': ('Délavage', 'Verblassung', 'Sbiadito', 'Desvanecido', 'Vervaagd', 'Sprane'),
    'Flat felled seams': ('Coutures rabattues', 'Kappnähte', 'Cuciture ribattute', 'Costuras planas', 'Platte naden', 'Szwy płaskie'),
    'Frayed': ('Effiloché', 'Ausgefranst', 'Sfilacciato', 'Deshilachado', 'Gerafeld', 'Postrzępiony'),
    'Garment dyed': ('Teinture pièce', 'Stückgefärbt', 'Tinto in capo', 'Teñido en prenda', 'Garment dyed', 'Barwiony po uszyciu'),
    'Gradient': ('Dégradé', 'Farbverlauf', 'Sfumato', 'Degradado', 'Verloop', 'Gradient'),
    'Hand embroidered': ('Brodé main', 'Handbestickt', 'Ricamato a mano', 'Bordado a mano', 'Handgeborduurd', 'Haftowany ręcznie'),
    'Hand painted': ('Peint main', 'Handbemalt', 'Dipinto a mano', 'Pintado a mano', 'Handgeschilderd', 'Malowany ręcznie'),
    'Hidden rivets': ('Rivets cachés', 'Verdeckte Nieten', 'Rivetti nascosti', 'Remaches ocultos', 'Verborgen klinknagels', 'Ukryte nity'),
    'Jacron patch': ('Patch Jacron', 'Jacron-Patch', 'Patch Jacron', 'Parche Jacron', 'Jacron patch', 'Naszywka Jacron'),
    'Lace detail': ('Détail dentelle', 'Spitzendetail', 'Dettaglio pizzo', 'Detalle de encaje', 'Kantdetail', 'Detal koronkowy'),
    'Leather label': ('Étiquette cuir', 'Lederetikett', 'Etichetta in pelle', 'Etiqueta de cuero', 'Leren label', 'Skórzana metka'),
    'Leather patch': ('Patch cuir', 'Lederpatch', 'Patch in pelle', 'Parche de cuero', 'Leren patch', 'Skórzana łata'),
    'Lined': ('Doublé', 'Gefüttert', 'Foderato', 'Forrado', 'Gevoerd', 'Podszewka'),
    'Original buttons': ('Boutons d\'origine', 'Originalknöpfe', 'Bottoni originali', 'Botones originales', 'Originele knopen', 'Oryginalne guziki'),
    'Padded': ('Rembourré', 'Gepolstert', 'Imbottito', 'Acolchado', 'Gewatteerd', 'Ocieplany'),
    'Painted': ('Peint', 'Bemalt', 'Dipinto', 'Pintado', 'Beschilderd', 'Malowany'),
    'Paneled': ('Panneaux', 'Mit Einsätzen', 'A pannelli', 'Con paneles', 'Met panelen', 'Panelowy'),
    'Paper patch': ('Patch papier', 'Papierpatch', 'Patch in carta', 'Parche de papel', 'Papieren patch', 'Papierowa naszywka'),
    'Patchwork': ('Patchwork', 'Patchwork', 'Patchwork', 'Patchwork', 'Patchwork', 'Patchwork'),
    'Pleated': ('Plissé', 'Plissiert', 'Plissettato', 'Plisado', 'Geplisseerd', 'Plisowany'),
    'Printed': ('Imprimé', 'Bedruckt', 'Stampato', 'Estampado', 'Bedrukt', 'Nadrukowany'),
    'Raw denim': ('Denim brut', 'Raw Denim', 'Denim grezzo', 'Denim crudo', 'Raw denim', 'Surowy denim'),
    'Raw hem': ('Ourlet brut', 'Offener Saum', 'Orlo grezzo', 'Dobladillo sin rematar', 'Onafgewerkte zoom', 'Surowy rąbek'),
    'Reinforced seams': ('Coutures renforcées', 'Verstärkte Nähte', 'Cuciture rinforzate', 'Costuras reforzadas', 'Versterkte naden', 'Wzmocnione szwy'),
    'Ripped': ('Déchiré', 'Zerrissen', 'Strappato', 'Rasgado', 'Gescheurd', 'Podarty'),
    'Rope dyed': ('Teinture corde', 'Rope Dyed', 'Tintura a corda', 'Teñido en cuerda', 'Rope dyed', 'Barwiony na linie'),
    'Sanforized': ('Sanforisé', 'Sanforisiert', 'Sanforizzato', 'Sanforizado', 'Gesanforiseerd', 'Sanforyzowany'),
    'Selvedge': ('Selvedge', 'Selvedge', 'Cimosa', 'Selvedge', 'Selvedge', 'Selvedge'),
    'Sequined': ('À sequins', 'Mit Pailletten', 'Con paillettes', 'Con lentejuelas', 'Met pailletten', 'Z cekinami'),
    'Shuttle loom': ('Métier navette', 'Schiffchenwebstuhl', 'Telaio a navetta', 'Telar de lanzadera', 'Schietspoel weefgetouw', 'Krosno czółenkowe'),
    'Single stitch': ('Simple couture', 'Einzelnaht', 'Cucitura singola', 'Puntada simple', 'Enkele steek', 'Pojedynczy szew'),
    'Stone washed': ('Stone washed', 'Stone Washed', 'Stone washed', 'Lavado a la piedra', 'Stone washed', 'Prany z kamieniami'),
    'Studded': ('Clouté', 'Mit Nieten', 'Borchiato', 'Con tachuelas', 'Met studs', 'Ćwiekowany'),
    'Triple stitch': ('Triple couture', 'Dreifachnaht', 'Tripla cucitura', 'Triple puntada', 'Drievoudige steek', 'Potrójny szew'),
    'Unsanforized': ('Non sanforisé', 'Unsanforisiert', 'Non sanforizzato', 'Sin sanforizar', 'Ongesanforiseerd', 'Niesanforyzowany'),
    'Vintage hardware': ('Quincaillerie vintage', 'Vintage-Beschläge', 'Ferramenta vintage', 'Herrajes vintage', 'Vintage hardware', 'Vintage okucia'),
    'Vintage wash': ('Lavage vintage', 'Vintage Wash', 'Lavaggio vintage', 'Lavado vintage', 'Vintage wash', 'Pranie vintage'),
    'Whiskering': ('Moustaches', 'Whiskers', 'Baffature', 'Bigotes', 'Whiskering', 'Wąsy'),
    'Woven label': ('Étiquette tissée', 'Gewebtes Etikett', 'Etichetta tessuta', 'Etiqueta tejida', 'Geweven label', 'Tkana metka'),
    'Zipper detail': ('Détail fermeture', 'Reißverschlussdetail', 'Dettaglio cerniera', 'Detalle de cremallera', 'Ritsdetail', 'Detal zamkowy'),
}


def upgrade() -> None:
    """Add/update translations (FR, DE, IT, ES, NL, PL) to unique_features."""
    conn = op.get_bind()

    for name_en, (name_fr, name_de, name_it, name_es, name_nl, name_pl) in TRANSLATIONS.items():
        conn.execute(
            text("""
                UPDATE product_attributes.unique_features
                SET name_fr = :name_fr,
                    name_de = :name_de,
                    name_it = :name_it,
                    name_es = :name_es,
                    name_nl = :name_nl,
                    name_pl = :name_pl
                WHERE name_en = :name_en
            """),
            {
                'name_en': name_en,
                'name_fr': name_fr,
                'name_de': name_de,
                'name_it': name_it,
                'name_es': name_es,
                'name_nl': name_nl,
                'name_pl': name_pl,
            }
        )


def downgrade() -> None:
    """Remove translations (FR, DE, IT, ES, NL, PL) from unique_features."""
    conn = op.get_bind()

    for name_en in TRANSLATIONS.keys():
        conn.execute(
            text("""
                UPDATE product_attributes.unique_features
                SET name_fr = NULL,
                    name_de = NULL,
                    name_it = NULL,
                    name_es = NULL,
                    name_nl = NULL,
                    name_pl = NULL
                WHERE name_en = :name_en
            """),
            {'name_en': name_en}
        )
