"""
Unit Tests - SizeOriginalRepository

Tests unitaires pour le repository SizeOriginalRepository.

Tests:
- Normalisation des noms de tailles
- Auto-création de tailles (get_or_create)
- Lookup case-insensitive
- CRUD operations
"""

import pytest
from sqlalchemy.orm import Session

from models.public.size_original import SizeOriginal
from repositories.size_original_repository import SizeOriginalRepository


class TestSizeOriginalRepositoryNormalization:
    """Tests pour la normalisation des noms de tailles."""

    def test_normalize_name_uppercase_w_l_pattern(self):
        """Test normalisation pattern W/L (jeans)."""
        assert SizeOriginalRepository.normalize_name("w32/l34") == "W32/L34"
        assert SizeOriginalRepository.normalize_name("  W32/L34  ") == "W32/L34"
        assert SizeOriginalRepository.normalize_name("w28/l30") == "W28/L30"

    def test_normalize_name_preserve_other_cases(self):
        """Test préservation autres tailles."""
        assert SizeOriginalRepository.normalize_name("M") == "M"
        assert SizeOriginalRepository.normalize_name("42 EU") == "42 EU"
        assert SizeOriginalRepository.normalize_name("Small") == "Small"

    def test_normalize_name_strip_whitespace(self):
        """Test suppression espaces."""
        assert SizeOriginalRepository.normalize_name("  M  ") == "M"
        assert SizeOriginalRepository.normalize_name("\t42 EU\n") == "42 EU"


class TestSizeOriginalRepositoryGetOrCreate:
    """Tests pour get_or_create."""

    def test_get_or_create_new_size(self, db_session: Session):
        """Test création nouvelle taille."""
        size = SizeOriginalRepository.get_or_create(db_session, "W32/L34")

        assert size is not None
        assert size.name == "W32/L34"

        # Vérifier en DB
        db_size = db_session.query(SizeOriginal).filter(
            SizeOriginal.name == "W32/L34"
        ).first()
        assert db_size is not None
        assert db_size.name == "W32/L34"

    def test_get_or_create_existing_size(self, db_session: Session):
        """Test récupération taille existante."""
        # Créer première fois
        size1 = SizeOriginalRepository.get_or_create(db_session, "M")

        # Récupérer (pas créer)
        size2 = SizeOriginalRepository.get_or_create(db_session, "M")

        assert size1.name == size2.name
        assert size1.created_at == size2.created_at

        # Vérifier qu'il n'y a qu'une seule entrée
        count = db_session.query(SizeOriginal).filter(
            SizeOriginal.name == "M"
        ).count()
        assert count == 1

    def test_get_or_create_case_insensitive(self, db_session: Session):
        """Test évite duplicates case-insensitive."""
        # Créer avec lowercase
        size1 = SizeOriginalRepository.get_or_create(db_session, "w32/l34")

        # Récupérer avec uppercase
        size2 = SizeOriginalRepository.get_or_create(db_session, "W32/L34")

        # Doit être la même taille (normalisée en W32/L34)
        assert size1.name == size2.name
        assert size1.name == "W32/L34"

        # Vérifier qu'il n'y a qu'une seule entrée
        count = db_session.query(SizeOriginal).count()
        assert count == 1

    def test_get_or_create_with_mixed_case(self, db_session: Session):
        """Test création avec casse mixte."""
        size1 = SizeOriginalRepository.get_or_create(db_session, "m")
        size2 = SizeOriginalRepository.get_or_create(db_session, "M")

        # Les deux doivent pointer vers la même taille
        assert size1.name == size2.name


class TestSizeOriginalRepositoryGetByName:
    """Tests pour get_by_name."""

    def test_get_by_name_existing(self, db_session: Session):
        """Test récupération taille existante."""
        # Créer taille
        SizeOriginalRepository.get_or_create(db_session, "L")

        # Récupérer
        size = SizeOriginalRepository.get_by_name(db_session, "L")

        assert size is not None
        assert size.name == "L"

    def test_get_by_name_not_found(self, db_session: Session):
        """Test taille non trouvée."""
        size = SizeOriginalRepository.get_by_name(db_session, "XXL")

        assert size is None

    def test_get_by_name_exact_match(self, db_session: Session):
        """Test match exact uniquement."""
        # Créer W32/L34
        SizeOriginalRepository.get_or_create(db_session, "W32/L34")

        # Recherche exacte
        size_exact = SizeOriginalRepository.get_by_name(db_session, "W32/L34")
        assert size_exact is not None

        # Recherche avec casse différente (pas trouvé)
        size_case = SizeOriginalRepository.get_by_name(db_session, "w32/l34")
        assert size_case is None


class TestSizeOriginalRepositoryGetByNameCaseInsensitive:
    """Tests pour get_by_name_case_insensitive."""

    def test_get_by_name_case_insensitive_found(self, db_session: Session):
        """Test lookup case-insensitive."""
        # Créer avec uppercase
        SizeOriginalRepository.get_or_create(db_session, "W32/L34")

        # Recherche avec lowercase
        size = SizeOriginalRepository.get_by_name_case_insensitive(
            db_session, "w32/l34"
        )

        assert size is not None
        assert size.name == "W32/L34"

    def test_get_by_name_case_insensitive_not_found(self, db_session: Session):
        """Test taille non trouvée."""
        size = SizeOriginalRepository.get_by_name_case_insensitive(
            db_session, "XXL"
        )

        assert size is None


class TestSizeOriginalRepositoryListAll:
    """Tests pour list_all."""

    def test_list_all_empty(self, db_session: Session):
        """Test liste vide."""
        sizes = SizeOriginalRepository.list_all(db_session)

        assert sizes == []

    def test_list_all_with_sizes(self, db_session: Session):
        """Test liste avec tailles."""
        # Créer plusieurs tailles
        SizeOriginalRepository.get_or_create(db_session, "S")
        SizeOriginalRepository.get_or_create(db_session, "M")
        SizeOriginalRepository.get_or_create(db_session, "L")

        sizes = SizeOriginalRepository.list_all(db_session)

        assert len(sizes) == 3
        size_names = [s.name for s in sizes]
        assert "S" in size_names
        assert "M" in size_names
        assert "L" in size_names

    def test_list_all_ordered_by_created_at_desc(self, db_session: Session):
        """Test ordre décroissant par date de création."""
        # Créer dans un ordre
        size1 = SizeOriginalRepository.get_or_create(db_session, "S")
        size2 = SizeOriginalRepository.get_or_create(db_session, "M")
        size3 = SizeOriginalRepository.get_or_create(db_session, "L")

        sizes = SizeOriginalRepository.list_all(db_session)

        # Plus récentes d'abord
        assert sizes[0].name == "L"
        assert sizes[1].name == "M"
        assert sizes[2].name == "S"

    def test_list_all_with_limit(self, db_session: Session):
        """Test limite de résultats."""
        # Créer 5 tailles
        for name in ["XS", "S", "M", "L", "XL"]:
            SizeOriginalRepository.get_or_create(db_session, name)

        sizes = SizeOriginalRepository.list_all(db_session, limit=3)

        assert len(sizes) == 3


class TestSizeOriginalRepositoryCount:
    """Tests pour count."""

    def test_count_zero(self, db_session: Session):
        """Test comptage zéro."""
        count = SizeOriginalRepository.count(db_session)

        assert count == 0

    def test_count_with_sizes(self, db_session: Session):
        """Test comptage avec tailles."""
        SizeOriginalRepository.get_or_create(db_session, "S")
        SizeOriginalRepository.get_or_create(db_session, "M")
        SizeOriginalRepository.get_or_create(db_session, "L")

        count = SizeOriginalRepository.count(db_session)

        assert count == 3


class TestSizeOriginalRepositoryDelete:
    """Tests pour delete_by_name."""

    def test_delete_by_name_existing(self, db_session: Session):
        """Test suppression taille existante."""
        # Créer taille
        SizeOriginalRepository.get_or_create(db_session, "M")

        # Supprimer
        result = SizeOriginalRepository.delete_by_name(db_session, "M")

        assert result is True

        # Vérifier suppression
        size = SizeOriginalRepository.get_by_name(db_session, "M")
        assert size is None

    def test_delete_by_name_not_found(self, db_session: Session):
        """Test suppression taille non trouvée."""
        result = SizeOriginalRepository.delete_by_name(db_session, "XXL")

        assert result is False
