# Findings: [Feature Name]

Everything non-obvious learned while implementing this feature: behavior that
looks like a bug unless you know it is deliberate, traps in the libraries and
tools, and what worked. Each entry says what the rule is, how it was caught, and
what it cost.

Status: [in progress | complete for tasks X-Y]; keep it current as the code
changes.

## 1. Behavior that does not survive a naive implementation

### 1.1 [One-line statement of the rule]

[What the rule is, with `path:line` references]

**Caught by**: [the test, comparison or observation that revealed it]

**Cost**: [what getting it wrong changed, measured where possible]

## 2. Library and tooling traps

### 2.1 [One-line statement of the trap]

[What happens, how it was caught, and how the code avoids it]

## 3. Method — what actually worked

### 3.1 [Technique]

[How it helped, and when to use it again]
