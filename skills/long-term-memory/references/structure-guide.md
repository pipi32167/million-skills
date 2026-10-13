# Memory File Structure Guide

## File Layout

Every memory file is a Markdown file with this structure:

```markdown
# [Topic Title]

> Parent reference: `../parent-topic.md` (omit if root-level)

- [Key point 1, max 500 chars]
- [Key point 2, max 500 chars]
- ...
- [Key point N, 7 <= N <= 9]

## Sub-topics

- [Sub-topic description](../path/to/sub-topic.md)
- [Another sub-topic](../path/to/another.md)
```

## Constraints

| Rule | Limit | Action when exceeded |
|------|-------|----------------------|
| Points per file | 7–9 | Split overflow into child files |
| Point length | ≤ 500 chars | Summarize and link to child file |
| Nesting depth | No hard limit, but keep practical | Flatten if tree becomes too deep |

## Splitting Workflow

When a file grows beyond 9 points:

1. Group related points into logical clusters (2–4 points each).
2. Create child files under a new directory named after the parent file (without `.md`).
3. Move clustered points into child files.
4. In the parent file, replace moved points with short summaries + cross-references under `## Sub-topics`.
5. Ensure each child file also respects the 7–9 point limit.

### Example

**Before: `backend.md` (12 points)**

```markdown
# Backend Architecture

- Point 1...
- ...
- Point 12...
```

**After:**

```
backend/
├── overview.md
├── database.md
└── api-design.md
```

`backend/overview.md`:

```markdown
# Backend Architecture

- High-level summary of backend stack...
- Deployment pipeline overview...
- Monitoring and observability strategy...

## Sub-topics

- Database schema and migrations (./database.md)
- REST API design decisions (./api-design.md)
```

## Cross-Reference Syntax

Use relative Markdown links:

```markdown
- [Short label](./relative-path.md)
```

When a referenced file is deleted, remove or update the link in the parent.

## Merging Workflow

When sibling files are too small (each < 4 points):

1. Consider merging into a single file if topics are closely related.
2. Update parent cross-references.
3. Delete empty directories.
