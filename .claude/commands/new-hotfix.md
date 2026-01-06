Cree un nouveau worktree pour un hotfix urgent :

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

6. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  🚨 HOTFIX WORKTREE CREE                                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : hotfix/[nom]                                   ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  A PARTIR DE MAINTENANT :                                ║
║                                                              ║
║  TOUTES les modifications doivent etre faites dans :         ║
║  ~/StoFlow-[nom]/                                            ║
║                                                              ║
║  ❌ NE PAS modifier ~/StoFlow/ (c'est develop)               ║
║                                                              ║
║  Quand fini : /finish                                        ║
╚══════════════════════════════════════════════════════════════╝

7. REGLE OBLIGATOIRE pour la suite de cette session :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

8. Demande : "Quel bug dois-je corriger ?"

9. APRES avoir recu les consignes de l'utilisateur :
   - Utilise EnterPlanMode pour entrer en mode planification
   - Analyse le codebase dans ~/StoFlow-[nom]/
   - Identifie la cause du bug et propose un plan de correction
   - Attends la validation avant de coder
