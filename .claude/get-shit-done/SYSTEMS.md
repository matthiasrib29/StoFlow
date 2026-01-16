# Systèmes de Planning - Guide d'Utilisation

Ce projet dispose de **2 systèmes de planning** adaptés à différents besoins :

---

## 🚀 Système Simplifié (Nouveau)

**Quand l'utiliser :**
- ✅ Features simples/moyennes (1-5 jours)
- ✅ Tu veux coder rapidement sans overhead
- ✅ Équipe seule ou petit groupe
- ✅ Planning léger suffit

**Skills disponibles :**
- `/start [nom]` - Auto-détecte la taille et crée structure adaptée
- `/roadmap` - Crée roadmap light (2-5 phases, ~50 lignes)
- `/plan [phase]` - Crée plan light (2-5 tâches, ~30 lignes)
- `/exec [plan]` - Execute avec agents Task en parallèle

**Structure créée :**
```
.planning/
├── PROJECT.md          (~30 lignes)
├── ROADMAP.md          (~50 lignes)
├── STATE.md            (auto-géré)
└── plans/
    ├── 01-PLAN.md      (~30 lignes)
    ├── 01-SUMMARY.md   (auto-créé)
    ├── 02-PLAN.md
    └── ...
```

**Caractéristiques :**
- 📝 Documents courts et essentiels
- ⚡ Setup en 2 minutes
- 🤖 STATE.md auto-mis à jour
- 🚀 Exécution avec agents Task (parallélisation)
- 🎯 Focus sur l'action, pas la documentation

---

## 🏗️ Système GSD Complet (Original)

**Quand l'utiliser :**
- ✅ Projets complexes multi-semaines (2-4 semaines)
- ✅ Refactoring architectural majeur
- ✅ Équipe large avec besoin de coordination
- ✅ Documentation exhaustive requise
- ✅ Multiples milestones/versions

**Skills disponibles :**
- `/gsd:new-project` - Init avec questioning approfondi
- `/gsd:create-roadmap` - Roadmap complet avec dépendances
- `/gsd:plan-phase [phase]` - Plan détaillé avec checkpoints
- `/gsd:execute-plan [plan]` - Execute avec stratégies A/B/C
- `/gsd:map-codebase` - Analyse complète du codebase
- `/gsd:new-milestone` - Gestion de versions
- `/gsd:discuss-phase` - Gathering context avant planning
- `/gsd:research-phase` - Investigation avant implémentation
- `/gsd:pause-work` - Handoff de contexte
- `/gsd:resume-work` - Reprise avec contexte complet
- `/gsd:verify-work` - UAT guidé
- `/gsd:plan-fix` - Plans de correction
- `/gsd:consider-issues` - Review des issues différées
- `/gsd:complete-milestone` - Archivage milestone
- Et autres...

**Structure créée :**
```
.planning/
├── PROJECT.md          (~150 lignes)
├── ROADMAP.md          (~500 lignes)
├── STATE.md            (manuel)
├── config.json
├── codebase/
│   ├── ARCHITECTURE.md
│   ├── STACK.md
│   └── ... (7 documents)
└── phases/
    ├── 01-phase-name/
    │   ├── 01-01-PLAN.md    (~100 lignes)
    │   ├── 01-01-SUMMARY.md
    │   ├── 01-02-PLAN.md
    │   └── ...
    └── ...
```

**Caractéristiques :**
- 📚 Documentation exhaustive
- 🔍 Questioning approfondi
- 📊 Métriques et tracking détaillés
- 🗺️ Dependency graphs
- 🎯 Testing strategy complète
- 🔄 Milestone management
- 👥 Multi-team coordination

---

## 🤔 Comparaison Rapide

| Critère | Simplifié | GSD Complet |
|---------|-----------|-------------|
| **Setup time** | 2 min | 10 min |
| **PROJECT.md** | 30 lignes | 150 lignes |
| **ROADMAP.md** | 50 lignes | 500 lignes |
| **PLAN.md** | 30 lignes | 100 lignes |
| **Documentation** | Essentielle | Exhaustive |
| **Milestones** | Non | Oui |
| **STATE.md** | Auto | Manuel |
| **Codebase mapping** | Non | Oui (7 docs) |
| **Questioning** | Rapide (2-3 Q) | Approfondi (6+ Q) |
| **Best for** | 1-5 jours | 2-4 semaines |

---

## 💡 Recommandations

### Utilise le Système Simplifié si :
- "Je veux juste ajouter une feature"
- "C'est un refactoring localisé"
- "Je sais déjà ce que je dois faire"
- "Je travaille seul sur cette partie"

### Utilise le Système GSD Complet si :
- "C'est un projet de plusieurs semaines"
- "Je dois coordonner avec d'autres devs"
- "L'architecture est complexe"
- "Je dois comprendre le codebase d'abord"
- "Il y aura plusieurs milestones"

### Les 2 systèmes :
- ✅ Utilisent les **agents Task** pour l'exécution parallèle
- ✅ Créent des **commits atomiques** par tâche
- ✅ Génèrent des **SUMMARY.md** après exécution
- ✅ Supportent la **deviation handling** automatique

---

## 🎬 Exemples d'Utilisation

### Exemple 1 : Feature Simple (Simplifié)
```bash
/start add-logout-button
# → Auto-détecte "Quick", crée quick-PLAN.md
/exec
# → Execute, commit, done en 30min
```

### Exemple 2 : Feature Moyenne (Simplifié)
```bash
/start add-ebay-integration
# → Auto-détecte "Normal", crée PROJECT + ROADMAP light
/exec
# → Execute phase 1
/exec
# → Execute phase 2
# Done en 1 jour
```

### Exemple 3 : Refactoring Large (GSD Complet)
```bash
/gsd:new-project
# → Questioning approfondi (10min)
/gsd:map-codebase
# → Analyse codebase (5min)
/gsd:create-roadmap
# → Roadmap avec 12 phases
/gsd:plan-phase 1
# → Plan détaillé phase 1
/gsd:execute-plan phases/01-name/01-01-PLAN.md
# → Execute avec agents
# Continue sur 2-3 semaines
```

---

## 🔄 Migration Entre Systèmes

**Simplifié → GSD Complet:**

Si ton projet "simple" devient complexe, tu peux migrer :
1. Copier `.planning/PROJECT.md` et étendre
2. Créer `/gsd:create-roadmap` (va lire PROJECT existant)
3. Continuer avec GSD complet

**GSD Complet → Simplifié:**

Pas recommandé - si tu as commencé GSD complet, termine avec.

---

*Dernière mise à jour : 2026-01-16*
