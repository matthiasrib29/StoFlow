"""
Serveur HTTP simple qui fait le pont entre le backend et le plugin

Architecture:
    Backend Python
    → POST /api/plugin/execute
    → Ce serveur (FastAPI)
    → Page HTML (api-bridge.html)
    → Chrome Extension API
    → Plugin Content Script
    → Vinted API

Lancer avec: python api_bridge_server.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import asyncio
import os


app = FastAPI(title="StoFlow API Bridge", version="1.0.0")

# CORS pour permettre les requêtes depuis le backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production: mettre l'URL du backend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== MODELS ====================

class PluginRequest(BaseModel):
    """Requête HTTP à exécuter via le plugin"""
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    credentials: str = "include"
    timeout: int = 30000


class ExecuteCommand(BaseModel):
    """Commande à envoyer au plugin"""
    action: str
    request: Optional[PluginRequest] = None
    requests: Optional[List[PluginRequest]] = None


# ==================== STORAGE ====================

# Stockage temporaire des réponses
# (en production, utiliser Redis ou une vraie queue)
pending_requests = {}
completed_responses = {}


# ==================== ROUTES ====================

@app.get("/")
async def root():
    """Page d'accueil avec le pont API"""
    # Servir le fichier api-bridge.html
    html_path = "../../StoFlow_Plugin/public/api-bridge.html"

    if not os.path.exists(html_path):
        return HTMLResponse(content="""
        <html>
            <body>
                <h1>StoFlow API Bridge</h1>
                <p>⚠️ Fichier api-bridge.html non trouvé</p>
                <p>Chemin attendu: {}</p>
            </body>
        </html>
        """.format(html_path), status_code=200)

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    return HTMLResponse(content=content)


@app.post("/api/plugin/execute")
async def execute_plugin_command(command: ExecuteCommand):
    """
    Endpoint pour exécuter une commande via le plugin

    Le backend envoie une commande ici, qui est transmise au plugin
    via la page HTML ouverte dans le navigateur

    Args:
        command: Commande à exécuter (GET_USER_DATA, EXECUTE_HTTP_REQUEST, etc.)

    Returns:
        Réponse du plugin
    """
    print(f"📥 Commande reçue: {command.action}")

    # TODO: Implémenter la communication avec la page HTML
    # Pour l'instant, retourner une erreur explicative

    return {
        "success": False,
        "error": "Communication avec le plugin non implémentée",
        "info": {
            "message": "Pour utiliser cette API, vous devez:",
            "steps": [
                "1. Ouvrir http://localhost:8000 dans Firefox",
                "2. S'assurer que le plugin StoFlow est chargé",
                "3. Utiliser le client Python vinted_proxy_client.py",
                "4. Ou implémenter un WebSocket pour communication temps réel"
            ]
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "ok",
        "service": "StoFlow API Bridge",
        "version": "1.0.0"
    }


@app.get("/api/plugin/status")
async def plugin_status():
    """Vérifie si le plugin est connecté"""
    # TODO: Vérifier la connexion réelle avec le plugin
    return {
        "plugin_available": False,
        "message": "Ouvrez http://localhost:8000 dans Firefox avec le plugin chargé"
    }


# ==================== SOLUTION ALTERNATIVE: WebSocket ====================

"""
Pour une vraie communication temps réel, il faudrait:

1. Ajouter un WebSocket endpoint:

   from fastapi import WebSocket

   @app.websocket("/ws")
   async def websocket_endpoint(websocket: WebSocket):
       await websocket.accept()
       # Communication bidirectionnelle avec le plugin

2. Modifier api-bridge.html pour se connecter au WebSocket:

   const ws = new WebSocket('ws://localhost:8000/ws');
   ws.onmessage = (event) => {
       // Recevoir commandes du backend
       // Envoyer au plugin
       // Retourner réponse
   };

3. Le backend utilise le WebSocket pour envoyer des commandes:

   await websocket.send_json({
       "action": "EXECUTE_HTTP_REQUEST",
       "request": {...}
   })

   response = await websocket.receive_json()
"""


# ==================== MAIN ====================

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 StoFlow API Bridge Server")
    print("=" * 60)
    print()
    print("📡 Endpoints:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/api/plugin/execute")
    print("  - http://localhost:8000/api/health")
    print()
    print("📝 Instructions:")
    print("  1. Ouvrir http://localhost:8000 dans Firefox")
    print("  2. Charger le plugin StoFlow")
    print("  3. Ouvrir une page vinted.fr")
    print("  4. Utiliser vinted_proxy_client.py depuis le backend")
    print()
    print("⚠️  Note: Pour une vraie communication temps réel,")
    print("    il faut implémenter un WebSocket (voir code)")
    print()
    print("=" * 60)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
