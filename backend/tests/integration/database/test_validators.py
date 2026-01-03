"""
Tests pour AttributeValidator

Vérifie que la validation générique des attributs fonctionne correctement.
"""

import pytest
from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.category import Category
from models.public.condition import Condition
from services.validators import AttributeValidator


def test_validate_attribute_existing_brand(db_session: Session, seed_attributes):
    """Test validation d'une marque existante."""
    # Levi's existe dans seed_attributes
    AttributeValidator.validate_attribute(db_session, 'brand', "Levi's")
    # Pas d'exception = succès


def test_validate_attribute_nonexistent_brand(db_session: Session, seed_attributes):
    """Test validation d'une marque inexistante."""
    with pytest.raises(ValueError) as exc:
        AttributeValidator.validate_attribute(db_session, 'brand', 'NonExistentBrand')

    assert 'does not exist' in str(exc.value)
    assert '/api/attributes/brands' in str(exc.value)


def test_validate_attribute_optional_none(db_session: Session):
    """Test qu'un attribut optionnel peut être None."""
    # Brand est optionnel → None devrait être accepté
    AttributeValidator.validate_attribute(db_session, 'brand', None)
    # Pas d'exception = succès


def test_validate_attribute_required_none(db_session: Session):
    """Test qu'un attribut requis ne peut pas être None."""
    # Category est requis → None devrait lever une erreur
    with pytest.raises(ValueError) as exc:
        AttributeValidator.validate_attribute(db_session, 'category', None)

    assert 'required' in str(exc.value).lower()


def test_validate_attribute_unknown_attribute(db_session: Session):
    """Test validation d'un attribut non configuré."""
    with pytest.raises(KeyError) as exc:
        AttributeValidator.validate_attribute(db_session, 'invalid_attribute', 'value')

    assert 'Unknown attribute' in str(exc.value)


def test_validate_product_attributes_complete_valid(db_session: Session, seed_attributes):
    """Test validation complète avec toutes données valides."""
    data = {
        'category': 'Jeans',
        'condition': 'GOOD',
        'brand': "Levi's",
        'color': 'Blue',
        'size_original': 'M',
        'material': 'Cotton',
        'fit': 'Slim',
        'gender': 'Men',
        'season': 'All-Season'
    }

    # Ne devrait pas lever d'exception
    AttributeValidator.validate_product_attributes(db_session, data)


def test_validate_product_attributes_missing_required(db_session: Session, seed_attributes):
    """Test validation complète avec attribut requis manquant."""
    data = {
        # 'category': manquant (requis!)
        'condition': 'GOOD',
        'brand': "Levi's"
    }

    with pytest.raises(ValueError) as exc:
        AttributeValidator.validate_product_attributes(db_session, data)

    assert 'required' in str(exc.value).lower()
    assert 'Category' in str(exc.value)


def test_validate_product_attributes_invalid_value(db_session: Session, seed_attributes):
    """Test validation complète avec valeur invalide."""
    data = {
        'category': 'Jeans',
        'condition': 'GOOD',
        'brand': 'InvalidBrand'  # N'existe pas
    }

    with pytest.raises(ValueError) as exc:
        AttributeValidator.validate_product_attributes(db_session, data)

    assert 'InvalidBrand' in str(exc.value)
    assert 'does not exist' in str(exc.value)


def test_validate_product_attributes_partial_mode(db_session: Session, seed_attributes):
    """Test validation partielle (mode update)."""
    data = {
        'brand': "Levi's"  # Seul attribut modifié
        # Les autres attributs absents mais c'est OK en mode partial
    }

    # Ne devrait pas lever d'exception
    AttributeValidator.validate_product_attributes(db_session, data, partial=True)


def test_validate_product_attributes_partial_invalid(db_session: Session, seed_attributes):
    """Test validation partielle avec valeur invalide."""
    data = {
        'brand': 'InvalidBrand'
    }

    with pytest.raises(ValueError) as exc:
        AttributeValidator.validate_product_attributes(db_session, data, partial=True)

    assert 'InvalidBrand' in str(exc.value)


def test_get_attribute_list_brands(db_session: Session, seed_attributes):
    """Test récupération de la liste des marques."""
    brands = AttributeValidator.get_attribute_list(db_session, 'brand')

    assert isinstance(brands, list)
    assert len(brands) > 0
    assert "Levi's" in brands


def test_get_attribute_list_unknown_type(db_session: Session):
    """Test récupération liste avec type inconnu."""
    with pytest.raises(KeyError) as exc:
        AttributeValidator.get_attribute_list(db_session, 'invalid_type')

    assert 'Unknown attribute type' in str(exc.value)


def test_attribute_exists_true(db_session: Session, seed_attributes):
    """Test vérification existence d'un attribut existant."""
    assert AttributeValidator.attribute_exists(db_session, 'brand', "Levi's") is True


def test_attribute_exists_false(db_session: Session, seed_attributes):
    """Test vérification existence d'un attribut inexistant."""
    assert AttributeValidator.attribute_exists(db_session, 'brand', 'InvalidBrand') is False


def test_attribute_exists_invalid_type(db_session: Session):
    """Test vérification existence avec type invalide."""
    assert AttributeValidator.attribute_exists(db_session, 'invalid_type', 'value') is False


def test_validates_all_9_attributes(db_session: Session, seed_attributes):
    """
    Test critique: vérifier que les 9 attributs sont validés.

    Ce test garantit qu'aucun attribut n'est oublié dans la configuration.
    """
    expected_attributes = {
        'category', 'condition',  # Required
        'brand', 'color', 'size_original', 'material', 'fit', 'gender', 'season'  # Optional
    }

    configured_attributes = set(AttributeValidator.ATTRIBUTE_CONFIGS.keys())

    assert configured_attributes == expected_attributes, (
        f"Mismatch in configured attributes. "
        f"Missing: {expected_attributes - configured_attributes}, "
        f"Extra: {configured_attributes - expected_attributes}"
    )
