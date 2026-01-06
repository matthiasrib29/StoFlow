Cree un nouveau worktree pour un hotfix urgent avec env dev 1 (ports 8000/3000) :

1. Demande le nom du fix (ex: fix-login)
2. cd ~/StoFlow && git checkout develop && git pull origin develop
3. git worktree add ~/StoFlow-[nom] -b hotfix/[nom]
4. Copie les .env :
   - cp ~/StoFlow/backend/.env ~/StoFlow-[nom]/backend/.env
   - cp ~/StoFlow/frontend/.env ~/StoFlow-[nom]/frontend/.env

5. Cree des liens symboliques vers les environnements virtuels globaux :
   - ln -s ~/StoFlow/backend/venv ~/StoFlow-[nom]/backend/venv
   - ln -s ~/StoFlow/frontend/node_modules ~/StoFlow-[nom]/frontend/node_modules
   - mkdir -p ~/StoFlow-[nom]/logs

6. Lance l'environnement de dev 1 :
   - cd ~/StoFlow-[nom] && ./dev1.sh (en arrière-plan avec run_in_background: true)

7. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  🚨 HOTFIX WORKTREE CREE + DEV 1 LANCE                       ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : hotfix/[nom]                                   ║
║  🚀 Env dev : 1 (Backend 8000 + Frontend 3000)               ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  A PARTIR DE MAINTENANT :                                ║
║                                                              ║
║  TOUTES les modifications doivent etre faites dans :         ║
║  ~/StoFlow-[nom]/                                            ║
║                                                              ║
║  URLs :                                                      ║
║  • Backend  : http://localhost:8000                          ║
║  • Frontend : http://localhost:3000                          ║
║                                                              ║
║  ❌ NE PAS modifier ~/StoFlow/ (c'est develop)               ║
║                                                              ║
║  Quand fini : /finish                                        ║
╚══════════════════════════════════════════════════════════════╝

8. REGLE OBLIGATOIRE pour la suite de cette session :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

9. Demande : "Quel bug dois-je corriger ?"

10. APRES avoir recu les consignes de l'utilisateur :
   - Utilise EnterPlanMode pour entrer en mode planification
   - Analyse le codebase dans ~/StoFlow-[nom]/
   - Identifie la cause du bug et propose un plan de correction
   - Attends la validation avant de coder
