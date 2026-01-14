Cree un nouveau worktree pour une feature avec env dev 3 (ports 8002/3002).

**IMPORTANT** : NE PAS utiliser TodoWrite. Executer tout automatiquement.

1. Demande le nom de la feature (ex: add-ebay)

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
   - Bash: git worktree add ~/StoFlow-[nom] -b feature/[nom]
   - Bash: cp ~/StoFlow/backend/.env ~/StoFlow-[nom]/backend/.env && cp ~/StoFlow/frontend/.env ~/StoFlow-[nom]/frontend/.env
   - Bash: ln -s ~/StoFlow/backend/venv ~/StoFlow-[nom]/backend/.venv
   - Bash: cp -r ~/StoFlow/backend/keys ~/StoFlow-[nom]/backend/
   - Bash: mkdir -p ~/StoFlow-[nom]/logs
   - Bash: ~/StoFlow/.claude/worktree-init.sh ~/StoFlow-[nom] (initialise dépendances + migrations)
   - Bash: cd ~/StoFlow-[nom] && ./3-dev.sh (run_in_background: true)

4. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  ✅ WORKTREE CREE + DEV 3 LANCE                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : feature/[nom]                                  ║
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
║  Exemples :                                                  ║
║  • Backend : ~/StoFlow-[nom]/backend/                        ║
║  • Frontend : ~/StoFlow-[nom]/frontend/                      ║
║  • Plugin : ~/StoFlow-[nom]/plugin/                          ║
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

6. Integration GSD automatique :

   a) Copier .planning/codebase/ depuis repo principal (si existe) :
   ```bash
   if [ -d ~/StoFlow/.planning/codebase ]; then
     mkdir -p ~/StoFlow-[nom]/.planning
     cp -r ~/StoFlow/.planning/codebase ~/StoFlow-[nom]/.planning/
     echo "✅ Codebase map copié depuis repo principal"
   fi
   ```

   b) Lancer automatiquement /gsd:new-project dans le worktree :
   - Utilise Skill tool : skill="gsd:new-project"
   - Le workflow GSD va poser les questions interactives
   - PROJECT.md sera créé dans ~/StoFlow-[nom]/.planning/

   c) Après /gsd:new-project, affiche :

╔══════════════════════════════════════════════════════════════╗
║  🎯 PROJECT INITIALISÉ AVEC GSD                              ║
╠══════════════════════════════════════════════════════════════╣
║  📁 Project : ~/StoFlow-[nom]/.planning/PROJECT.md           ║
║  📋 Config  : ~/StoFlow-[nom]/.planning/config.json          ║
║                                                              ║
║  ▶ Prochaine étape :                                         ║
║    /gsd:create-roadmap                                       ║
║                                                              ║
║    Cela va créer le ROADMAP avec les phases de travail.     ║
╚══════════════════════════════════════════════════════════════╝

7. ATTENDRE que l'utilisateur lance /gsd:create-roadmap ou donne d'autres instructions.

8. REGLE : Tous les chemins utilisent ~/StoFlow-[nom]/...
