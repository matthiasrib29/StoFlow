Cree un nouveau worktree pour un hotfix urgent avec env dev 3 (ports 8002/3002).

**IMPORTANT** : NE PAS utiliser TodoWrite. Executer tout automatiquement.

1. Demande le nom du fix (ex: fix-login)

2. ⚠️ PROTECTION OBLIGATOIRE avant checkout (ajoutée 2026-01-13) :

   ```bash
   cd ~/StoFlow

   # 1. Vérifier les changements non commités
   if [ -n "$(git status --porcelain)" ]; then
     echo "⚠️ ~/StoFlow a des changements non commités!"
     git status --short
     # ⛔ ARRÊTER et DEMANDER : stash, commit, ou abandonner?
   fi

   # 2. Vérifier les commits locaux non poussés (sur la branche actuelle)
   CURRENT_BRANCH=$(git branch --show-current)
   LOCAL_COMMITS=$(git log origin/$CURRENT_BRANCH..$CURRENT_BRANCH --oneline 2>/dev/null)
   if [ -n "$LOCAL_COMMITS" ]; then
     echo "⚠️ ~/StoFlow a des commits locaux NON POUSSÉS sur $CURRENT_BRANCH!"
     echo "$LOCAL_COMMITS"
     # ⛔ ARRÊTER et DEMANDER : push, sauvegarder branche, ou abandonner?
   fi
   ```

   **Si problème détecté** → ARRÊTER et DEMANDER à l'utilisateur quoi faire.

3. Execute TOUT en sequence (seulement si étape 2 OK) :
   - Bash: cd ~/StoFlow && git checkout develop && git pull
   - Bash: git worktree add ~/StoFlow-[nom] -b hotfix/[nom]
   - Bash: cp ~/StoFlow/backend/.env ~/StoFlow-[nom]/backend/.env && cp ~/StoFlow/frontend/.env ~/StoFlow-[nom]/frontend/.env
   - Bash: ln -s ~/StoFlow/backend/.venv ~/StoFlow-[nom]/backend/.venv
   - Bash: cd ~/StoFlow-[nom]/backend && ln -s .venv venv
   - Bash: cp -r ~/StoFlow/backend/keys ~/StoFlow-[nom]/backend/
   - Bash: mkdir -p ~/StoFlow-[nom]/logs
   - Bash: cd ~/StoFlow-[nom]/frontend && npm install (timeout 120000)
   - Bash: cd ~/StoFlow-[nom] && ./3-dev.sh (run_in_background: true)

4. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  🚨 HOTFIX WORKTREE CREE + DEV 3 LANCE                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : hotfix/[nom]                                   ║
║  🚀 Env dev : 3 (Backend 8002 + Frontend 3002)               ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  A PARTIR DE MAINTENANT :                                ║
║                                                              ║
║  TOUTES les modifications doivent etre faites dans :         ║
║  ~/StoFlow-[nom]/                                            ║
║                                                              ║
║  URLs :                                                      ║
║  • Backend  : http://localhost:8002                          ║
║  • Frontend : http://localhost:3002                          ║
║                                                              ║
║  ❌ NE PAS modifier ~/StoFlow/ (c'est develop)               ║
║                                                              ║
║  Quand fini : /finish                                        ║
╚══════════════════════════════════════════════════════════════╝

5. REGLE OBLIGATOIRE pour la suite de cette session :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

6. Demande : "Quel bug dois-je corriger ?"

7. APRES avoir recu les consignes de l'utilisateur :
   - Utilise EnterPlanMode pour entrer en mode planification
   - Analyse le codebase dans ~/StoFlow-[nom]/
   - Identifie la cause du bug et propose un plan de correction
   - Attends la validation avant de coder
