---
name: shoufa
description: Help a complete beginner turn an idea into their first live product - a personal homepage, a product landing page, or a small working web tool such as a timer, budget or habit tracker - without touching code. Opens a friendly multiple-choice form in the browser, builds a well-designed page with the bundled Neatly engine and three looks built on shadcn/ui, shows a live preview where they can switch style and colour, then walks them through putting it online for free with Cloudflare and hands them a link to share. Use when someone says they want to make a website, a homepage, a personal site, a portfolio, a landing page, a page for their product, shop, event or idea, "my first product", "put something online", or 首发, 做个网站, 做个主页, 个人主页, 落地页, 上线一个页面, 做个小工具, 做个能用的网页.
---

# Shoufa (首发)

The person you are helping has probably never built a website. Your job is to get them from an idea to a live link they can share, while they only click choices in their browser. Never ask them to type commands, edit files or paste anything. Speak their language (Chinese if they write Chinese), skip jargon, and keep each message to two or three short sentences.

`<skill>` below means this skill's folder. `DIR` is the project folder: use the folder the person names, otherwise create `my-site` in the current directory. Run every command yourself.

## 1. Open the start form

```bash
python3 <skill>/scripts/ask.py open start --project DIR
python3 <skill>/scripts/ask.py wait start --project DIR
```

Tell them: "I've opened a short form in your browser. Pick a look first, then what you're making and a colour, and click the button." The form shows a full sample page in each look as they click, so they choose the look by seeing it. `wait` prints the answers as JSON. If it prints `STILL_WAITING`, run the same `wait` again; do not reopen the form.

The answers contain:
- `type`: `personal`, `landing`, `app` (a working tool; `other_description` says what it should do) or `other` (`other_description` says what they want)
- `style`: one of the three looks, all on a shadcn/ui base: `mono` (black and white, dot grid), `blueprint` (grid paper, ink lines, key-like button), `soft` (warm paper, round shapes, the accent on the main button)
- `accent`: a hex colour; `language`: `zh` or `en`
- `detail_level`: `basic` (three choices only) or `detailed`
- `fields`: whatever they filled in (names, texts, lists, links). Uploaded images arrive as paths like `assets/avatar-123.jpg`, already saved in `DIR/site/assets/`.
- `pricing` (landing): `free`, `once`, `subscription`, `none` or empty. With `none`, drop the pricing block; otherwise shape the plans to match, using `fields.price_detail` for the actual prices.
- `save` (app): `local` (remember data on this device), `none`, or empty.
- `parts` (other): the sections they want, from `intro`, `features`, `gallery`, `steps`, `pricing`, `faq`, `contact`. Keep those blocks of the layout and drop the rest.

## 2. Write the page

Pick the layout: `personal` → `personal`; `landing` → `landing`; `app` → `app`, and follow section 2b instead of the rest of this section. For `other`, first ask yourself whether it is something people use rather than read (a timer, a calculator, a tracker, a list, a picker, a converter): then it is an `app` too. Otherwise choose the closest: a person or creator → `personal`; a shop, service, event, app or project → `landing`; an article or story → `report`; a guide → `docs`.

Read the layout's body: `<skill>/neatly/layouts/<layout>.html`. Line 2 says which line `<body>` starts on; read from there to the end and never read the CSS above it. Read `<skill>/neatly/reference/components.md` for the available classes.

Write the page content to `DIR/body.html` (only what goes inside `<body>`), in the page language. Translate every word the layout ships with too: nav labels, section names like "Questions", footer links, `aria-label`s, and use the local currency sign (¥ for Chinese pages unless they wrote $).
- Use everything they gave you, in their words where possible. Put uploaded images where they belong (`<img class="nt-portrait" src="assets/...">` for a portrait, a screenshot in the hero figure, a logo in the brand).
- Where they left things blank, write short sample text that clearly fits their idea, so the first version already looks finished. Never invent facts: no awards, client names, user counts, numbers, quotes, or product capabilities they did not mention.
- Use the features they gave, as many as they gave (three is fine; the feature grid is two columns, not three cards). Only if they gave none, write two or three that follow directly from their one-sentence pitch.
- The numbers strip only holds facts they gave you (a price, a time, a count). Use two to four of them; with fewer than two, delete the strip.
- Keep the FAQ only for questions they wrote, or for questions answered by facts they gave (price, how to contact). Otherwise delete it.
- If they gave no link for the main button, point it at their email (`mailto:`) when they gave one, else at `#`, and mention in chat that they can send you the real link.
- Keep the writing plain: headings are sentences that say something, no slogans, no emoji, sentence case.
- Links they gave become real links; missing ones point to `#`.

Build it:

```bash
python3 <skill>/scripts/ask.py build --project DIR --layout personal --system soft --accent d9773b --lang zh-CN --title "Page title" --name suggested-address
```

`--lang` is `zh-CN` for Chinese pages and `en` for English. `--name` is a short lowercase web-address suggestion from their name or product (letters, numbers, dashes). The build runs Neatly's checker; fix every error it reports in `body.html` and build again.

## 2b. Write a tool

Read `<skill>/reference/tool.md`: the skeleton, the `sf-` parts and the rules. Then read `<skill>/samples/app-en.html`, a complete working tool, for the structure (not its demo data).

Write the whole tool, markup and one `<script>`, to `DIR/body.html` in the page language, and build it with `--layout app`:

```bash
python3 <skill>/scripts/ask.py build --project DIR --layout app --system mono --accent 2e4bff --lang zh-CN --title "Tool name" --name suggested-address
```

If Node.js is installed, copy the script into `DIR/.shoufa/check.js` and run `node --check` on it before you hand it over. Then read your own script once as the person would use it: add a record, reload the page, delete it, use every button you made. Fix what breaks.

## 3. Preview

```bash
python3 <skill>/scripts/ask.py open preview --project DIR
python3 <skill>/scripts/ask.py wait preview --project DIR
```

In the preview they can switch the look and colour instantly, see the phone view, and press one of three buttons. A tool works inside the preview, so tell them they can try it there. The answer has `action`, plus the `style` and `accent` they ended on:
- `revise`: `feedback` says what to change. Edit `DIR/body.html`, build again with their chosen `--system` and `--accent`, then open and wait on the preview again.
- `keep`: build once more with their chosen style and colour, tell them the page is saved at `DIR/site/index.html` (they can double-click it), and stop.
- `ship`: build once more with their chosen style and colour, then go to step 4.

## 4. Put it online (Cloudflare, free)

```bash
python3 <skill>/scripts/ask.py open deploy --project DIR
```

While they read the page, check that Node.js is installed: `node -v` (needs 18 or newer). If it is missing, post a status so the page shows it, and tell them in chat to install the LTS version from https://nodejs.org (a normal installer, click Next), then tell you when it's done:

```bash
python3 <skill>/scripts/ask.py status "Install Node.js from nodejs.org, then tell the AI" --project DIR --error
```

Then wait for them to confirm sign-up and pick a name:

```bash
python3 <skill>/scripts/ask.py wait deploy --project DIR      # prints {"project_name": "...", "ready": true}
```

Write status lines in their language (the examples below are English). Log in, with a status line before each step so the page moves along:

```bash
python3 <skill>/scripts/ask.py status "Opening the Cloudflare permission page" --project DIR --phase login
npx --yes wrangler@4 whoami          # already logged in? then skip login
npx --yes wrangler@4 login           # opens the browser; they click Allow
python3 <skill>/scripts/ask.py status "Uploading your page" --project DIR --phase upload
cd DIR && npx --yes wrangler@4 deploy --assets ./site --name PROJECT_NAME --compatibility-date 2026-10-01
```

The deploy prints a `https://PROJECT_NAME.<account>.workers.dev` address. Finish:

```bash
python3 <skill>/scripts/ask.py status "Done" --project DIR --url https://... --done
```

If the deploy says the account has no workers.dev subdomain yet, post an `--error` status and ask them to open https://dash.cloudflare.com, click "Workers & Pages" once (Cloudflare sets up the address automatically), then run the deploy again. If the name is taken, ask for another name in chat and deploy again.

Never ask for their Cloudflare password, API tokens or payment details. `wrangler login` uses Cloudflare's own permission page.

## 5. Wrap up

```bash
python3 <skill>/scripts/ask.py stop --project DIR
```

Give them the link, and one sentence on what comes next: to change anything later, they just tell you what to change; you edit `DIR/body.html`, build, and run the same deploy command. A custom domain can be added later in the Cloudflare dashboard.
