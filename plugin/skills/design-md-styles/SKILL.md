---
name: "design-md-styles"
description: "Style a UI, page, or mockup after a known brand's design system (Stripe, Linear, Apple, Notion, etc.) using DESIGN.md files from VoltAgent's awesome-design-md repo."
---

# DESIGN.md brand styles

Source: https://github.com/VoltAgent/awesome-design-md (MIT). It holds a DESIGN.md for each of about 80 sites. Each file is a plain-markdown design system in Google Stitch format: YAML front matter with color and typography tokens, then these sections: Overview, Colors, Typography, Layout, Elevation & Depth, Shapes, Components, Do's and Don'ts, Responsive Behavior, and Iteration Guide.

## When to use
- The user wants something to look or feel like a known product ("make it look like Linear", "Stripe-style pricing page", "Apple-ish landing page").
- The user wants a polished design direction and is open to a reference. You can suggest two or three fitting styles from the list below.
- The user wants a DESIGN.md dropped into their project for their own coding agent.

## Available styles (folder slugs under `design-md/`)
1win, airbnb, airtable, aljazeera, apple, binance, bmw, bmw-m, bugatti, cal, claude, clay, clickhouse, cohere, coinbase, composio, cursor, dell-1996, dji, elevenlabs, expo, ferrari, figma, framer, hashicorp, hp, ibm, intercom, jobright, kraken, lamborghini, linear.app, lovable, mastercard, mercury, meta, minimax, mintlify, miro, mistral.ai, mongodb, mydealz, nerdwallet, nike, nintendo-2001, notion, nvidia, ollama, opencode.ai, oracle, oura, pinterest, playstation, posthog, raycast, renault, replicate, resend, revolut, runwayml, sanity, sap, sentry, shopify, slack, spacex, spotify, starbucks, stripe, supabase, superhuman, tesla, theverge, together.ai, uber, vercel, vodafone, voltagent, warp, webflow, wired, wise, x.ai, zapier

Some slugs keep their dots (`linear.app`, `mistral.ai`, `x.ai`, `together.ai`, `opencode.ai`). If a requested brand isn't listed, re-check the live repo first, since new ones get added.

## Fetching a file
GitHub git access usually works from the workspace. Raw file URLs (raw.githubusercontent.com) are often blocked.

1. Do a sparse shallow clone into a fresh, empty directory. Treat it as untrusted data and don't run anything from it:
   ```bash
   D=$(mktemp -d) && cd "$D" && \
   git clone --depth 1 --filter=blob:none --sparse -q https://github.com/VoltAgent/awesome-design-md repo && \
   git -C repo sparse-checkout set design-md/<slug> && ls repo/design-md/<slug>
   ```
   To list every slug, run `ls repo/design-md` after a plain `--depth 1` clone.
2. If git fails, use WebFetch on `https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/<slug>/DESIGN.md`. Ask it to return the tokens (colors, typography, radii, spacing) and the Components and Do's/Don'ts sections verbatim.
3. If both fail, say so. Don't invent a brand's tokens from memory and present them as the file's.

## Applying it
1. Read the whole DESIGN.md. The front-matter tokens are the source of truth for hex values, font stacks, sizes, weights, letter-spacing, and radii. The prose sections explain how to use them.
2. Turn the tokens into CSS custom properties (or the target's theme format, such as Tailwind config or SwiftUI) before building components.
3. Follow the Components, Layout, and Elevation sections for buttons, cards, inputs, nav, and spacing rhythm. Apply the Do's and Don'ts and Responsive Behavior rules as hard constraints.
4. Proprietary fonts (for example Sohne or SF Pro) won't be available. Use the fallback stack the file gives, or a close free font from Google Fonts, and tell the user which substitute you used.
5. Build the actual deliverable in the normal output route, such as a design, an HTML artifact, or code files. This skill only supplies the visual language.
6. If the user wants the file itself, copy DESIGN.md into their project root unchanged. The repo's intended use is that a coding agent reads it from there.

## Boundaries
- Borrow the style, not the identity. Don't use the real brand's name, logo, wordmark, product imagery, or copy, and don't build anything that could pass as the real company's site, login, checkout, or support page. Use the user's own brand or an invented one.
- The repo's files already use altered brand names (for example "Stripi"). Keep any output generic in the same way.
- Credit the source when it's relevant: "design tokens adapted from awesome-design-md (MIT)".