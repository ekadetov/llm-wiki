# llm-wiki Walkthrough

A guided tour for new users. Read this top to bottom the first time, then use it as a reference.

---

## Part 1: Introduction

### What is an LLM Wiki?

Andrej Karpathy described a pattern where an LLM reads raw source material, writes cross-linked wiki articles from it, files Q&A answers back into the knowledge base, and periodically lints for gaps and contradictions. The result is a knowledge base that compounds over time: each new source enriches existing pages, and each query can surface connections across everything ingested so far.

This plugin implements that pattern inside Obsidian.

### Why Obsidian?

Obsidian stores everything as plain markdown files on disk. That means:

- **Graph view** renders your `[[wikilinks]]` as a visual network for free
- **Dataview** queries frontmatter across all pages, so you can build dynamic tables of concepts, people, or sources
- **Web Clipper** saves articles directly to your vault's `raw/` folder, ready to ingest
- **Marp** can export any page as a slide deck by adding `marp: true` to frontmatter

No lock-in. The files are yours.

### What this plugin does

Six operations, invoked from a Claude Code session:

| Operation | What it does |
|-----------|-------------|
| `init <name>` | Scaffolds a new wiki with directory structure, schema, and git tracking |
| `ingest <path\|url>` | Saves a source to raw/articles/. Does not create wiki pages. |
| `compile [<path>]` | Reads raw sources, creates/updates wiki pages with entity extraction |
| `query <question>` | Searches the wiki, synthesizes an answer with wikilink citations |
| `lint` | Audits for dead links, orphans, missing sections, index drift |
| `remove <name>` | Deletes a wiki and all its contents |

---

## Part 2: Key Concepts

### Wiki structure

Every wiki lives at `~/ObsidianVault/03-Resources/<name>/`:

```
<name>/
├── raw/                  ← immutable source drops (never edited by LLM)
│   ├── articles/         ← text source documents
│   └── attachments/      ← images and binary files
├── wiki/                 ← LLM-owned pages
│   ├── index.md          ← catalog, read first before any other page
│   ├── queries/          ← filed query answers
│   └── <concept>.md      ← entity and concept pages
├── outputs/
│   └── reports/          ← dated lint reports
├── CLAUDE.md             ← wiki schema and conventions
├── log.md                ← append-only operation log
├── .gitignore
└── qmd.yml               ← search collection config
```

The `raw/` folder is sacred: sources go in, nothing comes out. The LLM writes only to `wiki/`.

### Active wiki detection

When you run any operation, the plugin walks up from your current working directory looking for a folder that contains both `CLAUDE.md` and a `wiki/` subfolder. The first match becomes the active wiki. If nothing is found, it lists available wikis and asks which one to use.

This means you can `cd` into a wiki root before running commands, or run from anywhere and let the plugin ask.

### CLAUDE.md as schema

`CLAUDE.md` is the contract between you and the LLM. It defines:

- Directory layout and what each folder is for
- Entity templates (concept, person, source-summary) with their frontmatter schemas
- Naming conventions (lowercase-kebab-case filenames, `[[wikilinks]]` for internal links)
- Log format, index format, cross-reference rules

The schema co-evolves with the wiki. If you want to add a new entity type or change a convention, edit `CLAUDE.md` and the LLM will follow it on the next operation.

### Entity types

Three page types, each with a frontmatter schema:

**concept.md** — an idea, technology, or event:
```yaml
---
date: YYYY-MM-DD
tags: [domain]
type: concept
status: active
---
```

**person.md** — a named individual:
```yaml
---
date: YYYY-MM-DD
tags: [domain, person]
type: person
status: active
---
```

**source-summary.md** — a processed source document:
```yaml
---
date: YYYY-MM-DD
tags: [domain]
type: source-summary
source-url: https://...
---
```

Standardized frontmatter is what makes Dataview queries work across the whole wiki.

### Wikilinks and compounding

Every page links to related pages using `[[wikilinks]]`. After each ingest, the plugin runs a backlink audit: it greps existing pages for mentions of newly created page titles and adds wikilinks where they're missing. This keeps the graph dense.

The compounding effect comes from this density. When you query the wiki, the LLM follows wikilinks one level deep to gather context. A well-linked wiki surfaces connections that no single source contains.

### qmd (optional)

qmd provides hybrid BM25 + vector search over the wiki. For small wikis (under ~50 pages), reading `index.md` is fast enough. For larger wikis, qmd becomes essential for finding relevant pages without reading everything.

The plugin always uses the full path to qmd (`~/.claude/plugins/data/llm-wiki/node_modules/.bin/qmd`) and falls back gracefully to index-based search if qmd isn't available.

### Auto-commit

Every operation ends with a git commit to the Obsidian vault. This gives you a full history of how the wiki evolved, lets you diff any operation, and makes it safe to experiment.

---

## Part 3: Installation

### Prerequisites

- **Node.js 18+** — for automatic dependency installation
- **Git** — for auto-committing wiki changes, with `user.name` and `user.email` configured
- **Obsidian vault** at `~/ObsidianVault/` with a `03-Resources/` directory

Verify before installing:

```bash
node --version          # should be 18+
git --version           # should be 2.x
git config user.name    # should return your name
ls ~/ObsidianVault/03-Resources/
```

### Install

From the Claude Code marketplace:

```
/plugin marketplace add ekadetov/llm-wiki
/plugin install llm-wiki@llm-wiki
```

### Verify installation

In a Claude Code session, `/llm-wiki:wiki` should appear in the skill list. Try:

```
/llm-wiki:wiki
```

You should see the argument hint: `init <name> | ingest <path|url> | compile [<path>] | query <question> | lint | remove <name>`.

### Dependencies

`qmd` and `marp-cli` install automatically when you start a new Claude Code session after installing the plugin. The SessionStart hook runs `npm install` in the plugin data directory if the sentinel file `~/.claude/plugins/data/llm-wiki/.deps-ok` is missing.

To verify they installed:

```bash
ls ~/.claude/plugins/data/llm-wiki/node_modules/.bin/qmd
ls ~/.claude/plugins/data/llm-wiki/node_modules/.bin/marp
```

---

## Part 4: Your First Wiki (Guided Walkthrough)

Work through these steps in order. Each step builds on the previous one.

---

### Step 1: Init a wiki

```
/llm-wiki:wiki init test-wiki
```

**What happens:**

1. Creates `~/ObsidianVault/03-Resources/test-wiki/` with `raw/articles/`, `raw/attachments/`, `wiki/queries/`, and `outputs/reports/`
2. Writes `CLAUDE.md` with the full schema
3. Writes `wiki/index.md` with an empty catalog template
4. Writes `log.md` with an empty log template
5. Writes `.gitignore` and `qmd.yml`
6. Commits everything: `init: test-wiki wiki`
7. If qmd is available, creates a search collection and embeds the (empty) wiki
8. Prints Web Clipper setup instructions

**Verify from terminal:**

```bash
ls -la ~/ObsidianVault/03-Resources/test-wiki/
cat ~/ObsidianVault/03-Resources/test-wiki/CLAUDE.md
cat ~/ObsidianVault/03-Resources/test-wiki/wiki/index.md
git -C ~/ObsidianVault log --oneline -1
```

**Expected:**

- Directory exists with `raw/`, `wiki/`, `CLAUDE.md`, `.gitignore`, `qmd.yml`
- `CLAUDE.md` contains the full schema with entity templates and conventions
- `wiki/index.md` has the empty catalog template with a comment block
- Git log shows `init: test-wiki wiki`

---

### Step 2: Ingest a local file

First, create a test source:

```bash
cat > ~/ObsidianVault/03-Resources/test-wiki/raw/articles/2026-04-05-test-article.md << 'EOF'
# The History of Markdown

John Gruber created Markdown in 2004 with contributions from Aaron Swartz.
It was designed as a plain-text formatting syntax that converts to HTML.
Today Markdown is used on GitHub, Stack Overflow, Reddit, and Obsidian.
EOF
```

Then ingest it. Change to the wiki root first so active wiki detection finds it:

```bash
cd ~/ObsidianVault/03-Resources/test-wiki
```

```
/llm-wiki:wiki ingest raw/articles/2026-04-05-test-article.md
```

**What happens:**

1. Detects active wiki from cwd, reads `CLAUDE.md`
2. Reads the source file, classifies it as `article`
3. Saves to `raw/articles/` with frontmatter
4. Appends to `log.md`, commits
5. Prints: "Source saved. Run wiki compile to integrate."

**Verify:**

```bash
ls raw/articles/
cat log.md
git -C ~/ObsidianVault log --oneline -3
```

**Expected:**

- `raw/articles/` contains the saved source file
- `log.md` has an ingest entry with date
- Git log shows the ingest commit

---

### Step 2b: Compile into wiki pages

```
/llm-wiki:wiki compile
```

**What happens:**

1. Identifies uncompiled sources in `raw/articles/`
2. Creates `wiki/history-of-markdown.md` (source-summary page)
3. Creates `wiki/john-gruber.md` (person page)
4. Creates `wiki/aaron-swartz.md` (person page)
5. May create concept pages for Markdown, HTML, GitHub, etc.
6. Runs backlink audit
7. Updates `wiki/index.md`
8. Appends to `log.md`, commits

**Verify:**

```bash
ls wiki/
cat wiki/index.md
cat log.md
git -C ~/ObsidianVault log --oneline -3
```

**Expected:**

- `wiki/` contains multiple new `.md` files
- `index.md` has entries under a domain heading
- `log.md` has a compile entry with date and page count
- Git log shows the compile commit

---

### Step 3: Ingest from a URL

```
/llm-wiki:wiki ingest https://en.wikipedia.org/wiki/Markdown
```

**What happens:**

The plugin uses WebFetch to retrieve the page content, saves it to `raw/articles/` as `YYYY-MM-DD-markdown.md` with frontmatter, appends to `log.md`, and commits. It does not create wiki pages — use `compile` for that.

This is the primary workflow for building up a wiki from web research: clip or fetch articles, ingest them, then compile to create wiki pages.

---

### Step 4: Query the wiki

```
/llm-wiki:wiki query "Who created Markdown and when?"
```

**What happens:**

1. Detects active wiki, reads `CLAUDE.md`
2. If qmd is available, runs a hybrid search query. Otherwise reads `index.md` and identifies relevant pages
3. Opens the relevant pages, follows one level of wikilinks for additional context
4. Synthesizes an answer in prose with `[[wikilinks]]` as citations
5. Answer synthesized AND automatically filed to `wiki/queries/`
6. Asks: "Promote this to a concept page? (y/n)"
7. Appends to `log.md`, commits

**Example answer format:**

> Markdown was created by [[john-gruber]] in 2004, with significant contributions from [[aaron-swartz]]. It was designed as a plain-text formatting syntax that converts cleanly to HTML...

**Verify:**

```bash
cat log.md    # should have a query entry
git -C ~/ObsidianVault log --oneline -3
```

**Filing answers back:**

Answers are automatically filed to `wiki/queries/<slug>.md`. Then the plugin offers to promote the answer to `wiki/<slug>.md` as a full concept page. Promotion is how the wiki grows from queries, not just ingests.

---

### Step 5: Lint the wiki

```
/llm-wiki:wiki lint
```

**What happens:**

1. Reads all files in `wiki/`
2. Builds a link graph from all `[[wikilinks]]`
3. Runs the lint script if available, otherwise checks manually
4. Reports and fixes:
   - **Dead links**: creates stub pages for `[[wikilinks]]` pointing to nonexistent files
   - **Orphan pages**: lists pages with no inbound links, suggests where to add links
   - **Missing sections**: adds empty `## Counter-Arguments and Gaps` sections
   - **Contradictions**: lists pages with `[!WARNING]` markers
   - **Index drift**: adds missing entries, removes dead ones
5. Saves lint report to `outputs/reports/YYYY-MM-DD-lint.md`
6. Appends to `log.md`, commits

**Verify:**

```bash
cat log.md    # should have a lint entry with issue count
ls outputs/reports/
git -C ~/ObsidianVault log --oneline -3
```

After a fresh ingest of one small article, lint will likely find a few orphan pages or missing sections. That's normal and expected.

---

### Step 6: Open in Obsidian

Open Obsidian and navigate to `03-Resources/test-wiki/`.

**Graph view:** Open the graph view (Ctrl/Cmd+G). You should see interconnected nodes for each wiki page. Isolated nodes are orphans that lint would flag.

**Dataview query:** In any note, add a code block to query the wiki:

````
```dataview
TABLE date, type FROM "03-Resources/test-wiki/wiki"
SORT date DESC
```
````

This lists all wiki pages with their date and type, sorted newest first. Change `type` to filter by `concept`, `person`, or `source-summary`.

---

## Part 5: Obsidian Integration Tips

### Web Clipper

Install the [Obsidian Web Clipper](https://obsidian.md/clipper) browser extension. In its settings:

- **Destination folder:** `03-Resources/<wiki-name>/raw/articles`
- **Filename template:** `{{date:YYYY-MM-DD}}-{{title}}`

After clipping an article, run:

```
/llm-wiki:wiki ingest ~/ObsidianVault/03-Resources/<wiki-name>/raw/<clipped-file>.md
```

### Graph view as a visual lint

The graph view shows you what lint would find. Isolated nodes have no inbound links. Clusters of tightly connected nodes are your strongest knowledge areas. Thin bridges between clusters are candidates for new concept pages that would connect them.

### Dataview for wiki management

Useful queries:

```dataview
TABLE date, status FROM "03-Resources/my-wiki/wiki"
WHERE type = "concept" AND status = "stale"
SORT date ASC
```

```dataview
LIST FROM "03-Resources/my-wiki/wiki"
WHERE type = "source-summary"
SORT date DESC
LIMIT 10
```

### Marp slide export

Any wiki page can become a slide deck. Add `marp: true` to the frontmatter, then run:

```bash
~/.claude/plugins/data/llm-wiki/node_modules/.bin/marp wiki/my-page.md -o output.html
```

The source-summary template in `CLAUDE.md` includes this instruction as a reminder.

---

## Part 6: Advanced Usage

### Multiple wikis

Each topic gets its own folder under `03-Resources/`. Run `init` once per topic:

```
/llm-wiki:wiki init machine-learning
/llm-wiki:wiki init company-research
/llm-wiki:wiki init book-notes
```

Active wiki detection picks the right one based on your cwd. Wikis don't share pages, but you can cross-reference between them using full Obsidian paths if needed.

### Large wikis (200+ pages)

At this scale, reading `index.md` for every query becomes slow. qmd's hybrid search handles it well. You may also want to partition `index.md` by domain, keeping each section under 50 entries.

Signs you need qmd: queries start returning vague answers, or the LLM says it can't find relevant pages. Check that qmd is installed and the collection is up to date:

```bash
~/.claude/plugins/data/llm-wiki/node_modules/.bin/qmd collection list
```

### Contradiction handling

When the LLM finds conflicting information across sources, it adds a callout inline:

```markdown
> [!WARNING] Contradiction with [[other-page]]
> Source A says X, but [[other-page]] says Y. Needs resolution.
```

Lint surfaces all `[!WARNING]` markers in its report. Resolve them by reading both sources and updating the pages with the reconciled view.

### Filing query answers back

The query workflow has two promotion steps:

1. **File to `wiki/queries/`** — saves the answer as a query artifact
2. **Promote to `wiki/`** — elevates it to a first-class concept page

Use promotion when a query synthesizes something genuinely new that isn't captured in any existing page. Over time, queries become one of the primary ways the wiki grows beyond what any single source contains.

---

## Part 7: Cleanup

After testing, remove the test wiki:

```
/llm-wiki:wiki remove test-wiki
```

Your real wikis are unaffected. The plugin itself stays installed.

---

## Part 8: Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `/llm-wiki:wiki` not found | Plugin not installed | `/plugin install llm-wiki@llm-wiki` |
| qmd not found | Deps not installed | Check `~/.claude/plugins/data/llm-wiki/node_modules/.bin/qmd`; start a new session to trigger the hook |
| Git commit fails | No git user configured | `git config --global user.name "Name"` and `git config --global user.email "email"` |
| Init fails "directory exists" | Previous test not cleaned up | Run `wiki remove <name>` to delete it cleanly |
| Hook doesn't run on session start | hooks.json malformed | Reinstall the plugin |
| Ingest creates no entity pages | Source too short or unstructured | Add more content to the source file |
| Query returns vague answer | Wiki too small or qmd not indexed | Ingest more sources; run `qmd embed --collection <name>` |

---

For the full skill specification including all templates, see `skills/wiki/SKILL.md` in the plugin source.
