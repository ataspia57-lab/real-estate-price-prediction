---
name: "web-design-guidelines"
description: "Review UI code for Vercel's Web Interface Guidelines (accessibility, forms, focus, motion, typography, performance). Use for \"review my UI\", \"check accessibility\", \"audit design/UX\"."
---

# Web Interface Guidelines review

From vercel-labs/agent-skills. Reviews UI files against Vercel's Web Interface Guidelines.

## How it works
1. Get the latest guidelines. Raw GitHub URLs are usually blocked in this workspace, but git clone works:
   ```bash
   [ -d /tmp/wig/.git ] || git clone --depth 1 -q https://github.com/vercel-labs/web-interface-guidelines /tmp/wig
   ```
   Then read `/tmp/wig/command.md` in full with the Read tool. It holds every rule and the output format. If the clone fails, use WebFetch on `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md` and ask it to return the rules verbatim. If both fail, say so. Don't review from memory.
2. Read the files the user specified. If they didn't specify any, ask which files or pattern to review.
3. Check the files against every rule in the guidelines.
4. Report findings in the terse `file:line` format the guidelines specify, grouped the way they say. Keep it high-signal.

If the user then asks for fixes, apply them to copies of their files, or in place when they ask for that, and send the changed files back.