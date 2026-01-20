---
name: exec
description: Execute a PLAN.md file with intelligent agent delegation
argument-hint: "[path-to-PLAN.md or empty for auto-detect]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Task
  - AskUserQuestion
---

<objective>
Execute a PLAN.md file using intelligent agent delegation for parallel/autonomous execution.

**Key features:**
- Auto-detects plan if not specified
- Spawns Task agents for autonomous execution
- Per-task atomic commits (feat/fix/test/refactor)
- Auto-updates STATE.md (no manual intervention)
- Creates SUMMARY.md with results
</objective>

<context>
Plan path: $ARGUMENTS (optional - will auto-detect if empty)

**Project context:**
@.planning/PROJECT.md (if exists)
@.planning/ROADMAP.md (if exists)
@.planning/STATE.md (if exists)
</context>

<process>

<step name="set_working_directory">
**CRITIQUE - Exécuter en premier avant toute action :**

```bash
cd $PWD
```

Cela garantit que après un `/clear`, le plan s'exécute dans le bon worktree.
</step>

<step name="find_plan">
If $ARGUMENTS is empty:

```bash
# Auto-detect: find the most recent PLAN.md that hasn't been executed
if [ -f .planning/quick-PLAN.md ]; then
  echo ".planning/quick-PLAN.md"
elif [ -d .planning/plans ]; then
  # Find first plan without SUMMARY
  for plan in .planning/plans/*-PLAN.md; do
    summary="${plan%.md}-SUMMARY.md"
    if [ ! -f "$summary" ]; then
      echo "$plan"
      break
    fi
  done
fi
```

If no plan found, error: "No PLAN.md found. Run `/start` first."

Store as PLAN_PATH.
</step>

<step name="validate">
Check plan exists and hasn't been executed:

```bash
[ -f "$PLAN_PATH" ] || { echo "ERROR: Plan not found: $PLAN_PATH"; exit 1; }

# Check if SUMMARY already exists
SUMMARY_PATH="${PLAN_PATH%.md}-SUMMARY.md"
[ -f "$SUMMARY_PATH" ] && echo "WARNING: Plan already executed (SUMMARY exists)"
```

If WARNING, ask user:
- "Plan déjà exécuté. Réexécuter ?"
- Options: "Oui" / "Non, annuler"
</step>

<step name="parse_plan">
Read PLAN_PATH and identify:
1. Number of tasks
2. Whether there are verification checkpoints
3. Task complexity

Determine execution strategy:
- **Strategy A (Fully Autonomous):** No checkpoints → spawn single Task agent for entire plan
- **Strategy B (Segmented):** Has verify checkpoints → spawn Task agents per segment
- **Strategy C (Decision-Based):** Complex/interactive → execute in main context

Most plans will be Strategy A (fully autonomous).
</step>

<step name="execute">
**Strategy A - Fully Autonomous (PREFERRED):**

Spawn a single Task agent with:
```
Prompt: "Execute this PLAN.md file completely. For each task:
1. Implement the changes
2. Verify it works
3. Create atomic commit with format: {type}: {task-name}
   (types: feat, fix, test, refactor, perf, chore)

After all tasks:
1. Create SUMMARY.md with:
   - What was accomplished
   - Commits created (with hashes)
   - Any issues encountered
   - Next steps
2. Do NOT commit SUMMARY.md yet (parent will handle)

Plan to execute:
@[PLAN_PATH]

Project context (if exists):
@.planning/PROJECT.md
@.planning/ROADMAP.md
"
```

**Strategy B - Segmented:**

Execute in segments between checkpoints, spawning Task agents for each autonomous segment.

**Strategy C - Decision-Based:**

Execute in main context with manual task-by-task commits.

Most executions should use Strategy A.
</step>

<step name="post_execution">
After agent completes (or after Strategy C execution):

1. **Read SUMMARY.md** created by agent
2. **Auto-update STATE.md:**
   ```markdown
   ## Current Position
   - Phase: [X]
   - Plan: [plan name] ✓ Complete
   - Next: [next plan or "Ready for next phase"]

   ## Recent Decisions
   [Extract any decisions from SUMMARY]

   ## Active Issues
   [Extract any issues from SUMMARY]

   ## Last Session
   - Date: [now]
   - Plan: [plan name]
   - Result: Complete
   - Commits: [N commits]
   ```

3. **Update ROADMAP.md progress:**
   - Mark phase/task as complete if applicable
   - Update completion percentage

4. **Create metadata commit:**
   ```bash
   git add .planning/STATE.md .planning/ROADMAP.md [SUMMARY_PATH]
   git commit -m "docs: complete $(basename $PLAN_PATH .md)"
   ```
</step>

<step name="next_steps">
Inform user of completion and next steps:

```
✅ Plan executed successfully

**Commits created:** [N commits]
**Summary:** [SUMMARY_PATH]

---

## ▶ Next Up

[If more plans exist:]
**Next plan:** .planning/plans/0X-PLAN.md

`/exec`

[If no more plans:]
**All plans complete!** Review ROADMAP.md for next phase, or use `/start` for new task.

---
```
</step>

</process>

<deviation_handling>
During execution, agents should handle discoveries automatically:

1. **Auto-fix bugs** - Fix immediately, document in Summary
2. **Auto-add critical** - Security/correctness gaps, add and document
3. **Auto-fix blockers** - Can't proceed without fix, do it and document
4. **Log enhancements** - Nice-to-haves, log to issues, continue

Only architectural changes require stopping to ask user.
</deviation_handling>

<commit_format>
**Per-Task Commits (created by agent):**
```
{type}: {task-description}

[Optional details]

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

Types: feat, fix, test, refactor, perf, chore

**Metadata Commit (created by parent):**
```
docs: complete [plan-name]

Summary: [SUMMARY_PATH]
Updates STATE.md and ROADMAP.md
```
</commit_format>

<success_criteria>
- [ ] Plan found/provided
- [ ] Execution strategy determined
- [ ] Tasks executed (via agent or main context)
- [ ] Per-task commits created
- [ ] SUMMARY.md created
- [ ] STATE.md auto-updated
- [ ] ROADMAP.md progress updated
- [ ] Metadata commit created
- [ ] User informed of next steps
</success_criteria>
