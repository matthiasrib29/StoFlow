Switch vers un worktree existant.

**IMPORTANT** : NE PAS utiliser TodoWrite. Ce skill gère juste la navigation.

## 1. Lister les worktrees disponibles

```bash
cd ~/StoFlow
git worktree list
```

Affiche la liste formatée :

```
📂 Worktrees disponibles :

0. ~/StoFlow (develop)
1. ~/StoFlow-change-image-logique (feature/change-image-logique)
2. ~/StoFlow-fix-cancel-job (hotfix/fix-cancel-job)
...

Dans quel worktree veux-tu aller ?
```

## 2. Demander à l'utilisateur de choisir

Utiliser **AskUserQuestion** pour demander le numéro du worktree (0, 1, 2, etc.).

## 3. Déterminer le chemin du worktree choisi

Extraire le chemin correspondant au numéro choisi depuis `git worktree list`.

## 4. Vérifier que le worktree existe

```bash
if [ -d "[chemin]" ]; then
  echo "✅ Worktree trouvé"
else
  echo "❌ Erreur: Le worktree n'existe pas"
  exit 1
fi
```

## 5. Afficher les infos du worktree

```bash
cd [chemin]

# Afficher la branche actuelle
BRANCH=$(git branch --show-current)

# Afficher les ports utilisés (si c'est un worktree de dev)
# Déterminer l'env de dev basé sur le nom du worktree
WORKTREE_NAME=$(basename "$PWD")

# Afficher le message de confirmation
echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ WORKTREE ACTIF                                           ║"
echo "╠══════════════════════════════════════════════════════════════╣"
echo "║                                                              ║"
echo "║  📂 Répertoire: $PWD"
echo "║  🌿 Branche: $BRANCH"
echo "║                                                              ║"
echo "║  Pour lancer les serveurs:                                  ║"
echo "║  /1-dev, /2-dev, /3-dev ou /4-dev                            ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
```

## 6. REGLE OBLIGATOIRE pour la suite de cette session

**Tous les outils doivent maintenant pointer vers ce worktree :**
- Tous les Read() → [chemin-worktree]/...
- Tous les Write() → [chemin-worktree]/...
- Tous les Edit() → [chemin-worktree]/...
- Tous les Bash() → cd [chemin-worktree] && ...

**NE JAMAIS** travailler dans ~/StoFlow (sauf pour /deploy, /sync, /finish).

## Notes

- Ce skill ne lance PAS les serveurs de dev
- Pour lancer les serveurs après le switch : `/1-dev`, `/2-dev`, `/3-dev` ou `/4-dev`
- Pour voir l'état du projet : `/status`
