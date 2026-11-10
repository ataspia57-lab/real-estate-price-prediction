---
name: "vercel-composition-patterns"
description: "React composition patterns that scale: compound components, avoiding boolean-prop sprawl, lifting state into providers, React 19 APIs. Use when designing or refactoring component APIs."
---

# React Composition Patterns

From vercel-labs/agent-skills (MIT). These patterns keep React components flexible and maintainable. Instead of piling up boolean props, use compound components, lift state, and compose internals. Codebases built this way are easier for both people and AI agents to work in as they grow.

## Getting the rule files
Fetch them once per session:
```bash
[ -d /tmp/vercel-agent-skills/.git ] || git clone --depth 1 -q https://github.com/vercel-labs/agent-skills /tmp/vercel-agent-skills
R=/tmp/vercel-agent-skills/skills/composition-patterns
```
- One rule: `$R/rules/<rule-id>.md`. Each has an explanation and incorrect/correct code.
- Every rule expanded in one file (about 23 KB): `$R/AGENTS.md`.
If the clone fails, apply the quick reference below and say the detailed examples weren't available.

## When to apply
Use these rules when refactoring components that have many boolean props, building reusable component libraries, designing flexible component APIs, reviewing component architecture, or working with compound components and context providers. Before restructuring code based on a rule, read that rule's file.

## Categories by priority
| Priority | Category | Impact | Prefix |
|---|---|---|---|
| 1 | Component Architecture | HIGH | `architecture-` |
| 2 | State Management | MEDIUM | `state-` |
| 3 | Implementation Patterns | MEDIUM | `patterns-` |
| 4 | React 19 APIs | MEDIUM | `react19-` |

## Quick reference

### 1. Component Architecture (HIGH)
- `architecture-avoid-boolean-props`: don't add boolean props to customize behavior; use composition
- `architecture-compound-components`: structure complex components with shared context

### 2. State Management (MEDIUM)
- `state-decouple-implementation`: the provider is the only place that knows how state is managed
- `state-context-interface`: define a generic interface of state, actions, and meta for dependency injection
- `state-lift-state`: move state into provider components so siblings can access it

### 3. Implementation Patterns (MEDIUM)
- `patterns-explicit-variants`: create explicit variant components instead of boolean modes
- `patterns-children-over-render-props`: use children for composition instead of renderX props

### 4. React 19 APIs (MEDIUM). React 19+ only; skip on React 18 or earlier.
- `react19-no-forwardref`: don't use `forwardRef`; use `use()` instead of `useContext()`

Check the project's React version in package.json before applying section 4.