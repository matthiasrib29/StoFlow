# Claude Code - Automatisations & Optimisations

> Documentation complete de toutes les configurations Claude Code pour StoFlow

---

## Table des matieres

1. [Notifications sonores](#1-notifications-sonores)
2. [Permissions auto-approuvees](#2-permissions-auto-approuvees)
3. [Plugins actifs](#3-plugins-actifs)
4. [Slash Commands](#4-slash-commands)
5. [Git Worktrees](#5-git-worktrees)
6. [Bash Aliases](#6-bash-aliases)
7. [Fichiers ignores](#7-fichiers-ignores-claudeignore)
8. [Configuration globale](#8-configuration-globale-claudemd)
9. [Configuration projet](#9-configuration-projet-stoflowclaudemd)

---

## 1. Notifications sonores

**Fichier** : `~/.claude/settings.json`

### Hooks configures

| Evenement | Son | Description |
|-----------|-----|-------------|
| `Stop` | `complete.oga` | Quand Claude termine une reponse |
| `PermissionRequest` | `bell.oga` | Quand Claude demande une permission |

### Configuration JSON

```json
"hooks": {
  "Stop": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || true"
    }]
  }],
  "PermissionRequest": [{
    "matcher": "",
    "hooks": [{
      "type": "command",
      "command": "paplay /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null || true"
    }]
  }]
}
```

### Sons disponibles

```bash
# Lister les sons systeme
ls /usr/share/sounds/freedesktop/stereo/
# Tester un son
paplay /usr/share/sounds/freedesktop/stereo/bell.oga
```

---

## 2. Permissions auto-approuvees

**Fichier** : `~/.claude/settings.json`

### Categories principales

| Categorie | Commandes |
|-----------|-----------|
| **Git** | `git add`, `git commit`, `git push`, `git pull`, `git fetch`, `git branch`, `git checkout`, `git worktree` |
| **Python** | `python`, `pytest`, `pip install`, `uvicorn`, `alembic` |
| **Node.js** | `npm install`, `npm run dev`, `npm run build`, `node` |
| **Docker** | `docker compose`, `docker ps`, `docker exec` |
| **System** | `ls`, `mkdir`, `chmod`, `kill`, `lsof`, `curl` |

### Mode par defaut

```json
"defaultMode": "acceptEdits"
```

Claude peut editer les fichiers sans demander confirmation (mais demande pour les commandes non-listees).

---

## 3. Plugins actifs

**Fichier** : `~/.claude/settings.json`

| Plugin | Usage |
|--------|-------|
| `frontend-design@claude-code-plugins` | Design d'interfaces frontend |
| `context7@claude-plugins-official` | Contexte de documentation |
| `github@claude-plugins-official` | Integration GitHub |
| `playwright@claude-plugins-official` | Tests browser (Firefox) |

### Configuration Playwright

```json
"pluginConfigs": {
  "playwright@claude-plugins-official": {
    "mcpServers": {
      "playwright": {
        "browser": "firefox"
      }
    }
  }
}
```

---

## 4. Slash Commands

**Dossier** : `~/StoFlow/.claude/commands/`

### Developpement

| Commande | Description |
|----------|-------------|
| `/dev` | Lance backend + frontend en mode dev |
| `/dev-backend` | Lance uniquement le backend |
| `/dev-frontend` | Lance uniquement le frontend |
| `/stop` | Arrete tous les services |
| `/test` | Lance les tests du module courant |
| `/db-reset` | Reset la base de donnees |

### Git Workflow

| Commande | Description |
|----------|-------------|
| `/status` | Etat complet (worktrees, branches, PRs, docker, ports) |
| `/commit` | Propose un message de commit et attend validation |
| `/pr` | Push + cree une Pull Request |
| `/merge` | Merge une branche dans main |
| `/sync` | Synchronise tous les worktrees avec main |

### Git Worktrees

| Commande | Description |
|----------|-------------|
| `/new-feature` | Cree un worktree pour une nouvelle feature |
| `/new-hotfix` | Cree un worktree pour un hotfix urgent |
| `/finish` | PR + merge + cleanup (tout-en-un) |
| `/cleanup` | Supprime les worktrees inutilises |
| `/switch` | Change de worktree |

### Utilitaires

| Commande | Description |
|----------|-------------|
| `/done` | Notification sonore + visuelle de fin |

---

## 5. Git Worktrees

### Structure

```
~/StoFlow/           -> main (stable, jamais dev ici)
~/StoFlow-feature/   -> feature/current
~/StoFlow-hotfix/    -> hotfix/current
~/StoFlow-[nom]/     -> worktrees temporaires
```

### Commandes utiles

```bash
# Lister les worktrees
git worktree list

# Creer un nouveau worktree
git worktree add ../StoFlow-[nom] -b feature/[nom]

# Supprimer un worktree
git worktree remove ../StoFlow-[nom]

# Nettoyer les references mortes
git worktree prune
```

### Workflow quotidien

```
1. Matin    : sf && git pull && /sync
2. Tache    : /new-feature ou /new-hotfix
3. Dev      : commits frequents
4. Termine  : /finish
5. Soir     : /cleanup si besoin
```

---

## 6. Bash Aliases

**Fichier** : `~/.bashrc`

### Navigation

| Alias | Commande | Description |
|-------|----------|-------------|
| `sf` | `cd ~/StoFlow` | Aller sur main |
| `sff` | `cd ~/StoFlow-feature` | Aller sur feature |
| `sfh` | `cd ~/StoFlow-hotfix` | Aller sur hotfix |
| `sfw` | `git worktree list` | Lister les worktrees |

### Claude Code

| Alias | Commande | Description |
|-------|----------|-------------|
| `cdev` | `cd ~/StoFlow && claude` | Claude sur main |
| `cfeat` | `cd ~/StoFlow-feature && claude` | Claude sur feature |
| `cfix` | `cd ~/StoFlow-hotfix && claude` | Claude sur hotfix |

### Activer apres modification

```bash
source ~/.bashrc
```

---

## 7. Fichiers ignores (.claudeignore)

**Fichier** : `~/StoFlow/.claudeignore`

Claude ignore automatiquement ces fichiers/dossiers :

```
# Dependencies
node_modules/
venv/
.venv/

# Build
dist/
.nuxt/
.output/
__pycache__/
*.pyc

# Logs
*.log
logs/

# IDE
.idea/
.vscode/
*.swp

# Data
uploads/
*.sqlite

# Cache
.pytest_cache/
.mypy_cache/
htmlcov/
```

---

## 8. Configuration globale (CLAUDE.md)

**Fichier** : `~/.claude/CLAUDE.md`

S'applique a **TOUS les projets**.

### Points cles

| Regle | Description |
|-------|-------------|
| **Langue** | Reponses en francais, code en anglais |
| **Questions** | TOUJOURS demander avant d'implementer |
| **Fichiers** | Demander avant de creer/modifier/supprimer |
| **Max lignes** | 500 lignes max par fichier |
| **APIs externes** | JAMAIS de curl vers Vinted/eBay/Etsy |
| **Logs** | Utiliser `logger`, jamais `print()` |

### Stack technique

- **Backend** : FastAPI + SQLAlchemy + PostgreSQL + Alembic
- **Frontend** : Nuxt.js + Vue 3 + Tailwind CSS + Pinia
- **Tests** : Pytest (backend), npm test (frontend)

### Architecture

```
Backend:  api/ -> services/ -> repositories/ -> models/
Frontend: pages/ -> components/ -> stores/ -> services/
```

---

## 9. Configuration projet (StoFlow CLAUDE.md)

**Fichier** : `~/StoFlow/CLAUDE.md`

S'applique uniquement a **StoFlow**.

### Regles strictes

| Regle | Valeur |
|-------|--------|
| Fichiers modifies par commit | **MAX 3** |
| Tests par fonction | **MAX 3** |
| Refactoring non sollicite | **INTERDIT** |
| Commits | **Anglais** |

### Quick commands

```bash
# Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev

# Plugin
cd plugin && npm run dev

# Tests
cd backend && pytest
cd frontend && npm test
```

---

## Arborescence des fichiers de config

```
~/.claude/
├── settings.json          # Permissions, hooks, plugins
└── CLAUDE.md              # Instructions globales

~/StoFlow/
├── CLAUDE.md              # Instructions projet
├── .claudeignore          # Fichiers ignores
├── .claude/
│   └── commands/          # Slash commands
│       ├── dev.md
│       ├── status.md
│       ├── commit.md
│       ├── pr.md
│       ├── merge.md
│       ├── sync.md
│       ├── new-feature.md
│       ├── new-hotfix.md
│       ├── finish.md
│       ├── cleanup.md
│       ├── switch.md
│       ├── test.md
│       ├── stop.md
│       ├── done.md
│       └── db-reset.md
├── backend/
│   └── CLAUDE.md          # Instructions backend
├── frontend/
│   └── CLAUDE.md          # Instructions frontend
└── plugin/
    └── CLAUDE.md          # Instructions plugin
```

---

## Maintenance

### Recharger la config bash
```bash
source ~/.bashrc
```

### Verifier les worktrees
```bash
git worktree list
git worktree prune
```

### Verifier gh
```bash
gh auth status
gh pr list
```

### Tester les sons
```bash
paplay /usr/share/sounds/freedesktop/stereo/complete.oga
paplay /usr/share/sounds/freedesktop/stereo/bell.oga
```

---

*Derniere mise a jour : 2025-12-18*
