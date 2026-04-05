# Compilation Guide

Standards for writing and updating wiki articles during ingest.

## Article Length

Target 800-2000 words for concept articles. Source summaries can be shorter (300-600 words). If an article exceeds 2000 words, consider splitting into sub-topics with `[[wikilinks]]` between them.

## Wikilink Density

Every article should contain at least 3 `[[wikilinks]]` to other wiki pages. Dense cross-linking is what makes the wiki compound — isolated pages are nearly worthless.

On first mention of a related concept or person, use a wikilink: `[[concept-name]]`. Don't over-link: one link per entity per section is enough.

## Sourcing Rules

Every factual claim in a wiki article should trace back to a source in `raw/`. Reference sources in the article's "Sources" or "Entities Mentioned" section using wikilinks.

Never invent facts. If the source doesn't support a claim, don't include it.

## Backlink Audit (CRITICAL)

After creating or updating any page, grep all existing wiki pages for mentions of the new page's title or key terms:

```bash
grep -rln "<new page title>" wiki/
```

For each match, add a `[[wikilink]]` at the first natural mention. This is the most commonly skipped step — a compounding wiki depends on bidirectional links.

## Contradiction Handling

When a new source contradicts existing wiki content:

1. Don't silently overwrite — flag it with an Obsidian callout:
   ```
   > [!WARNING] Contradiction with [[other-page]]
   > Source A claims X, but [[other-page]] states Y.
   ```
2. Update both pages to acknowledge the disagreement
3. Note it in the ingest log entry

## Updating Existing Articles

When updating (not creating) an article:

1. Read the existing content fully
2. Identify what's changing and why
3. Preserve existing wikilinks and add new ones
4. Update the `date` in frontmatter
5. Add the new source to the "Sources" section
