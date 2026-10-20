---
name: pfb-spec-review
description:
  Review an implementation strictly against its specification in
  specs/NNNN-feature-name/ and produce a report with findings, a requirement
  coverage matrix and test gaps. Use when the user asks to review a feature,
  branch or PR against its spec.
argument-hint: "<spec folder> [branch, PR or path to review]"
---

# pfb-spec-review

You are a senior software engineer performing a Specification-Driven Development
(SDLD) code review. Be strict and specification-driven. Do not assume intent
beyond the provided documents. Do not modify any file: this skill only reports.

## Inputs

1. The spec folder (`requirements.md`, `design.md`, `tasks.md`). If not given,
   infer it from the current branch's changes or ask. If the folder is cancelled
   (`*-yanked` name or a `yanked.md` file), say so and stop.
2. The implementation: by default the diff of the current branch against the
   default branch (`git diff <default-branch>...HEAD` plus uncommitted changes).
   Use the PR, branch or paths the user gives instead, if any. Read whole files
   where the diff lacks context.
3. The project's `CLAUDE.md` / `AGENTS.md` for conventions.

## Review objectives

1. **Requirements compliance**: every acceptance criterion is fully implemented;
   flag missing, partial or incorrect behavior, and any functionality not
   defined in `requirements.md`.
2. **Architectural conformance**: the implementation follows `design.md`;
   abstractions and patterns are used as designed; no shortcuts that violate it.
3. **Task completion**: all files named in `tasks.md` exist and hold the
   intended logic; checked tasks are actually done; unchecked tasks are
   reported.
4. **Correctness and edge cases**: failure modes, race conditions, partial
   writes and invalid states; every correctness property in `design.md` is
   enforced.
5. **Code quality**: readability, modularity, typing, structure. Report style
   only when it materially affects maintainability.
6. **Test coverage**: tests exist for all major flows, edge cases and failure
   scenarios named in the spec.

Verify each finding against the code before reporting it: cite the file and
line, and drop findings you cannot point to. Run the project's tests if that
helps confirm a finding, and say so.

## Output

Produce the report in chat using this structure:

```md
## Summary

- Assessment: Pass / Needs Revision / Fail
- Key risks and concerns

## Findings

### <short title>

- **Severity**: Critical / Major / Minor
- **Category**: Requirements / Design / Tasks / Testing / Quality
- **Location**: `path/to/file:line` (function or class)
- **Issue**: what is wrong
- **Expected**: what the spec requires (cite requirement or design section)
- **Recommendation**: concrete fix

## Coverage Matrix

| Requirement | Criterion | Status | Evidence    |
| ----------- | --------- | ------ | ----------- |
| 1           | 1.1       | ✅     | `path:line` |

Status: ✅ Implemented, ⚠️ Partially implemented, ❌ Missing.

## Test Gaps

- missing or weak test cases
```

Order findings most severe first. Do not save the report to a file unless the
user asks, and never under `docs/`. If the user wants fixes, they can apply them
or run `pfb-spec-implement` again after updating the spec.
