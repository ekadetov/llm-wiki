# Frontmatter Schemas

Standard YAML frontmatter for each entity type. Copy the appropriate schema when creating new wiki pages.

## concept.md

```yaml
---
date: YYYY-MM-DD
tags: [domain]
type: concept
status: active
---
```

Fields:
- `date`: creation date (ISO 8601)
- `tags`: domain tags for Dataview queries
- `type`: always `concept`
- `status`: `active` | `stale` | `draft`

## person.md

```yaml
---
date: YYYY-MM-DD
tags: [domain, person]
type: person
status: active
---
```

Fields: same as concept, plus `person` tag.

## source-summary.md

```yaml
---
date: YYYY-MM-DD
tags: [domain]
type: source-summary
source-url: https://...
---
```

Fields:
- `source-url`: original URL of the ingested source
- All other fields same as concept

## query-output.md

```yaml
---
date: YYYY-MM-DD
tags: [domain]
type: query
question: "The original question"
informed-by:
  - "[[article-1]]"
  - "[[article-2]]"
status: filed
---
```

Fields:
- `question`: the original query text
- `informed-by`: list of wiki articles that informed the answer
- `status`: `filed` (initial) | `promoted` (moved to wiki/)
