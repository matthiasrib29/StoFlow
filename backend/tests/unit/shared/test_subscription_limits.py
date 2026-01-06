"""
Tests unitaires pour le système de quotas avec warning (shared/subscription_limits.py).

Couverture:
- QuotaStatus enum (OK, WARNING, BLOCKED)
- QuotaCheckResult dataclass
- _calculate_quota_status (logique de calcul)
- get_*_quota_status functions
- check_and_warn_* functions
- Seuil de warning à 80%

Author: Claude
Date: 2025-12-19

CRITIQUE: Ces tests vérifient le comportement des limites d'abonnement.
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import asdict


# ============================================================================
# QuotaStatus et QuotaCheckResult TESTS
# ============================================================================

class TestQuotaStatus:
    """Tests pour l'enum QuotaStatus."""

    def test_quota_status_values(self):
        """Test que QuotaStatus a les bonnes valeurs."""
        from shared.subscription_limits import QuotaStatus

        assert QuotaStatus.OK.value == "ok"
        assert QuotaStatus.WARNING.value == "warning"
        assert QuotaStatus.BLOCKED.value == "blocked"

    def test_quota_status_is_string_enum(self):
        """Test que QuotaStatus hérite de str."""
        from shared.subscription_limits import QuotaStatus

        assert isinstance(QuotaStatus.OK, str)
        assert QuotaStatus.OK == "ok"


class TestQuotaCheckResult:
    """Tests pour la dataclass QuotaCheckResult."""

    def test_quota_check_result_creation(self):
        """Test création d'un QuotaCheckResult."""
        from shared.subscription_limits import QuotaCheckResult, QuotaStatus

        result = QuotaCheckResult(
            status=QuotaStatus.OK,
            current=10,
            max_allowed=50,
            percentage=20.0,
            message=None
        )

        assert result.status == QuotaStatus.OK
        assert result.current == 10
        assert result.max_allowed == 50
        assert result.percentage == 20.0
        assert result.message is None

    def test_quota_check_result_is_warning_property(self):
        """Test la propriété is_warning."""
        from shared.subscription_limits import QuotaCheckResult, QuotaStatus

        ok_result = QuotaCheckResult(QuotaStatus.OK, 10, 50, 20.0)
        warning_result = QuotaCheckResult(QuotaStatus.WARNING, 45, 50, 90.0, "Warning!")
        blocked_result = QuotaCheckResult(QuotaStatus.BLOCKED, 50, 50, 100.0, "Blocked!")

        assert ok_result.is_warning is False
        assert warning_result.is_warning is True
        assert blocked_result.is_warning is False

    def test_quota_check_result_is_blocked_property(self):
        """Test la propriété is_blocked."""
        from shared.subscription_limits import QuotaCheckResult, QuotaStatus

        ok_result = QuotaCheckResult(QuotaStatus.OK, 10, 50, 20.0)
        warning_result = QuotaCheckResult(QuotaStatus.WARNING, 45, 50, 90.0)
        blocked_result = QuotaCheckResult(QuotaStatus.BLOCKED, 50, 50, 100.0)

        assert ok_result.is_blocked is False
        assert warning_result.is_blocked is False
        assert blocked_result.is_blocked is True

    def test_quota_check_result_to_dict(self):
        """Test la méthode to_dict."""
        from shared.subscription_limits import QuotaCheckResult, QuotaStatus

        result = QuotaCheckResult(
            status=QuotaStatus.WARNING,
            current=42,
            max_allowed=50,
            percentage=84.0,
            message="Attention!"
        )

        dict_result = result.to_dict()

        assert dict_result["status"] == "warning"
        assert dict_result["current"] == 42
        assert dict_result["max_allowed"] == 50
        assert dict_result["percentage"] == 84.0
        assert dict_result["message"] == "Attention!"


# ============================================================================
# _calculate_quota_status TESTS
# ============================================================================

class TestCalculateQuotaStatus:
    """Tests pour la fonction _calculate_quota_status."""

    def test_calculate_quota_status_ok_at_0_percent(self):
        """Test status OK à 0%."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(0, 100, "produits")

        assert result.status == QuotaStatus.OK
        assert result.percentage == 0.0
        assert result.message is None

    def test_calculate_quota_status_ok_at_50_percent(self):
        """Test status OK à 50%."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(50, 100, "produits")

        assert result.status == QuotaStatus.OK
        assert result.percentage == 50.0
        assert result.message is None

    def test_calculate_quota_status_ok_at_79_percent(self):
        """Test status OK à 79% (juste sous le seuil)."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(79, 100, "produits")

        assert result.status == QuotaStatus.OK
        assert result.percentage == 79.0
        assert result.message is None

    def test_calculate_quota_status_warning_at_80_percent(self):
        """Test status WARNING exactement à 80%."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(80, 100, "produits")

        assert result.status == QuotaStatus.WARNING
        assert result.percentage == 80.0
        assert result.message is not None
        assert "80%" in result.message
        assert "20" in result.message  # remaining

    def test_calculate_quota_status_warning_at_90_percent(self):
        """Test status WARNING à 90%."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(90, 100, "produits")

        assert result.status == QuotaStatus.WARNING
        assert result.percentage == 90.0
        assert "10" in result.message  # remaining

    def test_calculate_quota_status_warning_at_99_percent(self):
        """Test status WARNING à 99%."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(99, 100, "produits")

        assert result.status == QuotaStatus.WARNING
        assert result.percentage == 99.0
        assert "1" in result.message  # remaining

    def test_calculate_quota_status_blocked_at_100_percent(self):
        """Test status BLOCKED exactement à 100%."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(100, 100, "produits")

        assert result.status == QuotaStatus.BLOCKED
        assert result.percentage == 100.0
        assert result.message is not None
        assert "atteinte" in result.message.lower()

    def test_calculate_quota_status_blocked_over_100_percent(self):
        """Test status BLOCKED au-dessus de 100%."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(120, 100, "produits")

        assert result.status == QuotaStatus.BLOCKED
        assert result.percentage == 120.0

    def test_calculate_quota_status_unlimited_max(self):
        """Test status OK quand max_allowed <= 0 (illimité)."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result = _calculate_quota_status(1000, 0, "produits")

        assert result.status == QuotaStatus.OK
        assert result.percentage == 0.0
        assert result.message is None

    def test_calculate_quota_status_message_contains_limit_type(self):
        """Test que le message contient le type de limite."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus

        result_warning = _calculate_quota_status(85, 100, "plateformes")
        result_blocked = _calculate_quota_status(100, 100, "crédits IA")

        assert "plateformes" in result_warning.message
        assert "crédits IA" in result_blocked.message


# ============================================================================
# WARNING_THRESHOLD TESTS
# ============================================================================

class TestWarningThreshold:
    """Tests pour le seuil de warning."""

    def test_warning_threshold_is_80_percent(self):
        """Test que le seuil de warning est bien 80%."""
        from shared.subscription_limits import WARNING_THRESHOLD

        assert WARNING_THRESHOLD == 0.8

    def test_warning_threshold_boundary(self):
        """Test le comportement aux limites du seuil."""
        from shared.subscription_limits import _calculate_quota_status, QuotaStatus, WARNING_THRESHOLD

        # Juste sous le seuil (79.99%)
        result_below = _calculate_quota_status(7999, 10000, "test")
        assert result_below.status == QuotaStatus.OK

        # Exactement au seuil (80%)
        result_at = _calculate_quota_status(8000, 10000, "test")
        assert result_at.status == QuotaStatus.WARNING


# ============================================================================
# check_and_warn_* TESTS
# ============================================================================

class TestCheckAndWarnFunctions:
    """Tests pour les fonctions check_and_warn_*."""

    def test_check_and_warn_product_limit_returns_result_when_ok(self):
        """Test check_and_warn_product_limit retourne un résultat quand OK."""
        from shared.subscription_limits import check_and_warn_product_limit, QuotaStatus

        mock_user = Mock()
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_products = 100

        mock_db = Mock()

        # Mock le query chain du db - pas besoin de patcher Product car l'import est local
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        result = check_and_warn_product_limit(mock_user, mock_db)

        assert result.status == QuotaStatus.OK
        assert result.current == 10
        assert result.max_allowed == 100

    def test_check_and_warn_product_limit_returns_warning_at_80_percent(self):
        """Test check_and_warn_product_limit retourne WARNING à 80%."""
        from shared.subscription_limits import check_and_warn_product_limit, QuotaStatus

        mock_user = Mock()
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_products = 100

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.count.return_value = 85

        result = check_and_warn_product_limit(mock_user, mock_db)

        assert result.status == QuotaStatus.WARNING
        assert result.is_warning is True

    def test_check_and_warn_product_limit_raises_when_blocked(self):
        """Test check_and_warn_product_limit lève une exception quand BLOCKED."""
        from shared.subscription_limits import check_and_warn_product_limit, SubscriptionLimitError

        mock_user = Mock()
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_products = 100

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.count.return_value = 100

        with pytest.raises(SubscriptionLimitError) as exc_info:
            check_and_warn_product_limit(mock_user, mock_db)

        assert exc_info.value.status_code == 403
        assert "products" in str(exc_info.value.detail)

    def test_check_and_warn_platform_limit_returns_result_when_ok(self):
        """Test check_and_warn_platform_limit retourne un résultat quand OK."""
        from shared.subscription_limits import check_and_warn_platform_limit, QuotaStatus

        mock_user = Mock()
        mock_user.id = 1
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_platforms = 5

        mock_db = Mock()

        # Patcher la fonction de comptage des plateformes connectées
        with patch('shared.subscription_limits._count_connected_platforms') as mock_count:
            mock_count.return_value = 2

            result = check_and_warn_platform_limit(mock_user, mock_db)

            assert result.status == QuotaStatus.OK
            assert result.current == 2
            assert result.max_allowed == 5

    def test_check_and_warn_platform_limit_raises_when_blocked(self):
        """Test check_and_warn_platform_limit lève une exception quand BLOCKED."""
        from shared.subscription_limits import check_and_warn_platform_limit, SubscriptionLimitError

        mock_user = Mock()
        mock_user.id = 1
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_platforms = 2

        mock_db = Mock()

        # Patcher la fonction de comptage des plateformes connectées
        with patch('shared.subscription_limits._count_connected_platforms') as mock_count:
            mock_count.return_value = 2

            with pytest.raises(SubscriptionLimitError) as exc_info:
                check_and_warn_platform_limit(mock_user, mock_db)

            assert exc_info.value.status_code == 403

    def test_check_and_warn_ai_credits_returns_result_when_ok(self):
        """Test check_and_warn_ai_credits retourne un résultat quand OK."""
        from shared.subscription_limits import check_and_warn_ai_credits, QuotaStatus

        mock_user = Mock()
        mock_user.id = 1
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.ai_credits_monthly = 1000

        mock_db = Mock()

        with patch('models.user.ai_generation_log.AIGenerationLog') as mock_model:
            mock_model.user_id = Mock()
            mock_model.id = Mock()
            mock_model.created_at = Mock()
            mock_db.query.return_value.filter.return_value.scalar.return_value = 100

            result = check_and_warn_ai_credits(mock_user, mock_db)

            assert result.status == QuotaStatus.OK
            assert result.current == 100


# ============================================================================
# get_all_quotas_status TESTS
# ============================================================================

class TestGetAllQuotasStatus:
    """Tests pour la fonction get_all_quotas_status."""

    def test_get_all_quotas_status_returns_all_quotas(self):
        """Test que get_all_quotas_status retourne tous les quotas."""
        from shared.subscription_limits import (
            get_all_quotas_status,
            QuotaCheckResult,
            QuotaStatus,
        )
        from models.public.user import SubscriptionTier

        mock_user = Mock()
        mock_user.id = 1
        mock_user.subscription_tier = SubscriptionTier.STARTER
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_products = 500
        mock_user.subscription_quota.max_platforms = 2
        mock_user.subscription_quota.ai_credits_monthly = 1000

        mock_db = Mock()

        # Mock les fonctions individuelles pour éviter les imports de modèles
        mock_product_result = QuotaCheckResult(
            status=QuotaStatus.OK, current=10, max_allowed=500, percentage=2.0
        )
        mock_platform_result = QuotaCheckResult(
            status=QuotaStatus.OK, current=1, max_allowed=2, percentage=50.0
        )
        mock_ai_result = QuotaCheckResult(
            status=QuotaStatus.OK, current=50, max_allowed=1000, percentage=5.0
        )

        with patch('shared.subscription_limits.get_product_quota_status', return_value=mock_product_result), \
             patch('shared.subscription_limits.get_platform_quota_status', return_value=mock_platform_result), \
             patch('shared.subscription_limits.get_ai_credits_quota_status', return_value=mock_ai_result):

            result = get_all_quotas_status(mock_user, mock_db)

            assert "subscription_tier" in result
            assert result["subscription_tier"] == "starter"
            assert "products" in result
            assert "platforms" in result
            assert "ai_credits" in result
            assert "has_warnings" in result
            assert "has_blocked" in result
            assert result["has_warnings"] is False
            assert result["has_blocked"] is False

    def test_get_all_quotas_status_has_warnings_true_when_warning(self):
        """Test has_warnings est True quand au moins un quota est en warning."""
        from shared.subscription_limits import (
            get_all_quotas_status,
            QuotaCheckResult,
            QuotaStatus,
        )

        mock_user = Mock()
        mock_user.id = 1
        mock_user.subscription_tier = Mock()
        mock_user.subscription_tier.value = "free"
        mock_user.subscription_quota = Mock()

        mock_db = Mock()

        # Mock avec un warning sur les produits (90%)
        mock_product_result = QuotaCheckResult(
            status=QuotaStatus.WARNING, current=45, max_allowed=50, percentage=90.0, message="Warning!"
        )
        mock_platform_result = QuotaCheckResult(
            status=QuotaStatus.OK, current=0, max_allowed=1, percentage=0.0
        )
        mock_ai_result = QuotaCheckResult(
            status=QuotaStatus.OK, current=10, max_allowed=100, percentage=10.0
        )

        with patch('shared.subscription_limits.get_product_quota_status', return_value=mock_product_result), \
             patch('shared.subscription_limits.get_platform_quota_status', return_value=mock_platform_result), \
             patch('shared.subscription_limits.get_ai_credits_quota_status', return_value=mock_ai_result):

            result = get_all_quotas_status(mock_user, mock_db)

            assert result["has_warnings"] is True


# ============================================================================
# SubscriptionLimitError TESTS
# ============================================================================

class TestSubscriptionLimitError:
    """Tests pour l'exception SubscriptionLimitError."""

    def test_subscription_limit_error_has_correct_status_code(self):
        """Test que SubscriptionLimitError a le bon code HTTP."""
        from shared.subscription_limits import SubscriptionLimitError

        error = SubscriptionLimitError(
            message="Limite atteinte",
            limit_type="products",
            current=50,
            max_allowed=50
        )

        assert error.status_code == 403

    def test_subscription_limit_error_has_correct_detail(self):
        """Test que SubscriptionLimitError a les bonnes informations dans detail."""
        from shared.subscription_limits import SubscriptionLimitError

        error = SubscriptionLimitError(
            message="Limite de produits atteinte",
            limit_type="products",
            current=50,
            max_allowed=50
        )

        assert error.detail["error"] == "subscription_limit_reached"
        assert error.detail["limit_type"] == "products"
        assert error.detail["current"] == 50
        assert error.detail["max_allowed"] == 50
        assert "produits" in error.detail["message"].lower()


# ============================================================================
# BACKWARD COMPATIBILITY TESTS
# ============================================================================

class TestBackwardCompatibility:
    """Tests pour vérifier la compatibilité avec l'ancien code."""

    def test_check_product_limit_still_works(self):
        """Test que check_product_limit (ancienne fonction) fonctionne encore."""
        from shared.subscription_limits import check_product_limit

        mock_user = Mock()
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_products = 100

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        current, max_allowed = check_product_limit(mock_user, mock_db)

        assert current == 10
        assert max_allowed == 100

    def test_check_product_limit_raises_at_limit(self):
        """Test que check_product_limit lève une exception à la limite."""
        from shared.subscription_limits import check_product_limit, SubscriptionLimitError

        mock_user = Mock()
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_products = 50

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.count.return_value = 50

        with pytest.raises(SubscriptionLimitError):
            check_product_limit(mock_user, mock_db)

    def test_get_subscription_limits_info_still_works(self):
        """Test que get_subscription_limits_info fonctionne encore."""
        from shared.subscription_limits import get_subscription_limits_info
        from models.public.user import SubscriptionTier

        mock_user = Mock()
        mock_user.subscription_tier = SubscriptionTier.PRO
        mock_user.subscription_quota = Mock()
        mock_user.subscription_quota.max_products = 2000
        mock_user.subscription_quota.max_platforms = 5
        mock_user.subscription_quota.ai_credits_monthly = 5000

        result = get_subscription_limits_info(mock_user)

        assert result["subscription_tier"] == "pro"
        assert result["max_products"] == 2000
        assert result["max_platforms"] == 5
        assert result["ai_credits_monthly"] == 5000
