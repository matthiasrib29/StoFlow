Synchronise le worktree actuel avec develop :

## ⚠️ Pré-requis de sécurité (CRITIQUE)

**AVANT toute synchronisation, vérifier :**

```bash
# 1. S'assurer qu'on est dans un WORKTREE, pas dans ~/StoFlow
CURRENT_DIR=$(pwd)
if [ "$CURRENT_DIR" = "$HOME/StoFlow" ]; then
  echo "⚠️ ATTENTION: Tu es dans ~/StoFlow (repo principal)!"
  echo "Le /sync est conçu pour les WORKTREES uniquement."
  echo "Utilise plutôt: git pull origin develop"
  # ⛔ ARRÊTER et DEMANDER confirmation
fi

# 2. Vérifier la branche actuelle
BRANCH=$(git branch --show-current)
if [ "$BRANCH" = "develop" ] || [ "$BRANCH" = "prod" ] || [ "$BRANCH" = "main" ]; then
  echo "⚠️ ATTENTION: Tu es sur la branche $BRANCH!"
  echo "Le /sync est pour les branches feature/hotfix."
  # ⛔ ARRÊTER et DEMANDER confirmation
fi
```

---

## Étapes

### 1. Sauvegarder le travail en cours
```bash
git status
```

Si changements non commités :
```bash
git add .
git commit -m "wip: save changes before sync"
```
(ou demander un message de commit à l'utilisateur)

### 2. Récupérer les derniers changements
```bash
git fetch origin
```

### 3. Rebase sur develop
```bash
git rebase origin/develop
```

### 4. Gestion des conflits

**Si conflits détectés** → Afficher les fichiers en conflit et DEMANDER comment procéder :
- Option 1: Résoudre manuellement
- Option 2: `git rebase --abort` pour annuler

### 5. Rapport final

```
╔══════════════════════════════════════════╗
║  ✅ SYNC TERMINÉ                         ║
╠══════════════════════════════════════════╣
║  🌿 Branche : [nom]                      ║
║  📍 Worktree : [chemin]                  ║
║  ✅ Rebasé sur origin/develop            ║
╚══════════════════════════════════════════╝
```

---

## 🛡️ Règles de sécurité (ajoutées 2026-01-12)

> Ces règles protègent contre la perte de données lors de sync.

1. **JAMAIS** utiliser /sync dans ~/StoFlow (repo principal)
2. **JAMAIS** utiliser /sync sur develop/prod/main
3. **TOUJOURS** commiter le travail en cours avant sync
4. **JAMAIS** de `git reset --hard` - utiliser rebase
5. **EN CAS DE CONFLIT** → ARRÊTER et DEMANDER
