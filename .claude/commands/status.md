Montre l'etat complet du projet :

## ⚠️ Alertes de sécurité (vérifier en premier - ajouté 2026-01-13)

```bash
cd ~/StoFlow

# 1. Vérifier les changements non commités sur ~/StoFlow
if [ -n "$(git status --porcelain)" ]; then
  echo "⚠️ ALERTE: ~/StoFlow a des changements non commités!"
  git status --short
fi

# 2. Vérifier les commits locaux non poussés sur develop
LOCAL_COMMITS=$(git log origin/develop..develop --oneline 2>/dev/null)
if [ -n "$LOCAL_COMMITS" ]; then
  echo "🚨 ALERTE CRITIQUE: ~/StoFlow develop a des commits NON POUSSÉS!"
  echo "$LOCAL_COMMITS"
  echo ""
  echo "⚠️ Ces commits seront PERDUS si tu fais /finish ou /sync sans les pousser!"
fi
```

**Si alertes détectées** → Afficher en ROUGE en haut du rapport :
```
╔══════════════════════════════════════════════════════════════╗
║  🚨 ALERTES DÉTECTÉES SUR ~/StoFlow                          ║
╠══════════════════════════════════════════════════════════════╣
║  [Liste des alertes]                                         ║
║                                                              ║
║  Action recommandée: git push origin develop                 ║
╚══════════════════════════════════════════════════════════════╝
```

---

## État du projet

1. git worktree list

2. Pour chaque worktree :
   - Branche actuelle
   - Commits ahead/behind develop
   - Fichiers modifies
   - **État GSD** (si .planning/ existe) :
     ```bash
     WORKTREE_PATH=$(git worktree list | grep [branche] | awk '{print $1}')
     if [ -d "$WORKTREE_PATH/.planning/" ]; then
       echo "  📊 GSD actif:"
       # Affiche phase actuelle
       grep "^Phase:" "$WORKTREE_PATH/.planning/STATE.md" 2>/dev/null || echo "  - Pas encore de STATE.md"
       # Affiche progression
       grep "^Progress:" "$WORKTREE_PATH/.planning/STATE.md" 2>/dev/null
     fi
     ```

3. Branches locales vs remote : git branch -vv

4. PRs ouvertes : gh pr list

5. docker ps (services)

6. ports 8000/3000/8001/3001/8002/3002/8003/3003 utilises (lsof -i :PORT)

## 🔀 Détection de conflits potentiels

```bash
# Lister les fichiers modifiés par chaque worktree par rapport à develop
echo "=== Fichiers modifiés par worktree ==="
for wt in $(git worktree list --porcelain | grep worktree | cut -d' ' -f2); do
  if [ "$wt" != "$HOME/StoFlow" ]; then
    BRANCH=$(git -C "$wt" branch --show-current 2>/dev/null)
    if [ -n "$BRANCH" ]; then
      echo ""
      echo "📁 $BRANCH ($wt):"
      FILES=$(git -C "$wt" diff --name-only origin/develop 2>/dev/null | head -10)
      if [ -n "$FILES" ]; then
        echo "$FILES"
      else
        echo "  (aucun fichier modifié)"
      fi
    fi
  fi
done

# Détecter les fichiers modifiés dans plusieurs worktrees
echo ""
echo "=== ⚠️ Conflits potentiels ==="
ALL_FILES=""
for wt in $(git worktree list --porcelain | grep worktree | cut -d' ' -f2); do
  if [ "$wt" != "$HOME/StoFlow" ]; then
    FILES=$(git -C "$wt" diff --name-only origin/develop 2>/dev/null)
    ALL_FILES="$ALL_FILES $FILES"
  fi
done
DUPLICATES=$(echo $ALL_FILES | tr ' ' '\n' | sort | uniq -d)
if [ -n "$DUPLICATES" ]; then
  echo "⚠️ Fichiers modifiés dans PLUSIEURS worktrees:"
  echo "$DUPLICATES"
  echo ""
  echo "→ Risque de conflit lors du merge!"
else
  echo "✅ Aucun conflit détecté"
fi
```

## 📊 Santé des logs

```bash
echo "=== Taille des logs ==="
du -sh ~/StoFlow/logs/ 2>/dev/null || echo "~/StoFlow/logs/ n'existe pas"
du -sh ~/StoFlow/backend/logs/ 2>/dev/null || echo "~/StoFlow/backend/logs/ n'existe pas"

# Alerter si > 50MB total
TOTAL=$(du -sm ~/StoFlow/logs/ ~/StoFlow/backend/logs/ 2>/dev/null | awk '{s+=$1} END {print s+0}')
if [ "$TOTAL" -gt 50 ]; then
  echo ""
  echo "⚠️ Logs > 50MB! Recommandé: ./rotate-logs.sh"
fi
```
