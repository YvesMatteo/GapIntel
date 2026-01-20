---
name: ralph-loop
description: "Autonomous development loop methodology inspired by Ralph for Claude Code. Use this skill to execute complex, multi-step features by utilizing a persistent PROMPT.md and IMPLEMENTATION_PLAN.md."
---

# Ralph Loop Methodology

This skill implements the "Ralph Loop" or "Ralph for Claude Code" methodology, designed to enable autonomous, iterative development.

## Core Concept
Instead of relying on ephemeral chat context, this methodology uses persistent files to drive the development process. The agent (you) should cycle through reading instruction, executing work, and updating the plan.

## Required Files
These files should exist in the root of the workspace (or the specific feature directory):

1.  **`PROMPT.md`**: The "User's Voice". Contains the high-level objective, constraints, and success criteria.
    *   *Usage*: Read this at the start of every task boundary to ground yourself in the primary goal.
2.  **`IMPLEMENTATION_PLAN.md`**: The "Agent's Brain". Contains the detailed breakdown of tasks, their status, and technical notes.
    *   *Usage*: Read this to decide *what to do next*. Update this *after every meaningful step* to track progress.

## The Loop Protocol

When operating in Ralph Mode:

1.  **ANCHOR**: Read `PROMPT.md` to confirm the high-level goal hasn't successfully completed or changed.
2.  **CONTEXT**: Read `IMPLEMENTATION_PLAN.md` to identify the next pending task.
3.  **PLAN**: If `IMPLEMENTATION_PLAN.md` is empty or outdated, your first task is to populate it based on `PROMPT.md`.
4.  **EXECUTE**: Pick the *single most important* next step from the plan.
    *   Write code.
    *   Run commands.
    *   Verify results.
5.  **UPDATE**: Edit `IMPLEMENTATION_PLAN.md`.
    *   Mark the completed task as `[x]`.
    *   Add notes/findings.
    *   Refine future steps if new info was discovered.
6.  **REPEAT**: Go back to step 1.

## Best Practices
*   **Atomic Steps**: Break the Implementation Plan into small, verifiable chunks.
*   **Self-Correction**: If a step fails, update the Plan with a new "Fix X" task rather than blindly retrying.
*   **Transparency**: The `IMPLEMENTATION_PLAN.md` is your communication log with the user. Keep it clean and updated.
*   **Completion**: When all tasks in `IMPLEMENTATION_PLAN.md` are checked, and `PROMPT.md` criteria are met, explicitly Notify User that the loop is complete.

## Templates

See `templates/` directory for starter files.
