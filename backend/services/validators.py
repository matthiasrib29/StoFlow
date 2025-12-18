"""
Validators

Validators génériques pour:
- Attributs produits (FK vers tables public)
- Résultats des tâches plugin (Status HTTP + Structure JSON)

Business Rules (2025-12-11):
- Validation centralisée pour éviter duplication
- Configuration déclarative des attributs
- Messages d'erreur cohérents et utiles
- Support validation batch (tous attributs d'un coup)
- Validation des résultats plugin (nouvelle architecture headers côté plugin)
"""

from typing import Any, Optional

from sqlalchemy.orm import Session

from models.public.brand import Brand
from models.public.category import Category
from models.public.color import Color
from models.public.condition import Condition
from models.public.fit import Fit
from models.public.gender import Gender
from models.public.material import Material
from models.public.season import Season
from models.public.size import Size


class AttributeValidator:
    """
    Validator générique pour les attributs produits.

    Centralise toute la logique de validation FK pour éviter duplication
    entre create_product, update_product, et autres opérations.

    Example:
        >>> validator = AttributeValidator()
        >>> validator.validate_product_attributes(db, {
        ...     'category': 'Jeans',
        ...     'brand': 'Levi\\'s',
        ...     'color': 'Blue'
        ... })
        # Raises ValueError si un attribut invalide
    """

    # Configuration déclarative de tous les attributs
    # Format: {
    #   'field_name': {
    #       'model': Model class,
    #       'field': column name in model,
    #       'required': True/False,
    #       'display_name': Human-readable name
    #   }
    # }
    ATTRIBUTE_CONFIGS = {
        # Attributs obligatoires
        'category': {
            'model': Category,
            'field': 'name_en',
            'required': True,
            'display_name': 'Category'
        },
        'condition': {
            'model': Condition,
            'field': 'name',
            'required': True,
            'display_name': 'Condition'
        },

        # Attributs optionnels
        'brand': {
            'model': Brand,
            'field': 'name',
            'required': False,
            'display_name': 'Brand'
        },
        'color': {
            'model': Color,
            'field': 'name_en',
            'required': False,
            'display_name': 'Color'
        },
        'label_size': {
            'model': Size,
            'field': 'name',
            'required': False,
            'display_name': 'Size'
        },
        'material': {
            'model': Material,
            'field': 'name_en',
            'required': False,
            'display_name': 'Material'
        },
        'fit': {
            'model': Fit,
            'field': 'name_en',
            'required': False,
            'display_name': 'Fit'
        },
        'gender': {
            'model': Gender,
            'field': 'name_en',
            'required': False,
            'display_name': 'Gender'
        },
        'season': {
            'model': Season,
            'field': 'name_en',
            'required': False,
            'display_name': 'Season'
        },
    }

    @staticmethod
    def validate_attribute(
        db: Session,
        attr_name: str,
        attr_value: Optional[Any]
    ) -> None:
        """
        Valide un attribut produit unique.

        Args:
            db: Session SQLAlchemy
            attr_name: Nom de l'attribut (ex: 'brand', 'category')
            attr_value: Valeur à valider (peut être None)

        Raises:
            ValueError: Si attribut requis est None, ou si valeur n'existe pas
            KeyError: Si attr_name n'est pas dans ATTRIBUTE_CONFIGS

        Example:
            >>> AttributeValidator.validate_attribute(db, 'brand', 'Nike')
            # OK si Nike existe

            >>> AttributeValidator.validate_attribute(db, 'brand', 'InvalidBrand')
            ValueError: Brand 'InvalidBrand' does not exist. Use /api/attributes/brands...
        """
        # Vérifier que l'attribut est configuré
        if attr_name not in AttributeValidator.ATTRIBUTE_CONFIGS:
            raise KeyError(
                f"Unknown attribute '{attr_name}'. "
                f"Valid attributes: {', '.join(AttributeValidator.ATTRIBUTE_CONFIGS.keys())}"
            )

        config = AttributeValidator.ATTRIBUTE_CONFIGS[attr_name]

        # Si valeur est None
        if attr_value is None:
            if config['required']:
                raise ValueError(
                    f"{config['display_name']} is required and cannot be None"
                )
            # Attribut optionnel avec valeur None → OK
            return

        # Valeur non-None → vérifier qu'elle existe en DB
        model = config['model']
        field_name = config['field']
        field = getattr(model, field_name)

        exists = db.query(model).filter(field == attr_value).first()

        if not exists:
            # Message d'erreur avec suggestion d'API endpoint
            table_name = model.__tablename__
            raise ValueError(
                f"{config['display_name']} '{attr_value}' does not exist. "
                f"Use /api/attributes/{table_name} to get valid {table_name}."
            )

    @staticmethod
    def validate_product_attributes(
        db: Session,
        data: dict[str, Any],
        partial: bool = False
    ) -> None:
        """
        Valide tous les attributs produits d'un coup (batch validation).

        Args:
            db: Session SQLAlchemy
            data: Dictionnaire contenant les données produit
            partial: Si True, ignore les attributs absents (pour updates partiels)

        Raises:
            ValueError: Si un attribut est invalide

        Example:
            >>> # Validation complète (create)
            >>> AttributeValidator.validate_product_attributes(db, {
            ...     'category': 'Jeans',
            ...     'condition': 'GOOD',
            ...     'brand': 'Levi\\'s',
            ...     'color': 'Blue',
            ...     'label_size': 'M'
            ... })

            >>> # Validation partielle (update)
            >>> AttributeValidator.validate_product_attributes(db, {
            ...     'brand': 'Nike',  # Seul brand modifié
            ... }, partial=True)
        """
        for attr_name, config in AttributeValidator.ATTRIBUTE_CONFIGS.items():
            # Si attribut absent dans data
            if attr_name not in data:
                # Mode partial (update) → skip
                if partial:
                    continue
                # Mode complet (create) → vérifier si requis
                if config['required']:
                    raise ValueError(
                        f"{config['display_name']} is required but not provided"
                    )
                continue

            # Attribut présent → valider
            attr_value = data[attr_name]
            AttributeValidator.validate_attribute(db, attr_name, attr_value)

    @staticmethod
    def get_attribute_list(db: Session, attribute_type: str) -> list[str]:
        """
        Retourne la liste des valeurs valides pour un type d'attribut.

        Utile pour les endpoints API qui listent les attributs disponibles.

        Args:
            db: Session SQLAlchemy
            attribute_type: Type d'attribut (ex: 'brand', 'category')

        Returns:
            list[str]: Liste des valeurs valides

        Raises:
            KeyError: Si attribute_type invalide

        Example:
            >>> brands = AttributeValidator.get_attribute_list(db, 'brand')
            >>> print(brands)
            ['Nike', 'Adidas', 'Levi\\'s', ...]
        """
        if attribute_type not in AttributeValidator.ATTRIBUTE_CONFIGS:
            raise KeyError(f"Unknown attribute type: {attribute_type}")

        config = AttributeValidator.ATTRIBUTE_CONFIGS[attribute_type]
        model = config['model']
        field_name = config['field']
        field = getattr(model, field_name)

        results = db.query(field).all()
        return [row[0] for row in results if row[0] is not None]

    @staticmethod
    def attribute_exists(
        db: Session,
        attribute_type: str,
        value: str
    ) -> bool:
        """
        Vérifie si une valeur d'attribut existe (sans lever d'exception).

        Args:
            db: Session SQLAlchemy
            attribute_type: Type d'attribut
            value: Valeur à vérifier

        Returns:
            bool: True si existe, False sinon

        Example:
            >>> if AttributeValidator.attribute_exists(db, 'brand', 'Nike'):
            ...     print("Nike exists!")
        """
        try:
            AttributeValidator.validate_attribute(db, attribute_type, value)
            return True
        except (ValueError, KeyError):
            return False


class PluginTaskResultValidator:
    """
    Validator pour les résultats des tâches plugin.

    Business Rules (2025-12-11):
    - Valide le status HTTP (2xx = success, 4xx/5xx = error)
    - Valide la structure JSON selon le type de requête
    - Utilisé par api/plugin.py lors du submit_task_result

    Example:
        >>> validator = PluginTaskResultValidator()
        >>> validator.validate_result({
        ...     'success': True,
        ...     'result': {'status': 200, 'data': {'items': [...]}}
        ... }, 'vinted_api')
        # OK si structure valide
    """

    @staticmethod
    def validate_http_status(status: int, success: bool) -> tuple[bool, str | None]:
        """
        Valide le status HTTP et détermine si la tâche a réussi.

        Args:
            status: Status HTTP code (ex: 200, 404, 500)
            success: Flag success du plugin

        Returns:
            tuple[bool, str | None]: (is_valid, error_message)

        Example:
            >>> is_valid, error = PluginTaskResultValidator.validate_http_status(200, True)
            >>> print(is_valid)
            True

            >>> is_valid, error = PluginTaskResultValidator.validate_http_status(404, False)
            >>> print(error)
            'HTTP 404: Client error'
        """
        # Status 2xx = Success
        if 200 <= status < 300:
            return (True, None)

        # Status 4xx = Client error
        if 400 <= status < 500:
            return (False, f"HTTP {status}: Client error (bad request, not found, unauthorized, etc.)")

        # Status 5xx = Server error
        if 500 <= status < 600:
            return (False, f"HTTP {status}: Server error")

        # Status inattendu
        return (False, f"HTTP {status}: Unexpected status code")

    @staticmethod
    def validate_json_structure(data: dict, task_type: str) -> tuple[bool, str | None]:
        """
        Valide la structure JSON selon le type de tâche.

        Args:
            data: Données JSON retournées par le plugin
            task_type: Type de tâche (vinted_api, get_vinted_user_info, etc.)

        Returns:
            tuple[bool, str | None]: (is_valid, error_message)

        Example:
            >>> is_valid, error = PluginTaskResultValidator.validate_json_structure(
            ...     {'items': [], 'pagination': {}},
            ...     'vinted_api'
            ... )
        """
        # Pour l'instant, validation basique
        # TODO: Ajouter des validations spécifiques par task_type si nécessaire

        if not isinstance(data, dict):
            return (False, "Result data must be a dictionary")

        # Validation spécifique selon task_type
        if task_type == 'vinted_api':
            # Les réponses API Vinted peuvent avoir n'importe quelle structure
            # On vérifie juste que c'est un dict
            return (True, None)

        elif task_type == 'get_vinted_user_info':
            # Doit contenir connected, userId, login
            required_fields = ['connected', 'userId', 'login']
            missing = [f for f in required_fields if f not in data]
            if missing:
                return (False, f"Missing required fields: {', '.join(missing)}")
            return (True, None)

        # Par défaut, accepter toute structure valide
        return (True, None)

    @staticmethod
    def validate_task_result(result_data: dict) -> tuple[bool, str | None]:
        """
        Validation complète d'un résultat de tâche plugin.

        Args:
            result_data: Dict contenant {success, result, error_message}

        Returns:
            tuple[bool, str | None]: (is_valid, error_message)

        Example:
            >>> is_valid, error = PluginTaskResultValidator.validate_task_result({
            ...     'success': True,
            ...     'result': {'status': 200, 'data': {...}}
            ... })
        """
        # Vérifier présence des champs requis
        if 'success' not in result_data:
            return (False, "Field 'success' is required")

        success = result_data['success']

        # Si success = False, error_message devrait être présent
        if not success:
            if 'error_message' not in result_data:
                return (False, "Field 'error_message' is required when success=False")
            return (True, None)  # Erreur légitime, validation OK

        # Si success = True, result devrait être présent
        if 'result' not in result_data:
            return (False, "Field 'result' is required when success=True")

        # Valider la structure du result
        result = result_data['result']
        if not isinstance(result, dict):
            return (False, "Field 'result' must be a dictionary")

        # Vérifier status HTTP si présent
        if 'status' in result:
            status = result['status']
            if not isinstance(status, int):
                return (False, "HTTP status must be an integer")

            is_valid, error = PluginTaskResultValidator.validate_http_status(status, success)
            if not is_valid:
                return (is_valid, error)

        return (True, None)
