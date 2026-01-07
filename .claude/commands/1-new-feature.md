Cree un nouveau worktree pour une feature avec env dev 1 (ports 8000/3000).

**IMPORTANT** : NE PAS utiliser TodoWrite. Executer tout automatiquement.

1. Demande le nom de la feature (ex: add-ebay)

2. Execute TOUT en sequence sans demander de validation :
   - Bash: cd ~/StoFlow && git checkout develop && git pull origin develop
   - Bash: git worktree add ~/StoFlow-[nom] -b feature/[nom]
   - Bash: cp ~/StoFlow/backend/.env ~/StoFlow-[nom]/backend/.env && cp ~/StoFlow/frontend/.env ~/StoFlow-[nom]/frontend/.env
   - Bash: ln -s ~/StoFlow/backend/venv ~/StoFlow-[nom]/backend/venv && mkdir -p ~/StoFlow-[nom]/logs
   - Bash: cd ~/StoFlow-[nom]/frontend && npm install (timeout 120000)
   - Bash: cd ~/StoFlow-[nom] && ./dev1.sh (run_in_background: true)

3. Affiche ce message :

╔══════════════════════════════════════════════════════════════╗
║  ✅ WORKTREE CREE + DEV 1 LANCE                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  📁 Dossier : ~/StoFlow-[nom]                                ║
║  🌿 Branche : feature/[nom]                                  ║
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

5. Demande : "Que veux-tu implementer sur cette feature ?"

6. APRES avoir recu les consignes de l'utilisateur :
   - Utilise EnterPlanMode pour entrer en mode planification
   - Analyse le codebase dans ~/StoFlow-[nom]/
   - Propose un plan d'implementation detaille
   - Attends la validation avant de coder
