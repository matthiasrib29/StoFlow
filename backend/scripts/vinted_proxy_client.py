"""
Client HTTP pour communiquer avec le plugin StoFlow
et exécuter des requêtes Vinted via le navigateur de l'utilisateur

Architecture:
    Backend (ce script)
    → HTTP POST → Frontend Web Page
    → Chrome Extension API → Plugin Content Script
    → Fetch avec cookies → Vinted API
    → Réponse → Frontend → Backend
"""

import requests
import time
from typing import Optional, Dict, List, Any


class VintedProxyClient:
    """
    Client pour exécuter des requêtes Vinted via le plugin navigateur
    Le plugin utilise les cookies et le contexte du navigateur de l'utilisateur
    """

    def __init__(self, frontend_url: str = "http://localhost:8000"):
        """
        Args:
            frontend_url: URL du backend qui communique avec le plugin
        """
        self.frontend_url = frontend_url
        self.api_base = f"{frontend_url}/api/plugin"
        self.session = requests.Session()

    def execute_request(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Exécute une requête HTTP via le plugin

        Args:
            url: URL complète Vinted (ex: https://www.vinted.fr/api/v2/users/current)
            method: Méthode HTTP (GET, POST, PUT, DELETE, PATCH)
            headers: Headers personnalisés (optionnel)
            body: Body de la requête (pour POST/PUT/PATCH)
            timeout: Timeout en secondes

        Returns:
            dict: {
                "success": bool,
                "status": int,
                "statusText": str,
                "headers": dict,
                "data": any,
                "error": str (si erreur)
            }
        """
        payload = {
            "action": "EXECUTE_HTTP_REQUEST",
            "request": {
                "url": url,
                "method": method,
                "credentials": "include"  # Cookies automatiques
            }
        }

        if headers:
            payload["request"]["headers"] = headers

        if body:
            payload["request"]["body"] = body

        try:
            response = self.session.post(
                f"{self.api_base}/execute",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "status": 0,
                "statusText": "Timeout",
                "headers": {},
                "data": None,
                "error": "Request timeout"
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "status": 0,
                "statusText": "Error",
                "headers": {},
                "data": None,
                "error": str(e)
            }

    def execute_batch(
        self,
        requests_list: List[Dict],
        timeout: int = 60
    ) -> Dict[str, Any]:
        """
        Exécute plusieurs requêtes en parallèle

        Args:
            requests_list: Liste de requêtes [
                {"url": "...", "method": "GET", "headers": {...}},
                ...
            ]
            timeout: Timeout total en secondes

        Returns:
            dict: {
                "success": bool,
                "results": [response1, response2, ...]
            }
        """
        payload = {
            "action": "EXECUTE_BATCH_REQUESTS",
            "requests": [
                {
                    "url": req["url"],
                    "method": req.get("method", "GET"),
                    "headers": req.get("headers"),
                    "body": req.get("body"),
                    "credentials": "include"
                }
                for req in requests_list
            ]
        }

        try:
            response = self.session.post(
                f"{self.api_base}/execute",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }

    def get_user_data(self, timeout: int = 30) -> Optional[Dict]:
        """
        Récupère les données utilisateur Vinted (extraction depuis la page)

        Returns:
            dict: {
                "user_id": int,
                "login": str,
                "email": str,
                "anon_id": str,
                "csrf_token": str,
                "real_name": str,
                "business_account": int | None
            }
        """
        payload = {"action": "GET_USER_DATA"}

        try:
            response = self.session.post(
                f"{self.api_base}/execute",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"❌ Erreur récupération user data: {e}")
            return None

    # ==================== HELPERS VINTED ====================

    def get_user_products(
        self,
        user_id: int,
        csrf_token: str,
        anon_id: str,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Récupère les produits d'un utilisateur (1 page)"""
        return self.execute_request(
            url=f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items",
            method="GET",
            headers={
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            }
        )

    def get_all_products(
        self,
        user_id: int,
        csrf_token: str,
        anon_id: str,
        throttle: float = 0.1
    ) -> List[Dict]:
        """
        Récupère TOUS les produits d'un utilisateur (pagination automatique)

        Args:
            user_id: ID utilisateur Vinted
            csrf_token: Token CSRF
            anon_id: ID anonyme
            throttle: Délai entre les requêtes en secondes (défaut: 0.1s)

        Returns:
            list: Liste de tous les produits
        """
        all_products = []
        page = 1
        total_pages = None

        while True:
            response = self.execute_request(
                url=f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items?page={page}&per_page=20",
                method="GET",
                headers={
                    "X-CSRF-Token": csrf_token,
                    "X-Anon-Id": anon_id
                }
            )

            if not response["success"]:
                print(f"❌ Erreur page {page}: {response.get('error')}")
                break

            data = response["data"]
            items = data.get("items", [])
            pagination = data.get("pagination", {})

            if page == 1:
                total_pages = pagination.get("total_pages")
                total_items = pagination.get("total_entries")
                print(f"📊 Total: {total_items} produits sur {total_pages} pages")

            all_products.extend(items)
            print(f"📄 Page {page}/{total_pages}: {len(items)} produits")

            if page >= total_pages:
                break

            page += 1
            time.sleep(throttle)  # Throttling anti-rate-limit

        return all_products

    def create_product(
        self,
        csrf_token: str,
        anon_id: str,
        title: str,
        description: str,
        price: str,
        brand_id: int,
        size_id: int,
        catalog_id: int,
        color_ids: List[int],
        status_ids: List[int],
        **kwargs
    ) -> Dict:
        """
        Crée un nouveau produit sur Vinted

        Args:
            csrf_token: Token CSRF
            anon_id: ID anonyme
            title: Titre du produit
            description: Description
            price: Prix (string, ex: "15.00")
            brand_id: ID de la marque
            size_id: ID de la taille
            catalog_id: ID de la catégorie
            color_ids: Liste des IDs couleurs
            status_ids: Liste des IDs états
            **kwargs: Autres paramètres optionnels

        Returns:
            dict: Réponse avec le produit créé
        """
        product_data = {
            "title": title,
            "description": description,
            "price": price,
            "currency": "EUR",
            "brand_id": brand_id,
            "size_id": size_id,
            "catalog_id": catalog_id,
            "color_ids": color_ids,
            "status_ids": status_ids,
            **kwargs
        }

        return self.execute_request(
            url="https://www.vinted.fr/api/v2/items",
            method="POST",
            headers={
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id,
                "Content-Type": "application/json"
            },
            body=product_data
        )

    def update_product(
        self,
        item_id: int,
        csrf_token: str,
        anon_id: str,
        **updates
    ) -> Dict:
        """
        Modifie un produit existant

        Args:
            item_id: ID du produit
            csrf_token: Token CSRF
            anon_id: ID anonyme
            **updates: Champs à modifier (price, description, etc.)

        Returns:
            dict: Réponse avec le produit modifié
        """
        return self.execute_request(
            url=f"https://www.vinted.fr/api/v2/items/{item_id}",
            method="PUT",
            headers={
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id,
                "Content-Type": "application/json"
            },
            body=updates
        )

    def delete_product(
        self,
        item_id: int,
        csrf_token: str,
        anon_id: str
    ) -> Dict:
        """
        Supprime un produit

        Args:
            item_id: ID du produit
            csrf_token: Token CSRF
            anon_id: ID anonyme

        Returns:
            dict: Réponse (status 204 si succès)
        """
        return self.execute_request(
            url=f"https://www.vinted.fr/api/v2/items/{item_id}",
            method="DELETE",
            headers={
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            }
        )

    def upload_photo(
        self,
        item_id: int,
        csrf_token: str,
        anon_id: str,
        photo_data: bytes,
        filename: str = "photo.jpg"
    ) -> Dict:
        """
        Upload une photo pour un produit

        Args:
            item_id: ID du produit
            csrf_token: Token CSRF
            anon_id: ID anonyme
            photo_data: Données binaires de l'image
            filename: Nom du fichier

        Returns:
            dict: Réponse avec l'URL de la photo
        """
        # Note: L'upload d'images nécessite un FormData
        # Il faudra adapter selon l'API Vinted
        return self.execute_request(
            url=f"https://www.vinted.fr/api/v2/items/{item_id}/photos",
            method="POST",
            headers={
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            },
            body={
                "photo": {
                    "data": photo_data,
                    "filename": filename
                }
            }
        )

    def get_item_stats(
        self,
        item_id: int,
        csrf_token: str,
        anon_id: str
    ) -> Dict:
        """
        Récupère les statistiques d'un produit (vues, favoris)

        Args:
            item_id: ID du produit
            csrf_token: Token CSRF
            anon_id: ID anonyme

        Returns:
            dict: Statistiques du produit
        """
        return self.execute_request(
            url=f"https://www.vinted.fr/api/v2/items/{item_id}/stats",
            method="GET",
            headers={
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            }
        )


# ==================== EXEMPLE D'UTILISATION ====================

def example_usage():
    """Exemple d'utilisation du client"""

    # 1. Créer le client
    client = VintedProxyClient(frontend_url="http://localhost:8000")

    # 2. Récupérer les données utilisateur
    print("📥 Récupération des données utilisateur...")
    user_data = client.get_user_data()

    if not user_data:
        print("❌ Erreur: Données utilisateur non disponibles")
        print("⚠️ Assurez-vous que:")
        print("  1. Le plugin est chargé dans Firefox")
        print("  2. Vous êtes sur une page vinted.fr")
        print("  3. Vous êtes connecté à Vinted")
        print("  4. Le backend tourne sur http://localhost:8000")
        return

    user_id = user_data["user_id"]
    csrf_token = user_data["csrf_token"]
    anon_id = user_data["anon_id"]

    print(f"✅ User ID: {user_id}")
    print(f"✅ Login: {user_data['login']}")

    # 3. Récupérer tous les produits
    print("\n📦 Récupération de tous les produits...")
    products = client.get_all_products(user_id, csrf_token, anon_id)
    print(f"✅ Total: {len(products)} produits récupérés")

    # 4. Créer un nouveau produit
    print("\n➕ Création d'un produit...")
    new_product = client.create_product(
        csrf_token=csrf_token,
        anon_id=anon_id,
        title="T-shirt Nike Noir",
        description="T-shirt Nike en excellent état, taille M",
        price="15.00",
        brand_id=53,  # Nike
        size_id=206,  # M
        catalog_id=5,  # Vêtements homme
        color_ids=[1],  # Noir
        status_ids=[6]  # Très bon état
    )

    if new_product["success"]:
        item_id = new_product["data"]["item"]["id"]
        print(f"✅ Produit créé avec ID: {item_id}")

        # 5. Modifier le produit
        print(f"\n✏️ Modification du produit {item_id}...")
        updated = client.update_product(
            item_id=item_id,
            csrf_token=csrf_token,
            anon_id=anon_id,
            price="12.00",
            description="Prix réduit ! T-shirt Nike en excellent état"
        )

        if updated["success"]:
            print("✅ Produit modifié")

        # 6. Récupérer les stats
        print(f"\n📊 Statistiques du produit {item_id}...")
        stats = client.get_item_stats(item_id, csrf_token, anon_id)

        if stats["success"]:
            print(f"✅ Vues: {stats['data'].get('view_count', 0)}")
            print(f"✅ Favoris: {stats['data'].get('favourite_count', 0)}")

        # 7. Supprimer le produit (optionnel)
        # print(f"\n🗑️ Suppression du produit {item_id}...")
        # deleted = client.delete_product(item_id, csrf_token, anon_id)
        # if deleted["success"]:
        #     print("✅ Produit supprimé")


if __name__ == "__main__":
    example_usage()
