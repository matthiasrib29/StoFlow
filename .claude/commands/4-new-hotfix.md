Cree un nouveau worktree pour un hotfix urgent avec env dev 4 (ports 8003/3003).

**IMPORTANT** : NE PAS utiliser TodoWrite. Executer tout automatiquement.

1. Demande le nom du fix (ex: fix-login)

2. Execute TOUT en sequence sans demander de validation :
   - Bash: cd ~/StoFlow && git checkout develop && git pull origin develop
   - Bash: git worktree add ~/StoFlow-[nom] -b hotfix/[nom]
   - Bash: cp ~/StoFlow/backend/.env ~/StoFlow-[nom]/backend/.env && cp ~/StoFlow/frontend/.env ~/StoFlow-[nom]/frontend/.env
   - Bash: ln -s ~/StoFlow/backend/venv ~/StoFlow-[nom]/backend/venv && mkdir -p ~/StoFlow-[nom]/logs
   - Bash: cd ~/StoFlow-[nom]/frontend && npm install (timeout 120000)
   - Bash: cd ~/StoFlow-[nom] && ./dev4.sh (run_in_background: true)

3. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  🚨 HOTFIX WORKTREE CREE + DEV 4 LANCE                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : hotfix/[nom]                                   ║
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
║  ❌ NE PAS modifier ~/StoFlow/ (c'est develop)               ║
║                                                              ║
║  Quand fini : /finish                                        ║
╚══════════════════════════════════════════════════════════════╝

4. REGLE OBLIGATOIRE pour la suite de cette session :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

5. Demande : "Quel bug dois-je corriger ?"

6. APRES avoir recu les consignes de l'utilisateur :
   - Utilise EnterPlanMode pour entrer en mode planification
   - Analyse le codebase dans ~/StoFlow-[nom]/
   - Identifie la cause du bug et propose un plan de correction
   - Attends la validation avant de coder
