---
name: qa-review
description: "Full-system QA review: scan entire codebase for bugs across backend/frontend, produce prioritized bug report with reproduction steps"
---

# Full-System QA Review

## Overview

Perform a senior QA review of the entire system — not a git-diff review, but a comprehensive scan of all code layers to find bugs, logic errors, and integration issues. Produces a structured, prioritized bug report.

**Core principle:** Scan broadly, report precisely. Every bug must have a file path, line context, severity, and reproduction steps.

## When to Use

- User asks for a "revisão geral", "varredura completa", "QA review", or "busca de bugs"
- Before major releases or deployments
- After significant feature additions to verify nothing broke
- When the system feels unstable but no specific bug is reported

**Do NOT use for:**
- Reviewing a specific git diff (use `compose:review` instead)
- Debugging a single known bug (use `compose:debug` instead)
- Quick spot-checks (just read the code directly)

## The Process

### Phase 1: Project Discovery

1. **Identify project structure:**
   - Find the root, list top-level directories
   - Identify framework(s), language(s), build system
   - Find configuration files (package.json, .csproj, etc.)
   - Map the architecture (frontend/backend/shared/etc.)

2. **Map entry points:**
   - Backend: controllers/routes, Program.cs/Startup, middleware pipeline
   - Frontend: pages/routes, main entry, API client
   - Database: models/entities, migrations, seed data
   - Config: environment variables, secrets, feature flags

### Phase 2: Layered Scan

Scan each layer independently, then cross-reference for integration bugs.

**Backend scan:**
- Controllers: missing error handling, auth gaps, incorrect HTTP methods
- Services: logic errors, missing validation, race conditions
- Data layer: missing query filters, incorrect relationships, N+1 queries
- Identity: JWT issues, authorization policy gaps, secret handling

**Frontend scan:**
- Routes: missing auth guards, broken navigation, dead routes
- API calls: missing error handling, incorrect endpoints, stale types
- State: missing loading states, optimistic update bugs, memory leaks
- UI: broken layouts, missing responsive behavior, accessibility issues

**Integration scan:**
- API contract mismatches (frontend types vs backend DTOs)
- Missing CORS configuration
- WebSocket/signalr connection issues
- File upload/download mismatches

### Phase 3: Cross-Cutting Checks

- **Security:** SQL injection, XSS, CSRF, hardcoded secrets, missing rate limiting
- **Performance:** N+1 queries, missing pagination, large payload issues, missing caching
- **Reliability:** missing try-catch, unhandled promise rejections, missing retry logic
- **Consistency:** enum mismatches, timezone handling, decimal precision

### Phase 4: Bug Report

Produce a structured report. Group by severity, then by layer.

## Output Format

```markdown
# QA Review — [Project Name]
**Date:** YYYY-MM-DD
**Scope:** [backend/frontend/full-stack]
**Files scanned:** [count]

## Summary
- Critical: N
- High: N
- Medium: N
- Low: N

## Critical Bugs

### BUG-01: [Short title]
- **File:** `path/to/file.cs` (line ~N)
- **What:** [Brief description of the bug]
- **Impact:** [What breaks for the user]
- **Reproduction:** [Steps to trigger]
- **Suggested fix:** [How to fix, or "needs investigation"]

## High Bugs
[Same format]

## Medium Bugs
[Same format]

## Low Bugs / Improvements
[Same format]

## Architecture Notes
[Any structural observations, not bugs but worth knowing]
```

## Tips

- **Read before scanning:** Understand the architecture before diving into individual files
- **Check types first:** TypeScript/frontend type mismatches with backend DTOs are the most common bug source
- **Follow the data flow:** Trace a request from controller → service → repository → DB to find gaps
- **Look for TODO/FIXME/HACK:** These are intentional debt markers — count them but don't always report as bugs
- **Verify against seed data:** If entities don't match seed data expectations, that's a bug
- **Check multi-tenancy:** In multi-tenant systems, verify query filters are applied everywhere
- **Use TypeScript check:** `cmd /c "cd <frontend> && npx tsc -b"` catches type-level bugs automatically

## Example Invocation

```
User: "Haja como um QA senior e revise o sistema inteiro em busca de bugs"

You: [Follow this skill — scan all layers, produce bug report]
```
