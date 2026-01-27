"""
eBay Description Translations.

Multilingual translations for eBay HTML descriptions.
Supports 7 languages: FR, EN, DE, IT, ES, NL, PL.

Ported from pythonApiWOO/services/ebay/ebay_description_multilang_service.py
"""

# Section labels, messages, and field names per language
TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        "header_subtitle": "Mode Seconde Main Premium",
        "characteristics": "Caractéristiques",
        "measurements_title": "Mesures & Taille",
        "label_size": "Taille étiquette",
        "estimated_size": "Taille estimée",
        "see_guide": "Voir le guide ci-dessous",
        "shipping_title": "Livraison & Retours",
        "shipping_text": (
            '<b>Expédition rapide</b> sous 1-2 jours | '
            'Depuis France | <b>Retours 30 jours</b>'
        ),
        "footer_text": "Mode seconde main éco-responsable | Vendeur professionnel",
        "brand": "Marque",
        "model": "Modèle",
        "fit": "Coupe",
        "style": "Style",
        "color": "Couleur",
        "material": "Matière",
        "condition": "État",
        "era": "Époque",
        "gender": "Genre",
        "trend": "Tendance",
        "unique_detail": "Détail unique",
        "vintage": "vintage",
        "years": "Années",
        "in_condition": "en {} état",
        "in_cut": "en coupe {}",
        "this": "Ce",
        "size": "taille",
        "in_material": "en {}",
    },
    "en": {
        "header_subtitle": "Premium Second Hand Fashion",
        "characteristics": "Characteristics",
        "measurements_title": "Measurements & Size",
        "label_size": "Label size",
        "estimated_size": "Estimated size",
        "see_guide": "See guide below",
        "shipping_title": "Shipping & Returns",
        "shipping_text": (
            '<b>Fast shipping</b> within 1-2 days | '
            'From France | <b>30-day returns</b>'
        ),
        "footer_text": "Sustainable second-hand fashion | Professional seller",
        "brand": "Brand",
        "model": "Model",
        "fit": "Fit",
        "style": "Style",
        "color": "Color",
        "material": "Material",
        "condition": "Condition",
        "era": "Era",
        "gender": "Gender",
        "trend": "Trend",
        "unique_detail": "Unique detail",
        "vintage": "vintage",
        "years": "",
        "in_condition": "in {} condition",
        "in_cut": "in {} fit",
        "this": "This",
        "size": "size",
        "in_material": "in {}",
    },
    "de": {
        "header_subtitle": "Premium Second-Hand-Mode",
        "characteristics": "Eigenschaften",
        "measurements_title": "Maße & Größe",
        "label_size": "Etikettengröße",
        "estimated_size": "Geschätzte Größe",
        "see_guide": "Siehe Anleitung unten",
        "shipping_title": "Versand & Rücksendungen",
        "shipping_text": (
            '<b>Schneller Versand</b> innerhalb von 1-2 Tagen | '
            'Aus Frankreich | <b>30-Tage-Rückgabe</b>'
        ),
        "footer_text": "Nachhaltige Secondhand-Mode | Professioneller Verkäufer",
        "brand": "Marke",
        "model": "Modell",
        "fit": "Schnitt",
        "style": "Stil",
        "color": "Farbe",
        "material": "Material",
        "condition": "Zustand",
        "era": "Epoche",
        "gender": "Geschlecht",
        "trend": "Trend",
        "unique_detail": "Einzigartiges Detail",
        "vintage": "Vintage",
        "years": "er Jahre",
        "in_condition": "in {} Zustand",
        "in_cut": "in {} Schnitt",
        "this": "Diese",
        "size": "Größe",
        "in_material": "aus {}",
    },
    "it": {
        "header_subtitle": "Moda Second Hand Premium",
        "characteristics": "Caratteristiche",
        "measurements_title": "Misure & Taglia",
        "label_size": "Taglia etichetta",
        "estimated_size": "Taglia stimata",
        "see_guide": "Vedi guida sotto",
        "shipping_title": "Spedizione & Resi",
        "shipping_text": (
            '<b>Spedizione rapida</b> entro 1-2 giorni | '
            'Dalla Francia | <b>Resi 30 giorni</b>'
        ),
        "footer_text": "Moda second hand sostenibile | Venditore professionale",
        "brand": "Marca",
        "model": "Modello",
        "fit": "Vestibilità",
        "style": "Stile",
        "color": "Colore",
        "material": "Materiale",
        "condition": "Condizione",
        "era": "Epoca",
        "gender": "Genere",
        "trend": "Tendenza",
        "unique_detail": "Dettaglio unico",
        "vintage": "vintage",
        "years": "Anni",
        "in_condition": "in {} condizione",
        "in_cut": "in {} vestibilità",
        "this": "Questo",
        "size": "taglia",
        "in_material": "in {}",
    },
    "es": {
        "header_subtitle": "Moda de Segunda Mano Premium",
        "characteristics": "Características",
        "measurements_title": "Medidas & Talla",
        "label_size": "Talla etiqueta",
        "estimated_size": "Talla estimada",
        "see_guide": "Ver guía abajo",
        "shipping_title": "Envío & Devoluciones",
        "shipping_text": (
            '<b>Envío rápido</b> en 1-2 días | '
            'Desde Francia | <b>Devoluciones 30 días</b>'
        ),
        "footer_text": "Moda sostenible de segunda mano | Vendedor profesional",
        "brand": "Marca",
        "model": "Modelo",
        "fit": "Corte",
        "style": "Estilo",
        "color": "Color",
        "material": "Material",
        "condition": "Estado",
        "era": "Época",
        "gender": "Género",
        "trend": "Tendencia",
        "unique_detail": "Detalle único",
        "vintage": "vintage",
        "years": "Años",
        "in_condition": "en {} estado",
        "in_cut": "en corte {}",
        "this": "Este",
        "size": "talla",
        "in_material": "en {}",
    },
    "nl": {
        "header_subtitle": "Premium Tweedehands Mode",
        "characteristics": "Kenmerken",
        "measurements_title": "Afmetingen & Maat",
        "label_size": "Label maat",
        "estimated_size": "Geschatte maat",
        "see_guide": "Zie gids hieronder",
        "shipping_title": "Verzending & Retour",
        "shipping_text": (
            '<b>Snelle verzending</b> binnen 1-2 dagen | '
            'Vanuit Frankrijk | <b>30 dagen retour</b>'
        ),
        "footer_text": "Duurzame tweedehands mode | Professionele verkoper",
        "brand": "Merk",
        "model": "Model",
        "fit": "Pasvorm",
        "style": "Stijl",
        "color": "Kleur",
        "material": "Materiaal",
        "condition": "Staat",
        "era": "Tijdperk",
        "gender": "Geslacht",
        "trend": "Trend",
        "unique_detail": "Uniek detail",
        "vintage": "vintage",
        "years": "jaren",
        "in_condition": "in {} staat",
        "in_cut": "in {} pasvorm",
        "this": "Deze",
        "size": "maat",
        "in_material": "in {}",
    },
    "pl": {
        "header_subtitle": "Moda Second Hand Premium",
        "characteristics": "Charakterystyka",
        "measurements_title": "Wymiary & Rozmiar",
        "label_size": "Rozmiar na metce",
        "estimated_size": "Rozmiar szacowany",
        "see_guide": "Zobacz przewodnik poniżej",
        "shipping_title": "Wysyłka & Zwroty",
        "shipping_text": (
            '<b>Szybka wysyłka</b> w ciągu 1-2 dni | '
            'Z Francji | <b>Zwroty 30 dni</b>'
        ),
        "footer_text": "Zrównoważona moda z drugiej ręki | Profesjonalny sprzedawca",
        "brand": "Marka",
        "model": "Model",
        "fit": "Krój",
        "style": "Styl",
        "color": "Kolor",
        "material": "Materiał",
        "condition": "Stan",
        "era": "Epoka",
        "gender": "Płeć",
        "trend": "Trend",
        "unique_detail": "Unikalny detal",
        "vintage": "vintage",
        "years": "lata",
        "in_condition": "w {} stanie",
        "in_cut": "w {} kroju",
        "this": "Ten",
        "size": "rozmiar",
        "in_material": "w {}",
    },
}


# Measurement labels per category type and language.
# Each entry is a list of (dim_attr, translated_label) tuples.
MEASUREMENT_LABELS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "jeans": {
        "fr": [
            ("dim1", "Tour de taille"), ("dim2", "Longueur totale"),
            ("dim3", "Largeur cuisse"), ("dim4", "Largeur cheville"),
            ("dim5", "Largeur genou"), ("dim6", "Entrejambe"),
        ],
        "en": [
            ("dim1", "Waist width"), ("dim2", "Total length"),
            ("dim3", "Thigh width"), ("dim4", "Ankle width"),
            ("dim5", "Knee width"), ("dim6", "Inseam"),
        ],
        "de": [
            ("dim1", "Taillenweite"), ("dim2", "Gesamtlänge"),
            ("dim3", "Oberschenkelweite"), ("dim4", "Knöchelweite"),
            ("dim5", "Knieweite"), ("dim6", "Innenbeinlänge"),
        ],
        "it": [
            ("dim1", "Larghezza vita"), ("dim2", "Lunghezza totale"),
            ("dim3", "Larghezza coscia"), ("dim4", "Larghezza caviglia"),
            ("dim5", "Larghezza ginocchio"), ("dim6", "Interno gamba"),
        ],
        "es": [
            ("dim1", "Ancho cintura"), ("dim2", "Largo total"),
            ("dim3", "Ancho muslo"), ("dim4", "Ancho tobillo"),
            ("dim5", "Ancho rodilla"), ("dim6", "Entrepierna"),
        ],
        "nl": [
            ("dim1", "Taillebreedte"), ("dim2", "Totale lengte"),
            ("dim3", "Dijbreedte"), ("dim4", "Enkelbreedte"),
            ("dim5", "Kniebreedte"), ("dim6", "Binnenbeenlengte"),
        ],
        "pl": [
            ("dim1", "Szerokość talii"), ("dim2", "Długość całkowita"),
            ("dim3", "Szerokość uda"), ("dim4", "Szerokość kostki"),
            ("dim5", "Szerokość kolana"), ("dim6", "Długość kroku"),
        ],
    },
    "shorts": {
        "fr": [
            ("dim1", "Tour de taille"), ("dim2", "Longueur totale"),
            ("dim3", "Largeur cuisse"), ("dim4", "Largeur bas"),
            ("dim5", "Entrejambe"),
        ],
        "en": [
            ("dim1", "Waist width"), ("dim2", "Total length"),
            ("dim3", "Thigh width"), ("dim4", "Leg opening"),
            ("dim5", "Inseam"),
        ],
        "de": [
            ("dim1", "Taillenweite"), ("dim2", "Gesamtlänge"),
            ("dim3", "Oberschenkelweite"), ("dim4", "Beinöffnung"),
            ("dim5", "Innenbeinlänge"),
        ],
        "it": [
            ("dim1", "Larghezza vita"), ("dim2", "Lunghezza totale"),
            ("dim3", "Larghezza coscia"), ("dim4", "Apertura gamba"),
            ("dim5", "Interno gamba"),
        ],
        "es": [
            ("dim1", "Ancho cintura"), ("dim2", "Largo total"),
            ("dim3", "Ancho muslo"), ("dim4", "Apertura pierna"),
            ("dim5", "Entrepierna"),
        ],
        "nl": [
            ("dim1", "Taillebreedte"), ("dim2", "Totale lengte"),
            ("dim3", "Dijbreedte"), ("dim4", "Beenopening"),
            ("dim5", "Binnenbeenlengte"),
        ],
        "pl": [
            ("dim1", "Szerokość talii"), ("dim2", "Długość całkowita"),
            ("dim3", "Szerokość uda"), ("dim4", "Szerokość nogawki"),
            ("dim5", "Długość kroku"),
        ],
    },
    "tops": {
        "fr": [
            ("dim1", "Largeur épaules"), ("dim2", "Longueur totale"),
            ("dim3", "Largeur aisselle"), ("dim4", "Longueur manche"),
        ],
        "en": [
            ("dim1", "Shoulder width"), ("dim2", "Total length"),
            ("dim3", "Armpit width"), ("dim4", "Sleeve length"),
        ],
        "de": [
            ("dim1", "Schulterbreite"), ("dim2", "Gesamtlänge"),
            ("dim3", "Achselbreite"), ("dim4", "Ärmellänge"),
        ],
        "it": [
            ("dim1", "Larghezza spalle"), ("dim2", "Lunghezza totale"),
            ("dim3", "Larghezza ascelle"), ("dim4", "Lunghezza manica"),
        ],
        "es": [
            ("dim1", "Ancho hombros"), ("dim2", "Largo total"),
            ("dim3", "Ancho axila"), ("dim4", "Largo manga"),
        ],
        "nl": [
            ("dim1", "Schouderbreedte"), ("dim2", "Totale lengte"),
            ("dim3", "Okselbreedte"), ("dim4", "Mouwlengte"),
        ],
        "pl": [
            ("dim1", "Szerokość ramion"), ("dim2", "Długość całkowita"),
            ("dim3", "Szerokość pod pachami"), ("dim4", "Długość rękawa"),
        ],
    },
}
