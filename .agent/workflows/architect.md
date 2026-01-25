---
description: Generates a persistent implementation plan and prompt for the Claude CLI to execute. Use this when the user wants to "architect" a solution for the CLI to build.
---

1.  **Analyze Context**
    *   Understand the user's goal from the prompt.
    *   Explore relevant files in the codebase to understand the current state.

2.  **Generate `PROMPT.md`**
    *   Create or overwrite `PROMPT.md` in the workspace root.
    *   **Content**:
        *   `# Goal`: A clear, high-level summary of what needs to be built.
        *   `## Context`: Briefly mention relevant files or existing architecture.
        *   `## Requirements`: Bullet points of specific constraints or needs.

3.  **Generate `IMPLEMENTATION_PLAN.md`**
    *   Create or overwrite `IMPLEMENTATION_PLAN.md` in the workspace root.
    *   **Content**:
        *   `# Implementation Plan - [Goal Name]`
        *   `## Proposed Changes`: Group changes by component/file.
            *   Use `### [MODIFY] filename` or `### [NEW] filename`.
            *   Provide tech-spec level details (function names, logic changes) so the CLI knows *exactly* what to do.
        *   `## Verification`: Steps to verify the work (commands to run).

4.  **Handoff**
    *   Notify the user that the plan is ready.
    *   Instruct them to run `claude` in their terminal to start the build process.
