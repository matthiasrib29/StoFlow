Crée un nouveau worktree pour une feature ou un hotfix avec environnement de dev dédié.

**IMPORTANT** : NE PAS utiliser TodoWrite. Le script bash gère tout.

## Workflow

1. **Demander le nom du worktree** avec AskUserQuestion:
   - Header: "Nom"
   - Question: "Quel est le nom de la feature/hotfix ?"
   - Options:
     - "add-ebay" → description: "Exemple: ajouter intégration eBay"
     - "fix-login" → description: "Exemple: corriger le bug de login"
     - "refactor-api" → description: "Exemple: refactoriser l'API"
   - Note: L'utilisateur pourra saisir un nom custom via "Other"

2. **Demander le type** avec AskUserQuestion:
   - Header: "Type"
   - Question: "Est-ce une feature ou un hotfix ?"
   - Options:
     - "Feature" → description: "Nouvelle fonctionnalité (branche feature/...)"
     - "Hotfix" → description: "Correction urgente (branche hotfix/...)"

3. **Demander l'environnement** avec AskUserQuestion:
   - Header: "Env de dev"
   - Question: "Quel environnement de dev veux-tu utiliser ?"
   - Options:
     - "Env 1 (ports 8000/3000)" → description: "Backend sur 8000, Frontend sur 3000, favicon bleu"
     - "Env 2 (ports 8001/3001)" → description: "Backend sur 8001, Frontend sur 3001, favicon vert"
     - "Env 3 (ports 8002/3002)" → description: "Backend sur 8002, Frontend sur 3002, favicon orange"
     - "Env 4 (ports 8003/3003)" → description: "Backend sur 8003, Frontend sur 3003, favicon rouge"

4. **Exécuter le script de création** avec Bash:
   ```bash
   cd ~/StoFlow && ./scripts/new-worktree.sh [env] [nom] [type]
   ```

   Où `[type]` est "feature" ou "hotfix" (en minuscules)

5. **Gestion des erreurs** :
   - Si le script échoue (exit code != 0):
     - Lire attentivement les messages d'erreur affichés par le script
     - Les messages contiennent déjà les explications et solutions
     - Expliquer le problème à l'utilisateur en français
     - Proposer les solutions concrètes mentionnées dans l'erreur
     - Utiliser AskUserQuestion si l'utilisateur veut réessayer après correction

6. **Si le script réussit** (exit code 0):
   - Le script a déjà affiché le message de succès avec les URLs
   - Rappeler que tout le travail doit se faire dans ~/StoFlow-[nom]/

7. **REGLE OBLIGATOIRE pour la suite de cette session** :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

## Ce que fait le script

1. **Protections Git** :
   - Vérifie les changements non commités dans ~/StoFlow
   - Auto-commit si nécessaire avant création du worktree
   - Vérifie les commits locaux non poussés

2. **Création du worktree** :
   - Crée le worktree dans ~/StoFlow-[nom]/
   - Crée la branche feature/[nom] ou hotfix/[nom]

3. **Configuration** :
   - Copie .env backend et frontend
   - Configure un venv Python dédié (non partagé)
   - Copie les clés API
   - Initialise npm dependencies
   - Auto-copie les migrations manquantes
   - Lance l'environnement de dev choisi

## Quand terminé

Utiliser `/finish` pour merger et nettoyer le worktree.
