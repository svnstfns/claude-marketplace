# svnstfns/claude-marketplace

Personal Claude Code plugin marketplace. Skills, slash-commands, subagents, hooks, and MCP server configs that I build in-house and want to install (or share) cleanly.

## Install from this marketplace

```bash
# One-time setup — add the marketplace to your Claude Code
claude plugin marketplace add https://github.com/svnstfns/claude-marketplace

# Install any plugin by id
claude plugin install docs-methodology
```

See [`INDEX.md`](INDEX.md) for the full list of available plugins.

## What lives here

A **plugin** is the installable unit. Each plugin lives under `plugins/<plugin-name>/` and may contain any mix of:

- **skills** — markdown instructions Claude consults when their description matches the task
- **commands** — slash-commands (`/foo`)
- **agents** — specialized subagents with their own system prompt + tool restrictions
- **hooks** — scripts that fire on Claude Code lifecycle events
- **mcp** — Model Context Protocol server configs

## Contributing (or: how Claude adds new plugins here)

When this marketplace gains a new plugin, the workflow is in [`INSTRUCTIONS.md`](INSTRUCTIONS.md). That file is written for an LLM assistant to follow when the human says "build me a skill for X". The short version:

1. Build the skill / command / agent / hook / MCP wherever
2. Drop it into `plugins/<name>/` with a `plugin.json`
3. Append an entry to `.claude-plugin/marketplace.json`
4. Add a row to `INDEX.md`
5. Commit with `feat(plugin/<name>): ...`

## Layout

```
.
├── .claude-plugin/marketplace.json   # marketplace catalog
├── plugins/                          # all plugins live here
│   └── docs-methodology/             #   one folder per plugin
│       ├── plugin.json
│       └── skills/documentation-methodology/
├── INDEX.md                          # one-line table of plugins
├── INSTRUCTIONS.md                   # contributor guide (LLM-friendly)
└── README.md                         # this file
```

## License

MIT — see individual plugin folders for any plugin-specific licensing.
