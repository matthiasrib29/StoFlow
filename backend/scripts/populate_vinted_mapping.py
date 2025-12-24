"""
Populate vinted_mapping table

Inserts the mapping data between our categories and Vinted categories.

Usage:
    python scripts/populate_vinted_mapping.py

Author: Claude
Date: 2025-12-17
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from shared.database import engine


# Mapping data: (vinted_id, vinted_title, vinted_gender, my_category, my_gender, my_fit, my_length, my_rise, my_material, my_pattern, my_neckline, my_sleeve_length, is_default, priority)
MAPPING_DATA = [
    # Jeans
    (1845, "Jeans droits", "women", "jeans", "women", "straight", None, None, None, None, None, None, True, 0),
    (1844, "Jeans skinny", "women", "jeans", "women", "skinny", None, None, None, None, None, None, False, 10),
    (1841, "Jeans évasés", "women", "jeans", "women", "flare", None, None, None, None, None, None, False, 10),
    (1839, "Jeans boyfriend", "women", "jeans", "women", "relaxed", None, None, None, None, None, None, False, 10),
    (1842, "Jeans taille haute", "women", "jeans", "women", None, None, "high-rise", None, None, None, None, False, 8),
    (1840, "Jeans courts", "women", "jeans", "women", None, "cropped", None, None, None, None, None, False, 5),
    (1843, "Jeans troués", "women", "jeans", "women", None, None, None, None, None, None, None, False, 3),
    (1819, "Jeans coupe droite", "men", "jeans", "men", "straight", None, None, None, None, None, None, True, 0),
    (1817, "Jeans skinny", "men", "jeans", "men", "skinny", None, None, None, None, None, None, False, 10),
    (1818, "Jeans slim", "men", "jeans", "men", "slim", None, None, None, None, None, None, False, 10),
    (1816, "Jeans troués", "men", "jeans", "men", None, None, None, None, None, None, None, False, 3),
    (1559, "Jeans", "girls", "jeans", "girls", None, None, None, None, None, None, None, True, 0),
    (1560, "Jeans slim", "girls", "jeans", "girls", "slim", None, None, None, None, None, None, False, 10),
    (1696, "Jeans", "boys", "jeans", "boys", None, None, None, None, None, None, None, True, 0),
    (1697, "Jeans slim", "boys", "jeans", "boys", "slim", None, None, None, None, None, None, False, 10),

    # Dress
    (1059, "Robes casual", "women", "dress", "women", None, None, None, None, None, None, None, True, 0),
    (178, "Mini", "women", "dress", "women", None, "mini", None, None, None, None, None, False, 10),
    (1056, "Midi", "women", "dress", "women", None, "midi", None, None, None, None, None, False, 10),
    (1055, "Robes longues", "women", "dress", "women", None, "maxi", None, None, None, None, None, False, 10),
    (179, "Robes en jean", "women", "dress", "women", None, None, None, "denim", None, None, None, False, 5),
    (1775, "Fêtes et cocktails", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (1778, "Robes de soirée", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (1060, "Robes dos nu", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (1065, "Robes d'été", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (1779, "Robes d'hiver", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (1057, "Robes chics", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (1061, "Robes sans bretelles", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (1058, "Petites robes noires", "women", "dress", "women", None, None, None, None, None, None, None, False, 3),
    (176, "Autres robes", "women", "dress", "women", None, None, None, None, None, None, None, False, 1),
    (1554, "Robes courtes", "girls", "dress", "girls", None, "mini", None, None, None, None, None, True, 0),
    (1553, "Robes longues", "girls", "dress", "girls", None, "maxi", None, None, None, None, None, False, 10),

    # T-shirt
    (221, "T-shirts", "women", "t-shirt", "women", None, None, None, None, None, None, None, True, 0),
    (1806, "T-shirts unis", "men", "t-shirt", "men", None, None, None, None, "solid", None, None, True, 0),
    (1807, "T-shirts imprimés", "men", "t-shirt", "men", None, None, None, None, "printed", None, None, False, 5),
    (1808, "T-shirts à rayures", "men", "t-shirt", "men", None, None, None, None, "striped", None, None, False, 5),
    (1810, "T-shirts à manches longues", "men", "t-shirt", "men", None, None, None, None, None, None, "long sleeve", False, 8),
    (1535, "T-shirts", "girls", "t-shirt", "girls", None, None, None, None, None, None, None, True, 0),
    (1662, "T-shirts", "boys", "t-shirt", "boys", None, None, None, None, None, None, None, True, 0),

    # Tank-top
    (534, "Débardeurs", "women", "tank-top", "women", None, None, None, None, None, None, "sleeveless", True, 0),
    (560, "T-shirts sans manches", "men", "tank-top", "men", None, None, None, None, None, None, "sleeveless", True, 0),

    # Shirt
    (222, "Chemises", "women", "shirt", "women", None, None, None, None, None, None, None, True, 0),
    (1803, "Chemises unies", "men", "shirt", "men", None, None, None, None, "solid", None, None, True, 0),
    (1801, "Chemises à carreaux", "men", "shirt", "men", None, None, None, None, "checkered", None, None, False, 5),
    (1802, "Chemises en jean", "men", "shirt", "men", None, None, None, "denim", None, None, None, False, 5),
    (1805, "Chemises à rayures", "men", "shirt", "men", None, None, None, None, "striped", None, None, False, 5),
    (1804, "Chemises à motifs", "men", "shirt", "men", None, None, None, None, "printed", None, None, False, 3),
    (1537, "Chemises", "girls", "shirt", "girls", None, None, None, None, None, None, None, True, 0),
    (1664, "Chemises", "boys", "shirt", "boys", None, None, None, None, None, None, None, True, 0),

    # Blouse
    (1043, "Blouses", "women", "blouse", "women", None, None, None, None, None, None, None, True, 0),
    (223, "Blouses manches courtes", "women", "blouse", "women", None, None, None, None, None, None, "short sleeve", False, 5),
    (224, "Blouses manches longues", "women", "blouse", "women", None, None, None, None, None, None, "long sleeve", False, 5),
    (225, "Blouses ¾", "women", "blouse", "women", None, None, None, None, None, None, "3/4 sleeve", False, 5),

    # Top / Crop-top
    (1837, "Tops peplum", "women", "top", "women", None, None, None, None, None, None, None, True, 0),
    (1042, "Tops épaules dénudées", "women", "top", "women", None, None, None, None, None, "off-shoulder", None, False, 5),
    (1044, "Tops dos nu", "women", "top", "women", None, None, None, None, None, "halter", None, False, 5),
    (227, "Tuniques", "women", "top", "women", None, None, None, None, None, None, None, False, 3),
    (1041, "Tops courts", "women", "crop-top", "women", None, "cropped", None, None, None, None, None, True, 0),

    # Bodysuit
    (1835, "Bodies", "women", "bodysuit", "women", None, None, None, None, None, None, None, True, 0),

    # Sweater
    (529, "Pulls d'hiver", "women", "sweater", "women", None, None, None, None, None, None, None, True, 0),
    (1045, "Cols roulés", "women", "sweater", "women", None, None, None, None, None, "turtleneck", None, False, 10),
    (190, "Pulls col V", "women", "sweater", "women", None, None, None, None, None, "v-neck", None, False, 10),
    (191, "Pulls col roulé", "women", "sweater", "women", None, None, None, None, None, "turtleneck", None, False, 10),
    (1066, "Autres sweats", "women", "sweater", "women", None, None, None, None, None, None, None, False, 1),
    (1813, "Pulls ras de cou", "men", "sweater", "men", None, None, None, None, None, "crew neck", None, True, 0),
    (264, "Sweats à col V", "men", "sweater", "men", None, None, None, None, None, "v-neck", None, False, 10),
    (265, "Pulls à col roulé", "men", "sweater", "men", None, None, None, None, None, "turtleneck", None, False, 10),
    (1815, "Pulls d'hiver", "men", "sweater", "men", None, None, None, None, None, None, None, False, 5),
    (1542, "Pulls", "girls", "sweater", "girls", None, None, None, None, None, None, None, True, 0),
    (1543, "Pulls col V", "girls", "sweater", "girls", None, None, None, None, None, "v-neck", None, False, 10),
    (1544, "Pulls à col roulé", "girls", "sweater", "girls", None, None, None, None, None, "turtleneck", None, False, 10),
    (1668, "Pulls", "boys", "sweater", "boys", None, None, None, None, None, None, None, True, 0),
    (1669, "Pulls col V", "boys", "sweater", "boys", None, None, None, None, None, "v-neck", None, False, 10),
    (1670, "Pulls à col roulé", "boys", "sweater", "boys", None, None, None, None, None, "turtleneck", None, False, 10),

    # Cardigan
    (194, "Cardigans", "women", "cardigan", "women", None, None, None, None, None, None, None, True, 0),
    (195, "Boléros", "women", "cardigan", "women", None, None, None, None, None, None, None, False, 5),
    (266, "Cardigans", "men", "cardigan", "men", None, None, None, None, None, None, None, True, 0),

    # Sweatshirt
    (196, "Sweats & sweats à capuche", "women", "sweatshirt", "women", None, None, None, None, None, None, None, True, 0),
    (192, "Sweats longs", "women", "sweatshirt", "women", None, None, None, None, None, None, None, False, 5),
    (1811, "Sweats", "men", "sweatshirt", "men", None, None, None, None, None, None, None, True, 0),
    (1814, "Sweats longs", "men", "sweatshirt", "men", None, None, None, None, None, None, None, False, 5),

    # Hoodie
    (267, "Pulls et pulls à capuche", "women", "hoodie", "women", None, None, None, None, None, "hood", None, True, 0),
    (267, "Pulls et pulls à capuche", "men", "hoodie", "men", None, None, None, None, None, "hood", None, True, 0),
    (1812, "Pulls à capuche avec zip", "men", "hoodie", "men", None, None, None, None, None, "hood", None, False, 5),
    (1550, "Pulls à capuche & sweatshirts", "girls", "hoodie", "girls", None, None, None, None, None, "hood", None, True, 0),
    (1672, "Pulls à capuche et sweatshirts", "boys", "hoodie", "boys", None, None, None, None, None, "hood", None, True, 0),

    # Fleece
    (1086, "Vestes polaires", "women", "fleece", "women", None, None, None, "fleece", None, None, None, True, 0),
    (1858, "Vestes polaires", "men", "fleece", "men", None, None, None, "fleece", None, None, None, True, 0),
    (2547, "Vestes polaires", "girls", "fleece", "girls", None, None, None, "fleece", None, None, None, True, 0),
    (2575, "Vestes polaires", "boys", "fleece", "boys", None, None, None, "fleece", None, None, None, True, 0),

    # Overshirt
    (2529, "Vestes chemises", "women", "overshirt", "women", None, None, None, None, None, None, None, True, 0),
    (2538, "Vestes chemises", "men", "overshirt", "men", None, None, None, None, None, None, None, True, 0),

    # Polo
    (1809, "Polos", "men", "polo", "men", None, None, None, None, None, "polo collar", None, True, 0),
    (1536, "Polos", "girls", "polo", "girls", None, None, None, None, None, "polo collar", None, True, 0),
    (1663, "Polos", "boys", "polo", "boys", None, None, None, None, None, "polo collar", None, True, 0),

    # Pants
    (1846, "Pantalons droits", "women", "pants", "women", "straight", None, None, None, None, None, None, True, 0),
    (185, "Pantalons skinny", "women", "pants", "women", "skinny", None, None, None, None, None, None, False, 10),
    (187, "Pantalons ajustés", "women", "pants", "women", "slim", None, None, None, None, None, None, False, 10),
    (1071, "Pantalons à jambes larges", "women", "pants", "women", "loose", None, None, None, None, None, None, False, 10),
    (184, "Pantalons en cuir", "women", "pants", "women", None, None, None, "leather", None, None, None, False, 5),
    (259, "Pantalons skinny", "men", "pants", "men", "skinny", None, None, None, None, None, None, True, 0),
    (260, "Pantalons à jambes larges", "men", "pants", "men", "loose", None, None, None, None, None, None, False, 10),

    # Chinos
    (1070, "Pantalons courts & chinos", "women", "chinos", "women", None, None, None, None, None, None, None, True, 0),
    (1820, "Chinos", "men", "chinos", "men", None, None, None, None, None, None, None, True, 0),

    # Joggers
    (1821, "Jogging", "men", "joggers", "men", None, None, None, None, None, None, None, True, 0),

    # Shorts
    (1103, "Shorts cargo", "women", "shorts", "women", None, None, None, None, None, None, None, True, 0),
    (1099, "Shorts taille haute", "women", "shorts", "women", None, None, "high-rise", None, None, None, None, False, 8),
    (1838, "Shorts taille basse", "women", "shorts", "women", None, None, "low-rise", None, None, None, None, False, 8),
    (538, "Short en jean", "women", "shorts", "women", None, None, None, "denim", None, None, None, False, 5),
    (1100, "Shorts en cuir", "women", "shorts", "women", None, None, None, "leather", None, None, None, False, 5),
    (204, "Pantacourts", "women", "shorts", "women", None, None, None, None, None, None, None, False, 3),
    (1822, "Shorts cargo", "men", "shorts", "men", None, None, None, None, None, None, None, True, 0),
    (1823, "Shorts chino", "men", "shorts", "men", None, None, None, None, None, None, None, False, 5),
    (1824, "Shorts en jean", "men", "shorts", "men", None, None, None, "denim", None, None, None, False, 5),
    (1250, "Shorts et pantacourts", "girls", "shorts", "girls", None, None, None, None, None, None, None, True, 0),
    (1201, "Shorts et pantacourts", "boys", "shorts", "boys", None, None, None, None, None, None, None, True, 0),

    # Bermuda
    (203, "Shorts longueur genou", "women", "bermuda", "women", None, "knee length", None, None, None, None, None, True, 0),
    (271, "Pantacourts", "men", "bermuda", "men", None, "knee length", None, None, None, None, None, True, 0),

    # Skirt
    (198, "Minijupes", "women", "skirt", "women", None, "mini", None, None, None, None, None, True, 0),
    (2927, "Jupes longueur genou", "women", "skirt", "women", None, "knee length", None, None, None, None, None, False, 10),
    (199, "Jupes midi", "women", "skirt", "women", None, "midi", None, None, None, None, None, False, 10),
    (200, "Jupes longues", "women", "skirt", "women", None, "maxi", None, None, None, None, None, False, 10),
    (2928, "Jupes asymétriques", "women", "skirt", "women", None, None, None, None, None, None, None, False, 3),
    (1248, "Jupes", "girls", "skirt", "girls", None, None, None, None, None, None, None, True, 0),

    # Leggings
    (525, "Leggings", "women", "leggings", "women", None, None, None, None, None, None, None, True, 0),
    (1565, "Leggings", "girls", "leggings", "girls", None, None, None, None, None, None, None, True, 0),

    # Culottes
    (2929, "Jupes-shorts", "women", "culottes", "women", None, None, None, None, None, None, None, True, 0),

    # Jacket
    (1079, "Vestes en jean", "women", "jacket", "women", None, None, None, "denim", None, None, None, True, 0),
    (2528, "Vestes militaires et utilitaires", "women", "jacket", "women", None, None, None, None, None, None, None, False, 5),
    (2596, "Vestes matelassées", "women", "jacket", "women", None, None, None, None, None, None, None, False, 5),
    (1224, "Vestes en jean", "men", "jacket", "men", None, None, None, "denim", None, None, None, True, 0),
    (2535, "Vestes militaires et utilitaires", "men", "jacket", "men", None, None, None, None, None, None, None, False, 5),
    (2537, "Vestes matelassées", "men", "jacket", "men", None, None, None, None, None, None, None, False, 5),
    (1226, "Vestes Harrington", "men", "jacket", "men", None, None, None, None, None, None, None, False, 5),
    (2546, "Vestes en jean", "girls", "jacket", "girls", None, None, None, "denim", None, None, None, True, 0),
    (2574, "Vestes en jean", "boys", "jacket", "boys", None, None, None, "denim", None, None, None, True, 0),

    # Bomber
    (1078, "Blousons aviateur", "women", "bomber", "women", None, None, None, None, None, None, None, True, 0),
    (2531, "Blousons teddy", "women", "bomber", "women", None, None, None, None, None, None, None, False, 5),
    (2527, "Perfectos et blousons de moto", "women", "bomber", "women", None, None, None, None, None, None, None, False, 5),
    (1223, "Blousons aviateur", "men", "bomber", "men", None, None, None, None, None, None, None, True, 0),
    (2550, "Blousons teddy", "men", "bomber", "men", None, None, None, None, None, None, None, False, 5),
    (2534, "Perfectos et blousons de moto", "men", "bomber", "men", None, None, None, None, None, None, None, False, 5),
    (2545, "Blousons aviateur", "girls", "bomber", "girls", None, None, None, None, None, None, None, True, 0),
    (2573, "Blousons aviateur", "boys", "bomber", "boys", None, None, None, None, None, None, None, True, 0),

    # Puffer
    (2614, "Doudounes", "women", "puffer", "women", None, None, None, None, None, None, None, True, 0),
    (2536, "Doudounes", "men", "puffer", "men", None, None, None, None, None, None, None, True, 0),
    (2548, "Doudounes", "girls", "puffer", "girls", None, None, None, None, None, None, None, True, 0),
    (2576, "Doudounes", "boys", "puffer", "boys", None, None, None, None, None, None, None, True, 0),

    # Coat
    (1076, "Cabans", "women", "coat", "women", None, None, None, None, None, None, None, True, 0),
    (2525, "Duffle-coats", "women", "coat", "women", None, None, None, None, None, None, None, False, 5),
    (1090, "Manteaux en fausse fourrure", "women", "coat", "women", None, None, None, None, None, None, None, False, 5),
    (2526, "Pardessus et manteaux longs", "women", "coat", "women", None, None, None, None, None, None, None, False, 5),
    (1861, "Cabans", "men", "coat", "men", None, None, None, None, None, None, None, True, 0),
    (1225, "Duffle-coats", "men", "coat", "men", None, None, None, None, None, None, None, False, 5),
    (2533, "Pardessus et manteaux longs", "men", "coat", "men", None, None, None, None, None, None, None, False, 5),
    (2542, "Cabans", "girls", "coat", "girls", None, None, None, None, None, None, None, True, 0),
    (2540, "Duffle-coats", "girls", "coat", "girls", None, None, None, None, None, None, None, False, 5),
    (2563, "Cabans", "boys", "coat", "boys", None, None, None, None, None, None, None, True, 0),
    (2561, "Duffle-coats", "boys", "coat", "boys", None, None, None, None, None, None, None, False, 5),

    # Trench
    (1834, "Trenchs", "women", "trench", "women", None, None, None, None, None, None, None, True, 0),
    (1230, "Trenchs", "men", "trench", "men", None, None, None, None, None, None, None, True, 0),
    (2543, "Trenchs", "girls", "trench", "girls", None, None, None, None, None, None, None, True, 0),
    (2564, "Trenchs", "boys", "trench", "boys", None, None, None, None, None, None, None, True, 0),

    # Parka
    (1087, "Parkas", "women", "parka", "women", None, None, None, None, None, None, None, True, 0),
    (1227, "Parkas", "men", "parka", "men", None, None, None, None, None, None, None, True, 0),
    (2541, "Parkas", "girls", "parka", "girls", None, None, None, None, None, None, None, True, 0),
    (2562, "Parkas", "boys", "parka", "boys", None, None, None, None, None, None, None, True, 0),

    # Raincoat
    (1080, "Imperméables", "women", "raincoat", "women", None, None, None, None, None, None, None, True, 0),
    (1859, "Imperméables", "men", "raincoat", "men", None, None, None, None, None, None, None, True, 0),
    (2558, "Imperméables", "girls", "raincoat", "girls", None, None, None, None, None, None, None, True, 0),
    (2606, "Imperméables", "boys", "raincoat", "boys", None, None, None, None, None, None, None, True, 0),

    # Windbreaker
    (2532, "Vestes coupe-vent", "women", "windbreaker", "women", None, None, None, None, None, None, None, True, 0),
    (2551, "Vestes coupe-vent", "men", "windbreaker", "men", None, None, None, None, None, None, None, True, 0),
    (2549, "Vestes coupe-vent", "girls", "windbreaker", "girls", None, None, None, None, None, None, None, True, 0),
    (2577, "Vestes coupe-vent", "boys", "windbreaker", "boys", None, None, None, None, None, None, None, True, 0),

    # Blazer
    (532, "Blazers", "women", "blazer", "women", None, None, None, None, None, None, None, True, 0),
    (1786, "Blazers", "men", "blazer", "men", None, None, None, None, None, None, None, True, 0),
    (2544, "Blazers", "girls", "blazer", "girls", None, None, None, None, None, None, None, True, 0),
    (2571, "Blazers", "boys", "blazer", "boys", None, None, None, None, None, None, None, True, 0),

    # Vest
    (2524, "Vestes sans manches", "women", "vest", "women", None, None, None, None, None, None, None, True, 0),
    (2553, "Vestes sans manches", "men", "vest", "men", None, None, None, None, None, None, None, True, 0),
    (1518, "Vestes sans manches", "girls", "vest", "girls", None, None, None, None, None, None, None, True, 0),
    (1646, "Vestes sans manches", "boys", "vest", "boys", None, None, None, None, None, None, None, True, 0),

    # Cape / Poncho
    (1773, "Capes et ponchos", "women", "cape", "women", None, None, None, None, None, None, None, True, 0),
    (2552, "Ponchos", "men", "poncho", "men", None, None, None, None, None, None, None, True, 0),
    (2556, "Ponchos", "girls", "poncho", "girls", None, None, None, None, None, None, None, True, 0),
    (2604, "Ponchos", "boys", "poncho", "boys", None, None, None, None, None, None, None, True, 0),

    # Kimono
    (1067, "Kimonos", "women", "kimono", "women", None, None, None, None, None, None, None, True, 0),

    # Jumpsuit
    (1131, "Combinaisons", "women", "jumpsuit", "women", None, None, None, None, None, None, None, True, 0),

    # Overalls
    (1568, "Salopettes", "girls", "overalls", "girls", None, None, None, None, None, None, None, True, 0),
    (1702, "Salopettes", "boys", "overalls", "boys", None, None, None, None, None, None, None, True, 0),

    # Romper
    (1132, "Combi Shorts", "women", "romper", "women", None, None, None, None, None, None, None, True, 0),

    # Suit
    (1789, "Ensembles costume", "men", "suit", "men", None, None, None, None, None, None, None, True, 0),
    (1787, "Pantalons de costume", "men", "suit", "men", None, None, None, None, None, None, None, False, 5),
    (261, "Pantalons de costume", "men", "dress-pants", "men", None, None, None, None, None, None, None, True, 0),
    (1125, "Ensembles tailleur/pantalon", "women", "womens-suit", "women", None, None, None, None, None, None, None, True, 0),

    # Tuxedo
    # Note: vinted_id 1790 doesn't exist in our vinted_categories import, skipping

    # Suit-vest
    (1788, "Gilets de costume", "men", "suit-vest", "men", None, None, None, None, None, None, None, True, 0),
    (1551, "Gilets", "girls", "suit-vest", "girls", None, None, None, None, None, None, None, True, 0),
    (1673, "Gilets", "boys", "suit-vest", "boys", None, None, None, None, None, None, None, True, 0),
    (1548, "Gilets zippés", "girls", "suit-vest", "girls", None, None, None, None, None, None, None, False, 5),
    (1671, "Gilets zippés", "boys", "suit-vest", "boys", None, None, None, None, None, None, None, False, 5),

    # Sports-bra
    (1439, "Brassières", "women", "sports-bra", "women", None, None, None, None, None, None, None, True, 0),

    # Sports-top
    (576, "Hauts & t-shirts", "women", "sports-top", "women", None, None, None, None, None, None, None, True, 0),
    (584, "Hauts et t-shirts", "men", "sports-top", "men", None, None, None, None, None, None, None, True, 0),

    # Sports-shorts
    (578, "Shorts", "women", "sports-shorts", "women", None, None, None, None, None, None, None, True, 0),
    (586, "Shorts", "men", "sports-shorts", "men", None, None, None, None, None, None, None, True, 0),

    # Sports-leggings
    (573, "Pantalons & leggings", "women", "sports-leggings", "women", None, None, None, None, None, None, None, True, 0),
    (583, "Pantalons", "men", "sports-leggings", "men", None, None, None, None, None, None, None, True, 0),

    # Sports-jersey
    (3268, "Maillots", "women", "sports-jersey", "women", None, None, None, None, None, None, None, True, 0),
    (3267, "Maillots", "men", "sports-jersey", "men", None, None, None, None, None, None, None, True, 0),

    # Tracksuit
    (572, "Survêtements", "women", "tracksuit", "women", None, None, None, None, None, None, None, True, 0),
    (582, "Survêtements", "men", "tracksuit", "men", None, None, None, None, None, None, None, True, 0),

    # Swimsuit
    (218, "Une pièce", "women", "swimsuit", "women", None, None, None, None, None, None, None, True, 0),
    (84, "Maillots de bain", "men", "swimsuit", "men", None, None, None, None, None, None, None, True, 0),
    (1590, "Maillot de bain 1 pièce", "girls", "swimsuit", "girls", None, None, None, None, None, None, None, True, 0),
    (1750, "Maillots de bain", "boys", "swimsuit", "boys", None, None, None, None, None, None, None, True, 0),

    # Bikini
    (219, "Deux pièces", "women", "bikini", "women", None, None, None, None, None, None, None, True, 0),
    (1592, "Maillot de bain 2 pièces", "girls", "bikini", "girls", None, None, None, None, None, None, None, True, 0),

    # Tuniques for girls
    (1541, "Tuniques", "girls", "top", "girls", None, None, None, None, None, None, None, True, 0),

    # Sport for kids
    (1253, "Vêtements de sport", "girls", "sportswear", "girls", None, None, None, None, None, None, None, True, 0),
    (1204, "Vêtements de sport pour", "boys", "sportswear", "boys", None, None, None, None, None, None, None, True, 0),
]


def main():
    """Main entry point."""
    print("=" * 60)
    print("POPULATE VINTED MAPPING")
    print("=" * 60)

    with engine.connect() as conn:
        # Clear existing data
        conn.execute(text("DELETE FROM vinted.mapping"))
        conn.commit()
        print(f"\n🗑️  Cleared existing mapping data")

        # Insert new data
        inserted = 0
        skipped = 0
        errors = []

        for row in MAPPING_DATA:
            vinted_id, vinted_title, vinted_gender, my_category, my_gender, my_fit, my_length, my_rise, my_material, my_pattern, my_neckline, my_sleeve_length, is_default, priority = row

            # Check if vinted_id exists
            exists = conn.execute(text(
                "SELECT 1 FROM vinted.categories WHERE id = :id"
            ), {"id": vinted_id}).fetchone()

            if not exists:
                errors.append(f"Vinted ID {vinted_id} ({vinted_title}) not found")
                skipped += 1
                continue

            # Check if my_category exists
            exists = conn.execute(text(
                "SELECT 1 FROM product_attributes.categories WHERE name_en = :cat"
            ), {"cat": my_category}).fetchone()

            if not exists:
                errors.append(f"Category '{my_category}' not found")
                skipped += 1
                continue

            try:
                conn.execute(text("""
                    INSERT INTO vinted.mapping
                    (vinted_id, vinted_gender, my_category, my_gender, my_fit, my_length, my_rise, my_material, my_pattern, my_neckline, my_sleeve_length, is_default, priority)
                    VALUES (:vinted_id, :vinted_gender, :my_category, :my_gender, :my_fit, :my_length, :my_rise, :my_material, :my_pattern, :my_neckline, :my_sleeve_length, :is_default, :priority)
                """), {
                    "vinted_id": vinted_id,
                    "vinted_gender": vinted_gender,
                    "my_category": my_category,
                    "my_gender": my_gender,
                    "my_fit": my_fit,
                    "my_length": my_length,
                    "my_rise": my_rise,
                    "my_material": my_material,
                    "my_pattern": my_pattern,
                    "my_neckline": my_neckline,
                    "my_sleeve_length": my_sleeve_length,
                    "is_default": is_default,
                    "priority": priority
                })
                inserted += 1
            except Exception as e:
                errors.append(f"Error inserting {vinted_id}: {e}")
                skipped += 1

        conn.commit()

        print(f"\n✅ Inserted {inserted} mappings")
        if skipped:
            print(f"⚠️  Skipped {skipped} mappings")
            for err in errors[:10]:
                print(f"   • {err}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more errors")

        # Verification
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)

        # Stats
        result = conn.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM vinted.categories WHERE is_leaf = TRUE) as total_vinted_leaves,
                (SELECT COUNT(DISTINCT vinted_id) FROM vinted.mapping) as mapped_vinted,
                (SELECT COUNT(*) FROM public.expected_mappings) as expected_couples,
                (SELECT COUNT(DISTINCT (my_category, my_gender)) FROM vinted.mapping) as mapped_couples,
                (SELECT COUNT(*) FROM vinted.mapping WHERE is_default = TRUE) as defaults_count,
                (SELECT COUNT(*) FROM vinted.mapping_validation) as total_issues
        """)).fetchone()

        print(f"\n📊 Statistics:")
        print(f"   Total Vinted leaves:    {result[0]}")
        print(f"   Mapped Vinted:          {result[1]}")
        print(f"   Expected couples:       {result[2]}")
        print(f"   Mapped couples:         {result[3]}")
        print(f"   Defaults count:         {result[4]}")
        print(f"   Total issues:           {result[5]}")

        # Show issues
        issues = conn.execute(text("""
            SELECT issue, vinted_id, vinted_title, vinted_gender, my_category, my_gender
            FROM vinted.mapping_validation
            ORDER BY issue, my_category, my_gender
            LIMIT 30
        """)).fetchall()

        if issues:
            print(f"\n⚠️  Issues found ({len(issues)} shown):")
            for issue in issues:
                if issue[0] == 'VINTED_NOT_MAPPED':
                    print(f"   [{issue[0]}] Vinted {issue[1]}: {issue[2]} ({issue[3]})")
                elif issue[0] == 'NO_DEFAULT':
                    print(f"   [{issue[0]}] {issue[4]} / {issue[5]}")
                elif issue[0] == 'COUPLE_NOT_MAPPED':
                    print(f"   [{issue[0]}] {issue[4]} / {issue[5]}")
        else:
            print("\n✅ No issues found!")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
