# Inkstone · Markdown Editor

[![CI](https://github.com/techdou/inkstone/actions/workflows/ci.yml/badge.svg)](https://github.com/techdou/inkstone/actions/workflows/ci.yml)

**[在线试用 Live Demo →](https://techdou.github.io/inkstone/)** — 无需安装，打开即写。

A **single-file Markdown editor** for the AI era — open `index.html` and start writing. No install, no account, no build step, fully offline.

Built for people who write AGENTS.md, Skill.md, prompts, technical docs and paper notes: formulas, diagrams, outline navigation and one-key real save.

> Inkstone (砚台) — the stone where ink is ground before writing.

## Features

- **Open-and-go**: one HTML file + local vendor libraries, zero CDN dependency, works from `file://`
- **Live preview**: split view with ratio-draggable panes, synchronized scrolling, edit/preview/fullscreen layouts
- **Math**: KaTeX (`$...$` inline, `$$...$$` display) with formulas protected from the Markdown pipeline — multi-line `array`/`cases` render correctly; failures show a wavy-underline hint with tooltip
- **Diagrams**: Mermaid 11, with per-block error cards when the syntax is wrong
- **Outline panel**: auto-generated heading tree, click to jump
- **Real save**: File System Access API writes back to the original file on Ctrl+S (with graceful fallback to download on older browsers)
- **YAML frontmatter**: rendered as a collapsible meta card
- **Export**: MD / standalone HTML / Word (doc) / PDF (print) / long PNG with social ratios
- **Safe output**: all rendered and exported HTML is sanitized with DOMPurify
- **PWA**: installable, offline via service worker
- **Editor comforts**: syntax-ish toolbar, 8×8 table picker, find & replace, drag-and-drop open, word count, dark/light theme, 10 languages, autosave to localStorage, undo/redo
- **CI**: syntax check, asset budget and promo-free assertion on every push

## Quick start

```bash
git clone https://github.com/techdou/inkstone.git
cd inkstone
# double-click index.html, or:
python -m http.server 8080   # then open http://localhost:8080
```

`vendor/` ships all libraries locally — no network needed at runtime. The optional `web-to-md-proxy.py` converts web pages to Markdown for sites that block plain fetching.

## Keyboard shortcuts

| Keys | Action |
|---|---|
| `Ctrl/⌘ + S` | Save to the original file (File System Access) |
| `Ctrl/⌘ + B / I / U` | Bold / italic / underline |
| `Ctrl/⌘ + K` | Insert link |
| `Ctrl/⌘ + F` | Find & replace |
| `Tab` | Insert 4 spaces |

## Project layout

```
inkstone/
├── index.html          # the whole editor (HTML + CSS + JS in one file, by design)
├── i18n.js             # 10-language dictionary
├── manifest.json       # PWA manifest
├── sw.js               # service worker (offline cache)
├── icon.svg
├── vendor/             # marked 15 · KaTeX · Mermaid 11 · DOMPurify · dom-to-image (all local)
├── tools/check.js      # CI checks: syntax / assets / size budget
└── web-to-md-proxy.py  # optional local proxy for web-to-markdown
```

The single-file design is intentional: no build step, no framework, double-click and it works. Code inside `index.html` is organized in banner-comment sections.

## Development

```bash
node tools/check.js   # same checks CI runs
```

After editing, run the check script; keep `index.html` under the 200 KB budget.

## License & credits

MIT — see [LICENSE](LICENSE).

- Original project: [lengyi-markdown-editor](https://github.com/woyin2024/lengyi-markdown-editor) by 冷逸 / 沃垠AI (MIT)
- Inkstone fork: rebranded, hardened rendering pipeline (math protection, sanitization), Mermaid 11, outline panel, real save, PWA — maintained by [TechDou](https://github.com/techdou)

Libraries: [marked](https://github.com/markedjs/marked) · [KaTeX](https://katex.org/) · [Mermaid](https://mermaid.js.org/) · [DOMPurify](https://github.com/cure53/DOMPurify) · [dom-to-image](https://github.com/tsayen/dom-to-image)
