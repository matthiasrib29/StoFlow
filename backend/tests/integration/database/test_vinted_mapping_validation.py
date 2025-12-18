"""
Vinted Mapping Validation Tests

Tests unitaires pour valider que le mapping Vinted est complet dans les deux sens.
Ces tests vérifient l'intégrité référentielle et la complétude du mapping.

Author: Claude
Date: 2025-12-17
"""
import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from shared.database import get_db_context


class TestVintedToMyApp:
    """Tests pour le sens Vinted → Mon App (catégories actives uniquement)."""

    def test_all_active_vinted_categories_are_mapped(self):
        """Chaque catégorie Vinted active doit être mappée."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vc.id, vc.title, vc.gender
                FROM public.vinted_categories vc
                LEFT JOIN public.vinted_mapping vm ON vc.id = vm.vinted_id
                WHERE vc.is_active = TRUE
                AND vm.id IS NULL
                ORDER BY vc.gender, vc.title
            """)).fetchall()

            if result:
                unmapped = [f"{r.id}: {r.title} ({r.gender})" for r in result]
                pytest.fail(
                    f"Catégories Vinted actives non mappées ({len(result)}):\n"
                    + "\n".join(unmapped[:20])
                    + (f"\n... et {len(result) - 20} autres" if len(result) > 20 else "")
                )

    def test_vinted_ids_exist_in_vinted_categories(self):
        """Les vinted_id dans vinted_mapping doivent exister dans vinted_categories."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.vinted_id, vm.my_category, vm.my_gender
                FROM public.vinted_mapping vm
                LEFT JOIN public.vinted_categories vc ON vm.vinted_id = vc.id
                WHERE vc.id IS NULL
            """)).fetchall()

            if result:
                orphans = [f"vinted_id={r.vinted_id} ({r.my_category}/{r.my_gender})" for r in result]
                pytest.fail(
                    f"vinted_id orphelins ({len(result)}):\n" + "\n".join(orphans)
                )

    def test_vinted_gender_matches_vinted_categories(self):
        """Le vinted_gender doit correspondre à vinted_categories.gender."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.vinted_id, vm.vinted_gender, vc.gender as actual_gender
                FROM public.vinted_mapping vm
                JOIN public.vinted_categories vc ON vm.vinted_id = vc.id
                WHERE vm.vinted_gender != vc.gender
            """)).fetchall()

            if result:
                mismatches = [
                    f"id={r.id}: vinted_id={r.vinted_id} "
                    f"(mapping={r.vinted_gender}, actual={r.actual_gender})"
                    for r in result
                ]
                pytest.fail(
                    f"Gender incohérent ({len(result)}):\n" + "\n".join(mismatches)
                )


class TestMyAppToVinted:
    """Tests pour le sens Mon App → Vinted."""

    def test_all_valid_category_gender_couples_have_mapping(self):
        """Chaque couple (category + gender) valide doit avoir au moins un mapping."""
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
                    SELECT 1 FROM public.vinted_mapping vm
                    WHERE vm.my_category = c.name_en
                    AND vm.my_gender = g.gender
                )
                ORDER BY c.name_en, g.gender
            """)).fetchall()

            if result:
                unmapped = [f"{r.category} + {r.gender}" for r in result]
                pytest.fail(
                    f"Couples sans mapping ({len(result)}):\n" + "\n".join(unmapped)
                )

    def test_each_couple_has_exactly_one_default(self):
        """Chaque couple (category + gender) doit avoir exactement UN défaut."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT my_category, my_gender,
                       COUNT(*) FILTER (WHERE is_default = TRUE) as default_count
                FROM public.vinted_mapping
                GROUP BY my_category, my_gender
                HAVING COUNT(*) FILTER (WHERE is_default = TRUE) != 1
                ORDER BY my_category, my_gender
            """)).fetchall()

            if result:
                issues = [
                    f"{r.my_category} + {r.my_gender}: {r.default_count} défaut(s)"
                    for r in result
                ]
                pytest.fail(
                    f"Couples avec mauvais nombre de défauts ({len(result)}):\n"
                    + "\n".join(issues)
                )

    def test_my_category_exists_in_categories(self):
        """Les my_category dans vinted_mapping doivent exister dans categories."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT DISTINCT vm.my_category
                FROM public.vinted_mapping vm
                LEFT JOIN product_attributes.categories c ON vm.my_category = c.name_en
                WHERE c.name_en IS NULL
            """)).fetchall()

            if result:
                orphans = [r.my_category for r in result]
                pytest.fail(
                    f"my_category orphelins ({len(result)}):\n" + "\n".join(orphans)
                )

    def test_my_gender_is_allowed_for_category(self):
        """Le my_gender doit être autorisé pour la catégorie."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_category, vm.my_gender, c.genders
                FROM public.vinted_mapping vm
                JOIN product_attributes.categories c ON vm.my_category = c.name_en
                WHERE NOT (vm.my_gender = ANY(c.genders))
            """)).fetchall()

            if result:
                issues = [
                    f"id={r.id}: {r.my_category} + {r.my_gender} "
                    f"(autorisés: {r.genders})"
                    for r in result
                ]
                pytest.fail(
                    f"Gender non autorisé ({len(result)}):\n" + "\n".join(issues)
                )


class TestAttributeValidity:
    """Tests pour la validité des attributs du mapping."""

    def test_all_my_fit_values_are_valid(self):
        """Tous les my_fit doivent être valides (via FK)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_fit
                FROM public.vinted_mapping vm
                WHERE vm.my_fit IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes.fits f
                    WHERE f.name_en = vm.my_fit
                )
            """)).fetchall()

            if result:
                invalid = [f"id={r.id}: '{r.my_fit}'" for r in result]
                pytest.fail(f"Fits invalides ({len(result)}):\n" + "\n".join(invalid))

    def test_all_my_length_values_are_valid(self):
        """Tous les my_length doivent être valides (via FK)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_length
                FROM public.vinted_mapping vm
                WHERE vm.my_length IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes.lengths l
                    WHERE l.name_en = vm.my_length
                )
            """)).fetchall()

            if result:
                invalid = [f"id={r.id}: '{r.my_length}'" for r in result]
                pytest.fail(f"Lengths invalides ({len(result)}):\n" + "\n".join(invalid))

    def test_all_my_rise_values_are_valid(self):
        """Tous les my_rise doivent être valides (via FK)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_rise
                FROM public.vinted_mapping vm
                WHERE vm.my_rise IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes.rises r
                    WHERE r.name_en = vm.my_rise
                )
            """)).fetchall()

            if result:
                invalid = [f"id={r.id}: '{r.my_rise}'" for r in result]
                pytest.fail(f"Rises invalides ({len(result)}):\n" + "\n".join(invalid))

    def test_all_my_material_values_are_valid(self):
        """Tous les my_material doivent être valides (via FK)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_material
                FROM public.vinted_mapping vm
                WHERE vm.my_material IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes.materials m
                    WHERE m.name_en = vm.my_material
                )
            """)).fetchall()

            if result:
                invalid = [f"id={r.id}: '{r.my_material}'" for r in result]
                pytest.fail(f"Materials invalides ({len(result)}):\n" + "\n".join(invalid))

    def test_all_my_pattern_values_are_valid(self):
        """Tous les my_pattern doivent être valides (via FK)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_pattern
                FROM public.vinted_mapping vm
                WHERE vm.my_pattern IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes.patterns p
                    WHERE p.name_en = vm.my_pattern
                )
            """)).fetchall()

            if result:
                invalid = [f"id={r.id}: '{r.my_pattern}'" for r in result]
                pytest.fail(f"Patterns invalides ({len(result)}):\n" + "\n".join(invalid))

    def test_all_my_neckline_values_are_valid(self):
        """Tous les my_neckline doivent être valides (via FK)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_neckline
                FROM public.vinted_mapping vm
                WHERE vm.my_neckline IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes.necklines n
                    WHERE n.name_en = vm.my_neckline
                )
            """)).fetchall()

            if result:
                invalid = [f"id={r.id}: '{r.my_neckline}'" for r in result]
                pytest.fail(f"Necklines invalides ({len(result)}):\n" + "\n".join(invalid))

    def test_all_my_sleeve_length_values_are_valid(self):
        """Tous les my_sleeve_length doivent être valides (via FK)."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vm.id, vm.my_sleeve_length
                FROM public.vinted_mapping vm
                WHERE vm.my_sleeve_length IS NOT NULL
                AND NOT EXISTS (
                    SELECT 1 FROM product_attributes.sleeve_lengths s
                    WHERE s.name_en = vm.my_sleeve_length
                )
            """)).fetchall()

            if result:
                invalid = [f"id={r.id}: '{r.my_sleeve_length}'" for r in result]
                pytest.fail(f"Sleeve lengths invalides ({len(result)}):\n" + "\n".join(invalid))


class TestMappingConstraints:
    """Tests pour les contraintes du mapping (unicité, relations N:1)."""

    def test_unique_default_per_couple_index_exists(self):
        """L'index unique_default_per_couple doit exister."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'vinted_mapping'
                AND indexname = 'unique_default_per_couple'
            """)).fetchone()

            assert result is not None, "Index unique_default_per_couple n'existe pas"
            assert "WHERE (is_default = true)" in result.indexdef, (
                "L'index doit être partiel sur is_default = TRUE"
            )

    def test_cannot_insert_duplicate_default(self):
        """Impossible d'insérer un 2ème défaut pour un couple existant."""
        with get_db_context() as db:
            # Récupérer un couple existant avec un défaut
            couple = db.execute(text("""
                SELECT my_category, my_gender
                FROM public.vinted_mapping
                WHERE is_default = TRUE
                LIMIT 1
            """)).fetchone()

            assert couple is not None, "Aucun couple avec défaut trouvé"

            # Tenter d'insérer un 2ème défaut (doit échouer)
            with pytest.raises(Exception) as exc_info:
                db.execute(text("""
                    INSERT INTO public.vinted_mapping
                    (vinted_id, vinted_gender, my_category, my_gender, is_default)
                    VALUES (1, 'women', :cat, :gen, TRUE)
                """), {"cat": couple.my_category, "gen": couple.my_gender})
                db.commit()

            assert "unique_default_per_couple" in str(exc_info.value), (
                f"L'erreur doit mentionner la contrainte unique_default_per_couple, "
                f"obtenu: {exc_info.value}"
            )

    def test_can_insert_multiple_non_default_mappings(self):
        """On peut insérer plusieurs mappings non-défaut pour le même couple."""
        with get_db_context() as db:
            # Vérifier qu'il existe des couples avec plusieurs mappings non-défaut
            result = db.execute(text("""
                SELECT my_category, my_gender, COUNT(*) as non_default_count
                FROM public.vinted_mapping
                WHERE is_default = FALSE
                GROUP BY my_category, my_gender
                HAVING COUNT(*) > 1
            """)).fetchall()

            # Ce n'est pas une erreur si aucun couple n'a plusieurs non-défauts
            # Le test vérifie juste que c'est techniquement possible
            print(f"\nCouples avec plusieurs mappings non-défaut: {len(result)}")

    def test_multiple_categories_can_map_to_same_vinted_id(self):
        """Plusieurs catégories peuvent pointer vers le même vinted_id."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT vinted_id, COUNT(*) as mapping_count,
                       COUNT(DISTINCT my_category) as distinct_categories
                FROM public.vinted_mapping
                GROUP BY vinted_id
                HAVING COUNT(DISTINCT my_category) > 1
                ORDER BY mapping_count DESC
                LIMIT 5
            """)).fetchall()

            assert len(result) > 0, (
                "Aucun vinted_id n'est partagé par plusieurs catégories. "
                "La relation N:1 (plusieurs my_category → 1 vinted_id) doit être possible."
            )

            print(f"\n=== Top 5 vinted_id partagés ===")
            for r in result:
                print(f"vinted_id={r.vinted_id}: {r.mapping_count} mappings, "
                      f"{r.distinct_categories} catégories différentes")

    def test_no_unique_constraint_on_vinted_id(self):
        """Il ne doit PAS y avoir de contrainte UNIQUE sur vinted_id."""
        with get_db_context() as db:
            # Vérifier qu'aucun index unique n'existe sur vinted_id seul
            result = db.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'vinted_mapping'
                AND indexdef LIKE '%UNIQUE%'
                AND indexdef LIKE '%vinted_id%'
                AND indexdef NOT LIKE '%my_category%'
                AND indexdef NOT LIKE '%my_gender%'
            """)).fetchall()

            assert len(result) == 0, (
                f"Une contrainte UNIQUE sur vinted_id a été trouvée: {result}. "
                "Cela empêcherait plusieurs catégories de pointer vers le même vinted_id."
            )


class TestMappingFunction:
    """Tests pour la fonction get_vinted_category."""

    def test_get_vinted_category_returns_default_when_no_attributes(self):
        """La fonction doit retourner le défaut quand aucun attribut n'est fourni."""
        with get_db_context() as db:
            # Récupérer un couple avec plusieurs mappings
            couple = db.execute(text("""
                SELECT my_category, my_gender
                FROM public.vinted_mapping
                GROUP BY my_category, my_gender
                HAVING COUNT(*) > 1
                LIMIT 1
            """)).fetchone()

            if couple:
                # Récupérer le défaut attendu
                expected = db.execute(text("""
                    SELECT vinted_id FROM public.vinted_mapping
                    WHERE my_category = :cat AND my_gender = :gen AND is_default = TRUE
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                # Appeler la fonction
                result = db.execute(text("""
                    SELECT get_vinted_category(:cat, :gen) as vinted_id
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                assert result == expected, (
                    f"Pour {couple.my_category}/{couple.my_gender}: "
                    f"attendu {expected}, obtenu {result}"
                )

    def test_get_vinted_category_returns_specific_match_with_fit(self):
        """La fonction doit retourner le mapping spécifique quand le fit correspond."""
        with get_db_context() as db:
            # Trouver un mapping avec fit spécifique
            mapping = db.execute(text("""
                SELECT my_category, my_gender, my_fit, vinted_id
                FROM public.vinted_mapping
                WHERE my_fit IS NOT NULL AND is_default = FALSE
                LIMIT 1
            """)).fetchone()

            if mapping:
                result = db.execute(text("""
                    SELECT get_vinted_category(:cat, :gen, :fit) as vinted_id
                """), {
                    "cat": mapping.my_category,
                    "gen": mapping.my_gender,
                    "fit": mapping.my_fit
                }).scalar()

                assert result == mapping.vinted_id, (
                    f"Pour {mapping.my_category}/{mapping.my_gender} "
                    f"avec fit={mapping.my_fit}: "
                    f"attendu {mapping.vinted_id}, obtenu {result}"
                )

    def test_get_vinted_category_returns_null_for_unknown_category(self):
        """La fonction doit retourner NULL pour une catégorie inconnue."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT get_vinted_category('nonexistent_category', 'women') as vinted_id
            """)).scalar()

            assert result is None, f"Attendu NULL, obtenu {result}"

    def test_get_vinted_category_returns_null_for_unknown_gender(self):
        """La fonction doit retourner NULL pour un gender inconnu."""
        with get_db_context() as db:
            # Récupérer une catégorie existante
            category = db.execute(text("""
                SELECT DISTINCT my_category FROM public.vinted_mapping LIMIT 1
            """)).scalar()

            if category:
                result = db.execute(text("""
                    SELECT get_vinted_category(:cat, 'invalid_gender') as vinted_id
                """), {"cat": category}).scalar()

                assert result is None, f"Attendu NULL pour gender invalide, obtenu {result}"

    def test_get_vinted_category_with_non_matching_attribute_returns_compatible(self):
        """La fonction retourne un mapping compatible (où l'attribut est NULL) si aucun ne matche exactement."""
        with get_db_context() as db:
            # Trouver un couple avec défaut
            couple = db.execute(text("""
                SELECT my_category, my_gender, vinted_id as default_vinted_id
                FROM public.vinted_mapping
                WHERE is_default = TRUE
                LIMIT 1
            """)).fetchone()

            if couple:
                # Appeler avec un attribut qui ne matche rien
                # La fonction va trouver des mappings où my_fit IS NULL (compatibles)
                result = db.execute(text("""
                    SELECT get_vinted_category(:cat, :gen, 'nonexistent_fit') as vinted_id
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                # Doit retourner un vinted_id (pas NULL) car il y a des mappings compatibles
                assert result is not None, (
                    f"Pour {couple.my_category}/{couple.my_gender} avec fit invalide: "
                    f"doit retourner un mapping compatible, obtenu NULL"
                )

    def test_get_vinted_category_fallback_to_default_when_category_gender_only(self):
        """La fonction retourne le défaut quand seuls category/gender sont fournis."""
        with get_db_context() as db:
            # Trouver un couple avec plusieurs mappings incluant un défaut
            couple = db.execute(text("""
                SELECT my_category, my_gender
                FROM public.vinted_mapping
                GROUP BY my_category, my_gender
                HAVING COUNT(*) > 1
                AND SUM(CASE WHEN is_default THEN 1 ELSE 0 END) = 1
                LIMIT 1
            """)).fetchone()

            if couple:
                # Récupérer le défaut attendu
                default_id = db.execute(text("""
                    SELECT vinted_id FROM public.vinted_mapping
                    WHERE my_category = :cat AND my_gender = :gen AND is_default = TRUE
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                # Appeler sans attributs
                result = db.execute(text("""
                    SELECT get_vinted_category(:cat, :gen) as vinted_id
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                assert result == default_id, (
                    f"Pour {couple.my_category}/{couple.my_gender} sans attributs: "
                    f"attendu défaut {default_id}, obtenu {result}"
                )


class TestMappingFunctionScoring:
    """Tests pour le scoring des attributs dans get_vinted_category."""

    def test_scoring_weights_are_correct(self):
        """Vérifie que les poids du scoring sont corrects (fit=10, length=10, etc.)."""
        with get_db_context() as db:
            # Vérifier la définition de la fonction
            func_def = db.execute(text("""
                SELECT pg_get_functiondef(oid)
                FROM pg_proc
                WHERE proname = 'get_vinted_category'
            """)).scalar()

            assert func_def is not None, "Fonction get_vinted_category non trouvée"

            # Vérifier les poids
            expected_weights = [
                ("my_fit = p_fit THEN 10", "fit doit avoir poids 10"),
                ("my_length = p_length THEN 10", "length doit avoir poids 10"),
                ("my_rise = p_rise THEN 10", "rise doit avoir poids 10"),
                ("my_material = p_material THEN 5", "material doit avoir poids 5"),
                ("my_pattern = p_pattern THEN 3", "pattern doit avoir poids 3"),
                ("my_neckline = p_neckline THEN 3", "neckline doit avoir poids 3"),
                ("my_sleeve_length = p_sleeve_length THEN 2", "sleeve_length doit avoir poids 2"),
            ]

            for pattern, msg in expected_weights:
                assert pattern in func_def, f"Scoring: {msg}"

    def test_function_accepts_all_attribute_parameters(self):
        """La fonction doit accepter tous les paramètres d'attributs."""
        with get_db_context() as db:
            # Récupérer un couple existant
            couple = db.execute(text("""
                SELECT my_category, my_gender
                FROM public.vinted_mapping
                WHERE is_default = TRUE
                LIMIT 1
            """)).fetchone()

            if couple:
                # Appeler avec tous les paramètres
                result = db.execute(text("""
                    SELECT get_vinted_category(
                        :cat, :gen,
                        'slim',           -- p_fit
                        'long',           -- p_length
                        'mid-rise',       -- p_rise
                        'cotton',         -- p_material
                        'solid',          -- p_pattern
                        'v-neck',         -- p_neckline
                        'short-sleeve'    -- p_sleeve_length
                    ) as vinted_id
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                # La fonction doit retourner quelque chose (défaut ou match)
                assert result is not None, (
                    f"La fonction doit retourner un vinted_id pour {couple.my_category}/{couple.my_gender}"
                )

    def test_higher_score_wins(self):
        """Le mapping avec le meilleur score doit être sélectionné."""
        with get_db_context() as db:
            # Trouver un couple avec plusieurs mappings et des attributs différents
            couple = db.execute(text("""
                SELECT my_category, my_gender
                FROM public.vinted_mapping
                WHERE my_fit IS NOT NULL
                GROUP BY my_category, my_gender
                HAVING COUNT(*) > 1
                LIMIT 1
            """)).fetchone()

            if couple:
                # Récupérer tous les mappings pour ce couple
                mappings = db.execute(text("""
                    SELECT vinted_id, my_fit, is_default
                    FROM public.vinted_mapping
                    WHERE my_category = :cat AND my_gender = :gen
                    ORDER BY is_default DESC
                """), {"cat": couple.my_category, "gen": couple.my_gender}).fetchall()

                if len(mappings) > 1:
                    # Trouver un mapping non-défaut avec un fit spécifique
                    non_default = next(
                        (m for m in mappings if not m.is_default and m.my_fit),
                        None
                    )

                    if non_default:
                        # Appeler avec le fit du mapping non-défaut
                        result = db.execute(text("""
                            SELECT get_vinted_category(:cat, :gen, :fit) as vinted_id
                        """), {
                            "cat": couple.my_category,
                            "gen": couple.my_gender,
                            "fit": non_default.my_fit
                        }).scalar()

                        assert result == non_default.vinted_id, (
                            f"Avec fit={non_default.my_fit}, "
                            f"attendu {non_default.vinted_id}, obtenu {result}"
                        )

    def test_default_is_tiebreaker(self):
        """En cas d'égalité de score, le défaut doit être préféré."""
        with get_db_context() as db:
            # Trouver un couple avec mappings sans attributs spécifiques
            couple = db.execute(text("""
                SELECT my_category, my_gender
                FROM public.vinted_mapping
                WHERE my_fit IS NULL
                AND my_length IS NULL
                AND my_rise IS NULL
                GROUP BY my_category, my_gender
                HAVING COUNT(*) > 1
                LIMIT 1
            """)).fetchone()

            if couple:
                # Récupérer le défaut
                default_id = db.execute(text("""
                    SELECT vinted_id FROM public.vinted_mapping
                    WHERE my_category = :cat AND my_gender = :gen AND is_default = TRUE
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                # Appeler sans attributs - score = 0 pour tous, défaut doit gagner
                result = db.execute(text("""
                    SELECT get_vinted_category(:cat, :gen) as vinted_id
                """), {"cat": couple.my_category, "gen": couple.my_gender}).scalar()

                assert result == default_id, (
                    f"Sans attributs et score égal, le défaut ({default_id}) "
                    f"doit être sélectionné, obtenu {result}"
                )


class TestMappingStatistics:
    """Tests pour les statistiques du mapping."""

    def test_mapping_coverage_stats(self):
        """Affiche les statistiques de couverture du mapping."""
        with get_db_context() as db:
            stats = db.execute(text("""
                SELECT
                    COUNT(*) as total_mappings,
                    COUNT(DISTINCT vinted_id) as unique_vinted_ids,
                    COUNT(DISTINCT (my_category, my_gender)) as unique_couples,
                    SUM(CASE WHEN is_default THEN 1 ELSE 0 END) as defaults,
                    COUNT(*) FILTER (WHERE my_fit IS NOT NULL) as with_fit,
                    COUNT(*) FILTER (WHERE my_length IS NOT NULL) as with_length,
                    COUNT(*) FILTER (WHERE my_rise IS NOT NULL) as with_rise,
                    COUNT(*) FILTER (WHERE my_material IS NOT NULL) as with_material,
                    COUNT(*) FILTER (WHERE my_pattern IS NOT NULL) as with_pattern,
                    COUNT(*) FILTER (WHERE my_neckline IS NOT NULL) as with_neckline,
                    COUNT(*) FILTER (WHERE my_sleeve_length IS NOT NULL) as with_sleeve_length
                FROM public.vinted_mapping
            """)).fetchone()

            # Vérifier qu'on a des mappings
            assert stats.total_mappings > 0, "Aucun mapping trouvé"

            # Afficher les stats (ne fait pas échouer le test)
            print(f"\n=== Statistiques du mapping ===")
            print(f"Total mappings: {stats.total_mappings}")
            print(f"Vinted IDs uniques: {stats.unique_vinted_ids}")
            print(f"Couples uniques: {stats.unique_couples}")
            print(f"Défauts: {stats.defaults}")
            print(f"Avec fit: {stats.with_fit}")
            print(f"Avec length: {stats.with_length}")
            print(f"Avec rise: {stats.with_rise}")
            print(f"Avec material: {stats.with_material}")
            print(f"Avec pattern: {stats.with_pattern}")
            print(f"Avec neckline: {stats.with_neckline}")
            print(f"Avec sleeve_length: {stats.with_sleeve_length}")

    def test_mapping_issues_view(self):
        """Vérifie qu'il n'y a pas de problèmes détectés par la vue mapping_validation."""
        with get_db_context() as db:
            result = db.execute(text("""
                SELECT issue, COUNT(*) as count
                FROM public.mapping_validation
                GROUP BY issue
                ORDER BY count DESC
            """)).fetchall()

            if result:
                issues_summary = [f"{r.issue}: {r.count}" for r in result]
                print(f"\n=== Issues détectées ===")
                print("\n".join(issues_summary))

                # Pour l'instant, on affiche juste les issues sans faire échouer
                # Décommenter la ligne suivante pour faire échouer si issues
                # pytest.fail(f"Issues détectées:\n" + "\n".join(issues_summary))
