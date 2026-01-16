---
name: roadmap
description: Create a lightweight roadmap with 2-5 phases
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---

<objective>
Create a lightweight roadmap breaking down the project into 2-5 phases.

Each phase has:
- Name
- 2-3 line description
- Key deliverables

Much simpler than full GSD roadmap (no dependencies graph, no timeline, no testing strategy).
</objective>

<context>
@.planning/PROJECT.md (must exist)
</context>

<process>

<step name="validate">
```bash
[ -f .planning/PROJECT.md ] || { echo "ERROR: No PROJECT.md found. Run `/start` first."; exit 1; }

# Check if roadmap exists
[ -f .planning/ROADMAP.md ] && echo "ROADMAP_EXISTS" || echo "NO_ROADMAP"
```

If ROADMAP_EXISTS, ask:
- "Roadmap existe déjà. Remplacer ?"
- Options: "Oui, remplacer" / "Non, annuler"

If "Non, annuler": exit
</step>

<step name="identify_phases">
Read PROJECT.md and identify natural phases (2-5 phases).

Ask user to confirm with AskUserQuestion:
- header: "Phases"
- question: "Voici les phases que je propose. OK ?"
- Show phases as description
- Options: "OK, créer" / "Ajuster" / "Me laisser définir"

If "Ajuster": Ask what to change (freeform), then recreate
If "Me laisser définir": Get phases from user (freeform), then use those
</step>

<step name="create_roadmap">
Create ROADMAP.md using template: `templates/roadmap-light.md`

Fill in:
- Each phase name
- 2-3 line description per phase
- Key deliverables per phase
- Progress checklist at bottom

Keep it to ~50 lines max.
</step>

<step name="create_directories">
```bash
mkdir -p .planning/plans
```

No phase subdirectories - all plans go in `.planning/plans/` with naming:
- `01-PLAN.md` (phase 1)
- `02-PLAN.md` (phase 2)
- etc.
</step>

<step name="initialize_state">
Create or update STATE.md:

```markdown
# Project State

## Current Position
- Phase: 1
- Plan: None yet
- Next: Create plan for Phase 1

## Recent Decisions
(None yet)

## Active Issues
(None yet)

## Last Session
- Date: [now]
- Action: Roadmap created
- Result: [N] phases defined

---
*Auto-updated by /exec*
```
</step>

<step name="commit">
```bash
git add .planning/ROADMAP.md .planning/STATE.md
git commit -m "docs: create roadmap with [N] phases"
```
</step>

<step name="next">
Tell user:

```
✅ Roadmap créé

**Phases:** [N]
**Fichier:** .planning/ROADMAP.md

---

## ▶ Next Up

**Phase 1: [Name]** — [description]

`/plan 1`

---
```
</step>

</process>

<success_criteria>
- [ ] PROJECT.md validated
- [ ] Phases identified (2-5)
- [ ] ROADMAP.md created (light version)
- [ ] STATE.md initialized
- [ ] Changes committed
- [ ] User knows next command
</success_criteria>
