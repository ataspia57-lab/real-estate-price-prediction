# realestate-capstone plugin

Claude plugin for the Real Estate Price Prediction System. It contains the four project skills
and a copy of every other skill that was available in the author's Claude account when this was built.

## Install

Open the repo in Claude Code. `.claude/settings.json` registers the local marketplace in
`.claude-plugin/marketplace.json` and enables this plugin, so Claude Code asks you to trust it on first run.
Manual install:

```
/plugin marketplace add ./
/plugin install realestate-capstone@realestate-capstone-marketplace
```

For claude.ai, zip any single skill folder from `skills/` and upload it under Settings → Capabilities → Skills.

## Project skills

| Skill | When it is used |
|---|---|
| `capstone-report` | Write or update SE331 capstone deliverables for the Real Estate Price Prediction System — progress reports, final report, SRS sections, UML/diagrams,… |
| `run-price-app` | Run, debug, test or deploy the Flask web app and REST API for the real estate price predictor. Use for anything about the UI, /api/predict, validation… |
| `train-price-model` | Retrain, tune or compare the real estate price models in this project. Use when asked to retrain, add a new regressor, change hyperparameters, check R² /… |
| `use-real-dataset` | Replace the synthetic demo data with a real housing dataset (Kaggle, bproperty-style listings, Bengaluru house data, etc.) and map its columns to this… |

## Bundled skills

Copied unchanged from their original plugins and skill packs; each keeps its own LICENSE file where one was provided.

| Skill | When it is used |
|---|---|
| `accessibility-review` | Run a WCAG 2.1 AA accessibility audit on a design or page. Trigger with "audit accessibility", "check a11y", "is this accessible?", or when reviewing a… |
| `analyze` | Answer data questions -- from quick lookups to full analyses. Use when looking up a single metric, investigating what's driving a trend or drop, comparing… |
| `animation-studio` | This skill should be used when the user asks to "make an animated video about X with music", "make a cartoon / animated short", "animate this story", "make… |
| `build-dashboard` | Build an interactive HTML dashboard with charts, filters, and tables. Use when creating an executive overview with KPI cards, turning query results into a… |
| `built-in-browser` | Read this skill before the first step that uses the built-in browser, the browser pane inside the Claude desktop app (also called the in-app browser, the… |
| `chrome-browser` | Read this skill before the first step that uses Claude in Chrome, the browser extension whose tools are named mcp__claude-in-chrome__* (also called Chrome,… |
| `computer-use` | Read this skill before the first step of any request to do something in an app on the person's own computer (Notes, Finder, System Settings, any desktop… |
| `create-viz` | Create publication-quality visualizations with Python. Use when turning query results or a DataFrame into a chart, selecting the right chart type for a… |
| `data-context-extractor` | Generate or improve a company-specific data analysis skill by extracting tribal knowledge from analysts.\nBOOTSTRAP MODE - Triggers: \"Create a data context… |
| `data-visualization` | Create effective data visualizations with Python (matplotlib, seaborn, plotly). Use when building charts, choosing the right chart type for a dataset,… |
| `deep-research` | Use this skill when the user's prompt requires (1) researching a topic across multiple sources, comparing options or alternatives, analyzing trends or… |
| `design-critique` | Get structured design feedback on usability, hierarchy, and consistency. Trigger with "review this design", "critique this mockup", "what do you think of… |
| `design-handoff` | Generate developer handoff specs from a design. Use when a design is ready for engineering and needs a spec sheet covering layout, design tokens, component… |
| `design-md-styles` | Style a UI, page, or mockup after a known brand's design system (Stripe, Linear, Apple, Notion, etc.) using DESIGN.md files from VoltAgent's… |
| `design-system` | Audit, document, or extend your design system. Use when checking for naming inconsistencies or hardcoded values across components, writing documentation for… |
| `docs` | 'docs (editable docs people share and comment on; the default for any document, named as a doc or not: a document, report, proposal, resume, cover letter,… |
| `docx` | Use this skill whenever the user wants to create, read, edit, or manipulate Word documents (.docx) or Word templates (.dotx). Triggers include: any mention… |
| `explore-data` | Profile and explore a dataset to understand its shape, quality, and patterns. Use when encountering a new table or file, checking null rates and column… |
| `figma-code-connect` | Creates and maintains Figma Code Connect template files that map Figma components to code snippets. Use when the user mentions Code Connect, Figma component… |
| `figma-code-workflows` | Import or upload local HTML or project files into Figma, choose editable Design frames, runnable Code Layers or standalone Code (also known as Make), and… |
| `figma-create-new-file` | Always use this skill when the user wants to create a new Figma Design, FigJam, or Slides file. You MUST invoke this skill BEFORE every `create_new_file`… |
| `figma-design-to-code` | **MANDATORY prerequisite** — you MUST invoke this skill BEFORE calling the `get_design_context` Figma MCP tool. You MUST trigger this skill whenever the… |
| `figma-generate-design` | Use this skill alongside figma-use when the task involves translating an application page, view, or multi-section layout into Figma. Triggers: 'write to… |
| `figma-generate-diagram` | MANDATORY prerequisite — load this skill BEFORE every `generate_diagram` tool call. NEVER call `generate_diagram` directly without loading this skill first.… |
| `figma-generate-library` | Build or update a professional-grade design system in Figma from a codebase. Use when the user wants to create variables/tokens, build component libraries,… |
| `figma-generative-plugins` | **MANDATORY prerequisite** — load this skill before calling `create_generative_plugin` or `update_generative_plugin`. Use when the user asks to create,… |
| `figma-implement-motion` | Translates Figma motion and animations into production-ready application code. Use when implementing animation/motion from a Figma design — user mentions… |
| `figma-shaders` | **MANDATORY prerequisite** — load this skill before calling `create_shader` or `update_shader`. Use when the user asks to create, author, change, fix, or… |
| `figma-spec` | This skill is required to create, read, edit, review, or comment on Figma specs. You must read it when working on a PRD, brief, RFC or any kind of document… |
| `figma-swiftui` | SwiftUI ↔ Figma translation. Use whenever the user mentions Swift, SwiftUI, iOS, iPhone, or iPad — in EITHER direction — translating a Figma design into… |
| `figma-use` | **MANDATORY prerequisite** — you MUST invoke this skill BEFORE every `use_figma` tool call. NEVER call `use_figma` directly without loading this skill… |
| `figma-use-figjam` | This skill helps agents use Figma's use_figma MCP tool in the FigJam context. Can be used alongside figma-use which has foundational context for using the… |
| `figma-use-motion` | Motion / animation context for the `use_figma` MCP tool — animating Figma nodes via manual keyframes, animation styles, easing, and timeline duration. Load… |
| `figma-use-slides` | This skill helps agents use Figma's use_figma MCP tool in the Slides context. Can be used alongside figma-use which has foundational context for using the… |
| `frontend-patterns` | Frontend patterns for React, Next.js, state management, performance and UI best practices. Use when building or reviewing React or Next.js components,… |
| `google-workspace` | Read this before the first Google Drive, Docs, Sheets or Slides connector call whenever the task creates or changes a Google file. Use this skill whenever… |
| `impeccable` | Use to design, redesign, critique, audit, polish or animate a frontend: websites, landing pages, dashboards, app UI, components, native iOS/Android screens,… |
| `import-memory` | Import a memory export from another AI assistant into Claude's memory — conversationally, additively, and with the content treated as data. |
| `memory-management` | Two-tier memory system that makes Claude a true workplace collaborator. Decodes shorthand, acronyms, nicknames, and internal language so Claude understands… |
| `morning` | Render the user's morning brief as a styled HTML artifact, or set it up as a recurring weekday task. Use only when the user explicitly asks to run, see, or… |
| `pdf` | Use this skill whenever the user wants to do anything with PDF files. This includes reading or extracting text/tables from PDFs, combining or merging… |
| `pptx` | Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or… |
| `research-synthesis` | Synthesize user research into themes, insights, and recommendations. Use when you have interview transcripts, survey results, usability test notes, support… |
| `search-first` | Research-before-coding: search npm/PyPI, MCP servers, skills and GitHub for existing tools before writing custom code. Use when starting a feature, adding a… |
| `security-review` | Use when adding authentication, handling user input, working with secrets, creating API endpoints, or implementing payment/sensitive features. Provides a… |
| `skill-creator` | Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize… |
| `sql-queries` | Write correct, performant SQL across all major data warehouse dialects (Snowflake, BigQuery, Databricks, PostgreSQL, etc.). Use when writing queries,… |
| `start` | Initialize the productivity system and open the dashboard. Use when setting up the plugin for the first time, bootstrapping working memory from your… |
| `statistical-analysis` | Apply statistical methods including descriptive stats, trend analysis, outlier detection, and hypothesis testing. Use when analyzing distributions, testing… |
| `task-management` | Simple task management using a shared TASKS.md file. Reference this when the user asks about their tasks, wants to add/complete tasks, or needs help… |
| `taste-frontend` | Art direction for landing pages, marketing sites, portfolios, and app screens (dashboards, settings) so they don't look generic or AI-made. Uses Leonxlnx's… |
| `ui-ux-pro-max` | UI/UX design intelligence for designing, building, reviewing or fixing web, mobile and desktop interfaces: styles, palettes, font pairings, UX/accessibility… |
| `update` | Sync tasks and refresh memory from your current activity. Use when pulling new assignments from your project tracker into TASKS.md, triaging stale or… |
| `user-research` | Plan, conduct, and synthesize user research. Trigger with "user research plan", "interview guide", "usability test", "survey design", "research questions",… |
| `ux-copy` | Write or review UX copy — microcopy, error messages, empty states, CTAs. Trigger with "write copy for", "what should this button say?", "review this error… |
| `validate-data` | QA an analysis before sharing -- methodology, accuracy, and bias checks. Use when reviewing an analysis before a stakeholder presentation, spot-checking… |
| `vercel-composition-patterns` | React composition patterns that scale: compound components, avoiding boolean-prop sprawl, lifting state into providers, React 19 APIs. Use when designing or… |
| `vercel-react-best-practices` | Vercel's 70 React/Next.js performance rules (waterfalls, bundle size, server, re-renders). Use when writing, reviewing, or refactoring React/Next.js code or… |
| `video-making` | Use this skill before making a new video. Not for editing a video file the user supplied. |
| `web-design-guidelines` | Review UI code for Vercel's Web Interface Guidelines (accessibility, forms, focus, motion, typography, performance). Use for \"review my UI\", \"check… |
| `write-query` | Write optimized SQL for your dialect with best practices. Use when translating a natural-language data need into SQL, building a multi-CTE query with joins… |
| `xlsx` | Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing… |
| `youtube-transcriber` | Transcribe YouTube videos and playlists by extracting auto-generated captions directly from the browser — no API key, no external service, completely free.… |
