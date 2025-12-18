"""
SKU Generator Service

⚠️  DEPRECATED (2025-12-09): Ce service n'est plus utilisé.

Architecture simplifiée (2025-12-09):
- Les produits utilisent maintenant uniquement l'ID auto-incrémenté (PostgreSQL SERIAL)
- Plus besoin de SKU ni de séquences product_sku_seq
- Ce fichier est conservé pour référence historique mais ne doit plus être importé

Business Rules (obsolète - 2025-12-08):
- Génération automatique via séquence product_sku_seq
- Format numérique simple (ex: 1000, 1001, 1002...)
- Thread-safe (séquence PostgreSQL garantit unicité)
- Séquence isolée par tenant (schema user_X)

Author: Claude
Date: 2025-12-08
"""

from sqlalchemy import text
from sqlalchemy.orm import Session


class SKUGeneratorService:
    """Service pour générer des SKU uniques."""

    @staticmethod
    def generate_next_sku(db: Session, schema_name: str) -> str:
        """
        Génère le prochain SKU disponible via séquence PostgreSQL.

        Business Rules (2025-12-08):
        - Utilise nextval() pour obtenir le prochain numéro
        - Format: numérique simple (ex: "1000")
        - Thread-safe (pas de race condition)
        - Séquence isolée par tenant

        Args:
            db: Session SQLAlchemy
            schema_name: Nom du schema (ex: "user_1")

        Returns:
            str: Le SKU généré (ex: "1000")

        Raises:
            Exception: Si la séquence n'existe pas dans le schema

        Example:
            >>> sku = SKUGeneratorService.generate_next_sku(db, "user_1")
            >>> print(sku)
            "1000"
        """
        try:
            result = db.execute(
                text(f"SELECT nextval('{schema_name}.product_sku_seq')")
            )
            next_value = result.scalar()

            # Retourner le SKU comme string simple
            return str(next_value)

        except Exception as e:
            raise Exception(
                f"Erreur lors de la génération du SKU dans {schema_name}: {e}"
            )

    @staticmethod
    def get_current_sku(db: Session, schema_name: str) -> str | None:
        """
        Récupère le SKU actuel (dernier généré) sans l'incrémenter.

        Business Rules:
        - Utilise currval() pour obtenir la valeur actuelle
        - Retourne None si aucun SKU n'a encore été généré

        Args:
            db: Session SQLAlchemy
            schema_name: Nom du schema (ex: "user_1")

        Returns:
            str | None: Le SKU actuel ou None

        Example:
            >>> sku = SKUGeneratorService.get_current_sku(db, "user_1")
            >>> print(sku)
            "1000"
        """
        try:
            result = db.execute(
                text(f"SELECT currval('{schema_name}.product_sku_seq')")
            )
            current_value = result.scalar()
            return str(current_value)

        except Exception:
            # currval() échoue si nextval() n'a jamais été appelé
            return None

    @staticmethod
    def reset_sequence(db: Session, schema_name: str, start_value: int = 1000) -> None:
        """
        Réinitialise la séquence à une valeur de départ.

        WARNING: Cette méthode est DANGEREUSE et ne devrait être utilisée
        qu'en développement ou pour des migrations de données.

        Business Rules:
        - Réinitialise à start_value (défaut: 1000)
        - Peut causer des conflits de SKU si utilisé en production

        Args:
            db: Session SQLAlchemy
            schema_name: Nom du schema (ex: "user_1")
            start_value: Valeur de départ (défaut: 1000)

        Raises:
            Exception: Si la séquence n'existe pas
        """
        try:
            db.execute(
                text(f"ALTER SEQUENCE {schema_name}.product_sku_seq RESTART WITH {start_value}")
            )
            db.commit()

        except Exception as e:
            db.rollback()
            raise Exception(
                f"Erreur lors de la réinitialisation de la séquence dans {schema_name}: {e}"
            )
