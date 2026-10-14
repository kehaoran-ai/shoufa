# Building a tool

A tool is a page people use, not read: a timer, a budget, a habit tracker, a picker, a calculator. It is one HTML file with plain JavaScript, built with `--layout app`. Every look (mono, blueprint, soft) styles it, so never hard-code colours, fonts or radii.

A complete working example is `<skill>/samples/app-en.html` (a pomodoro timer). Copy its structure. Do not copy its demo data: the example fills in a week of history only so the start form has something to show (`DEMO = true`). A real tool starts empty.

## Skeleton

```html
<div class="sf-app">                       <!-- add sf-wide for tables or two columns -->
  <header class="sf-bar">
    <a class="nt-brand" href="#">Tool name</a>
    <span class="nt-grow"></span>
    <div class="sf-seg" role="tablist" aria-label="Views">   <!-- only if there are 2 or 3 views -->
      <button role="tab" aria-selected="true" data-view="main">Today</button>
      <button role="tab" aria-selected="false" data-view="stats">Stats</button>
    </div>
  </header>
  <main class="sf-main">
    <section class="sf-view" id="v-main"> ... </section>
    <section class="sf-view" id="v-stats" hidden> ... </section>
  </main>
  <div class="sf-toast" id="toast" role="status"></div>
</div>
<script>
(function () {
  var KEY = "shoufa.tool-name.v1";
  function load() { try { return JSON.parse(localStorage.getItem(KEY)) || { items: [] }; } catch (e) { return { items: [] }; } }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(data)); } catch (e) {} }
  var data = load();
  // render(), event handlers ...
})();
</script>
```

## Parts

Panels are `.nt-card`; buttons are `.nt-btn`, `.nt-btn--primary` (one per view), `.nt-btn--quiet`, sizes `--sm` and `--lg`; groups of buttons sit in `.nt-actions`. On top of those:

| Class | What it is |
|---|---|
| `.sf-title` | An `h1` and a `p` at the top of a view, when the view needs a heading |
| `.sf-center` | A card whose content is centred, for a timer or a single result |
| `.sf-head` | A row with a `<b>` title on the left and a `.sf-hint` on the right, at the top of a card |
| `.sf-field` | A `<label>` above an input; `.sf-hint` under it for help text |
| `.sf-input`, `.sf-select`, `.sf-textarea` | Inputs |
| `.sf-row` | Inputs and a button on one line, e.g. amount + note + Add |
| `.sf-seg` | Segmented switch; buttons with `aria-pressed` or `aria-selected` |
| `.sf-chips` > `.sf-chip` | Small toggles with `aria-pressed`, e.g. categories |
| `.sf-list` > `.sf-item` | A record: `.sf-tick` (optional), `.sf-item-main` with `<b>` and `<small>`, `.sf-item-end` for an amount or time, `.sf-x` to delete. Add `.is-done` to strike it through |
| `.sf-tick` | Round checkbox: a `<button>` with `aria-pressed` |
| `.sf-big` | The one big number: a countdown, a total, a result. `<small>` inside for the unit. Add `.sf-big--text` when the result is a word or a name |
| `.sf-ring` | Circular progress; set `--p` from 0 to 1 on it, put `.sf-big` inside |
| `.sf-meter` | Progress bar; set `--p` from 0 to 1 |
| `.sf-stats` > `.sf-stat` | Two to four small numbers: `<b>` value, `<span>` label |
| `.sf-bars` | Seven or so bars: each child `<div>` has `<i style="--v:0.4">` and a `<span>` label; `.is-accent` on the current one |
| `.sf-empty` | What shows before there is any data: a small `.nt-line` icon, a `<b>`, one sentence on what to do |
| `.sf-toast` | Short message; add `.is-on` for two seconds after an action |
| `<dialog class="sf-dialog nt-card">` | Confirmations and small forms; buttons in `.sf-actions` |

Line icons: `<svg class="nt-line" viewBox="0 0 40 40">` with plain shapes; wrap the one important shape in `<g class="is-accent">`.

## Rules

- Build exactly what they asked for, plus what it needs to work: adding and deleting records, an empty state, a confirmation before anything destructive. Add editing only when a record has several fields worth fixing. No accounts, no sharing, no sync, no features they did not mention.
- Plain JavaScript in one `<script>` at the end of the body. No frameworks, no CDNs, no network requests, so it works when they double-click the file and when it is offline.
- Remember data in `localStorage` when `save` is `local`, or when it is empty and the tool is useless without memory (a budget, a habit tracker). Use one key, `shoufa.<name>.v1`, and wrap every read and write in `try/catch`. With `save` = `none`, keep everything in memory.
- Start empty. Never ship sample records, sample history or made-up numbers.
- Every action shows its result at once: the list updates, the number changes, a toast confirms. Never use `alert()`, `confirm()` or `prompt()`; use `.sf-toast` and `.sf-dialog`.
- Clearing or deleting more than one thing asks first, in an `.sf-dialog`.
- Works on a phone: one column, nothing narrower than 40px to tap, inputs use the right `type` and `inputmode` (`decimal` for money). Enter submits a form.
- Numbers and dates in the page language: `toLocaleDateString("zh-CN")`, `¥` for Chinese money unless they wrote another currency.
- Text follows the same writing rules as pages: plain, specific, no emoji, no slogans. Labels say what happens: 「记一笔」, not 「提交」.
- Escape anything the person typed before putting it in the page: set `textContent`, never build HTML from their text.
- Keep inline `style` to layout only (`max-width`, `justify-self`, `padding`). When a part is missing (a calendar grid, a chart), add a small `<style>` at the top of body.html that uses only `var(--nt-*)` tokens, never raw colours, gradients or fonts.
- The checker rejects a row of exactly three `.nt-card`s. For three numbers use `.sf-stats`; otherwise use two or four cards.
- Disabled buttons (`disabled`) are styled already; keep them visible instead of hiding them.
