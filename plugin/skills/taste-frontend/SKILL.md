---
name: "taste-frontend"
description: "Art direction for landing pages, marketing sites, portfolios, and app screens (dashboards, settings) so they don't look generic or AI-made. Uses Leonxlnx's tasteskill (design-taste-frontend)."
---

# tasteskill loader (design-taste-frontend)

This is a loader for **tasteskill v2** (`design-taste-frontend`) by Leonxlnx, MIT licence. It's the default design skill that ships with the TasteCode app. The real skill is a folder of about 212 files: a SKILL.md, `scripts/` (draw, inspect, lint, scenes, assets), a `library/` of directions researched from 247 gallery sites, `references/` for type, colour, layout, copy, critique, motion and app screens, and `assets/` (base.css, app.css, charts.js). This loader downloads that folder and then hands over to its SKILL.md.

## When to use
Use it whenever you build, design, redesign, restyle, polish, or review a public-facing web page. That covers landing pages, marketing and product sites, portfolios, one-pagers, heroes, event and restaurant sites, in any stack. It also covers app screens such as dashboards, admin and analytics views, settings, and inboxes. Use it too when a page looks generic, templated, or "AI-made", or when the user wants it to look premium or award-level.

## 1. Download the skill (once per session)
Run this from the workspace, not inside the user's project. If `$TASTE` already exists, skip this step.
```bash
export TASTE_ROOT=/tmp/taste-skill-src
[ -d "$TASTE_ROOT/.git" ] || git clone --depth 1 -q https://github.com/Leonxlnx/taste-skill.git "$TASTE_ROOT"
export TASTE="$TASTE_ROOT/skills/taste-skill"
ls "$TASTE"   # expect SKILL.md scripts library references assets
```
If the clone fails, tell the user. Don't reconstruct the skill from memory.

## 2. Point its scripts at a browser
The scripts need Node 22 or newer and a Chrome or Chromium, and they install nothing. In a cloud container running as root, Chromium also needs `--no-sandbox`, so wrap Playwright's bundled Chromium:
```bash
P=$(node -e "console.log(require('playwright').chromium.executablePath())" 2>/dev/null || command -v chromium || command -v google-chrome)
printf '#!/bin/sh\nexec "%s" --no-sandbox "$@"\n' "$P" > /tmp/chrome-nosandbox && chmod +x /tmp/chrome-nosandbox
export CHROME_PATH=/tmp/chrome-nosandbox
```
Shell state doesn't persist between calls. Prefix every script call with `CHROME_PATH=/tmp/chrome-nosandbox` and use the full path `/tmp/taste-skill-src/skills/taste-skill` wherever its docs say `<skill>`.

## 3. Follow the real skill
Read `/tmp/taste-skill-src/skills/taste-skill/SKILL.md` in full with the Read tool and follow it as your instructions for this task. Read the `references/*.md` files it points to when it tells you to. For app screens, that means reading `references/app-screens.md` in full first.

Its main steps:
- **Draw:** `node <skill>/scripts/draw.mjs --sector <sector> --brief "<subject>" [--app --kind <kind>] --out .taste-skill/...`. `--sector` is required and must be one of: saas, dev-tool, ai-product, consumer-app, finance, agency, studio-portfolio, personal-portfolio, ecommerce, physical-product, fashion, hospitality, restaurant, real-estate, architecture, event, health, education, nonprofit, culture, music, other.
- **Gate:** run `lint.mjs` on the source, `inspect.mjs <url or index.html>` (add `--app` for app screens), and `scenes.mjs` when the page has scroll scenes. Fix every FAIL.
- **Look:** open the screenshots in `.taste-skill/inspect/` with Read, critique them using `references/critique.md`, fix the top three problems, and re-inspect. Do at most three rounds.

Run these scripts from the root of the project being built so their working files land in `.taste-skill/` there. Don't include `.taste-skill/` in the user's deliverable.

## Fitting this environment
- `assets.mjs` downloads photos and needs network access, which is usually blocked here. If it fails, say so and use the user's own images or clearly-marked placeholders. Don't hotlink random web images.
- The deliverable still follows the normal output rules (for example a published HTML artifact or a design). This skill decides how it looks, not where it goes.
- Credit when relevant: "art direction via tasteskill by Leonxlnx (MIT)".