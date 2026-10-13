# long-term-memory

🧠 Tree-structured long-term memory: save, organize and delete persistent knowledge as Markdown files.

## What it does

Keeps durable knowledge in a topic tree of Markdown files under `~/.agents/skills/long-term-memory/`, so agents can accumulate context across sessions instead of relearning it. Each memory file is a self-contained unit with **7–9 bullet points**, each **≤ 500 characters**; oversized files are split into child files with cross-references.

Commands:

| Command | Purpose |
|---------|---------|
| `save [...]` | Create or update a memory file |
| `organize` | Restructure the tree: merge, split, fix stale links |
| `delete [topic]` | Remove a memory and clean up references |

Topic auto-load: when a request matches a keyword in the skill's routing table (e.g. `PR` / `code review` → `workflows/pr-workflow.md`), that memory file is loaded into context first.

## Structure

```
long-term-memory/
├── SKILL.md                      # Skill definition, commands, constraints
├── references/
│   └── structure-guide.md        # File layout, constraints, split/merge workflow
├── principles/
│   └── evidence-discipline.md    # Evidence standards for analysis tasks
└── workflows/
    └── pr-workflow.md            # PR / MR workflow memory
```

Sensitive data (tokens, credentials) never goes into `.md` files — only into the append-only `~/.agents/skills/long-term-memory/.secret-memory`, which is intentionally **not** part of this repo.

## Installation

```bash
npx skills add https://github.com/pipi32167/million-skills --skill long-term-memory
```

## Usage

Trigger by saying:

- "long-term-memory" / "/skill:long-term-memory"
- "save memory" / "保存记忆"
- "organize memory" / "整理记忆"
- "delete memory" / "删除记忆"

Typical flow:

1. `save` the topic and content → the skill picks a path in the topic tree and writes/updates the file.
2. Constraints are enforced after every edit (7–9 points, ≤ 500 chars each).
3. `organize` periodically rebalances the tree and repairs cross-references.

## Notes

- The memory root is inside the skill directory itself (`~/.agents/skills/long-term-memory/`), so memories live next to the skill that manages them.
- `principles/evidence-discipline.md` encodes the "no single-source conclusions" rule for analysis work: conclusions need at least two independent sources, and evidence grade must be stated.
