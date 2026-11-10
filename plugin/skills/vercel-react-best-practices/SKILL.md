---
name: "vercel-react-best-practices"
description: "Vercel's 70 React/Next.js performance rules (waterfalls, bundle size, server, re-renders). Use when writing, reviewing, or refactoring React/Next.js code or chasing performance."
---

# Vercel React Best Practices

A performance guide for React and Next.js from Vercel Engineering (vercel-labs/agent-skills, MIT). It has 70 rules in 8 categories, ordered by impact.

## Getting the rule files
The detailed rule files, each with an explanation and incorrect/correct code, are in the repo. Fetch them once per session:
```bash
[ -d /tmp/vercel-agent-skills/.git ] || git clone --depth 1 -q https://github.com/vercel-labs/agent-skills /tmp/vercel-agent-skills
R=/tmp/vercel-agent-skills/skills/react-best-practices
```
- One rule: `$R/rules/<rule-id>.md`, for example `rules/async-parallel.md`.
- Every rule expanded in one file (about 108 KB): `$R/AGENTS.md`. Read it in parts, only when doing a full audit.
If the clone fails, apply the quick reference below and say the detailed examples weren't available.

## When to apply
Use these rules when writing React components or Next.js pages, fetching data on the client or server, reviewing for performance, refactoring, or reducing bundle size and load time. Work from the highest priority down. Open a rule's file before citing it or making a non-obvious change based on it.

## Categories by priority
| Priority | Category | Impact | Prefix |
|---|---|---|---|
| 1 | Eliminating Waterfalls | CRITICAL | `async-` |
| 2 | Bundle Size Optimization | CRITICAL | `bundle-` |
| 3 | Server-Side Performance | HIGH | `server-` |
| 4 | Client-Side Data Fetching | MEDIUM-HIGH | `client-` |
| 5 | Re-render Optimization | MEDIUM | `rerender-` |
| 6 | Rendering Performance | MEDIUM | `rendering-` |
| 7 | JavaScript Performance | LOW-MEDIUM | `js-` |
| 8 | Advanced Patterns | LOW | `advanced-` |

## Quick reference

### 1. Eliminating Waterfalls (CRITICAL)
- `async-cheap-condition-before-await`: check cheap sync conditions before awaiting flags or remote values
- `async-defer-await`: move await into the branches where it's actually used
- `async-parallel`: use Promise.all() for independent operations
- `async-dependencies`: use better-all for partial dependencies
- `async-api-routes`: start promises early and await late in API routes
- `async-suspense-boundaries`: use Suspense to stream content

### 2. Bundle Size Optimization (CRITICAL)
- `bundle-barrel-imports`: import directly and avoid barrel files
- `bundle-analyzable-paths`: prefer statically analyzable import and file paths
- `bundle-dynamic-imports`: use next/dynamic for heavy components
- `bundle-defer-third-party`: load analytics and logging after hydration
- `bundle-conditional`: load modules only when their feature is activated
- `bundle-preload`: preload on hover or focus for perceived speed

### 3. Server-Side Performance (HIGH)
- `server-auth-actions`: authenticate server actions like API routes
- `server-cache-react`: use React.cache() for per-request deduplication
- `server-cache-lru`: use an LRU cache for cross-request caching
- `server-dedup-props`: avoid duplicate serialization in RSC props
- `server-hoist-static-io`: hoist static I/O (fonts, logos) to module level
- `server-no-shared-module-state`: avoid module-level mutable request state in RSC/SSR
- `server-serialization`: minimize data passed to client components
- `server-parallel-fetching`: restructure components so fetches run in parallel
- `server-parallel-nested-fetching`: chain nested fetches per item inside Promise.all
- `server-after-nonblocking`: use after() for non-blocking operations

### 4. Client-Side Data Fetching (MEDIUM-HIGH)
- `client-swr-dedup`: use SWR for automatic request deduplication
- `client-event-listeners`: deduplicate global event listeners
- `client-passive-event-listeners`: use passive listeners for scroll
- `client-localstorage-schema`: version and minimize localStorage data

### 5. Re-render Optimization (MEDIUM)
- `rerender-defer-reads`: don't subscribe to state that's only used in callbacks
- `rerender-memo`: extract expensive work into memoized components
- `rerender-memo-with-default-value`: hoist default non-primitive props
- `rerender-dependencies`: use primitive dependencies in effects
- `rerender-derived-state`: subscribe to derived booleans, not raw values
- `rerender-derived-state-no-effect`: derive state during render, not in effects
- `rerender-functional-setstate`: use functional setState for stable callbacks
- `rerender-lazy-state-init`: pass a function to useState for expensive initial values
- `rerender-simple-expression-in-memo`: don't memo simple primitives
- `rerender-split-combined-hooks`: split hooks with independent dependencies
- `rerender-move-effect-to-event`: put interaction logic in event handlers
- `rerender-transitions`: use startTransition for non-urgent updates
- `rerender-use-deferred-value`: defer expensive renders to keep input responsive
- `rerender-use-ref-transient-values`: use refs for transient, frequently changing values
- `rerender-no-inline-components`: don't define components inside components

### 6. Rendering Performance (MEDIUM)
- `rendering-animate-svg-wrapper`: animate a div wrapper, not the SVG element
- `rendering-content-visibility`: use content-visibility for long lists
- `rendering-hoist-jsx`: extract static JSX outside components
- `rendering-svg-precision`: reduce SVG coordinate precision
- `rendering-hydration-no-flicker`: use an inline script for client-only data
- `rendering-hydration-suppress-warning`: suppress expected hydration mismatches
- `rendering-activity`: use the Activity component for show/hide
- `rendering-conditional-render`: use a ternary, not &&, for conditionals
- `rendering-usetransition-loading`: prefer useTransition for loading state
- `rendering-resource-hints`: use React DOM resource hints for preloading
- `rendering-script-defer-async`: use defer or async on script tags

### 7. JavaScript Performance (LOW-MEDIUM)
- `js-batch-dom-css`: group CSS changes via classes or cssText
- `js-index-maps`: build a Map for repeated lookups
- `js-cache-property-access`: cache object properties in loops
- `js-cache-function-results`: cache function results in a module-level Map
- `js-cache-storage`: cache localStorage/sessionStorage reads
- `js-combine-iterations`: combine multiple filter/map calls into one loop
- `js-length-check-first`: check array length before an expensive comparison
- `js-early-exit`: return early from functions
- `js-hoist-regexp`: create RegExps outside loops
- `js-min-max-loop`: use a loop for min/max instead of sort
- `js-set-map-lookups`: use Set/Map for O(1) lookups
- `js-tosorted-immutable`: use toSorted() for immutability
- `js-flatmap-filter`: use flatMap to map and filter in one pass
- `js-request-idle-callback`: defer non-critical work to browser idle time

### 8. Advanced Patterns (LOW)
- `advanced-effect-event-deps`: don't put `useEffectEvent` results in effect deps
- `advanced-event-handler-refs`: store event handlers in refs
- `advanced-init-once`: initialize the app once per app load
- `advanced-use-latest`: use useLatest for stable callback refs

## Output
When reviewing, list findings by priority as `file:line`, then the rule id, then a one-line fix. When writing code, apply the rules silently and mention only the non-obvious ones.