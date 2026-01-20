---
name: plan
description: Create a lightweight PLAN.md for a phase
argument-hint: "[phase-number]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Grep
  - Glob
  - AskUserQuestion
---

<objective>
Create a lightweight PLAN.md for a specific phase.

Plan contains:
- 2-5 tasks
- Files to modify per task
- Brief description per task
- Verification commands

Much simpler than full GSD plans (no context section, no dependencies, no checkpoints).
</objective>

<context>
Phase number: $ARGUMENTS

@.planning/PROJECT.md
@.planning/ROADMAP.md
</context>

<process>

<step name="set_working_directory">
**CRITIQUE - Exécuter en premier avant toute action :**

```bash
cd $PWD
```

Cela garantit que après un `/clear`, le plan s'exécute dans le bon worktree.
</step>

<step name="validate">
```bash
[ -f .planning/PROJECT.md ] || { echo "ERROR: No PROJECT.md found. Run `/start` first."; exit 1; }
[ -f .planning/ROADMAP.md ] || { echo "ERROR: No ROADMAP.md found. Run `/roadmap` first."; exit 1; }
```

Get phase number from $ARGUMENTS or ask:
- "Pour quelle phase veux-tu créer un plan ?" (if empty)

Store as PHASE_NUM.
</step>

<step name="get_phase_info">
Read ROADMAP.md and extract Phase [PHASE_NUM] information:
- Name
- Description
- Deliverables

If phase doesn't exist in roadmap, error: "Phase [N] not found in ROADMAP.md"
</step>

<step name="explore_codebase">
Quickly explore relevant files for this phase:

```bash
# Find relevant files based on phase description keywords
# Example: if phase is "Add authentication", search for auth files
```

Use Glob/Grep to find ~5-10 relevant files to understand context.
</step>

<step name="draft_tasks">
Based on phase goals and codebase, draft 2-5 tasks.

Each task should:
- Be completable in 5-30 minutes
- Modify 1-3 files
- Have clear success criteria
</step>

<step name="confirm_tasks">
Show tasks to user with AskUserQuestion:
- header: "Tasks"
- question: "Voici les tâches pour Phase [N]. OK ?"
- Show tasks in description
- Options: "OK, créer plan" / "Ajuster" / "Me laisser définir"

If "Ajuster": Ask what to change, regenerate
If "Me laisser définir": Get tasks from user (freeform)
</step>

<step name="create_plan">
Create PLAN.md using template: `templates/plan-light.md`

Filename: `.planning/plans/0[PHASE_NUM]-PLAN.md`

Fill in:
- Phase name
- Each task with:
  - Task name
  - Files to modify
  - Brief what-to-do
- Verification section with commands

Keep it to ~30-40 lines max.
</step>

<step name="update_state">
Update STATE.md:

```markdown
## Current Position
- Phase: [PHASE_NUM]
- Plan: 0[PHASE_NUM]-PLAN created
- Next: Execute plan with /exec
```
</step>

<step name="commit">
```bash
PLAN_PATH=".planning/plans/0${PHASE_NUM}-PLAN.md"
git add "$PLAN_PATH" .planning/STATE.md
git commit -m "docs: plan phase ${PHASE_NUM}"
```
</step>

<step name="next">
Tell user:

```
✅ Plan créé

**Phase:** [PHASE_NUM] - [Name]
**Tasks:** [N]
**Fichier:** .planning/plans/0[PHASE_NUM]-PLAN.md

---

## ▶ Next Up

Execute the plan:

`/exec`

---
```
</step>

</process>

<success_criteria>
- [ ] Phase validated in ROADMAP
- [ ] Codebase explored
- [ ] Tasks identified (2-5)
- [ ] PLAN.md created (light version)
- [ ] STATE.md updated
- [ ] Changes committed
- [ ] User knows next command
</success_criteria>
