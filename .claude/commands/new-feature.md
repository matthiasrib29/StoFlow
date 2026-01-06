Cree un nouveau worktree pour une feature :

1. Demande le nom de la feature (ex: add-ebay)
2. cd ~/StoFlow && git checkout develop && git pull origin develop
3. git worktree add ~/StoFlow-[nom] -b feature/[nom]
4. Copie les .env :
   - cp ~/StoFlow/backend/.env ~/StoFlow-[nom]/backend/.env
   - cp ~/StoFlow/frontend/.env ~/StoFlow-[nom]/frontend/.env

5. Cree des liens symboliques vers les environnements virtuels globaux :
   - ln -s ~/StoFlow/backend/venv ~/StoFlow-[nom]/backend/venv
   - ln -s ~/StoFlow/frontend/node_modules ~/StoFlow-[nom]/frontend/node_modules
   - mkdir -p ~/StoFlow-[nom]/logs

6. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  ✅ WORKTREE CREE                                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : feature/[nom]                                  ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  ⚠️  A PARTIR DE MAINTENANT :                                ║
║                                                              ║
║  TOUTES les modifications doivent etre faites dans :         ║
║  ~/StoFlow-[nom]/                                            ║
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

7. REGLE OBLIGATOIRE pour la suite de cette session :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

8. Demande : "Que veux-tu implementer sur cette feature ?"

9. APRES avoir recu les consignes de l'utilisateur :
   - Utilise EnterPlanMode pour entrer en mode planification
   - Analyse le codebase dans ~/StoFlow-[nom]/
   - Propose un plan d'implementation detaille
   - Attends la validation avant de coder
