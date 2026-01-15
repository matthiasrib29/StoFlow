Cree un nouveau worktree pour un hotfix urgent avec env dev 3 (ports 8002/3002).

**IMPORTANT** : NE PAS utiliser TodoWrite. Le script bash gère tout.

1. Demande le nom du fix (ex: fix-login)

2. Lance le script de création:
   - Bash: cd ~/StoFlow && ./scripts/new-hotfix.sh 3 [nom]

3. Si le script échoue (exit code != 0):
   - Lire attentivement les messages d'erreur affichés par le script
   - Les messages contiennent déjà les explications et solutions
   - Expliquer le problème à l'utilisateur en français
   - Proposer les solutions concrètes mentionnées dans l'erreur
   - Utiliser AskUserQuestion si l'utilisateur veut réessayer après correction

4. Si le script réussit (exit code 0):
   - Le script a déjà affiché le message de succès avec les URLs
   - Rappeler que tout le travail doit se faire dans ~/StoFlow-[nom]/
   - Demander : "Quel bug dois-je corriger ?"

5. REGLE OBLIGATOIRE pour la suite de cette session :
   - Tous les Read() → ~/StoFlow-[nom]/...
   - Tous les Write() → ~/StoFlow-[nom]/...
   - Tous les Edit() → ~/StoFlow-[nom]/...
   - Tous les Bash() → cd ~/StoFlow-[nom] && ...

6. APRES avoir reçu les consignes de l'utilisateur :
   - Utilise EnterPlanMode pour entrer en mode planification
   - Analyse le codebase dans ~/StoFlow-[nom]/
   - Identifie la cause du bug et propose un plan de correction
   - Attends la validation avant de coder
