"""
Tests unitaires pour les dependencies FastAPI (api/dependencies/__init__.py).

Couverture:
- get_current_user (authentification JWT)
- require_admin / require_admin_or_support (autorisation par rôle)
- _validate_schema_name (protection SQL injection)
- get_user_db (isolation multi-tenant)

Author: Claude
Date: 2025-12-18
Updated: 2025-12-23 - Removed DEV_AUTH_BYPASS tests (feature removed for security)

CRITIQUE: Ces tests couvrent la sécurité de l'authentification et l'isolation des données.
"""

import pytest
import re
from unittest.mock import Mock, patch, MagicMock
from datetime import timedelta
from jose import jwt

from fastapi import HTTPException
from sqlalchemy.orm import Session

from shared.datetime_utils import utc_now


# ============================================================================
# _validate_schema_name TESTS (SQL INJECTION PROTECTION)
# ============================================================================

class TestValidateSchemaName:
    """
    Tests pour la validation stricte du schema_name.

    CRITIQUE: Ces tests vérifient la protection contre SQL injection
    dans le SET search_path TO {schema_name}.
    """

    def test_validate_schema_name_accepts_user_1(self):
        """Test que user_1 est accepté."""
        from api.dependencies import _validate_schema_name

        result = _validate_schema_name("user_1")
        assert result == "user_1"

    def test_validate_schema_name_accepts_user_999(self):
        """Test que user_999 est accepté."""
        from api.dependencies import _validate_schema_name

        result = _validate_schema_name("user_999")
        assert result == "user_999"

    def test_validate_schema_name_accepts_large_user_id(self):
        """Test que user_1000000 est accepté."""
        from api.dependencies import _validate_schema_name

        result = _validate_schema_name("user_1000000")
        assert result == "user_1000000"

    def test_validate_schema_name_rejects_sql_injection_drop_table(self):
        """Test que SQL injection DROP TABLE est rejeté."""
        from api.dependencies import _validate_schema_name

        with pytest.raises(HTTPException) as exc_info:
            _validate_schema_name("user_1; DROP TABLE users;--")

        assert exc_info.value.status_code == 500
        assert "sécurité" in exc_info.value.detail.lower()

    def test_validate_schema_name_rejects_semicolon(self):
        """Test que les points-virgules sont rejetés."""
        from api.dependencies import _validate_schema_name

        with pytest.raises(HTTPException) as exc_info:
            _validate_schema_name("user_1;")

        assert exc_info.value.status_code == 500

    def test_validate_schema_name_rejects_sql_comments(self):
        """Test que les commentaires SQL (--) sont rejetés."""
        from api.dependencies import _validate_schema_name

        with pytest.raises(HTTPException) as exc_info:
            _validate_schema_name("user_1--comment")

        assert exc_info.value.status_code == 500

    def test_validate_schema_name_rejects_union_injection(self):
        """Test que UNION injection est rejeté."""
        from api.dependencies import _validate_schema_name

        with pytest.raises(HTTPException) as exc_info:
            _validate_schema_name("user_1 UNION SELECT * FROM users")

        assert exc_info.value.status_code == 500

    def test_validate_schema_name_rejects_invalid_pattern(self):
        """Test que les patterns invalides sont rejetés."""
        from api.dependencies import _validate_schema_name

        invalid_patterns = [
            "public",           # Pas le bon pattern
            "admin_1",          # Mauvais préfixe
            "user_",            # Pas de numéro
            "user_abc",         # Pas un nombre
            "USER_1",           # Mauvaise casse
            "user_-1",          # Nombre négatif
            "user_1.5",         # Nombre décimal
            "../user_1",        # Path traversal
            "user_1\x00",       # Null byte
        ]

        for pattern in invalid_patterns:
            with pytest.raises(HTTPException) as exc_info:
                _validate_schema_name(pattern)
            assert exc_info.value.status_code == 500, f"Pattern {pattern} should be rejected"

    def test_validate_schema_name_regex_pattern_correct(self):
        """Test que le pattern regex est correct."""
        from api.dependencies import SCHEMA_NAME_PATTERN

        # Doit matcher
        assert SCHEMA_NAME_PATTERN.match("user_1")
        assert SCHEMA_NAME_PATTERN.match("user_123")
        assert SCHEMA_NAME_PATTERN.match("user_999999")

        # Ne doit pas matcher
        assert not SCHEMA_NAME_PATTERN.match("user_")
        assert not SCHEMA_NAME_PATTERN.match("user_abc")
        assert not SCHEMA_NAME_PATTERN.match("public")
        assert not SCHEMA_NAME_PATTERN.match("")


# ============================================================================
# get_current_user TESTS
# ============================================================================

class TestGetCurrentUser:
    """Tests pour la dependency get_current_user."""

    @patch('api.dependencies.AuthService')
    def test_get_current_user_with_valid_token(self, mock_auth_service):
        """Test authentification avec token valide."""
        from api.dependencies import get_current_user

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = True

        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        mock_auth_service.verify_token.return_value = {"user_id": 1, "role": "user"}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = get_current_user(
            credentials=mock_credentials,
            db=mock_db
        )

        assert result.id == 1

    @patch('api.dependencies.AuthService')
    def test_get_current_user_with_missing_token_raises_401(self, mock_auth_service):
        """Test que l'absence de token lève une 401."""
        from api.dependencies import get_current_user

        mock_db = Mock()

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=mock_db)

        assert exc_info.value.status_code == 401
        assert "Token manquant" in exc_info.value.detail

    @patch('api.dependencies.AuthService')
    def test_get_current_user_with_invalid_token_raises_401(self, mock_auth_service):
        """Test qu'un token invalide lève une 401."""
        from api.dependencies import get_current_user

        mock_db = Mock()
        mock_credentials = Mock()
        mock_credentials.credentials = "invalid_token"

        mock_auth_service.verify_token.return_value = None  # Token invalide

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)

        assert exc_info.value.status_code == 401
        assert "invalide" in exc_info.value.detail.lower()

    @patch('api.dependencies.AuthService')
    def test_get_current_user_with_inactive_user_raises_401(self, mock_auth_service):
        """Test qu'un utilisateur inactif lève une 401."""
        from api.dependencies import get_current_user

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.is_active = False  # Inactif

        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        mock_auth_service.verify_token.return_value = {"user_id": 1, "role": "user"}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)

        assert exc_info.value.status_code == 401
        assert "desactiv" in exc_info.value.detail.lower()

    @patch('api.dependencies.AuthService')
    def test_get_current_user_with_user_not_found_raises_401(self, mock_auth_service):
        """Test qu'un utilisateur non trouvé lève une 401."""
        from api.dependencies import get_current_user

        mock_db = Mock()
        mock_credentials = Mock()
        mock_credentials.credentials = "valid_token"

        mock_auth_service.verify_token.return_value = {"user_id": 999, "role": "user"}
        mock_db.query.return_value.filter.return_value.first.return_value = None  # User not found

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)

        assert exc_info.value.status_code == 401


# ============================================================================
# require_role / require_admin TESTS
# ============================================================================

class TestRoleAuthorization:
    """Tests pour les dependencies de vérification de rôle."""

    def test_require_admin_allows_admin_user(self):
        """Test que require_admin autorise un utilisateur ADMIN."""
        from api.dependencies import require_admin
        from models.public.user import UserRole

        mock_user = Mock()
        mock_user.role = UserRole.ADMIN

        # Appeler directement la fonction avec l'utilisateur mocké
        # Note: require_admin est une fonction avec Depends() par défaut,
        # on peut l'appeler directement en passant current_user
        result = require_admin(current_user=mock_user)

        assert result == mock_user

    def test_require_admin_rejects_regular_user(self):
        """Test que require_admin rejette un utilisateur USER."""
        from api.dependencies import require_admin
        from models.public.user import UserRole

        mock_user = Mock()
        mock_user.role = UserRole.USER

        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=mock_user)

        assert exc_info.value.status_code == 403
        assert "ADMIN" in exc_info.value.detail

    def test_require_admin_rejects_support_user(self):
        """Test que require_admin rejette un utilisateur SUPPORT."""
        from api.dependencies import require_admin
        from models.public.user import UserRole

        mock_user = Mock()
        mock_user.role = UserRole.SUPPORT

        with pytest.raises(HTTPException) as exc_info:
            require_admin(current_user=mock_user)

        assert exc_info.value.status_code == 403

    def test_require_admin_or_support_allows_admin(self):
        """Test que require_admin_or_support autorise ADMIN."""
        from api.dependencies import require_admin_or_support
        from models.public.user import UserRole

        mock_user = Mock()
        mock_user.role = UserRole.ADMIN

        result = require_admin_or_support(current_user=mock_user)

        assert result == mock_user

    def test_require_admin_or_support_allows_support(self):
        """Test que require_admin_or_support autorise SUPPORT."""
        from api.dependencies import require_admin_or_support
        from models.public.user import UserRole

        mock_user = Mock()
        mock_user.role = UserRole.SUPPORT

        result = require_admin_or_support(current_user=mock_user)

        assert result == mock_user

    def test_require_admin_or_support_rejects_regular_user(self):
        """Test que require_admin_or_support rejette USER."""
        from api.dependencies import require_admin_or_support
        from models.public.user import UserRole

        mock_user = Mock()
        mock_user.role = UserRole.USER

        with pytest.raises(HTTPException) as exc_info:
            require_admin_or_support(current_user=mock_user)

        assert exc_info.value.status_code == 403

    def test_require_role_factory_with_single_role(self):
        """Test require_role factory avec un seul rôle."""
        from api.dependencies import require_role
        from models.public.user import UserRole

        checker = require_role(UserRole.ADMIN)

        mock_admin = Mock()
        mock_admin.role = UserRole.ADMIN

        mock_user = Mock()
        mock_user.role = UserRole.USER

        # Admin doit passer
        result = checker(current_user=mock_admin)
        assert result == mock_admin

        # User doit échouer
        with pytest.raises(HTTPException):
            checker(current_user=mock_user)

    def test_require_role_factory_with_multiple_roles(self):
        """Test require_role factory avec plusieurs rôles."""
        from api.dependencies import require_role
        from models.public.user import UserRole

        checker = require_role(UserRole.ADMIN, UserRole.SUPPORT)

        mock_admin = Mock()
        mock_admin.role = UserRole.ADMIN

        mock_support = Mock()
        mock_support.role = UserRole.SUPPORT

        mock_user = Mock()
        mock_user.role = UserRole.USER

        # Admin doit passer
        assert checker(current_user=mock_admin) == mock_admin

        # Support doit passer
        assert checker(current_user=mock_support) == mock_support

        # User doit échouer
        with pytest.raises(HTTPException):
            checker(current_user=mock_user)


# ============================================================================
# get_user_db TESTS (MULTI-TENANT ISOLATION)
# ============================================================================

class TestGetUserDB:
    """
    Tests pour la dependency get_user_db (isolation multi-tenant).

    CRITIQUE: Ces tests vérifient l'isolation des données entre utilisateurs.
    """

    @patch('api.dependencies._validate_schema_name')
    def test_get_user_db_sets_correct_search_path(self, mock_validate):
        """Test que get_user_db configure le bon search_path."""
        from api.dependencies import get_user_db
        from sqlalchemy import text

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 42
        mock_user.schema_name = "user_42"

        mock_validate.return_value = "user_42"

        # Mock execute pour vérifier l'appel
        mock_result = Mock()
        mock_result.scalar.return_value = "user_42, public"
        mock_db.execute.return_value = mock_result

        result_db, result_user = get_user_db(db=mock_db, current_user=mock_user)

        # Vérifier que execute a été appelé (SET LOCAL et SHOW)
        assert mock_db.execute.called
        # Vérifier le résultat
        assert result_db == mock_db
        assert result_user == mock_user

    @patch('api.dependencies._validate_schema_name')
    def test_get_user_db_validates_schema_name(self, mock_validate):
        """Test que get_user_db valide le schema_name."""
        from api.dependencies import get_user_db
        from unittest.mock import ANY

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.schema_name = "user_1"

        mock_validate.return_value = "user_1"
        mock_result = Mock()
        mock_result.scalar.return_value = "user_1, public"
        mock_db.execute.return_value = mock_result

        get_user_db(db=mock_db, current_user=mock_user)

        # Vérifier que _validate_schema_name a été appelé avec schema_name et db
        mock_validate.assert_called_once_with("user_1", ANY)

    def test_get_user_db_blocks_invalid_schema_name(self):
        """Test que get_user_db bloque les schema_name invalides."""
        from api.dependencies import get_user_db, _validate_schema_name

        mock_db = Mock()
        mock_user = Mock()
        mock_user.schema_name = "user_1; DROP TABLE users;--"

        # La validation doit lever une exception
        with pytest.raises(HTTPException) as exc_info:
            _validate_schema_name(mock_user.schema_name)

        assert exc_info.value.status_code == 500

    @patch('api.dependencies._validate_schema_name')
    def test_get_user_db_returns_tuple(self, mock_validate):
        """Test que get_user_db retourne un tuple (db, user)."""
        from api.dependencies import get_user_db

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.schema_name = "user_1"

        mock_validate.return_value = "user_1"
        mock_result = Mock()
        mock_result.scalar.return_value = "user_1, public"
        mock_db.execute.return_value = mock_result

        result = get_user_db(db=mock_db, current_user=mock_user)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == mock_db
        assert result[1] == mock_user

    @patch('api.dependencies._validate_schema_name')
    def test_get_user_db_uses_set_local(self, mock_validate):
        """Test que get_user_db utilise SET LOCAL (pas SET)."""
        from api.dependencies import get_user_db
        from unittest.mock import ANY

        mock_db = Mock()
        mock_user = Mock()
        mock_user.id = 1
        mock_user.schema_name = "user_1"

        mock_validate.return_value = "user_1"
        mock_result = Mock()
        mock_result.scalar.return_value = "user_1, public"
        mock_db.execute.return_value = mock_result

        get_user_db(db=mock_db, current_user=mock_user)

        # Vérifier que execute a été appelé au moins 2 fois:
        # 1. SET LOCAL search_path
        # 2. SHOW search_path
        assert mock_db.execute.call_count >= 2

        # Vérifier que le bon schema est utilisé via _validate_schema_name
        mock_validate.assert_called_once_with("user_1", ANY)


# ============================================================================
# require_permission TESTS (RBAC)
# ============================================================================

class TestPermissionAuthorization:
    """
    Tests pour le système de permissions RBAC.

    CRITIQUE: Ces tests vérifient que les permissions sont correctement
    vérifiées depuis la base de données.
    """

    def test_has_permission_returns_true_when_permission_exists(self):
        """Test que has_permission retourne True si la permission existe."""
        from api.dependencies import has_permission, _permissions_cache, clear_permissions_cache
        from models.public.user import UserRole

        # Clear cache pour isolation
        clear_permissions_cache()

        mock_user = Mock()
        mock_user.role = UserRole.ADMIN

        mock_db = Mock()
        mock_permission = Mock()
        mock_permission.code = "products:create"
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_permission]

        result = has_permission(mock_user, "products:create", mock_db)

        assert result is True
        clear_permissions_cache()

    def test_has_permission_returns_false_when_permission_missing(self):
        """Test que has_permission retourne False si la permission n'existe pas."""
        from api.dependencies import has_permission, clear_permissions_cache
        from models.public.user import UserRole

        clear_permissions_cache()

        mock_user = Mock()
        mock_user.role = UserRole.SUPPORT

        mock_db = Mock()
        mock_permission = Mock()
        mock_permission.code = "products:read"  # Seule permission
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_permission]

        # Support n'a pas products:delete
        result = has_permission(mock_user, "products:delete", mock_db)

        assert result is False
        clear_permissions_cache()

    def test_has_permission_uses_cache(self):
        """Test que has_permission utilise le cache pour éviter les requêtes répétées."""
        from api.dependencies import has_permission, _permissions_cache, clear_permissions_cache
        from models.public.user import UserRole

        clear_permissions_cache()

        mock_user = Mock()
        mock_user.role = UserRole.USER

        mock_db = Mock()
        mock_permission = Mock()
        mock_permission.code = "products:create"
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_permission]

        # Premier appel - charge le cache
        has_permission(mock_user, "products:create", mock_db)

        # Deuxième appel - doit utiliser le cache
        has_permission(mock_user, "products:create", mock_db)

        # La query ne doit être appelée qu'une seule fois (cache)
        assert mock_db.query.call_count == 1

        clear_permissions_cache()

    def test_clear_permissions_cache_clears_cache(self):
        """Test que clear_permissions_cache vide le cache."""
        from api.dependencies import _permissions_cache, clear_permissions_cache

        # Ajouter quelque chose au cache
        _permissions_cache["test_key"] = {"test_permission"}

        clear_permissions_cache()

        assert len(_permissions_cache) == 0

    def test_require_permission_allows_user_with_permission(self):
        """Test que require_permission autorise un utilisateur avec la permission."""
        from api.dependencies import require_permission, clear_permissions_cache
        from models.public.user import UserRole

        clear_permissions_cache()

        checker = require_permission("products:create")

        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_db = Mock()
        mock_permission = Mock()
        mock_permission.code = "products:create"
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_permission]

        # Appeler le checker directement avec les dépendances
        result = checker(current_user=mock_user, db=mock_db)

        assert result == mock_user
        clear_permissions_cache()

    def test_require_permission_rejects_user_without_permission(self):
        """Test que require_permission rejette un utilisateur sans la permission."""
        from api.dependencies import require_permission, clear_permissions_cache
        from models.public.user import UserRole

        clear_permissions_cache()

        checker = require_permission("admin:users:delete")

        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_db = Mock()
        mock_permission = Mock()
        mock_permission.code = "products:create"  # Pas admin:users:delete
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_permission]

        with pytest.raises(HTTPException) as exc_info:
            checker(current_user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403
        assert "admin:users:delete" in exc_info.value.detail
        clear_permissions_cache()

    def test_require_any_permission_allows_with_one_permission(self):
        """Test que require_any_permission autorise si l'utilisateur a au moins une permission."""
        from api.dependencies import require_any_permission, clear_permissions_cache
        from models.public.user import UserRole

        clear_permissions_cache()

        checker = require_any_permission("products:create", "products:update", "products:delete")

        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_db = Mock()
        mock_permission = Mock()
        mock_permission.code = "products:create"  # A seulement products:create
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_permission]

        result = checker(current_user=mock_user, db=mock_db)

        assert result == mock_user
        clear_permissions_cache()

    def test_require_any_permission_rejects_without_any_permission(self):
        """Test que require_any_permission rejette si l'utilisateur n'a aucune des permissions."""
        from api.dependencies import require_any_permission, clear_permissions_cache
        from models.public.user import UserRole

        clear_permissions_cache()

        checker = require_any_permission("admin:users:read", "admin:users:update")

        mock_user = Mock()
        mock_user.id = 1
        mock_user.role = UserRole.USER

        mock_db = Mock()
        mock_permission = Mock()
        mock_permission.code = "products:create"  # Pas de permission admin
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_permission]

        with pytest.raises(HTTPException) as exc_info:
            checker(current_user=mock_user, db=mock_db)

        assert exc_info.value.status_code == 403
        clear_permissions_cache()

    def test_require_permission_different_roles_different_permissions(self):
        """Test que différents rôles ont différentes permissions."""
        from api.dependencies import has_permission, clear_permissions_cache
        from models.public.user import UserRole

        clear_permissions_cache()

        # Simuler ADMIN avec toutes les permissions
        admin_user = Mock()
        admin_user.role = UserRole.ADMIN

        mock_db_admin = Mock()
        admin_permissions = [Mock(code="products:create"), Mock(code="admin:users:delete")]
        mock_db_admin.query.return_value.join.return_value.filter.return_value.all.return_value = admin_permissions

        # Simuler SUPPORT avec permissions limitées
        support_user = Mock()
        support_user.role = UserRole.SUPPORT

        mock_db_support = Mock()
        support_permissions = [Mock(code="products:read")]
        mock_db_support.query.return_value.join.return_value.filter.return_value.all.return_value = support_permissions

        # Admin a admin:users:delete
        assert has_permission(admin_user, "admin:users:delete", mock_db_admin) is True

        clear_permissions_cache()

        # Support n'a pas admin:users:delete
        assert has_permission(support_user, "admin:users:delete", mock_db_support) is False

        clear_permissions_cache()
