Cree un nouveau worktree pour une feature avec env dev 4 (ports 8003/3003).

**IMPORTANT** : NE PAS utiliser TodoWrite. Executer tout automatiquement.

1. Demande le nom de la feature (ex: add-ebay)

2. Execute TOUT en sequence sans demander de validation :
   - Bash: cd ~/StoFlow && git checkout develop && git pull origin develop
   - Bash: git worktree add ~/StoFlow-[nom] -b feature/[nom]
   - Bash: cp ~/StoFlow/backend/.env ~/StoFlow-[nom]/backend/.env && cp ~/StoFlow/frontend/.env ~/StoFlow-[nom]/frontend/.env
   - Bash: ln -s ~/StoFlow/backend/.venv ~/StoFlow-[nom]/backend/venv && mkdir -p ~/StoFlow-[nom]/logs
   - Bash: cd ~/StoFlow-[nom]/frontend && npm install (timeout 120000)
   - Bash: cd ~/StoFlow-[nom] && ./4-dev.sh (run_in_background: true)

3. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  ✅ WORKTREE CREE + DEV 4 LANCE                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : feature/[nom]                                  ║
║  🚀 Env dev : 4 (Backend 8003 + Frontend 3003)               ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  A PARTIR DE MAINTENANT :                                ║
║                                                              ║
║  TOUTES les modifications doivent etre faites dans :         ║
║  ~/StoFlow-[nom]/                                            ║
║                                                              ║
║  URLs :                                                      ║
║  • Backend  : http://localhost:8003                          ║
║  • Frontend : http://localhost:3003                          ║
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

4. REGLE OBLIGATOIRE pour la suite de cette session :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

5. Integration GSD automatique :

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

6. ATTENDRE que l'utilisateur lance /gsd:create-roadmap ou donne d'autres instructions.

7. REGLE : Tous les chemins utilisent ~/StoFlow-[nom]/...
