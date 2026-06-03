---
name: talent-map-registration-design
description: Use when implementing, reviewing, or restoring the Talent Map local registration page, including the left/right login split, email verification cooldown, four-character image captcha, and first-run account flow in app.py plus static HTML/CSS/JS.
---

# Talent Map Registration Design

## Overview

Use this skill when changing the Talent Map local login/register experience. It preserves the product-specific registration flow, the quiet split-screen page design, and the traditional four-character image captcha pattern.

## Workflow

1. Inspect the current auth files before editing: `app.py`, `static/index.html`, `static/app.js`, and `static/styles.css`.
2. Keep the registration flow from `references/registration-flow.md` intact unless the user explicitly changes the product rules.
3. Apply the page layout and visual constraints from `references/page-design.md`.
4. Implement captcha changes using `references/captcha-design.md`.
5. Verify with focused checks: Python syntax, JavaScript syntax, `/api/register-challenge`, and the send-code cooldown behavior when practical.

## Design Guardrails

- Keep the first screen as the usable auth experience, not a landing page.
- Preserve the left form module and right product-intelligence art module on desktop.
- Keep a faint gray vertical divider between the modules; remove it on single-column mobile.
- Keep registration compact enough to show all required fields without decorative cards inside the form.
- Use a traditional image captcha with four distorted characters on a noisy background, refreshed by a compact icon button.

## References

- `references/registration-flow.md`
- `references/page-design.md`
- `references/captcha-design.md`
