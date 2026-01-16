---
name: start
description: Start a new task with auto-detection of size and appropriate planning level
argument-hint: "[task-name]"
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
  - Glob
---

<objective>
Auto-detect task size and create appropriate planning structure:
- Quick (1-3h) → PLAN.md light only
- Normal (1 day) → PROJECT.md + ROADMAP.md + PLAN.md (all light versions)
- Large (2-5 days) → Full PROJECT + ROADMAP with 3-5 phases

Maintains intelligent agent execution from GSD but with simplified structure.
</objective>

<context>
Task name: $ARGUMENTS (optional - can ask if not provided)
</context>

<process>

<step name="get_task_name">
If $ARGUMENTS is empty, ask user:

"Quel est le nom de la tâche ?" (freeform response)

Store as TASK_NAME.
</step>

<step name="detect_size">
Use AskUserQuestion to detect size:

- header: "Taille estimée"
- question: "Quelle est la taille de cette tâche ?"
- options:
  - "Quick (1-3h)" — Bug fix, petite amélioration, ajustement simple
  - "Normal (1 jour)" — Feature simple, refactoring ciblé
  - "Large (2-5 jours)" — Feature complexe, intégration, refactoring large

Store response as TASK_SIZE.
</step>

<step name="create_structure">
Based on TASK_SIZE, create appropriate structure:

**If Quick:**
1. Create `.planning/` if it doesn't exist
2. Create lightweight PLAN using quick template
3. File: `.planning/quick-PLAN.md`
4. Structure:
   ```markdown
   # Quick: [TASK_NAME]

   ## Tâches
   - [ ] Task 1
   - [ ] Task 2
   - [ ] Task 3

   ## Vérification
   ```bash
   # Commands to verify completion
   ```
   ```
5. Commit: `docs: quick plan for [task-name]`
6. Tell user: "Plan créé. Lance `/exec` pour exécuter."

**If Normal:**
1. Create `.planning/` if it doesn't exist
2. Ask freeform: "Qu'est-ce que tu veux accomplir ?"
3. Create light PROJECT.md (use template: templates/project-light.md)
4. Create light ROADMAP.md with 2-4 steps (use template: templates/roadmap-light.md)
5. Create first PLAN.md in `.planning/plans/01-PLAN.md` (use template: templates/plan-light.md)
6. Initialize STATE.md (auto-managed, simple version)
7. Commit: `docs: init [task-name] (normal mode)`
8. Tell user: "Projet créé. Lance `/exec plans/01-PLAN.md` pour commencer."

**If Large:**
1. Create `.planning/` if it doesn't exist
2. Ask 2-3 questions to understand scope (brief, not full GSD questioning)
3. Create light PROJECT.md (same as Normal)
4. Create ROADMAP.md with 3-5 phases (use template: templates/roadmap-light.md)
5. Tell user phases created
6. Ask which phase to plan first
7. Create PLAN.md for chosen phase in `.planning/plans/0X-PLAN.md`
8. Initialize STATE.md
9. Commit: `docs: init [task-name] (large mode)`
10. Tell user: "Projet créé avec [N] phases. Lance `/exec plans/0X-PLAN.md` pour phase [X]."
</step>

</process>

<templates_reference>
Templates are in:
- `.claude/get-shit-done/templates/project-light.md` (to create)
- `.claude/get-shit-done/templates/roadmap-light.md` (to create)
- `.claude/get-shit-done/templates/plan-light.md` (to create)
- `.claude/get-shit-done/templates/quick-plan.md` (to create)

All light versions are 50-80% shorter than current templates.
</templates_reference>

<execution_notes>
- No milestones/versions
- No discussion/research phases
- Quick questions, not exhaustive
- STATE.md is auto-managed (don't ask user to update)
- Use existing GSD execution engine (/exec will handle agent spawning)
</execution_notes>

<success_criteria>
- [ ] Task name captured
- [ ] Size detected
- [ ] Appropriate structure created (quick/normal/large)
- [ ] Files committed
- [ ] User knows next command (/exec)
</success_criteria>
