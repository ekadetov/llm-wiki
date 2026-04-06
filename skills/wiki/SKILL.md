---
name: wiki
description: >-
  LLM Wiki — persistent, compounding knowledge base inside Obsidian.
  Use when the user says "/llm-wiki:wiki", "wiki init", "wiki ingest",
  "wiki query", "wiki lint", or asks about managing a knowledge base wiki.
argument-hint: init <name> | ingest <path|url> | compile [<path>] | query <question> | lint | remove <name>
---

# LLM Wiki

Persistent, compounding knowledge base inside an Obsidian vault.

## Operations

```
/llm-wiki:wiki init my-topic
/llm-wiki:wiki ingest ~/ObsidianVault/03-Resources/my-topic/raw/article.md
/llm-wiki:wiki ingest https://example.com/article
/llm-wiki:wiki query "What is X?"
/llm-wiki:wiki lint
```

---

## Active Wiki Detection

Walk up from `cwd` looking for a directory containing **both** `CLAUDE.md` and a `wiki/` subfolder.

1. Start at `cwd`. Check if `CLAUDE.md` and `wiki/` exist in the current directory.
2. If found → that directory is the **active wiki root**. Read `CLAUDE.md` for schema.
3. If not found → move to parent directory and repeat until filesystem root.
4. If no wiki found anywhere in the path, prompt the user:
   > "Which wiki should I use?"
   List available wikis by running: `ls -d ~/ObsidianVault/03-Resources/*/wiki 2>/dev/null`
   and presenting the parent directory names.

---

## qmd Availability

Reference paths used throughout this skill:

```
QMD="env -u BUN_INSTALL ${CLAUDE_PLUGIN_DATA}/node_modules/.bin/qmd"
MARP="${CLAUDE_PLUGIN_DATA}/node_modules/.bin/marp"
```

**Check:** Test if `"${CLAUDE_PLUGIN_DATA}/node_modules/.bin/qmd"` exists and is executable via Bash: `test -x "${CLAUDE_PLUGIN_DATA}/node_modules/.bin/qmd"`.

**Important:** Always invoke qmd via `env -u BUN_INSTALL` to force Node.js runtime. If `BUN_INSTALL` is set in the environment, qmd runs under Bun, which uses a SQLite build without extension loading support and cannot load sqlite-vec.

- **If present:** use it for `query` and `embed` operations. ALWAYS use the full path — never bare `qmd`.
- **If absent:** fall back to reading `wiki/index.md` manually and grepping wiki files.

---

## `init <name>`

Create a new wiki scaffold under the Obsidian vault.

### Steps

1. **Check if wiki already exists:**
   If `~/ObsidianVault/03-Resources/<name>/` exists, abort with:
   "Wiki '<name>' already exists at ~/ObsidianVault/03-Resources/<name>/. Use `wiki remove <name>` first, or choose a different name."

2. Create directory structure:
   ```bash
   mkdir -p ~/ObsidianVault/03-Resources/<name>/raw/attachments
   mkdir -p ~/ObsidianVault/03-Resources/<name>/wiki/queries
   ```

3. Write `~/ObsidianVault/03-Resources/<name>/CLAUDE.md` using the **CLAUDE.md template** below (fill in `<name>`).

4. Write `~/ObsidianVault/03-Resources/<name>/wiki/index.md` using the **index.md template** below.

5. Write `~/ObsidianVault/03-Resources/<name>/wiki/log.md` using the **log.md template** below.

6. Write `~/ObsidianVault/03-Resources/<name>/.gitignore` using the **.gitignore template** below.

7. Write `~/ObsidianVault/03-Resources/<name>/qmd.yml` using the **qmd.yml template** below.

8. Commit to vault git:
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<name>/" && git -C ~/ObsidianVault commit -m "init: <name> wiki"
   ```

9. If qmd available:
   ```bash
   "${QMD}" collection add ~/ObsidianVault/03-Resources/<name>/wiki --name <name> && "${QMD}" embed --collection <name>
   ```

10. Print Web Clipper setup instruction:
    ```
    Obsidian Web Clipper setup:
    1. Install: https://obsidian.md/clipper
    2. In clipper settings, set Destination folder to:
       03-Resources/<name>/raw
    3. Set filename template to: {{date:YYYY-MM-DD}}-{{title}}
    4. After clipping, run: /llm-wiki:wiki ingest ~/ObsidianVault/03-Resources/<name>/raw/<clipped-file>.md
    ```

---

## `ingest <path|url>`

Ingest a source document into the wiki, creating/updating entity pages and cross-references.

### Steps

1. **Detect active wiki** (see Active Wiki Detection). Read `CLAUDE.md` for schema and templates.

2. **Acquire source:**
   - If input is a **URL**: use the WebFetch tool to retrieve content. Save to `raw/` as `YYYY-MM-DD-<slug>.md`.
   - If input is a **file path**: read the file directly.

3. **Classify** the source as one of: `article` | `paper` | `transcript` | `conversation` | `image-set`.

4. **Write or update source-summary page** in `wiki/` using the `source-summary` template from `CLAUDE.md`. Filename: `<slug>.md`.

5. **Entity extraction:** For each mentioned entity (person, concept, event):
   - Check if a page already exists in `wiki/`.
   - If yes → update it with new information, preserving existing content.
   - If no → create a new page using the appropriate template (`concept.md` or `person.md`) from `CLAUDE.md`.
   - Add `[[wikilinks]]` to related pages in both directions.

6. **Backlink audit** (CRITICAL — do not skip):
   For every newly created or updated page, run:
   ```bash
   grep -rln "<new page title>" wiki/
   ```
   For each file that mentions the new page title but does NOT already contain `[[new-page-name]]`:
   - Open the file.
   - Add a `[[wikilink]]` at the first mention of the term.
   This ensures the wiki graph stays densely connected.

7. **Update `wiki/index.md`** with new/updated entries under the appropriate domain heading.

8. **Append to `wiki/log.md`:**
   ```
   ## [YYYY-MM-DD] ingest | <title>
   Ingested <source-type> from <source>. Created/updated N pages.
   ```

9. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "ingest: <title>"
   ```

10. **If qmd available:**
    ```bash
    "${QMD}" embed --collection <name>
    ```

---

## `query <question>`

Answer a question using wiki knowledge, with citations.

### Steps

1. **Detect active wiki.** Read `CLAUDE.md`.

2. **Find relevant pages:**
   - If qmd available:
     ```bash
     "${QMD}" query "<question>" --collection <name>
     ```
     Parse output for candidate page paths.
   - Otherwise: read `wiki/index.md` and identify relevant pages by title/description matching.

3. **Read all relevant pages.** Follow one level of `[[wikilinks]]` if targets look relevant to the question.

4. **Synthesize answer** with `[[wikilinks]]` as citations. Format rules:
   - **Default:** prose with inline wikilink citations.
   - **If question contains "table":** markdown table with wikilink citations in cells.
   - **If question contains "slides":** Marp markdown with `marp: true` frontmatter. Render with: `"${MARP}" <file> -o output.html`

5. **Ask:** "File this answer back into the wiki? (y/n)"
   - If yes: save to `wiki/queries/<slug>.md` first.
   - Then offer: "Promote to `wiki/<slug>.md` as a concept page? (y/n)"

6. **Append to `wiki/log.md`:**
   ```
   ## [YYYY-MM-DD] query | <question-slug>
   Answered question. Referenced N pages.
   ```

7. **Commit:**
   ```bash
   git -C ~/ObsidianVault add "03-Resources/<wiki-name>/" && git -C ~/ObsidianVault commit -m "query: <slug>"
   ```

---

## `lint`

Audit wiki integrity and fix issues.

### Steps

1. **Read all files** in `wiki/`.

2. **Build a link graph:** for each `[[wikilink]]` on each page, record the edge (source → target).

3. **Run deterministic lint script** if available:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/lint-wiki.py" <wiki-root>/wiki/
   ```

4. **Report and fix:**

   | Check | Action |
   |-------|--------|
   | **Orphan pages** (no inbound links) | List them. Suggest adding links from related pages. |
   | **Dead links** (`[[wikilinks]]` to nonexistent files) | Create stub pages with appropriate template. |
   | **Contradictions** | Scan for `[!WARNING]` markers. List them. |
   | **Missing "Counter-Arguments and Gaps" sections** | Add empty `## Counter-Arguments and Gaps` section. |
   | **Stale pages** | Flag pages with `status: stale` in frontmatter. |
   | **Index drift** | Compare `index.md` entries vs actual files. Add missing, remove dead. |

5. **Append lint report to `wiki/log.md`:**
   ```
   ## [YYYY-MM-DD] lint | N issues found, M fixed
   <summary of issues>
   ```

6. **Commit:**
   ```bash
    git -C ~/ObsidianVault commit -am "lint: YYYY-MM-DD"
    ```

---

## `remove <name>`

Delete a wiki and all its contents.

### Steps

1. **Resolve wiki path:** `~/ObsidianVault/03-Resources/<name>/`

2. **Verify it exists.** If not, abort: "Wiki '<name>' does not exist."

3. **Confirm with user:** List the directory contents and ask "This will permanently delete the '<name>' wiki and all its contents. Proceed? (y/n)"

4. **Remove qmd collection** (if qmd available):
   ```bash
   "${QMD}" collection remove <name>
   ```

5. **Remove from git and filesystem:**
   ```bash
   git -C ~/ObsidianVault rm -rf "03-Resources/<name>/" && git -C ~/ObsidianVault commit -m "remove: <name> wiki"
   ```

6. **Confirm:** "Wiki '<name>' has been removed."

---

## Templates

Used by the `init` operation. Apply verbatim, replacing `<name>` with the wiki name.

### CLAUDE.md

```markdown
# <name> Wiki Schema

## Directory Layout
- raw/           -- immutable source drops. Never edit files here.
- raw/attachments/ -- images and binary attachments.
- wiki/          -- LLM-owned pages. You have full write access here.
- wiki/index.md  -- catalog. Read this FIRST before opening any other page.
- wiki/log.md    -- append-only log. Never edit existing entries.
- wiki/queries/  -- filed query answers. Promote to wiki/ when durable.

## Entity Types and Templates

### concept.md
---
date: YYYY-MM-DD
tags: [domain]
type: concept
status: active
---
# Concept Name
<one-paragraph summary>

## Details
...

## See Also
- [[related-concept]]

## Counter-Arguments and Gaps
...

### person.md
---
date: YYYY-MM-DD
tags: [domain, person]
type: person
status: active
---
# Person Name
Role / affiliation.

## Key Contributions
...

## See Also
- [[related-concept]]

### source-summary.md
---
date: YYYY-MM-DD
tags: [domain]
type: source-summary
source-url: https://...
---
# Source Title
One-paragraph summary.

## Key Points
...

## Entities Mentioned
- [[person-or-concept]]

## Slides
To export as a Marp slide deck, add `marp: true` to frontmatter and run:
  "${MARP}" wiki/<filename>.md -o output.html

## Naming Conventions
- All filenames: lowercase-kebab-case.md
- Wikilinks: [[filename-without-extension]]
- Never use standard markdown links for internal links

## Log Format
Append to wiki/log.md after every operation. Format:
  ## [YYYY-MM-DD] <operation> | <title>
  <one-line description>

Operations: ingest | query | lint

## Index Format
wiki/index.md is a human- and LLM-readable catalog. Format:
  ## Domain Name
  - [[page-name]] -- one-line description (YYYY-MM-DD)

Keep entries under 80 chars. Update after every ingest.

## Cross-Reference Rules
- Every page must link to at least one other page when content warrants it
- When creating or updating a concept page, scan index.md for related entities and add [[wikilinks]]
- Flag contradictions inline: > [!WARNING] Contradiction with [[other-page]]

## Ingest Rules
1. Read and classify the source
2. Write or update a source-summary page in wiki/
3. For each entity: create or update its concept/person page
4. Backlink audit: grep existing pages for mentions of new titles
5. Update wiki/index.md
6. Append to wiki/log.md
7. Commit changes
One source typically touches 5-15 pages. This is normal.

## Query Rules
1. Read wiki/index.md first
2. Open relevant pages
3. Synthesize answer with [[wikilinks]] as citations
4. If novel synthesis, offer to file to wiki/queries/ then promote
5. Append to wiki/log.md
6. Commit changes

## Lint Rules
Scan all pages in wiki/ and report:
- Contradictions between pages
- Orphan pages (no inbound [[links]])
- Pages with status: stale older than 90 days
- Missing Counter-Arguments and Gaps section
- Index entries pointing to missing files
After fixing, append to log.md and commit.
```

### .gitignore

```
.DS_Store
*.sqlite
*.sqlite-wal
*.sqlite-shm
```

### qmd.yml

```yaml
collections:
  <name>:
    path: ./wiki
    pattern: "**/*.md"
```

### wiki/index.md

```markdown
# <name> Wiki Index

Last updated: YYYY-MM-DD

<!-- Add entries after each ingest. Format:
## Domain
- [[page-name]] -- description (YYYY-MM-DD)
-->
```

### wiki/log.md

```markdown
# <name> Wiki Log

<!-- Append only. Never edit existing entries. Format:
## [YYYY-MM-DD] ingest | Title
One-line description.
-->
```
