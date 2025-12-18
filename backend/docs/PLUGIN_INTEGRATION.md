# Intégration Plugin Stoflow

**Version:** 1.0
**Dernière mise à jour:** 2025-12-08

---

## 🎯 Vue d'ensemble

Le plugin Stoflow est une extension Firefox/Chrome qui permet au backend d'interagir avec l'API Vinted en utilisant les cookies et la session de l'utilisateur.

**Rôle du plugin:** Proxy entre le backend Python et l'API Vinted

---

## 🏗️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────┐
│  BACKEND PYTHON (FastAPI)                                    │
│  ├─ API Endpoints (/api/integrations/vinted/*)              │
│  ├─ VintedProxyClient (scripts/vinted_proxy_client.py)      │
│  └─ Services (vinted_adapter, vinted_mapper, etc.)          │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP POST
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  API BRIDGE SERVER (FastAPI, port 8000)                     │
│  ├─ scripts/api_bridge_server.py                            │
│  ├─ POST /api/plugin/execute                                │
│  └─ Sert page HTML (api-bridge.html)                        │
└─────────────────┬───────────────────────────────────────────┘
                  │ Transmet via Page HTML
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PAGE WEB (http://localhost:8000)                           │
│  ├─ Ouverte dans Firefox                                    │
│  ├─ Communique avec plugin via chrome.runtime API           │
│  └─ Bridge entre backend et plugin                          │
└─────────────────┬───────────────────────────────────────────┘
                  │ chrome.runtime.sendMessage()
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  PLUGIN FIREFOX (Extension)                                 │
│  ├─ background.js (message handler)                         │
│  ├─ content.js (injecté sur vinted.fr)                      │
│  ├─ popup.html (UI authentification)                        │
│  └─ Accès aux cookies Vinted                                │
└─────────────────┬───────────────────────────────────────────┘
                  │ fetch() avec credentials: 'include'
                  ▼
┌─────────────────────────────────────────────────────────────┐
│  VINTED API (https://www.vinted.fr/api/v2/*)                │
│  ├─ Reçoit requêtes avec cookies utilisateur                │
│  └─ Retourne données JSON                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Composants du Plugin

### 1. Manifest (manifest.json)

**Firefox (manifest v2):**
```json
{
  "manifest_version": 2,
  "name": "Stoflow Plugin",
  "version": "1.0.0",
  "description": "Publier vos produits sur Vinted automatiquement",

  "permissions": [
    "storage",
    "tabs",
    "https://www.vinted.fr/*",
    "https://www.vinted.com/*",
    "https://www.vinted.be/*"
  ],

  "background": {
    "scripts": ["background.js"]
  },

  "content_scripts": [
    {
      "matches": [
        "https://www.vinted.fr/*",
        "https://www.vinted.com/*",
        "https://www.vinted.be/*"
      ],
      "js": ["content.js"],
      "run_at": "document_end"
    }
  ],

  "browser_action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

**Chrome (manifest v3):**
```json
{
  "manifest_version": 3,
  "name": "Stoflow Plugin",
  "version": "1.0.0",
  "description": "Publier vos produits sur Vinted automatiquement",

  "permissions": [
    "storage",
    "tabs"
  ],

  "host_permissions": [
    "https://www.vinted.fr/*",
    "https://www.vinted.com/*",
    "https://www.vinted.be/*"
  ],

  "background": {
    "service_worker": "background.js"
  },

  "content_scripts": [
    {
      "matches": [
        "https://www.vinted.fr/*",
        "https://www.vinted.com/*",
        "https://www.vinted.be/*"
      ],
      "js": ["content.js"],
      "run_at": "document_end"
    }
  ],

  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

---

### 2. Background Script (background.js)

**Rôle:** Gérer les messages entre popup, content script et page bridge.

```javascript
// Écouter messages depuis popup ou content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("[Background] Message reçu:", request.action);

  if (request.action === "execute_vinted_request") {
    // Transmettre à content script injecté sur vinted.fr
    executeOnVinted(request.data)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));

    return true; // Permet réponse asynchrone
  }

  if (request.action === "get_user_data") {
    getUserDataFromVinted()
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));

    return true;
  }
});

// Exécuter requête sur onglet Vinted
async function executeOnVinted(requestData) {
  // Trouver onglet Vinted ouvert
  const tabs = await chrome.tabs.query({ url: "https://www.vinted.fr/*" });

  if (tabs.length === 0) {
    throw new Error("Aucun onglet Vinted ouvert");
  }

  // Envoyer message au content script
  const response = await chrome.tabs.sendMessage(tabs[0].id, {
    action: "execute_request",
    data: requestData
  });

  return response;
}

// Récupérer données utilisateur depuis Vinted
async function getUserDataFromVinted() {
  const tabs = await chrome.tabs.query({ url: "https://www.vinted.fr/*" });

  if (tabs.length === 0) {
    throw new Error("Aucun onglet Vinted ouvert");
  }

  const response = await chrome.tabs.sendMessage(tabs[0].id, {
    action: "get_user_data"
  });

  return response;
}
```

---

### 3. Content Script (content.js)

**Rôle:** Injecté sur vinted.fr, exécute les requêtes avec les cookies utilisateur.

```javascript
// Écouter messages depuis background
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("[Content Script] Message reçu:", request.action);

  if (request.action === "execute_request") {
    executeVintedRequest(request.data)
      .then(result => sendResponse({ success: true, data: result }))
      .catch(error => sendResponse({ success: false, error: error.message }));

    return true;
  }

  if (request.action === "get_user_data") {
    extractUserData()
      .then(data => sendResponse({ success: true, data }))
      .catch(error => sendResponse({ success: false, error: error.message }));

    return true;
  }
});

// Exécuter requête HTTP avec credentials
async function executeVintedRequest(requestData) {
  const { url, method, headers, body } = requestData;

  const response = await fetch(url, {
    method: method || "GET",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
      ...headers
    },
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include" // 🔑 CRUCIAL: Inclut les cookies
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const data = await response.json();
  return data;
}

// Extraire données utilisateur depuis window.vinted
function extractUserData() {
  // Vinted expose des données dans window.vinted
  if (!window.vinted || !window.vinted.config) {
    throw new Error("Vinted config non disponible. Es-tu connecté ?");
  }

  const config = window.vinted.config;

  return {
    user_id: config.user?.id,
    login: config.user?.login,
    email: config.user?.email,
    anon_id: config.user?.anon_id,
    csrf_token: config.csrf_token,
    real_name: config.user?.real_name,
    business_account: config.user?.business_account
  };
}
```

---

### 4. Popup (popup.html + popup.js)

**Rôle:** Interface utilisateur pour authentification et status.

**popup.html:**
```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Stoflow Plugin</title>
  <style>
    body {
      width: 300px;
      padding: 20px;
      font-family: Arial, sans-serif;
    }
    .status {
      padding: 10px;
      border-radius: 5px;
      margin-bottom: 15px;
    }
    .status.connected {
      background-color: #d4edda;
      color: #155724;
    }
    .status.disconnected {
      background-color: #f8d7da;
      color: #721c24;
    }
    button {
      width: 100%;
      padding: 10px;
      background-color: #007bff;
      color: white;
      border: none;
      border-radius: 5px;
      cursor: pointer;
    }
    button:hover {
      background-color: #0056b3;
    }
    input {
      width: 100%;
      padding: 8px;
      margin-bottom: 10px;
      border: 1px solid #ccc;
      border-radius: 3px;
    }
  </style>
</head>
<body>
  <div id="status-container"></div>

  <div id="login-form">
    <h3>Connexion Stoflow</h3>
    <input type="email" id="email" placeholder="Email">
    <input type="password" id="password" placeholder="Mot de passe">
    <button id="login-btn">Se connecter</button>
  </div>

  <div id="connected-view" style="display: none;">
    <h3>Connecté</h3>
    <p id="user-email"></p>
    <button id="logout-btn">Se déconnecter</button>
  </div>

  <script src="popup.js"></script>
</body>
</html>
```

**popup.js:**
```javascript
// Charger status au démarrage
document.addEventListener("DOMContentLoaded", async () => {
  const token = await getStoredToken();

  if (token) {
    showConnectedView(token);
  } else {
    showLoginForm();
  }
});

// Configuration Backend
const BACKEND_URL = 'http://localhost:8000';

// Connexion
document.getElementById("login-btn").addEventListener("click", async () => {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;

  if (!email || !password) {
    showStatus("Veuillez remplir tous les champs", "disconnected");
    return;
  }

  try {
    showStatus("Connexion en cours...", "disconnected");

    const response = await fetch(`${BACKEND_URL}/api/auth/login?source=plugin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error("Identifiants incorrects");
    }

    const data = await response.json();

    // Stocker token
    await chrome.storage.local.set({
      access_token: data.access_token,
      user_id: data.user_id,
      tenant_id: data.tenant_id,
      user_email: email
    });

    showConnectedView(data);
    showStatus("Connecté avec succès", "connected");

  } catch (error) {
    showStatus(`Erreur: ${error.message}`, "disconnected");
  }
});

// Déconnexion
document.getElementById("logout-btn").addEventListener("click", async () => {
  await chrome.storage.local.clear();
  showLoginForm();
  showStatus("Déconnecté", "disconnected");
});

// Helpers
async function getStoredToken() {
  const result = await chrome.storage.local.get(["access_token"]);
  return result.access_token;
}

function showLoginForm() {
  document.getElementById("login-form").style.display = "block";
  document.getElementById("connected-view").style.display = "none";
}

function showConnectedView(data) {
  document.getElementById("login-form").style.display = "none";
  document.getElementById("connected-view").style.display = "block";

  chrome.storage.local.get(["user_email"], (result) => {
    document.getElementById("user-email").textContent = result.user_email;
  });
}

function showStatus(message, type) {
  const statusContainer = document.getElementById("status-container");
  statusContainer.innerHTML = `<div class="status ${type}">${message}</div>`;

  setTimeout(() => {
    statusContainer.innerHTML = "";
  }, 3000);
}
```

---

## 🔄 Système de Polling (Communication Backend → Plugin)

### Principe

Le plugin interroge le backend **toutes les 5 secondes** pour savoir s'il y a des tâches à exécuter.

### Architecture

```
Plugin (toutes les 5s) → GET /api/plugin/tasks?user_id=42
                       ←  {task_id: "abc123", action: "get_all_products", ...}

Plugin exécute la tâche sur Vinted

Plugin → POST /api/plugin/tasks/abc123/result
       ←  {success: true}
```

### Endpoints Backend

#### 1. GET /api/plugin/tasks

**Requête:**
```http
GET /api/plugin/tasks?user_id=42
Authorization: Bearer <token>
```

**Réponse (si tâche disponible):**
```json
{
  "task_id": "abc123",
  "action": "get_all_products",
  "params": {
    "user_id": 29535217
  },
  "priority": 1,
  "timeout": 60
}
```

**Réponse (si aucune tâche):**
```json
{
  "task_id": null,
  "message": "No pending tasks"
}
```

#### 2. POST /api/plugin/tasks/{task_id}/result

**Requête:**
```http
POST /api/plugin/tasks/abc123/result
Content-Type: application/json
Authorization: Bearer <token>

{
  "success": true,
  "data": {
    "products": [...],
    "total": 1595
  },
  "execution_time_ms": 15000,
  "executed_at": "2025-12-08T10:00:15Z"
}
```

**Réponse:**
```json
{
  "status": "received",
  "message": "Task result saved successfully"
}
```

### Background Task Poller (Plugin)

**Fichier:** `background.js` (ajout)

**Configuration Backend URL:** `http://localhost:8000`

```javascript
// Configuration
const BACKEND_URL = 'http://localhost:8000';
const POLL_INTERVAL = 5000; // 5 secondes

// Démarrer polling au chargement
let pollingInterval = null;

chrome.runtime.onInstalled.addListener(() => {
  console.log("[Task Poller] Extension installée, démarrage polling");
  startTaskPolling();
});

// Démarrer polling
function startTaskPolling() {
  if (pollingInterval) {
    return; // Déjà démarré
  }

  console.log(`[Task Poller] ✅ Démarrage polling (intervalle: ${POLL_INTERVAL}ms)`);

  pollingInterval = setInterval(async () => {
    await checkForTasks();
  }, POLL_INTERVAL);

  // Premier check immédiat
  checkForTasks();
}

// Arrêter polling
function stopTaskPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
    console.log("[Task Poller] ❌ Polling arrêté");
  }
}

// Vérifier s'il y a des tâches
async function checkForTasks() {
  try {
    // Récupérer token et user_id
    const result = await chrome.storage.local.get(["access_token", "user_id"]);

    if (!result.access_token || !result.user_id) {
      // Pas connecté, skip
      return;
    }

    // Interroger backend
    const response = await fetch(
      `${BACKEND_URL}/api/plugin/tasks?user_id=${result.user_id}`,
      {
        headers: {
          "Authorization": `Bearer ${result.access_token}`
        }
      }
    );

    if (!response.ok) {
      console.error("[Task Poller] Erreur requête:", response.status);
      return;
    }

    const data = await response.json();

    if (!data.task_id) {
      // Pas de tâche, skip
      return;
    }

    console.log(`[Task Poller] ✅ Nouvelle tâche: ${data.action} ${data.task_id}`);

    // Exécuter tâche
    await executeTask(data);

  } catch (error) {
    console.error("[Task Poller] Erreur:", error);
  }
}

// Exécuter une tâche
async function executeTask(task) {
  const startTime = Date.now();

  try {
    console.log(`[Task Poller] 🚀 Exécution tâche ${task.task_id}: ${task.action}`);

    let result;

    switch (task.action) {
      case "get_user_data":
        result = await getUserDataFromVinted();
        break;

      case "get_all_products":
        result = await getAllProductsFromVinted(task.params);
        break;

      case "create_product":
        result = await createProductOnVinted(task.params);
        break;

      case "update_product":
        result = await updateProductOnVinted(task.params);
        break;

      case "delete_product":
        result = await deleteProductOnVinted(task.params);
        break;

      default:
        throw new Error(`Action inconnue: ${task.action}`);
    }

    // Envoyer résultat au backend
    const executionTime = Date.now() - startTime;

    await sendTaskResult(task.task_id, {
      success: true,
      data: result,
      execution_time_ms: executionTime,
      executed_at: new Date().toISOString()
    });

    console.log(`[Task Poller] ✅ Résultat envoyé pour ${task.task_id}`);

  } catch (error) {
    console.error(`[Task Poller] ❌ Erreur tâche ${task.task_id}:`, error);

    // Envoyer erreur au backend
    await sendTaskResult(task.task_id, {
      success: false,
      error: error.message,
      execution_time_ms: Date.now() - startTime,
      executed_at: new Date().toISOString()
    });
  }
}

// Envoyer résultat au backend
async function sendTaskResult(taskId, result) {
  const token = await getStoredToken();

  const response = await fetch(
    `${BACKEND_URL}/api/plugin/tasks/${taskId}/result`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(result)
    }
  );

  if (!response.ok) {
    throw new Error(`Erreur envoi résultat: ${response.status}`);
  }

  return await response.json();
}
```

---

## 🎬 Actions Disponibles

### 1. get_user_data

Extrait les données utilisateur depuis la page Vinted.

**Paramètres:** Aucun

**Résultat:**
```json
{
  "user_id": 29535217,
  "login": "shop.ton.outfit",
  "email": "user@example.com",
  "anon_id": "6f646e72-5010-4da3-8640-6c0cf62aa346",
  "csrf_token": "75f6c9fa-dc8e-4e52-a000-e09dd4084b3e",
  "real_name": "John Doe",
  "business_account": 23111
}
```

### 2. get_all_products

Récupère tous les produits d'un utilisateur avec pagination automatique.

**Paramètres:**
```json
{
  "user_id": 29535217
}
```

**Résultat:**
```json
{
  "products": [
    {
      "id": 123456,
      "title": "T-shirt Nike",
      "price": "15.00",
      "brand": {"title": "Nike"},
      "size_title": "M",
      ...
    },
    ...
  ],
  "total": 1595
}
```

### 3. create_product

Crée un nouveau produit sur Vinted.

**Paramètres:**
```json
{
  "title": "T-shirt Nike Noir",
  "description": "T-shirt Nike en excellent état",
  "price": "15.00",
  "brand_id": 53,
  "size_id": 206,
  "catalog_id": 5,
  "color_ids": [1],
  "status_ids": [6]
}
```

**Résultat:**
```json
{
  "item": {
    "id": 789456,
    "title": "T-shirt Nike Noir",
    "price": "15.00",
    ...
  }
}
```

### 4. update_product

Modifie un produit existant.

**Paramètres:**
```json
{
  "item_id": 123456,
  "price": "12.00",
  "description": "Prix réduit !"
}
```

### 5. delete_product

Supprime un produit.

**Paramètres:**
```json
{
  "item_id": 123456
}
```

**Résultat:**
```json
{
  "success": true
}
```

### 6. upload_photo

Upload une photo pour un produit.

**Paramètres:**
```json
{
  "item_id": 123456,
  "photo_url": "https://backend.com/photos/abc.jpg"
}
```

---

## 🐛 Debug & Troubleshooting

### Logs Plugin

**Firefox:**
1. `about:debugging` → This Firefox
2. Cliquer sur **Inspect** à côté de Stoflow Plugin
3. Onglet **Console**

**Chrome:**
1. `chrome://extensions`
2. Activer "Mode développeur"
3. Cliquer sur "Inspecter les vues" → background page

### Problèmes Courants

#### ❌ "Plugin non disponible"

**Causes:**
- Plugin pas chargé dans le navigateur
- Page bridge pas ouverte

**Solutions:**
1. Vérifier que le plugin est chargé (`about:debugging`)
2. Ouvrir `http://localhost:8000` dans Firefox

#### ❌ "Aucun onglet Vinted ouvert"

**Solution:**
1. Ouvrir `https://www.vinted.fr`
2. Se connecter avec son compte

#### ❌ "CSRF token manquant"

**Solution:**
1. Recharger la page Vinted (F5)
2. Le plugin extraira automatiquement le nouveau token

#### ❌ "User ID non disponible"

**Solution:**
1. Le plugin n'a pas encore stocké l'user_id
2. Appeler d'abord une action `get_user_data`

---

## 📚 Références

- **Backend to Plugin Communication:** `BACKEND_TO_PLUGIN.md`
- **Plugin Polling API:** `PLUGIN_POLLING_API.md`
- **Architecture:** `ARCHITECTURE.md`

---

**Dernière mise à jour:** 2025-12-08
