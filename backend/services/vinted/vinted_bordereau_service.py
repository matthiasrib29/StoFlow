"""
Vinted Bordereau Service

Service de gestion des bordereaux d'expédition Vinted.
Responsabilité: Téléchargement et gestion des bordereaux PDF.

Business Rules (2024-12-10):
- Téléchargement bordereaux depuis URLs fournies par le plugin
- Sauvegarde locale des PDFs
- Génération PDF combiné pour impression batch
- Pas d'accès direct API Vinted (géré par plugin navigateur)

Architecture:
- Service pur (pas d'accès API direct)
- Reçoit URLs de bordereaux du plugin
- Gestion fichiers temporaires
- Compatible multi-tenant

Created: 2024-12-10
Author: Claude (adapted from pythonApiWOO)
"""

import os
import requests
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class VintedBordereauService:
    """
    Service pour gérer les bordereaux d'expédition Vinted.

    Le plugin navigateur récupère les URLs des bordereaux depuis l'API Vinted,
    puis ce service télécharge et sauvegarde les PDFs.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialise le service avec un dossier temporaire.

        Args:
            temp_dir: Chemin du dossier temporaire (défaut: ./temp/bordereaux)
        """
        if temp_dir is None:
            temp_dir = os.path.join(os.getcwd(), "temp", "bordereaux")

        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def download_bordereau(
        self,
        label_url: str,
        transaction_id: int,
        user_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Télécharge un bordereau PDF depuis une URL.

        Args:
            label_url: URL du bordereau Vinted
            transaction_id: ID de la transaction Vinted
            user_id: ID utilisateur (pour isolation multi-tenant)

        Returns:
            Chemin du fichier PDF téléchargé, ou None si échec

        Example:
            >>> service = VintedBordereauService()
            >>> pdf_path = service.download_bordereau(
            ...     "https://vinted.com/shipments/123/label.pdf",
            ...     transaction_id=456,
            ...     user_id=1
            ... )
            >>> print(pdf_path)
            '/path/to/temp/bordereaux/user_1/bordereau_456_20241210_103045.pdf'
        """
        try:
            # Créer sous-dossier par utilisateur si multi-tenant
            if user_id:
                user_dir = self.temp_dir / f"user_{user_id}"
                user_dir.mkdir(exist_ok=True)
            else:
                user_dir = self.temp_dir

            # Générer nom de fichier unique
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bordereau_{transaction_id}_{timestamp}.pdf"
            pdf_path = user_dir / filename

            # Télécharger le PDF
            logger.info(f"📥 Téléchargement bordereau transaction #{transaction_id}")
            response = requests.get(label_url, stream=True, timeout=30)

            if response.status_code == 200:
                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.info(f"✅ Bordereau téléchargé: {pdf_path}")
                return str(pdf_path)
            else:
                logger.error(f"❌ Échec téléchargement: HTTP {response.status_code}")
                return None

        except requests.RequestException as e:
            logger.error(f"❌ Erreur téléchargement bordereau: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"❌ Erreur inattendue: {e}", exc_info=True)
            return None

    def download_multiple_bordereaux(
        self,
        bordereaux_data: List[Dict[str, any]],
        user_id: Optional[int] = None
    ) -> Dict[str, any]:
        """
        Télécharge plusieurs bordereaux en batch.

        Args:
            bordereaux_data: Liste de dicts avec 'label_url' et 'transaction_id'
            user_id: ID utilisateur (pour isolation multi-tenant)

        Returns:
            Dict avec statistiques et chemins des fichiers:
            {
                'total': int,
                'success': int,
                'failed': int,
                'files': List[str],
                'errors': List[Dict]
            }

        Example:
            >>> service = VintedBordereauService()
            >>> bordereaux = [
            ...     {'label_url': 'https://...', 'transaction_id': 123},
            ...     {'label_url': 'https://...', 'transaction_id': 124}
            ... ]
            >>> result = service.download_multiple_bordereaux(bordereaux, user_id=1)
            >>> print(result)
            {'total': 2, 'success': 2, 'failed': 0, 'files': [...], 'errors': []}
        """
        logger.info(f"🚀 Téléchargement de {len(bordereaux_data)} bordereaux")

        result = {
            'total': len(bordereaux_data),
            'success': 0,
            'failed': 0,
            'files': [],
            'errors': []
        }

        for i, bordereau in enumerate(bordereaux_data, 1):
            transaction_id = bordereau.get('transaction_id')
            label_url = bordereau.get('label_url')

            if not label_url or not transaction_id:
                logger.warning(f"⚠️  [{i}/{result['total']}] Données manquantes (label_url ou transaction_id)")
                result['failed'] += 1
                result['errors'].append({
                    'transaction_id': transaction_id,
                    'error': 'Missing label_url or transaction_id'
                })
                continue

            logger.info(f"📋 [{i}/{result['total']}] Traitement transaction #{transaction_id}")

            pdf_path = self.download_bordereau(label_url, transaction_id, user_id)

            if pdf_path:
                result['success'] += 1
                result['files'].append(pdf_path)
                logger.info(f"   ✅ Téléchargé")
            else:
                result['failed'] += 1
                result['errors'].append({
                    'transaction_id': transaction_id,
                    'error': 'Download failed'
                })
                logger.warning(f"   ❌ Échec")

        logger.info(
            f"✅ Téléchargement terminé: {result['success']}/{result['total']} réussis, "
            f"{result['failed']} échecs"
        )

        return result

    def get_bordereau_path(
        self,
        transaction_id: int,
        user_id: Optional[int] = None
    ) -> Optional[str]:
        """
        Récupère le chemin du bordereau le plus récent pour une transaction.

        Args:
            transaction_id: ID de la transaction Vinted
            user_id: ID utilisateur

        Returns:
            Chemin du fichier PDF si trouvé, None sinon

        Example:
            >>> service = VintedBordereauService()
            >>> path = service.get_bordereau_path(123, user_id=1)
            >>> print(path)
            '/path/to/temp/bordereaux/user_1/bordereau_123_20241210_103045.pdf'
        """
        # Déterminer le dossier de recherche
        if user_id:
            search_dir = self.temp_dir / f"user_{user_id}"
        else:
            search_dir = self.temp_dir

        if not search_dir.exists():
            return None

        # Chercher tous les fichiers correspondant au pattern
        pattern = f"bordereau_{transaction_id}_*.pdf"
        matching_files = list(search_dir.glob(pattern))

        if not matching_files:
            return None

        # Retourner le plus récent (par nom de fichier qui contient timestamp)
        latest_file = sorted(matching_files, reverse=True)[0]
        return str(latest_file)

    def list_bordereaux(self, user_id: Optional[int] = None) -> List[Dict[str, any]]:
        """
        Liste tous les bordereaux téléchargés.

        Args:
            user_id: ID utilisateur (optionnel)

        Returns:
            Liste de dicts avec infos sur chaque bordereau:
            [
                {
                    'path': str,
                    'transaction_id': int,
                    'filename': str,
                    'size_bytes': int,
                    'created_at': datetime
                }
            ]

        Example:
            >>> service = VintedBordereauService()
            >>> bordereaux = service.list_bordereaux(user_id=1)
            >>> print(len(bordereaux))
            15
        """
        # Déterminer le dossier de recherche
        if user_id:
            search_dir = self.temp_dir / f"user_{user_id}"
        else:
            search_dir = self.temp_dir

        if not search_dir.exists():
            return []

        bordereaux = []

        # Parcourir tous les PDFs
        for pdf_file in search_dir.glob("bordereau_*.pdf"):
            try:
                # Extraire transaction_id du nom de fichier
                # Format: bordereau_{transaction_id}_{timestamp}.pdf
                filename_parts = pdf_file.stem.split('_')
                if len(filename_parts) >= 2:
                    transaction_id = int(filename_parts[1])
                else:
                    transaction_id = None

                # Récupérer infos fichier
                stats = pdf_file.stat()

                bordereaux.append({
                    'path': str(pdf_file),
                    'transaction_id': transaction_id,
                    'filename': pdf_file.name,
                    'size_bytes': stats.st_size,
                    'created_at': datetime.fromtimestamp(stats.st_ctime)
                })

            except (ValueError, IndexError) as e:
                logger.warning(f"⚠️  Fichier ignoré (format invalide): {pdf_file.name}")
                continue

        # Trier par date décroissante
        bordereaux.sort(key=lambda x: x['created_at'], reverse=True)

        return bordereaux

    def delete_bordereau(
        self,
        transaction_id: int,
        user_id: Optional[int] = None
    ) -> bool:
        """
        Supprime le(s) bordereau(x) d'une transaction.

        Args:
            transaction_id: ID de la transaction
            user_id: ID utilisateur

        Returns:
            True si au moins un fichier supprimé, False sinon

        Example:
            >>> service = VintedBordereauService()
            >>> deleted = service.delete_bordereau(123, user_id=1)
            >>> print(deleted)
            True
        """
        # Déterminer le dossier
        if user_id:
            search_dir = self.temp_dir / f"user_{user_id}"
        else:
            search_dir = self.temp_dir

        if not search_dir.exists():
            return False

        # Chercher et supprimer tous les fichiers correspondants
        pattern = f"bordereau_{transaction_id}_*.pdf"
        matching_files = list(search_dir.glob(pattern))

        deleted_count = 0
        for file_path in matching_files:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.info(f"🗑️  Bordereau supprimé: {file_path.name}")
            except Exception as e:
                logger.error(f"❌ Erreur suppression {file_path.name}: {e}", exc_info=True)

        return deleted_count > 0

    def cleanup_old_bordereaux(
        self,
        days: int = 30,
        user_id: Optional[int] = None
    ) -> int:
        """
        Nettoie les bordereaux plus anciens que X jours.

        Args:
            days: Nombre de jours (défaut: 30)
            user_id: ID utilisateur (optionnel)

        Returns:
            Nombre de fichiers supprimés

        Example:
            >>> service = VintedBordereauService()
            >>> deleted = service.cleanup_old_bordereaux(days=90, user_id=1)
            >>> print(f"{deleted} bordereaux supprimés")
            12 bordereaux supprimés
        """
        # Déterminer le dossier
        if user_id:
            search_dir = self.temp_dir / f"user_{user_id}"
        else:
            search_dir = self.temp_dir

        if not search_dir.exists():
            return 0

        # Calculer timestamp limite
        cutoff_timestamp = datetime.now().timestamp() - (days * 24 * 3600)

        deleted_count = 0

        # Parcourir tous les bordereaux
        for pdf_file in search_dir.glob("bordereau_*.pdf"):
            try:
                # Vérifier date de création
                stats = pdf_file.stat()
                if stats.st_ctime < cutoff_timestamp:
                    pdf_file.unlink()
                    deleted_count += 1
                    logger.debug(f"🗑️  Bordereau ancien supprimé: {pdf_file.name}")

            except Exception as e:
                logger.error(f"❌ Erreur suppression {pdf_file.name}: {e}", exc_info=True)

        if deleted_count > 0:
            logger.info(f"🧹 Nettoyage: {deleted_count} bordereaux supprimés (>{days} jours)")

        return deleted_count
