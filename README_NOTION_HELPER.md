# Notion Helper - Guide d'Utilisation

Service Python pour créer et modifier des tâches dans Notion via l'API officielle.

## 🚀 Configuration

### 1. Obtenir votre clé API Notion

1. Aller sur https://www.notion.so/my-integrations
2. Créer une nouvelle intégration ou utiliser une existante
3. Copier le "Internal Integration Token"

### 2. Donner accès à la base de données

1. Ouvrir votre base de données "✅ Tâches MVP" dans Notion
2. Cliquer sur "..." en haut à droite
3. Cliquer sur "Add connections"
4. Sélectionner votre intégration

### 3. Configurer les variables d'environnement

```bash
# Copier le fichier exemple
cp .env.notion.example .env.notion

# Éditer avec votre clé API
nano .env.notion

# Charger les variables
export $(cat .env.notion | xargs)
```

Ou définir directement :
```bash
export NOTION_API_KEY="secret_votre_cle_ici"
export NOTION_DATABASE_ID="7469559e-46b6-4431-a344-36e808f8297b"
```

## 📝 Utilisation

### Créer une tâche simple

```bash
python notion_helper.py create \
  --title "Ma nouvelle tâche" \
  --status "📝 À faire" \
  --sprint "Sprint 3 - Backend" \
  --mvp "MVP 1 (Lancement)" \
  --priority "🔴 Haute" \
  --estimation 5 \
  --categories Backend API \
  --notes "Description détaillée de la tâche"
```

### Créer depuis un fichier JSON

```bash
python notion_helper.py create-from-file /tmp/task_1.json
```

### Créer en masse (20 tâches)

```bash
python notion_helper.py create-bulk "/tmp/task_*.json"
```

### Modifier une tâche existante

```bash
python notion_helper.py update <page_id> --status "✅ Terminé"
```

## 📊 Statuts Disponibles

- 📝 À faire
- 🔄 En cours
- ✅ Terminé
- ❌ Annulé

## 🎯 Priorités Disponibles

- 🔴 Haute
- 🟡 Moyenne
- 🟢 Basse

## 🏃 Sprints Disponibles

- Sprint 1 - Infrastructure
- Sprint 2 - Extension
- Sprint 3 - Backend
- Sprint 4 - IA & Vinted
- Sprint 5 - Frontend
- Sprint 6 - Admin
- Sprint 7 - Analytics
- Sprint 8 - Polish

## 🎯 MVPs Disponibles

- MVP 1 (Lancement)
- MVP 2 (Croissance)

## 🏷️ Catégories Disponibles

- Backend
- Frontend
- Extension
- Infrastructure
- Admin
- IA
- Vinted
- eBay
- Etsy
- Docs

## 🐍 Utilisation Programmatique

```python
from notion_helper import NotionHelper

# Initialiser
helper = NotionHelper(
    api_key="secret_...",
    database_id="7469559e-46b6-4431-a344-36e808f8297b"
)

# Créer une tâche
result = helper.create_task(
    title="Implémenter feature X",
    status="🔄 En cours",
    sprint="Sprint 3 - Backend",
    mvp="MVP 1 (Lancement)",
    priority="🔴 Haute",
    estimation=8,
    categories=["Backend", "API"],
    notes="Notes détaillées..."
)

print(f"Tâche créée: {result['id']}")

# Modifier une tâche
helper.update_task(
    page_id="xxx-xxx-xxx",
    status="✅ Terminé"
)

# Créer depuis JSON
helper.create_from_file("task.json")
```

## ❓ Troubleshooting

### Erreur 401 Unauthorized
- Vérifier que `NOTION_API_KEY` est correctement défini
- Vérifier que la clé API est valide

### Erreur 404 Not Found
- Vérifier que `NOTION_DATABASE_ID` est correct
- Vérifier que l'intégration a accès à la base de données

### Erreur 400 Bad Request
- Vérifier que les noms de statuts/sprints/MVPs existent dans Notion
- Vérifier le format du JSON pour create-from-file

## 📦 Exemple Complet

```bash
# 1. Configuration
export NOTION_API_KEY="secret_..."
export NOTION_DATABASE_ID="7469559e-46b6-4431-a344-36e808f8297b"

# 2. Créer les 20 tâches manquantes
python notion_helper.py create-bulk "/tmp/task_*.json"

# 3. Vérifier dans Notion
# Les tâches devraient apparaître dans la base de données
```

---

*Dernière mise à jour : 2026-01-14*
