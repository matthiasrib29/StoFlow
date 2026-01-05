Déploie develop vers prod (production Railway) :

## 0. Détection worktree (finish automatique si nécessaire)
- Vérifie la branche actuelle : `git branch --show-current`
- Si la branche commence par `feature/` ou `hotfix/` :
  - Affiche : "📦 Worktree détecté, exécution de /finish d'abord..."
  - **Exécute le skill /finish** (commit, PR, merge, cleanup)
  - Une fois /finish terminé, continue avec le deploy ci-dessous
- Si on est sur `prod` → `cd ~/StoFlow && git checkout develop`

## 1. Vérifications
- Vérifie qu'on est sur develop : `git branch --show-current`
- Si pas sur develop → `cd ~/StoFlow && git checkout develop`
- `git status` - vérifie pas de changements non commités
- `git pull origin develop` - récupère les derniers changements

## 2. Merge vers prod
- `git checkout prod`
- `git pull origin prod`
- `git merge develop --no-edit`
- **Si conflit** → ARRÊTER et DEMANDER à l'utilisateur

## 3. Push (déclenche Railway)
- `git push origin prod`
- Affiche : "🚀 Déploiement lancé sur Railway..."

## 4. Retour sur develop
- `git checkout develop`

## 5. Notification
- Affiche :

╔══════════════════════════════════════════════════════════════╗
║  🚀 DÉPLOIEMENT LANCÉ                                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Railway va automatiquement :                                ║
║  1. Rebuilder l'image                                        ║
║  2. Exécuter les migrations (alembic upgrade head)           ║
║  3. Démarrer l'API                                           ║
║                                                              ║
║  📊 Vérifier : https://railway.app                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

- `notify-send "Claude" "🚀 Deploy lancé" && paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || echo "🔔 DONE"`
