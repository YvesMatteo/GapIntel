# Architect

Generate a persistent implementation plan and prompt for Claude Code to execute. Use this when you want to plan out a solution before building.

## Instructions

When the user wants to "architect" a solution:

1. **Analyze Context**
   - Understand the user's goal from the prompt
   - Explore relevant files in the codebase to understand current state

2. **Generate `PROMPT.md`**
   - Create or overwrite `PROMPT.md` in the workspace root
   - **Content**:
     - `# Goal`: A clear, high-level summary of what needs to be built
     - `## Context`: Briefly mention relevant files or existing architecture
     - `## Requirements`: Bullet points of specific constraints or needs

3. **Generate `IMPLEMENTATION_PLAN.md`**
   - Create or overwrite `IMPLEMENTATION_PLAN.md` in the workspace root
   - **Content**:
     - `# Implementation Plan - [Goal Name]`
     - `## Proposed Changes`: Group changes by component/file
       - Use `### [MODIFY] filename` or `### [NEW] filename`
       - Provide tech-spec level details (function names, logic changes) so we know exactly what to do
     - `## Verification`: Steps to verify the work (commands to run)

4. **Handoff**
   - Notify user that the plan is ready
   - The Ralph Loop can then be used to execute the plan step by step
