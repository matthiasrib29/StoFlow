# 🔄 Flux Simplifié d'Intégration Vinted

**Date**: 2025-12-11
**Auteur**: Claude
**Objectif**: Simplifier l'extraction des credentials Vinted en ne gardant que le strict minimum (userId + login)

---

## 📋 Vue d'Ensemble

### Ancien Système (Complexe)
- ✗ Extraction de `csrf_token`, `anon_id`, et 15+ champs utilisateur
- ✗ Dépendance sur des endpoints API Vinted spécifiques
- ✗ Table `vinted_credentials` surchargée

### Nouveau Système (Simplifié)
- ✅ Extraction simple: `userId` + `login` uniquement
- ✅ Fonctionne sur **n'importe quelle page** Vinted si connecté
- ✅ Table `vinted_connection` légère
- ✅ Script JavaScript universel extrait depuis HTML

---

## 🔍 Script d'Extraction JavaScript

Le plugin utilise ce script qui fonctionne sur n'importe quelle page Vinted :

```javascript
function getVintedUserInfo() {
    const html = document.documentElement.innerHTML;

    // Chercher le bloc qui contient userId ET login ensemble
    const userIdMatch = html.match(/\\"userId\\":\\"(\d+)\\"/);
    const userId = userIdMatch ? userIdMatch[1] : null;

    if (!userId) {
        return { userId: null, login: null };
    }

    // Chercher login près du userId dans le même contexte
    const pattern = new RegExp(`\\\\"userId\\\\":\\\\"${userId}\\\\"[^}]*\\\\"login\\\\":\\\\"([^"\\\\]+)\\\\"`);
    const loginMatch = html.match(pattern);

    // Sinon prendre le premier login trouvé
    const fallbackLogin = html.match(/\\"login\\":\\"([^"\\]+)\\"/);

    return {
        userId: userId,
        login: loginMatch ? loginMatch[1] : (fallbackLogin ? fallbackLogin[1] : null)
    };
}
```

---

## 🔄 Flux Complet

### 1️⃣ **Détection & Extraction (Plugin → Backend)**

```
Extension Chrome
│
├─ N'importe quelle page Vinted (si utilisateur connecté)
│
└─ src/content/vinted-detector.ts
      ↓ getVintedUserInfo()
      ↓ Extrait: { userId: "123456", login: "username" }
      ↓
   src/api/StoflowAPI.ts
      ↓ syncVintedUser(userId, login)
      ↓
   POST /api/vinted/user/sync
      ↓ Body: { vinted_user_id: 123456, login: "username" }
      ↓
Backend: api/vinted.py → sync_vinted_user_simple()
      ↓
   1. Cherche VintedConnection existante (WHERE vinted_user_id = 123456)
   2. Si existe → UPDATE login + last_sync
   3. Si n'existe pas → INSERT nouvelle ligne
   4. Met à jour users.vinted_user_id et users.vinted_username
      ↓
PostgreSQL:
   • user_X.vinted_connection (table)
   • public.users (colonnes vinted_user_id, vinted_username)
```

---

### 2️⃣ **Affichage du Statut (Frontend → Backend)**

```
Frontend: pages/dashboard/platforms/vinted.vue
│
├─ onMounted() s'exécute au chargement de la page
│
└─ fetchConnectionStatus()
      ↓
   GET /api/vinted/user/status
      ↓
Backend: api/vinted.py → get_vinted_user_status_simple()
      ↓
   SELECT * FROM vinted_connection LIMIT 1
      ↓
   Retourne: {
     "is_connected": true,
     "vinted_user_id": 123456,
     "login": "username",
     "last_sync": "2025-12-11T10:30:00Z"
   }
      ↓
Frontend met à jour l'interface:
   • connectionInfo.userId = 123456
   • connectionInfo.username = "username"
   • isConnected = true
   • Affiche carte "Informations de connexion"
```

---

### 3️⃣ **Système de Polling Existant** (Inchangé)

Le système de polling pour les tâches reste identique :

```
Plugin: background/PollingManager.ts
   ↓ Toutes les 5 secondes
   ↓
GET /api/plugin/tasks/pending
   ↓
Backend retourne tâches en attente
   ↓
Plugin exécute (requêtes HTTP sur vinted.fr)
   ↓
POST /api/plugin/tasks/{id}/result (rapport résultat)
```

---

## 📂 Architecture des Fichiers

### **Backend**

```
Stoflow_BackEnd/
├── models/
│   ├── public/
│   │   └── user.py ........................... Modèle User avec relation vinted_connection
│   └── user/
│       └── vinted_connection.py .............. 🆕 Nouvelle table simplifiée
│
├── schemas/
│   └── vinted_schemas.py ..................... Ajout de VintedUserSyncRequest, VintedSimpleConnectionResponse
│
├── api/
│   └── vinted.py ............................. 🆕 Nouveaux endpoints:
│                                                   • POST /api/vinted/user/sync
│                                                   • GET  /api/vinted/user/status
│
└── docs/
    └── VINTED_SIMPLIFIED_FLOW.md ............. 📄 Ce fichier
```

### **Plugin**

```
StoFlow_Plugin/
├── src/
│   ├── content/
│   │   └── vinted-detector.ts ................ 🆕 Script d'extraction simplifié
│   │
│   ├── api/
│   │   └── StoflowAPI.ts ..................... 🆕 Ajout de syncVintedUser()
│   │
│   └── background/
│       └── PollingManager.ts ................. (Inchangé, gère les tâches)
```

### **Frontend**

```
Stoflow_FrontEnd/
└── pages/dashboard/platforms/
    └── vinted.vue ............................ Modifié:
                                                • fetchConnectionStatus() automatique
                                                • Affiche User ID + Username
```

---

## 🗄️ Structure de la Base de Données

### **Nouvelle Table: `vinted_connection`**

```sql
CREATE TABLE user_X.vinted_connection (
    vinted_user_id INTEGER PRIMARY KEY,        -- ID utilisateur Vinted (PK)
    login VARCHAR(255) NOT NULL,               -- Login/username
    user_id INTEGER NOT NULL,                  -- FK vers public.users.id
    created_at TIMESTAMP WITH TIME ZONE,       -- Date de création
    last_sync TIMESTAMP WITH TIME ZONE,        -- Dernière sync

    CONSTRAINT fk_vinted_connection_user
        FOREIGN KEY (user_id)
        REFERENCES public.users(id)
        ON DELETE CASCADE
);

CREATE INDEX ix_vinted_connection_user_id ON user_X.vinted_connection(user_id);
```

### **Colonnes dans `public.users`** (Inchangées)

```sql
-- Ces colonnes existent déjà et sont mises à jour pour accès rapide
vinted_user_id INTEGER,
vinted_username VARCHAR(255)
```

---

## 🔀 Comparaison Ancien vs Nouveau

| Aspect | Ancien Système | Nouveau Système |
|--------|---------------|-----------------|
| **Extraction** | csrf_token, anon_id, 15+ champs | userId + login uniquement |
| **Complexité** | Endpoint API Vinted spécifique | N'importe quelle page HTML |
| **Table DB** | `vinted_credentials` (20+ colonnes) | `vinted_connection` (5 colonnes) |
| **Endpoints** | `/credentials/sync` + `/credentials/status` | `/user/sync` + `/user/status` |
| **Robustesse** | Dépendance API Vinted | Parsing HTML (plus stable) |

---

## 🚀 Migration depuis l'Ancien Système

### Option 1: Coexistence
- Garder les deux systèmes en parallèle
- Nouveau frontend utilise `/user/status`
- Ancien système reste fonctionnel

### Option 2: Migration Complète
1. Créer migration Alembic pour la nouvelle table
2. Copier `vinted_user_id` et `login` depuis `vinted_credentials` → `vinted_connection`
3. Supprimer `vinted_credentials` après migration complète
4. Déprécier les anciens endpoints

---

## ✅ Checklist de Mise en Production

### Backend
- [ ] Créer migration Alembic pour `vinted_connection`
- [ ] Exécuter migration sur toutes les DB user_X
- [ ] Tester endpoints `/user/sync` et `/user/status`

### Plugin
- [ ] Build et deploy du plugin avec `vinted-detector.ts`
- [ ] Vérifier que `syncVintedUser()` est appelé correctement

### Frontend
- [ ] Déployer vinted.vue avec `fetchConnectionStatus()` automatique
- [ ] Vérifier affichage User ID + Username

---

## 🐛 Troubleshooting

### Problème: userId ou login est `null`
**Solution**: Vérifier que l'utilisateur est bien connecté sur Vinted. Le script ne peut extraire les infos que si l'utilisateur est authentifié.

### Problème: Table `vinted_connection` n'existe pas
**Solution**: Créer migration Alembic puis l'exécuter sur tous les schemas user_X.

### Problème: Frontend affiche "Non connecté" alors que connecté
**Solution**: Vérifier que le plugin a bien appelé `/user/sync` au moins une fois.

---

## 📞 Contact

Pour questions ou problèmes avec ce système :
1. Vérifier les logs du plugin (Console Extension)
2. Vérifier les logs du backend (Uvicorn)
3. Consulter les endpoints Swagger: http://localhost:8000/docs

---

**Dernière mise à jour**: 2025-12-11 par Claude
