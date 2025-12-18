"""
Test du proxy HTTP générique du plugin StoFlow
Le backend peut exécuter n'importe quelle requête Vinted via le plugin
"""

import asyncio
import websockets
import json


class VintedProxyClient:
    """
    Client pour communiquer avec le plugin StoFlow et exécuter
    des requêtes Vinted en utilisant les cookies du navigateur
    """

    def __init__(self, websocket_url="ws://localhost:8765"):
        self.websocket_url = websocket_url
        self.ws = None

    async def connect(self):
        """Connecte au WebSocket du plugin"""
        self.ws = await websockets.connect(self.websocket_url)
        print("✅ Connecté au plugin StoFlow")

    async def disconnect(self):
        """Déconnecte du plugin"""
        if self.ws:
            await self.ws.close()
            print("👋 Déconnecté du plugin")

    async def execute_request(self, url, method="GET", headers=None, body=None, timeout=30000):
        """
        Exécute une requête HTTP via le plugin

        Args:
            url: URL complète (ex: https://www.vinted.fr/api/v2/users/current)
            method: Méthode HTTP (GET, POST, PUT, DELETE, PATCH)
            headers: Dict des headers personnalisés
            body: Body de la requête (pour POST/PUT/PATCH)
            timeout: Timeout en ms (défaut: 30000)

        Returns:
            dict: {
                "success": bool,
                "status": int,
                "statusText": str,
                "headers": dict,
                "data": any
            }
        """
        message = {
            "action": "EXECUTE_HTTP_REQUEST",
            "request": {
                "url": url,
                "method": method,
                "credentials": "include"  # IMPORTANT: inclut les cookies automatiquement
            }
        }

        if headers:
            message["request"]["headers"] = headers

        if body:
            message["request"]["body"] = body

        if timeout:
            message["request"]["timeout"] = timeout

        # Envoyer au plugin
        await self.ws.send(json.dumps(message))
        print(f"📤 Envoyé: {method} {url}")

        # Recevoir la réponse
        response = await self.ws.recv()
        result = json.loads(response)

        if result.get("success"):
            print(f"✅ Réponse: {result['status']} {result['statusText']}")
        else:
            print(f"❌ Erreur: {result.get('error', 'Unknown error')}")

        return result

    async def execute_batch(self, requests):
        """
        Exécute plusieurs requêtes en parallèle

        Args:
            requests: Liste de requêtes [{url, method, headers, body}, ...]

        Returns:
            dict: {"success": bool, "results": [response1, response2, ...]}
        """
        message = {
            "action": "EXECUTE_BATCH_REQUESTS",
            "requests": [
                {
                    "url": req["url"],
                    "method": req.get("method", "GET"),
                    "headers": req.get("headers"),
                    "body": req.get("body"),
                    "credentials": "include"
                }
                for req in requests
            ]
        }

        await self.ws.send(json.dumps(message))
        print(f"📦 Batch: {len(requests)} requêtes")

        response = await self.ws.recv()
        result = json.loads(response)

        return result

    async def get_user_data(self):
        """Récupère les données utilisateur (extraction + tokens)"""
        message = {"action": "GET_USER_DATA"}

        await self.ws.send(json.dumps(message))
        print("👤 Récupération données utilisateur...")

        response = await self.ws.recv()
        result = json.loads(response)

        return result


async def test_get_user_info(client):
    """Test 1: Récupérer les infos utilisateur"""
    print("\n" + "=" * 50)
    print("TEST 1: Récupérer les infos utilisateur")
    print("=" * 50)

    response = await client.execute_request(
        url="https://www.vinted.fr/api/v2/users/current",
        method="GET"
    )

    if response["success"]:
        user = response["data"]
        print(f"\n👤 Utilisateur:")
        print(f"  - ID: {user.get('id')}")
        print(f"  - Login: {user.get('login')}")
        print(f"  - Email: {user.get('email')}")


async def test_get_products(client, user_id, csrf_token, anon_id):
    """Test 2: Récupérer les produits d'un utilisateur"""
    print("\n" + "=" * 50)
    print("TEST 2: Récupérer les produits (page 1)")
    print("=" * 50)

    response = await client.execute_request(
        url=f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items?page=1&per_page=20",
        method="GET",
        headers={
            "X-CSRF-Token": csrf_token,
            "X-Anon-Id": anon_id
        }
    )

    if response["success"]:
        data = response["data"]
        items = data.get("items", [])
        pagination = data.get("pagination", {})

        print(f"\n📦 Produits:")
        print(f"  - Total: {pagination.get('total_entries')}")
        print(f"  - Pages: {pagination.get('total_pages')}")
        print(f"  - Page actuelle: {len(items)} produits")

        if items:
            print(f"\nPremiers produits:")
            for item in items[:3]:
                print(f"  - [{item['id']}] {item['title']} - {item['price']} €")


async def test_get_all_products_pagination(client, user_id, csrf_token, anon_id):
    """Test 3: Récupérer TOUS les produits avec pagination"""
    print("\n" + "=" * 50)
    print("TEST 3: Récupérer TOUS les produits (pagination)")
    print("=" * 50)

    all_products = []
    page = 1
    total_pages = None

    while True:
        response = await client.execute_request(
            url=f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items?page={page}&per_page=20",
            method="GET",
            headers={
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            }
        )

        if not response["success"]:
            print(f"❌ Erreur page {page}")
            break

        data = response["data"]
        items = data.get("items", [])
        pagination = data.get("pagination", {})

        if page == 1:
            total_pages = pagination.get("total_pages")
            print(f"📊 Total: {pagination.get('total_entries')} produits sur {total_pages} pages")

        all_products.extend(items)
        print(f"📄 Page {page}/{total_pages}: {len(items)} produits récupérés")

        if page >= total_pages:
            break

        page += 1

        # Throttling pour éviter rate limiting
        await asyncio.sleep(0.1)

    print(f"\n✅ Total récupéré: {len(all_products)} produits")
    return all_products


async def test_batch_requests(client, user_id, csrf_token, anon_id):
    """Test 4: Requêtes en batch (parallèle)"""
    print("\n" + "=" * 50)
    print("TEST 4: Batch - Récupérer 3 pages en parallèle")
    print("=" * 50)

    requests = [
        {
            "url": f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items?page=1&per_page=20",
            "method": "GET",
            "headers": {
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            }
        },
        {
            "url": f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items?page=2&per_page=20",
            "method": "GET",
            "headers": {
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            }
        },
        {
            "url": f"https://www.vinted.fr/api/v2/wardrobe/{user_id}/items?page=3&per_page=20",
            "method": "GET",
            "headers": {
                "X-CSRF-Token": csrf_token,
                "X-Anon-Id": anon_id
            }
        }
    ]

    result = await client.execute_batch(requests)

    if result["success"]:
        total_items = 0
        for i, response in enumerate(result["results"]):
            if response["success"]:
                items = response["data"].get("items", [])
                total_items += len(items)
                print(f"✅ Page {i + 1}: {len(items)} produits")

        print(f"\n📦 Total récupéré en batch: {total_items} produits")


async def test_create_product(client, csrf_token, anon_id):
    """Test 5: Créer un nouveau produit (POST)"""
    print("\n" + "=" * 50)
    print("TEST 5: Créer un nouveau produit (POST)")
    print("=" * 50)

    new_product = {
        "title": "Test - T-shirt Nike",
        "description": "T-shirt Nike en très bon état",
        "price": "15.00",
        "currency": "EUR",
        "brand_id": 53,  # Nike
        "size_id": 206,  # M
        "catalog_id": 5,  # Vêtements homme
        "color_ids": [1],  # Noir
        "status_ids": [6],  # Très bon état
    }

    response = await client.execute_request(
        url="https://www.vinted.fr/api/v2/items",
        method="POST",
        headers={
            "X-CSRF-Token": csrf_token,
            "X-Anon-Id": anon_id,
            "Content-Type": "application/json"
        },
        body=new_product
    )

    if response["success"]:
        item = response["data"].get("item", {})
        print(f"\n✅ Produit créé:")
        print(f"  - ID: {item.get('id')}")
        print(f"  - Titre: {item.get('title')}")
        print(f"  - Prix: {item.get('price')} €")


async def test_update_product(client, item_id, csrf_token, anon_id):
    """Test 6: Modifier un produit (PUT)"""
    print("\n" + "=" * 50)
    print(f"TEST 6: Modifier le produit {item_id} (PUT)")
    print("=" * 50)

    updates = {
        "price": "12.00",
        "description": "Prix réduit ! T-shirt Nike en excellent état"
    }

    response = await client.execute_request(
        url=f"https://www.vinted.fr/api/v2/items/{item_id}",
        method="PUT",
        headers={
            "X-CSRF-Token": csrf_token,
            "X-Anon-Id": anon_id,
            "Content-Type": "application/json"
        },
        body=updates
    )

    if response["success"]:
        item = response["data"].get("item", {})
        print(f"\n✅ Produit modifié:")
        print(f"  - Nouveau prix: {item.get('price')} €")
        print(f"  - Nouvelle description: {item.get('description')[:50]}...")


async def test_delete_product(client, item_id, csrf_token, anon_id):
    """Test 7: Supprimer un produit (DELETE)"""
    print("\n" + "=" * 50)
    print(f"TEST 7: Supprimer le produit {item_id} (DELETE)")
    print("=" * 50)

    response = await client.execute_request(
        url=f"https://www.vinted.fr/api/v2/items/{item_id}",
        method="DELETE",
        headers={
            "X-CSRF-Token": csrf_token,
            "X-Anon-Id": anon_id
        }
    )

    if response["success"] and response["status"] == 204:
        print(f"\n✅ Produit {item_id} supprimé")
    else:
        print(f"\n❌ Erreur suppression: {response.get('error')}")


async def main():
    """Fonction principale de test"""
    print("🚀 Test du Proxy HTTP Générique - Plugin StoFlow")
    print("=" * 60)

    # Créer le client
    client = VintedProxyClient()

    try:
        # Se connecter au plugin (via WebSocket)
        await client.connect()

        # 1. D'abord récupérer les données utilisateur et tokens
        print("\n📥 Récupération des données utilisateur et tokens...")
        user_data = await client.get_user_data()

        if not user_data:
            print("❌ Impossible de récupérer les données utilisateur")
            print("⚠️ Assurez-vous que:")
            print("  1. Le plugin est chargé dans Firefox")
            print("  2. Vous êtes sur une page vinted.fr")
            print("  3. Vous êtes connecté à Vinted")
            return

        user_id = user_data.get("user_id")
        csrf_token = user_data.get("csrf_token")
        anon_id = user_data.get("anon_id")

        print(f"✅ Données récupérées:")
        print(f"  - User ID: {user_id}")
        print(f"  - CSRF Token: {'✅' if csrf_token else '❌'}")
        print(f"  - Anon ID: {'✅' if anon_id else '❌'}")

        # Tests des différentes fonctionnalités
        await test_get_user_info(client)
        await test_get_products(client, user_id, csrf_token, anon_id)
        await test_batch_requests(client, user_id, csrf_token, anon_id)

        # Test de pagination complète (optionnel)
        # await test_get_all_products_pagination(client, user_id, csrf_token, anon_id)

        # Tests de modification (à décommenter pour tester)
        # await test_create_product(client, csrf_token, anon_id)
        # await test_update_product(client, ITEM_ID, csrf_token, anon_id)
        # await test_delete_product(client, ITEM_ID, csrf_token, anon_id)

        print("\n" + "=" * 60)
        print("✅ Tous les tests terminés avec succès !")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Déconnexion
        await client.disconnect()


if __name__ == "__main__":
    # Lancer les tests
    asyncio.run(main())
