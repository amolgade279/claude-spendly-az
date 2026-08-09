# Claude Prompts Log

A record of the prompts used with Claude while building this project, in chronological order.

---

## 1. Add Terms and conditions and Privacy policy links to footer

Add two placeholder footer links — "Terms and conditions" and "Privacy policy" — to the Spendly footer.

1. `app.py` — add two new routes, `/terms` and `/privacy`, each returning a plain placeholder string (e.g. "Terms and Conditions — coming soon"), matching the existing stub pattern already used for `/logout` and `/profile`. Do not create templates for these yet.

2. `templates/base.html` — inside the existing `<footer>`, add a `.footer-links` div containing the two links. Use `url_for('terms')` and `url_for('privacy')` for the hrefs (not hardcoded paths), so the links work on every page that extends this layout.

3. `static/css/style.css` — add minimal `.footer-links` and `.footer-links a` styles consistent with the existing `.footer-copy` rule (0.8rem font-size, `--ink-faint` color, hover to `--paper`).

Keep the diff minimal: no new dependencies, no real Terms/Privacy page content yet — just the links and their placeholder targets.

**Commit:**
```
! git commit -m "Add Terms and conditions and Privacy policy links to footer" -m "- New placeholder routes: /terms and /privacy
```

---

## 2. Add generic terms and conditions and Privacy policy content

Replace the placeholder `/terms` and `/privacy` routes with real generic Terms and conditions / Privacy policy pages — standard boilerplate content like most websites use, not legal advice.

1. Create `templates/terms.html` (extends `base.html`) covering these standard sections: acceptance of terms, description of service, account responsibilities, acceptable use, user data ownership (link to Privacy policy), intellectual property, disclaimer of warranties, limitation of liability, termination, changes to terms, governing law, contact.

2. Create `templates/privacy.html` (extends `base.html`) covering: what data is collected (name, email, hashed password, expense records), how it's used, cookies, third-party sharing (state no selling of data), data security, data retention, user rights (access/correct/delete), children's privacy, changes to policy, contact.

3. Update `app.py` — change the `/terms` and `/privacy` routes to `render_template("terms.html")` / `render_template("privacy.html")` instead of returning placeholder strings.

4. Add a "legal pages" section to `static/css/style.css` for readable prose (heading styles, paragraph spacing, ~720px reading width), reusing the existing `--font-display` / `--ink-soft` / `--accent` variables — no new colors.

Leave `[Effective Date]`, `[Contact Email]`, and `[Governing Jurisdiction]` as clearly bracketed placeholders in both pages — this is boilerplate only, not reviewed by a lawyer, and needs real values before it ever goes live.

**Commit:**
```
! git commit -m "Add generic terms and conditions and Privacy policy content."
```

---

## 3. Redesigning landing page hero section

Update ONLY the hero section (the part visible above the fold) on the landing page to match the attached design. Do not touch anything else — not the features section, not the CTA section, not the footer, not the nav, not login/register/terms/privacy templates, and not the existing `.btn-primary` or `.btn-ghost` button styles (reuse them as-is).

In `@templates/landing.html`:
- Replace the entire `<section class="hero">...</section>` block (the first section in `{% block content %}`, right before `<section class="features">`) with a new centered, single-column hero:
  - A small pill badge: "Free to use · No credit card needed" with a leading dot
  - Headline: "Track every rupee." on one line, "Know where it goes." on the next, in the accent color
  - Subtitle: "Spendly helps you log expenses, spot patterns, and stay on budget — without the spreadsheet headache."
  - Same two buttons as now, reusing `.btn-primary` ("Create free account", links to register) and `.btn-ghost` ("See how it works", href="#" placeholder for now)
  - Below that, a full-width dashboard mockup: three stat cards in a row (This month / Budget left / Transactions with ₹18,240 +12% vs last, ₹6,760 43% remaining, 34 this month), then a card with three horizontal progress bars for Food / Travel / Bills
- Do not touch anything from `<section class="features">` onward in this file.

In `@static/css/style.css`:
- Replace only the block between the `/* Hero */` comment and the `/* Buttons */` comment (currently `.hero`, `.hero-badge`, `.hero-title`, `.hero-subtitle`, `.hero-actions`, `.hero-visual`, and all `.mock-*` rules) with new rules for the new hero classes above (`.hero-single`, `.hero-pill`, `.hero-dashboard`, `.stat-card`, `.bar-fill-*`, etc.)
- Reuse existing CSS variables only (`--accent`, `--accent-2`, `--danger`, `--ink*`, `--paper*`, `--border*`, `--radius-*`) — no new colors. For the two extra bar colors beyond the accent variables, reuse the same hex values already used by the `.mock-bar-3` / `.mock-bar-4` rules you're removing (`#5b7fa6` and `#8b5e83`).
- Leave everything from the `/* Buttons */` comment onward completely untouched.
- The image is `@"Screenshot 2026-03-25 at 12.36.20 AM.png"`

**Commit:**
```
! git commit -m "Redesigning landing page hero section."
```

---

## 4. Add video modal to hero section

Add a popup video modal that opens when "See how it works" is clicked. There's no real video yet — use a clearly marked placeholder that's easy to find and swap later. Don't touch anything else on the page or site.

In `@templates/landing.html`:
- Add `id="how-it-works-btn"` to the existing `<a href="#" class="btn-ghost">See how it works</a>` link inside `.hero-actions` — don't change its classes, text, or styling.
- Immediately after the hero `</section>` closes and before `<section class="features">` begins, insert a hidden modal overlay containing a close button and a 16:9 iframe. Use a `data-src` attribute (not `src` directly) pointing at `https://www.youtube.com/embed/REPLACE_WITH_VIDEO_ID?autoplay=1` — leave `src=""` empty until JS sets it on open. `REPLACE_WITH_VIDEO_ID` is the one thing that must change once the real video exists.

In `@static/js/main.js` (currently just a placeholder comment):
- Add `DOMContentLoaded` logic that: looks up the trigger, modal, close button, and iframe by id; returns early if any are missing (this file loads on every page, so it must not error on login/register/terms/privacy where the modal doesn't exist); on open, copies `data-src` into `src` and un-hides the modal; on close (close button, click outside the modal, or Escape key), re-hides the modal and resets `src` back to `""` so the video actually stops playing, not just visually disappears.

In `@static/css/style.css`:
- Add a new "Video modal" section right before the `/* Footer */` comment — a fixed, full-viewport dark overlay centering a max-width ~860px white card with a 16:9 video frame and a round close button in the top-right corner. Reuse existing variables (`--paper-card`, `--radius-md`, `--ink`, `--paper`) — no new colors. Don't touch any other section.

**Commit:**
```
! git commit -m "Add video modal to hero section."
```
