---
name: long-term-memory
description: |
  树状结构的长期记忆管理系统，用于保存、组织和检索需要持久化的知识与信息。
  触发条件：用户提到 "long-term-memory"、"/skill:long-term-memory"、
  "save memory"、"organize memory"、"delete memory"、
  "保存记忆"、"整理记忆"、"删除记忆"、
  "长期记忆"、"记忆管理" 或任何涉及长期记忆存取的操作。
---

# Long-Term Memory

Manage persistent knowledge in a tree-structured markdown file system.

## Root Directory

All memory files live under:

```
~/.agents/skills/long-term-memory/
```

Organize as a **topic tree** using nested directories and `.md` files:

```
long-term-memory/
├── projects/
│   ├── project-alpha.md
│   └── project-beta/
│       ├── overview.md
│       └── backend.md
├── personal/
│   └── reading-list.md
└── work/
    └── quarterly-goals.md
```

## Memory File Format

Each `.md` file is a self-contained memory unit. Load `references/structure-guide.md` for the full specification, splitting rules, and template.

**Constraints:**
- 7–9 bullet points per file
- Each bullet ≤ 500 characters
- Exceeding limits → split into child file(s) with cross-references

## Topic Auto-Load

Before executing any command, check if the user's request matches keywords in the table below. If matched, load the associated memory file into context first.

| Keywords | File to load |
|----------|-------------|
| PR, Merge Request, MR, 提代码, 代码评审, code review | `workflows/pr-workflow.md` |

If the file does not exist, proceed without loading.

## Commands

When the user invokes a command, follow the matching workflow below.

### `save [...]` — Create or Update Memory

1. Parse the topic and content from the user's request.
2. Determine the target file path in the tree.
3. If the file does not exist, create it using the format in `references/structure-guide.md`.
4. If the file exists, append or update points.
5. **After any edit**, enforce constraints (7–9 points, ≤ 500 chars each):
   - If a point exceeds 500 chars, summarize it and link to a sub-file.
   - If total points exceed 9, split the overflow into child files.
6. Save and confirm the file path.

### `organize` — Restructure the Memory Tree

1. Scan the entire `long-term-memory/` directory.
2. Identify files violating constraints (too many points, oversized bullets, orphaned files).
3. Merge undersized sibling files when appropriate.
4. Split oversized files into child files with cross-references.
5. Fix broken or stale cross-reference links.
6. Report what changed.

### `delete [topic]` — Remove a Memory

1. Locate the file or directory matching `topic`.
2. Remove the file(s).
3. Search the tree for cross-references pointing to the deleted path and remove or update them.
4. If a parent file is left with too few points, consider merging with a sibling or adding a placeholder note.
5. Confirm deletion and cleanup summary.

## Sensitive Information

**Never** write secrets, passwords, tokens, PII, or other sensitive data into regular `.md` memory files.

Store sensitive content exclusively in:

```
~/.agents/skills/long-term-memory/.secret-memory
```

Rules for `.secret-memory`:
- Read it **only** when the user explicitly requests sensitive information.
- Do **not** load `.secret-memory` into context during normal `save` / `organize` / `delete` operations.
- Treat it as append-only; delete by user request only.
- Do **not** create `.secret-memory` automatically. The user creates it when needed.
