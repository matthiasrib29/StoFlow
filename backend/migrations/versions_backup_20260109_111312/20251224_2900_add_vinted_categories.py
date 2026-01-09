"""add vinted categories

Revision ID: 20251224_2900
Revises: 20251224_2800
Create Date: 2025-12-24

Adds Vinted categories to vinted.categories table.
"""

from alembic import op
from sqlalchemy import text


# revision identifiers, used by Alembic
revision = "20251224_2900"
down_revision = "20251224_2800"
branch_labels = None
depends_on = None


# Categories data: (id, gender, title)
CATEGORIES = [
    (84, "men", "Maillots de bain"),
    (176, "women", "Autres robes"),
    (178, "women", "Mini"),
    (179, "women", "Robes en jean"),
    (184, "women", "Pantalons en cuir"),
    (185, "women", "Pantalons skinny"),
    (187, "women", "Pantalons ajustés"),
    (189, "women", "Autres pantalons"),
    (190, "women", "Pulls col V"),
    (191, "women", "Pulls col roulé"),
    (192, "women", "Sweats longs"),
    (194, "women", "Cardigans"),
    (195, "women", "Boléros"),
    (196, "women", "Sweats & sweats à capuche"),
    (197, "women", "Autres pull-overs & sweat-shirts"),
    (198, "women", "Minijupes"),
    (199, "women", "Jupes midi"),
    (200, "women", "Jupes longues"),
    (203, "women", "Shorts longueur genou"),
    (204, "women", "Pantacourts"),
    (205, "women", "Autres shorts"),
    (218, "women", "Une pièce"),
    (219, "women", "Deux pièces"),
    (221, "women", "T-shirts"),
    (222, "women", "Chemises"),
    (223, "women", "Blouses manches courtes"),
    (224, "women", "Blouses manches longues"),
    (225, "women", "Blouses ¾"),
    (227, "women", "Tuniques"),
    (228, "women", "Autres hauts"),
    (259, "men", "Pantalons skinny"),
    (260, "men", "Pantalons à jambes larges"),
    (261, "men", "Pantalons de costume"),
    (263, "men", "Autres pantalons"),
    (264, "men", "Sweats à col V"),
    (265, "men", "Pulls à col roulé"),
    (266, "men", "Cardigans"),
    (267, "men", "Pulls et pulls à capuche"),
    (268, "men", "Autres"),
    (271, "men", "Pantacourts"),
    (272, "men", "Autres shorts"),
    (525, "women", "Leggings"),
    (526, "women", "Sarouels"),
    (529, "women", "Pulls d'hiver"),
    (532, "women", "Blazers"),
    (534, "women", "Débardeurs"),
    (538, "women", "Short en jean"),
    (560, "men", "T-shirts sans manches"),
    (571, "women", "Vêtements d'extérieur"),
    (572, "women", "Survêtements"),
    (573, "women", "Pantalons & leggings"),
    (576, "women", "Hauts & t-shirts"),
    (577, "women", "Sweats et sweats à capuche"),
    (578, "women", "Shorts"),
    (581, "men", "Vêtements d'extérieur"),
    (582, "men", "Survêtements"),
    (583, "men", "Pantalons"),
    (584, "men", "Hauts et t-shirts"),
    (585, "men", "Pulls & sweats"),
    (586, "men", "Shorts"),
    (1041, "women", "Tops courts"),
    (1042, "women", "Tops épaules dénudées"),
    (1043, "women", "Blouses"),
    (1044, "women", "Tops dos nu"),
    (1045, "women", "Cols roulés"),
    (1055, "women", "Robes longues"),
    (1056, "women", "Midi"),
    (1057, "women", "Robes chics"),
    (1058, "women", "Petites robes noires"),
    (1059, "women", "Robes casual"),
    (1060, "women", "Robes dos nu"),
    (1061, "women", "Robes sans bretelles"),
    (1065, "women", "Robes d'été"),
    (1066, "women", "Autres sweats"),
    (1067, "women", "Kimonos"),
    (1070, "women", "Pantalons courts & chinos"),
    (1071, "women", "Pantalons à jambes larges"),
    (1076, "women", "Cabans"),
    (1078, "women", "Blousons aviateur"),
    (1079, "women", "Vestes en jean"),
    (1080, "women", "Imperméables"),
    (1086, "women", "Vestes polaires"),
    (1087, "women", "Parkas"),
    (1090, "women", "Manteaux en fausse fourrure"),
    (1099, "women", "Shorts taille haute"),
    (1100, "women", "Shorts en cuir"),
    (1103, "women", "Shorts cargo"),
    (1125, "women", "Ensembles tailleur/pantalon"),
    (1126, "women", "Jupes et robes tailleurs"),
    (1128, "women", "Tailleurs pièces séparées"),
    (1131, "women", "Combinaisons"),
    (1132, "women", "Combi Shorts"),
    (1134, "women", "Autres combinaisons & combishorts"),
    (1201, "boys", "Shorts et pantacourts"),
    (1204, "boys", "Vêtements de sport"),
    (1223, "men", "Blousons aviateur"),
    (1224, "men", "Vestes en jean"),
    (1225, "men", "Duffle-coats"),
    (1226, "men", "Vestes Harrington"),
    (1227, "men", "Parkas"),
    (1230, "men", "Trenchs"),
    (1248, "girls", "Jupes"),
    (1250, "girls", "Shorts et pantacourts"),
    (1253, "girls", "Vêtements de sport"),
    (1439, "women", "Brassières"),
    (1518, "girls", "Vestes sans manches"),
    (1535, "girls", "T-shirts"),
    (1536, "girls", "Polos"),
    (1537, "girls", "Chemises"),
    (1538, "girls", "Chemises manches courtes"),
    (1539, "girls", "Chemises manches longues"),
    (1540, "girls", "Chemises sans manches"),
    (1541, "girls", "Tuniques"),
    (1542, "girls", "Pulls"),
    (1543, "girls", "Pulls col V"),
    (1544, "girls", "Pulls à col roulé"),
    (1548, "girls", "Gilets zippés"),
    (1550, "girls", "Pulls à capuche & sweatshirts"),
    (1551, "girls", "Gilets"),
    (1553, "girls", "Robes longues"),
    (1554, "girls", "Robes courtes"),
    (1559, "girls", "Jeans"),
    (1560, "girls", "Jeans slim"),
    (1562, "girls", "Pantalons pattes d'éléphant"),
    (1565, "girls", "Leggings"),
    (1568, "girls", "Salopettes"),
    (1590, "girls", "Maillot de bain 1 pièce"),
    (1592, "girls", "Maillot de bain 2 pièces"),
    (1646, "boys", "Vestes sans manches"),
    (1662, "boys", "T-shirts"),
    (1663, "boys", "Polos"),
    (1664, "boys", "Chemises"),
    (1665, "boys", "Chemises manches courtes"),
    (1666, "boys", "Chemises manches longues"),
    (1667, "boys", "Chemises sans manches"),
    (1668, "boys", "Pulls"),
    (1669, "boys", "Pulls col V"),
    (1670, "boys", "Pulls à col roulé"),
    (1671, "boys", "Gilets zippés"),
    (1672, "boys", "Pulls à capuche et sweatshirts"),
    (1673, "boys", "Gilets"),
    (1696, "boys", "Jeans"),
    (1697, "boys", "Jeans slim"),
    (1698, "boys", "Pantalons pattes d'éléphant"),
    (1701, "boys", "Leggings"),
    (1702, "boys", "Salopettes"),
    (1750, "boys", "Maillots de bain"),
    (1773, "women", "Capes et ponchos"),
    (1775, "women", "Fêtes et cocktails"),
    (1778, "women", "Robes de soirée"),
    (1779, "women", "Robes d'hiver"),
    (1786, "men", "Blazers"),
    (1787, "men", "Pantalons de costume"),
    (1788, "men", "Gilets de costume"),
    (1789, "men", "Ensembles costume"),
    (1801, "men", "Chemises à carreaux"),
    (1802, "men", "Chemises en jean"),
    (1803, "men", "Chemises unies"),
    (1804, "men", "Chemises à motifs"),
    (1805, "men", "Chemises à rayures"),
    (1806, "men", "T-shirts unis"),
    (1807, "men", "T-shirts imprimés"),
    (1808, "men", "T-shirts à rayures"),
    (1809, "men", "Polos"),
    (1810, "men", "T-shirts à manches longues"),
    (1811, "men", "Sweats"),
    (1812, "men", "Pulls à capuche avec zip"),
    (1813, "men", "Pulls ras de cou"),
    (1814, "men", "Sweats longs"),
    (1815, "men", "Pulls d'hiver"),
    (1816, "men", "Jeans troués"),
    (1817, "men", "Jeans skinny"),
    (1818, "men", "Jeans slim"),
    (1819, "men", "Jeans coupe droite"),
    (1820, "men", "Chinos"),
    (1821, "men", "Jogging"),
    (1822, "men", "Shorts cargo"),
    (1823, "men", "Shorts chino"),
    (1824, "men", "Shorts en jean"),
    (1825, "men", "Vestes"),
    (1834, "women", "Trenchs"),
    (1835, "women", "Bodies"),
    (1837, "women", "Tops peplum"),
    (1838, "women", "Shorts taille basse"),
    (1839, "women", "Jeans boyfriend"),
    (1840, "women", "Jeans courts"),
    (1841, "women", "Jeans évasés"),
    (1842, "women", "Jeans taille haute"),
    (1843, "women", "Jeans troués"),
    (1844, "women", "Jeans skinny"),
    (1845, "women", "Jeans droits"),
    (1846, "women", "Pantalons droits"),
    (1858, "men", "Vestes polaires"),
    (1859, "men", "Imperméables"),
    (1861, "men", "Cabans"),
    (1865, "men", "Autres chemises"),
    (1868, "men", "Autres T-shirts"),
    (1870, "boys", "Autres"),
    (1874, "women", "Vestes"),
    (1877, "girls", "Autre"),
    (1878, "girls", "Autre"),
    (1880, "girls", "Autres"),
    (1886, "boys", "Autre"),
    (1887, "boys", "Autre"),
    (2079, "girls", "Sarouels"),
    (2082, "boys", "Sarouels"),
    (2524, "women", "Vestes sans manches"),
    (2525, "women", "Duffle-coats"),
    (2526, "women", "Pardessus et manteaux longs"),
    (2527, "women", "Perfectos et blousons de moto"),
    (2528, "women", "Vestes militaires et utilitaires"),
    (2529, "women", "Vestes chemises"),
    (2530, "women", "Vestes de ski et snowboard"),
    (2531, "women", "Blousons teddy"),
    (2532, "women", "Vestes coupe-vent"),
    (2533, "men", "Pardessus et manteaux longs"),
    (2534, "men", "Perfectos et blousons de moto"),
    (2535, "men", "Vestes militaires et utilitaires"),
    (2536, "men", "Doudounes"),
    (2537, "men", "Vestes matelassées"),
    (2538, "men", "Vestes chemises"),
    (2539, "men", "Vestes de ski et snowboard"),
    (2540, "girls", "Duffle-coats"),
    (2541, "girls", "Parkas"),
    (2542, "girls", "Cabans"),
    (2543, "girls", "Trenchs"),
    (2544, "girls", "Blazers"),
    (2545, "girls", "Blousons aviateur"),
    (2546, "girls", "Vestes en jean"),
    (2547, "girls", "Vestes polaires"),
    (2548, "girls", "Doudounes"),
    (2549, "girls", "Vestes coupe-vent"),
    (2550, "men", "Blousons teddy"),
    (2551, "men", "Vestes coupe-vent"),
    (2552, "men", "Ponchos"),
    (2553, "men", "Vestes sans manches"),
    (2556, "girls", "Ponchos"),
    (2558, "girls", "Imperméables"),
    (2561, "boys", "Duffle-coats"),
    (2562, "boys", "Parkas"),
    (2563, "boys", "Cabans"),
    (2564, "boys", "Trenchs"),
    (2571, "boys", "Blazers"),
    (2573, "boys", "Blousons aviateur"),
    (2574, "boys", "Vestes en jean"),
    (2575, "boys", "Vestes polaires"),
    (2576, "boys", "Doudounes"),
    (2577, "boys", "Vestes coupe-vent"),
    (2604, "boys", "Ponchos"),
    (2606, "boys", "Imperméables"),
    (2614, "women", "Doudounes"),
    (2596, "women", "Vestes matelassées"),
    (2927, "women", "Jupes longueur genou"),
    (2928, "women", "Jupes asymétriques"),
    (2929, "women", "Jupes-shorts"),
    (3267, "men", "Maillots"),
    (3268, "women", "Maillots"),
    (14, "women", "Vestes"),
]


def upgrade() -> None:
    """
    Add Vinted categories to vinted.categories table.
    """
    conn = op.get_bind()

    inserted = 0
    updated = 0

    for cat_id, gender, title in CATEGORIES:
        # Check if category exists
        exists = conn.execute(
            text("SELECT id FROM vinted.categories WHERE id = :id"),
            {"id": cat_id}
        ).fetchone()

        if exists:
            # Update existing category
            conn.execute(
                text("""
                    UPDATE vinted.categories
                    SET gender = :gender, title = :title, is_leaf = TRUE, is_active = TRUE
                    WHERE id = :id
                """),
                {"id": cat_id, "gender": gender, "title": title}
            )
            updated += 1
        else:
            # Insert new category
            conn.execute(
                text("""
                    INSERT INTO vinted.categories (id, title, gender, is_leaf, is_active)
                    VALUES (:id, :title, :gender, TRUE, TRUE)
                """),
                {"id": cat_id, "title": title, "gender": gender}
            )
            inserted += 1

    print(f"  ✓ Inserted {inserted} new categories")
    print(f"  ✓ Updated {updated} existing categories")
    print(f"  ✓ Total: {len(CATEGORIES)} categories processed")


def downgrade() -> None:
    """
    Remove added categories (only if they were inserted, not updated).
    Note: This won't restore original values for updated categories.
    """
    conn = op.get_bind()

    cat_ids = [cat[0] for cat in CATEGORIES]

    # Delete categories that were added
    result = conn.execute(
        text("""
            DELETE FROM vinted.categories
            WHERE id = ANY(:ids)
        """),
        {"ids": cat_ids}
    )

    print(f"  ✓ Removed {result.rowcount} categories")
