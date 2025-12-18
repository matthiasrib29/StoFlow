"""
Tests unitaires pour le module ownership.

Couverture:
- check_resource_ownership (USER, ADMIN, SUPPORT)
- ensure_user_owns_resource
- ensure_can_modify
- can_modify_resource
- can_view_resource

Author: Claude
Date: 2025-12-10
"""

import pytest
from unittest.mock import Mock
from fastapi import HTTPException

from shared.ownership import (
    check_resource_ownership,
    ensure_user_owns_resource,
    ensure_can_modify,
    can_modify_resource,
    can_view_resource,
)
from models.public.user import UserRole


def create_mock_user(user_id: int, role: UserRole) -> Mock:
    """Crée un mock utilisateur."""
    user = Mock()
    user.id = user_id
    user.role = role
    return user


class TestCheckResourceOwnership:
    """Tests pour la fonction check_resource_ownership."""

    def test_user_can_access_own_resource(self):
        """Test USER peut accéder à sa propre ressource."""
        user = create_mock_user(1, UserRole.USER)

        # Ne doit pas lever d'exception
        check_resource_ownership(user, resource_user_id=1)

    def test_user_cannot_access_other_resource(self):
        """Test USER ne peut pas accéder à la ressource d'un autre."""
        user = create_mock_user(1, UserRole.USER)

        with pytest.raises(HTTPException) as exc_info:
            check_resource_ownership(user, resource_user_id=2)

        assert exc_info.value.status_code == 403
        assert "accès" in exc_info.value.detail.lower()

    def test_admin_can_access_any_resource(self):
        """Test ADMIN peut accéder à toute ressource."""
        admin = create_mock_user(1, UserRole.ADMIN)

        # Ne doit pas lever d'exception pour une autre ressource
        check_resource_ownership(admin, resource_user_id=999)

    def test_admin_blocked_when_allow_admin_false(self):
        """Test ADMIN bloqué si allow_admin=False."""
        admin = create_mock_user(1, UserRole.ADMIN)

        with pytest.raises(HTTPException) as exc_info:
            check_resource_ownership(admin, resource_user_id=2, allow_admin=False)

        assert exc_info.value.status_code == 403

    def test_support_cannot_access_by_default(self):
        """Test SUPPORT ne peut pas accéder par défaut."""
        support = create_mock_user(1, UserRole.SUPPORT)

        with pytest.raises(HTTPException) as exc_info:
            check_resource_ownership(support, resource_user_id=2)

        assert exc_info.value.status_code == 403

    def test_support_can_access_when_allowed(self):
        """Test SUPPORT peut accéder si allow_support=True."""
        support = create_mock_user(1, UserRole.SUPPORT)

        # Ne doit pas lever d'exception
        check_resource_ownership(support, resource_user_id=2, allow_support=True)

    def test_custom_resource_type_in_error(self):
        """Test message d'erreur avec type de ressource personnalisé."""
        user = create_mock_user(1, UserRole.USER)

        with pytest.raises(HTTPException) as exc_info:
            check_resource_ownership(user, resource_user_id=2, resource_type="produit")

        assert "produit" in exc_info.value.detail


class TestEnsureUserOwnsResource:
    """Tests pour la fonction ensure_user_owns_resource."""

    def test_resource_with_user_id(self):
        """Test ressource avec user_id."""
        user = create_mock_user(1, UserRole.USER)
        resource = Mock()
        resource.user_id = 1

        # Ne doit pas lever d'exception
        ensure_user_owns_resource(user, resource)

    def test_resource_with_different_user_id(self):
        """Test ressource avec user_id différent."""
        user = create_mock_user(1, UserRole.USER)
        resource = Mock()
        resource.user_id = 2

        with pytest.raises(HTTPException) as exc_info:
            ensure_user_owns_resource(user, resource)

        assert exc_info.value.status_code == 403

    def test_resource_without_user_id_user_allowed(self):
        """Test ressource sans user_id (multi-tenant) - USER autorisé."""
        user = create_mock_user(1, UserRole.USER)
        resource = Mock(spec=[])  # Pas d'attribut user_id

        # Ne doit pas lever d'exception (isolation par schema)
        ensure_user_owns_resource(user, resource)

    def test_resource_without_user_id_admin_allowed(self):
        """Test ressource sans user_id - ADMIN autorisé."""
        admin = create_mock_user(1, UserRole.ADMIN)
        resource = Mock(spec=[])

        # Ne doit pas lever d'exception
        ensure_user_owns_resource(admin, resource)

    def test_resource_without_user_id_support_allowed(self):
        """Test ressource sans user_id - SUPPORT autorisé par défaut."""
        support = create_mock_user(1, UserRole.SUPPORT)
        resource = Mock(spec=[])

        # Ne doit pas lever d'exception
        ensure_user_owns_resource(support, resource)

    def test_resource_without_user_id_support_blocked(self):
        """Test ressource sans user_id - SUPPORT bloqué si allow_support=False."""
        support = create_mock_user(1, UserRole.SUPPORT)
        resource = Mock()
        resource.user_id = 999  # Ressource d'un autre

        with pytest.raises(HTTPException) as exc_info:
            ensure_user_owns_resource(support, resource, allow_support=False)

        assert exc_info.value.status_code == 403


class TestEnsureCanModify:
    """Tests pour la fonction ensure_can_modify."""

    def test_user_can_modify(self):
        """Test USER peut modifier."""
        user = create_mock_user(1, UserRole.USER)

        # Ne doit pas lever d'exception
        ensure_can_modify(user)

    def test_admin_can_modify(self):
        """Test ADMIN peut modifier."""
        admin = create_mock_user(1, UserRole.ADMIN)

        # Ne doit pas lever d'exception
        ensure_can_modify(admin)

    def test_support_cannot_modify(self):
        """Test SUPPORT ne peut pas modifier."""
        support = create_mock_user(1, UserRole.SUPPORT)

        with pytest.raises(HTTPException) as exc_info:
            ensure_can_modify(support)

        assert exc_info.value.status_code == 403
        assert "SUPPORT" in exc_info.value.detail
        assert "lecture seule" in exc_info.value.detail.lower()

    def test_custom_resource_type_in_error(self):
        """Test message d'erreur avec type de ressource personnalisé."""
        support = create_mock_user(1, UserRole.SUPPORT)

        with pytest.raises(HTTPException) as exc_info:
            ensure_can_modify(support, resource_type="commande")

        assert "commande" in exc_info.value.detail


class TestCanModifyResource:
    """Tests pour la fonction can_modify_resource."""

    def test_user_can_modify_own_resource(self):
        """Test USER peut modifier sa propre ressource."""
        user = create_mock_user(1, UserRole.USER)

        assert can_modify_resource(user, resource_user_id=1) is True

    def test_user_cannot_modify_other_resource(self):
        """Test USER ne peut pas modifier la ressource d'un autre."""
        user = create_mock_user(1, UserRole.USER)

        assert can_modify_resource(user, resource_user_id=2) is False

    def test_admin_can_modify_any_resource(self):
        """Test ADMIN peut modifier toute ressource."""
        admin = create_mock_user(1, UserRole.ADMIN)

        assert can_modify_resource(admin, resource_user_id=999) is True

    def test_support_cannot_modify_any_resource(self):
        """Test SUPPORT ne peut modifier aucune ressource."""
        support = create_mock_user(1, UserRole.SUPPORT)

        # Même sa propre ressource
        assert can_modify_resource(support, resource_user_id=1) is False
        # Ni celle d'un autre
        assert can_modify_resource(support, resource_user_id=2) is False


class TestCanViewResource:
    """Tests pour la fonction can_view_resource."""

    def test_user_can_view_own_resource(self):
        """Test USER peut consulter sa propre ressource."""
        user = create_mock_user(1, UserRole.USER)

        assert can_view_resource(user, resource_user_id=1) is True

    def test_user_cannot_view_other_resource(self):
        """Test USER ne peut pas consulter la ressource d'un autre."""
        user = create_mock_user(1, UserRole.USER)

        assert can_view_resource(user, resource_user_id=2) is False

    def test_admin_can_view_any_resource(self):
        """Test ADMIN peut consulter toute ressource."""
        admin = create_mock_user(1, UserRole.ADMIN)

        assert can_view_resource(admin, resource_user_id=999) is True

    def test_support_can_view_any_resource(self):
        """Test SUPPORT peut consulter toute ressource."""
        support = create_mock_user(1, UserRole.SUPPORT)

        assert can_view_resource(support, resource_user_id=999) is True


class TestRoleInteractions:
    """Tests pour les interactions entre rôles."""

    def test_admin_accessing_user_resource(self):
        """Test ADMIN accédant à une ressource USER."""
        admin = create_mock_user(1, UserRole.ADMIN)

        # Peut modifier
        assert can_modify_resource(admin, resource_user_id=2) is True
        # Peut voir
        assert can_view_resource(admin, resource_user_id=2) is True
        # Ne lève pas d'exception
        check_resource_ownership(admin, resource_user_id=2)

    def test_support_read_only_access(self):
        """Test SUPPORT accès lecture seule."""
        support = create_mock_user(1, UserRole.SUPPORT)

        # Peut voir
        assert can_view_resource(support, resource_user_id=2) is True
        # Ne peut pas modifier
        assert can_modify_resource(support, resource_user_id=2) is False

        # ensure_can_modify lève une exception
        with pytest.raises(HTTPException):
            ensure_can_modify(support)

    def test_user_strict_isolation(self):
        """Test USER isolation stricte."""
        user = create_mock_user(1, UserRole.USER)

        # Peut accéder à ses ressources
        assert can_view_resource(user, resource_user_id=1) is True
        assert can_modify_resource(user, resource_user_id=1) is True

        # Ne peut pas accéder aux ressources des autres
        assert can_view_resource(user, resource_user_id=2) is False
        assert can_modify_resource(user, resource_user_id=2) is False

        with pytest.raises(HTTPException):
            check_resource_ownership(user, resource_user_id=2)


class TestEdgeCases:
    """Tests pour les cas limites."""

    def test_same_user_id_different_roles(self):
        """Test même user_id avec différents rôles."""
        user1 = create_mock_user(1, UserRole.USER)
        user2 = create_mock_user(1, UserRole.ADMIN)
        user3 = create_mock_user(1, UserRole.SUPPORT)

        # USER peut modifier sa ressource
        assert can_modify_resource(user1, resource_user_id=1) is True
        # ADMIN aussi
        assert can_modify_resource(user2, resource_user_id=1) is True
        # SUPPORT non (même si c'est "sa" ressource)
        assert can_modify_resource(user3, resource_user_id=1) is False

    def test_resource_user_id_zero(self):
        """Test resource_user_id = 0."""
        user = create_mock_user(0, UserRole.USER)

        assert can_view_resource(user, resource_user_id=0) is True
        assert can_modify_resource(user, resource_user_id=0) is True

    def test_negative_user_ids(self):
        """Test user_ids négatifs."""
        user = create_mock_user(-1, UserRole.USER)

        assert can_view_resource(user, resource_user_id=-1) is True
        assert can_view_resource(user, resource_user_id=-2) is False
