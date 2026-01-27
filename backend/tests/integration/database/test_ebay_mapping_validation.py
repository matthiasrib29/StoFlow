"""
eBay Mapping Validation Tests

Tests d'intégrité pour valider le mapping bidirectionnel eBay (StoFlow ↔ eBay).
Vérifie la complétude du mapping, l'intégrité référentielle et les contraintes.

Author: Claude
Date: 2026-01-26
"""
import pytest
from sqlalchemy import text

from shared.database import get_db_context


class TestEbayToStoFlow:
    """Tests pour le sens eBay → StoFlow (reverse mapping)."""

    def test_each_ebay_category_gender_group_has_exactly_one_default(self):
        """Chaque groupe (ebay_category_id, my_gender) doit avoir exactement 1 is_default=true."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT ebay_category_id, my_gender,
                       COUNT(*) FILTER (WHERE is_default = TRUE) as default_count
                FROM ebay.mapping
                GROUP BY ebay_category_id, my_gender
                HAVING COUNT(*) FILTER (WHERE is_default = TRUE) != 1
                ORDER BY ebay_category_id, my_gender
            """)).fetchall()

            if result:
                issues = [
                    f"ebay_category_id={r.ebay_category_id} + {r.my_gender}: "
                    f"{r.default_count} default(s)"
                    for r in result
                ]
                pytest.fail(
                    f"Groupes avec mauvais nombre de defaults ({len(result)}):\n"
                    + "\n".join(issues)
                )

    def test_no_ebay_category_gender_group_without_default(self):
        """Aucun groupe (ebay_category_id, my_gender) ne doit manquer de default."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT ebay_category_id, my_gender,
                       COUNT(*) as mapping_count,
                       COUNT(*) FILTER (WHERE is_default = TRUE) as default_count
                FROM ebay.mapping
                GROUP BY ebay_category_id, my_gender
                HAVING COUNT(*) FILTER (WHERE is_default = TRUE) = 0
                ORDER BY ebay_category_id, my_gender
            """)).fetchall()

            if result:
                missing = [
                    f"ebay_category_id={r.ebay_category_id} + {r.my_gender} "
                    f"({r.mapping_count} mappings, 0 default)"
                    for r in result
                ]
                pytest.fail(
                    f"Groupes sans default ({len(result)}):\n"
                    + "\n".join(missing)
                )

    def test_ebay_category_ids_exist_in_ebay_categories(self):
        """Tous les ebay_category_id doivent exister dans ebay.categories."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT DISTINCT em.ebay_category_id, em.my_category, em.my_gender
                FROM ebay.mapping em
                LEFT JOIN ebay.categories ec ON em.ebay_category_id = ec.category_id
                WHERE ec.category_id IS NULL
            """)).fetchall()

            if result:
                orphans = [
                    f"ebay_category_id={r.ebay_category_id} "
                    f"({r.my_category}/{r.my_gender})"
                    for r in result
                ]
                pytest.fail(
                    f"ebay_category_id orphelins ({len(result)}):\n"
                    + "\n".join(orphans)
                )


class TestStoFlowToEbay:
    """Tests pour le sens StoFlow → eBay (forward mapping)."""

    def test_all_valid_category_gender_couples_have_mapping(self):
        """Chaque couple (category + gender) valide dans product_attributes doit avoir un mapping."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT c.name_en as category, g.gender
                FROM product_attributes.categories c
                CROSS JOIN (VALUES ('men'), ('women'), ('boys'), ('girls')) AS g(gender)
                WHERE g.gender = ANY(c.genders)
                AND c.parent_category IS NOT NULL
                AND c.name_en NOT IN (
                    'tops', 'bottoms', 'outerwear', 'dresses-jumpsuits',
                    'formalwear', 'sportswear', 'clothing'
                )
                AND NOT EXISTS (
                    SELECT 1 FROM ebay.mapping em
                    WHERE em.my_category = c.name_en
                    AND em.my_gender = g.gender
                )
                ORDER BY c.name_en, g.gender
            """)).fetchall()

            if result:
                unmapped = [f"{r.category} + {r.gender}" for r in result]
                pytest.fail(
                    f"Couples sans mapping eBay ({len(result)}):\n"
                    + "\n".join(unmapped)
                )

    def test_my_category_exists_in_product_attributes(self):
        """Tous les my_category doivent exister dans product_attributes.categories."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT DISTINCT em.my_category
                FROM ebay.mapping em
                LEFT JOIN product_attributes.categories c ON em.my_category = c.name_en
                WHERE c.name_en IS NULL
            """)).fetchall()

            if result:
                orphans = [r.my_category for r in result]
                pytest.fail(
                    f"my_category orphelins ({len(result)}):\n"
                    + "\n".join(orphans)
                )

    def test_my_gender_is_allowed_for_category(self):
        """Le my_gender doit être autorisé par la colonne genders de la catégorie."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT em.id, em.my_category, em.my_gender, c.genders
                FROM ebay.mapping em
                JOIN product_attributes.categories c ON em.my_category = c.name_en
                WHERE NOT (em.my_gender = ANY(c.genders))
            """)).fetchall()

            if result:
                issues = [
                    f"id={r.id}: {r.my_category} + {r.my_gender} "
                    f"(autorisés: {r.genders})"
                    for r in result
                ]
                pytest.fail(
                    f"Gender non autorisé ({len(result)}):\n"
                    + "\n".join(issues)
                )


class TestEbayCategoryIntegrity:
    """Tests pour l'intégrité de la table ebay.categories."""

    def test_all_leaf_categories_are_mapped(self):
        """Toutes les catégories feuilles eBay doivent être utilisées dans le mapping."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT ec.category_id, ec.category_name, ec.path
                FROM ebay.categories ec
                LEFT JOIN ebay.mapping em ON ec.category_id = em.ebay_category_id
                WHERE ec.is_leaf = TRUE
                AND em.id IS NULL
                ORDER BY ec.path
            """)).fetchall()

            if result:
                unmapped = [
                    f"{r.category_id}: {r.category_name} ({r.path})"
                    for r in result
                ]
                pytest.fail(
                    f"Catégories feuilles eBay non mappées ({len(result)}):\n"
                    + "\n".join(unmapped)
                )

    def test_parent_child_hierarchy_is_valid(self):
        """Chaque parent_id doit pointer vers une catégorie existante."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT ec.category_id, ec.category_name, ec.parent_id
                FROM ebay.categories ec
                LEFT JOIN ebay.categories parent ON ec.parent_id = parent.category_id
                WHERE ec.parent_id IS NOT NULL
                AND parent.category_id IS NULL
            """)).fetchall()

            if result:
                orphans = [
                    f"{r.category_id} ({r.category_name}): "
                    f"parent_id={r.parent_id} inexistant"
                    for r in result
                ]
                pytest.fail(
                    f"Catégories avec parent_id invalide ({len(result)}):\n"
                    + "\n".join(orphans)
                )

    def test_path_is_consistent_with_hierarchy(self):
        """Le path doit se terminer par le nom de la catégorie elle-même."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT ec.category_id, ec.category_name, ec.path
                FROM ebay.categories ec
                WHERE ec.path IS NOT NULL
                AND ec.path NOT LIKE '%' || ec.category_name
            """)).fetchall()

            if result:
                issues = [
                    f"{r.category_id}: name='{r.category_name}' "
                    f"path='{r.path}'"
                    for r in result
                ]
                pytest.fail(
                    f"Path incohérent avec le nom ({len(result)}):\n"
                    + "\n".join(issues[:20])
                    + (f"\n... et {len(result) - 20} autres" if len(result) > 20 else "")
                )


class TestMappingConstraints:
    """Tests pour les contraintes du mapping eBay."""

    def test_unique_constraint_on_category_gender(self):
        """La contrainte uq_ebay_mapping_category_gender doit exister."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT conname, contype
                FROM pg_constraint
                WHERE conname = 'uq_ebay_mapping_category_gender'
                AND contype = 'u'
            """)).fetchone()

            assert result is not None, (
                "Contrainte unique uq_ebay_mapping_category_gender non trouvée"
            )

    def test_multiple_categories_can_map_to_same_ebay_id(self):
        """Relation N:1 : plusieurs StoFlow categories → 1 eBay category doit être possible."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT ebay_category_id, COUNT(DISTINCT my_category) as distinct_categories
                FROM ebay.mapping
                GROUP BY ebay_category_id
                HAVING COUNT(DISTINCT my_category) > 1
                ORDER BY COUNT(DISTINCT my_category) DESC
                LIMIT 5
            """)).fetchall()

            assert len(result) > 0, (
                "Aucun ebay_category_id n'est partagé par plusieurs catégories StoFlow. "
                "La relation N:1 (plusieurs my_category → 1 ebay_category_id) doit être possible."
            )

            print(f"\n=== Top 5 ebay_category_id partagés ===")
            for r in result:
                print(
                    f"ebay_category_id={r.ebay_category_id}: "
                    f"{r.distinct_categories} catégories différentes"
                )

    def test_no_duplicate_defaults_per_ebay_group(self):
        """Pas de double is_default=true dans un même groupe (ebay_category_id, my_gender)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT ebay_category_id, my_gender,
                       COUNT(*) as default_count,
                       array_agg(my_category) as categories
                FROM ebay.mapping
                WHERE is_default = TRUE
                GROUP BY ebay_category_id, my_gender
                HAVING COUNT(*) > 1
                ORDER BY ebay_category_id, my_gender
            """)).fetchall()

            if result:
                issues = [
                    f"ebay_category_id={r.ebay_category_id} + {r.my_gender}: "
                    f"{r.default_count} defaults ({r.categories})"
                    for r in result
                ]
                pytest.fail(
                    f"Doubles defaults détectés ({len(result)}):\n"
                    + "\n".join(issues)
                )


class TestMappingStatistics:
    """Tests pour les statistiques de couverture du mapping eBay."""

    def test_mapping_coverage_stats(self):
        """Affiche les statistiques de couverture du mapping eBay."""
        with get_db_context() as db:
            stats = db.execute(text("""
                SELECT
                    COUNT(*) as total_mappings,
                    COUNT(DISTINCT ebay_category_id) as unique_ebay_ids,
                    COUNT(DISTINCT (my_category, my_gender)) as unique_couples,
                    SUM(CASE WHEN is_default THEN 1 ELSE 0 END) as defaults,
                    COUNT(DISTINCT my_category) as unique_categories,
                    COUNT(DISTINCT my_gender) as unique_genders
                FROM ebay.mapping
            """)).fetchone()

            assert stats.total_mappings > 0, "Aucun mapping eBay trouvé"

            print(f"\n=== Statistiques du mapping eBay ===")
            print(f"Total mappings: {stats.total_mappings}")
            print(f"eBay IDs uniques: {stats.unique_ebay_ids}")
            print(f"Couples (category, gender) uniques: {stats.unique_couples}")
            print(f"Defaults: {stats.defaults}")
            print(f"Catégories StoFlow uniques: {stats.unique_categories}")
            print(f"Genders uniques: {stats.unique_genders}")
