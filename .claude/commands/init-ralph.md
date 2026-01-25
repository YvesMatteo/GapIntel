# Initialize Ralph Loop

Set up the `PROMPT.md` and `IMPLEMENTATION_PLAN.md` files in the current directory to start a Ralph Loop session.

## Steps

1. Create `PROMPT.md` from template:
```bash
cat > PROMPT.md << 'EOF'
# Project Prompt

## Goal
[Describe the high-level goal here. Example: "Implement the new Login Page with OAuth support."]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Constraints
- Must use existing Tailwind theme.
- No new external libraries without approval.

## Success Criteria
- [ ] All tests pass.
- [ ] UI matches the design mockup.
EOF
```

2. Create `IMPLEMENTATION_PLAN.md` from template:
```bash
cat > IMPLEMENTATION_PLAN.md << 'EOF'
# Implementation Plan

## Status
- [ ] Planning
- [ ] In Progress
- [ ] Verification
- [ ] Complete

## Task List

### Phase 1: Setup
- [ ] [Create file structure]
- [ ] [Install dependencies]

### Phase 2: Implementation
- [ ] [Implement Component A]
- [ ] [Implement Component B]

### Phase 3: Verification
- [ ] [Run Unit Tests]
- [ ] [Manual Verification]

## Notes & Findings
- [Date]: Started work.
EOF
```

3. Open `PROMPT.md` and fill in your objective.

## The Ralph Loop Protocol

Once initialized:
1. **ANCHOR**: Read `PROMPT.md` to confirm the goal
2. **CONTEXT**: Read `IMPLEMENTATION_PLAN.md` for next task
3. **PLAN**: Populate plan if empty/outdated
4. **EXECUTE**: Pick single most important next step
5. **UPDATE**: Edit IMPLEMENTATION_PLAN.md with progress
6. **REPEAT**: Go back to step 1
