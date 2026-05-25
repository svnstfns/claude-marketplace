# Instructions for LLMs adding content to this marketplace

> Read this when you (Claude, or any assistant) help the human add a new skill, plugin, MCP server, agent, command or hook to this marketplace. Follow it exactly.

## What this repository is

This is svnstfns's personal Claude Code marketplace. Anything reusable that the human builds with you — a skill, a slash-command, a subagent, a hook, an MCP server — lands here as a **plugin**, so it can be installed via `claude plugin install <name>` and shared.

**Hard rule:** When the human asks you to "build a skill / plugin / MCP / hook / agent / command for X", finish the build, then package it into this repository under `plugins/<name>/`. Don't ask whether to do it — it's the default. Only skip when the human explicitly says "don't add to the marketplace".

## Repository layout

```
0004-claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json        ← Catalog of all plugins (every new plugin appears here)
├── plugins/
│   └── <plugin-name>/
│       ├── plugin.json         ← Plugin manifest (required)
│       ├── README.md           ← Plugin-specific docs (recommended)
│       ├── skills/             ← Skill folders (each is its own SKILL.md + bundled assets)
│       ├── commands/           ← Slash-command .md files
│       ├── agents/             ← Subagent definition .md files
│       ├── hooks/              ← Hook scripts + hooks.json
│       └── mcp/                ← MCP server configs
├── INDEX.md                    ← One-line table of every plugin
├── INSTRUCTIONS.md             ← This file
└── README.md                   ← Human-facing entry point
```

A single plugin may contain **any mix** of skills, commands, agents, hooks and MCP configs. Group things that belong together (e.g. a Python-toolkit plugin with both a `python-patterns` skill and a `pytest-runner` command). Don't fragment one logical unit into multiple plugins; don't bundle unrelated things into one plugin.

## How to add a new plugin

### Step 1 — Pick names

- **Plugin folder name:** short, kebab-case, no `claude-` prefix (the marketplace context is implicit). Examples: `docs-methodology`, `python-toolkit`, `homelab-mcps`.
- **Skill / command / agent IDs inside:** match the file/folder name. The skill `documentation-methodology` lives at `plugins/docs-methodology/skills/documentation-methodology/SKILL.md`.

### Step 2 — Create the plugin directory

```
plugins/<plugin-name>/
├── plugin.json
├── README.md
└── <one or more of:> skills/  commands/  agents/  hooks/  mcp/
```

### Step 3 — Write `plugin.json`

Minimal:

```json
{
  "name": "<plugin-name>",
  "version": "1.0.0",
  "description": "One-sentence what-and-why.",
  "author": "svnstfns",
  "license": "MIT",
  "type": "plugin",
  "skills":   ["<skill-id-1>", "<skill-id-2>"],
  "commands": ["<command-id>"],
  "agents":   ["<agent-id>"],
  "hooks":    ["<hook-id>"],
  "mcp":      ["<mcp-server-id>"]
}
```

Only include the keys that the plugin actually contains. Versioning: bump the `version` semver when you change behaviour.

### Step 4 — Put the actual content in

**Skills** — copy the entire skill folder (with its `SKILL.md`, `assets/`, `references/`, `scripts/` etc.) into `plugins/<plugin>/skills/<skill-id>/`. Do not flatten — keep the directory structure.

**Commands** — one `.md` file per slash-command in `plugins/<plugin>/commands/<command-id>.md`. First line is the description; rest is the prompt.

**Agents** — one `.md` file per subagent in `plugins/<plugin>/agents/<agent-id>.md` with frontmatter (`name`, `description`, `tools`) and the system prompt below.

**Hooks** — scripts (any executable) plus a `hooks.json` describing when they fire (`SessionStart`, `PostToolUse`, etc.).

**MCP servers** — config snippets that get merged into the user's MCP config, in `plugins/<plugin>/mcp/<server>.json`.

### Step 5 — Register the plugin in `marketplace.json`

Edit `.claude-plugin/marketplace.json` and append an entry to the `plugins` array:

```json
{
  "id": "<plugin-name>",
  "name": "<Human-readable name>",
  "description": "Same as plugin.json description, or longer if it helps discovery.",
  "version": "1.0.0",
  "author": "svnstfns",
  "repository": "https://github.com/svnstfns/claude-marketplace",
  "path": "plugins/<plugin-name>",
  "type": "plugin",
  "tags": ["topic-1", "topic-2", "language-if-any"]
}
```

The `tags` matter for discoverability — be honest, not exhaustive (3–6 tags).

### Step 6 — Update `INDEX.md`

Add a single row to the table at the bottom of `INDEX.md`. Keep the description tight (under 100 chars). The INDEX is what humans skim.

### Step 7 — Verify locally

If the plugin contains a skill, you can install the entire skill folder globally for a quick check:

```bash
cp -r plugins/<plugin>/skills/<skill> ~/.claude/skills/
# Then in a Claude Code session, the skill should appear in the available-skills list.
```

For schema sanity, run:

```bash
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
python3 -c "import json; json.load(open('plugins/<plugin>/plugin.json'))"
```

### Step 8 — Commit

Use conventional commits:

```
feat(plugin/<plugin-name>): add <one-line summary>
```

Example: `feat(plugin/docs-methodology): add arc42-inspired documentation methodology skill`.

## How **users** install from this marketplace

```bash
# One-time: add the marketplace
claude plugin marketplace add https://github.com/svnstfns/claude-marketplace

# Then: install any plugin by its id
claude plugin install docs-methodology
```

## Anti-patterns — don't do these

- **Don't put the same skill into multiple plugins.** Pick one home, link from elsewhere.
- **Don't create empty stub plugin folders** as placeholders for future work. Empty folders rot and confuse downstream tooling.
- **Don't edit `marketplace.json` without also creating the corresponding `plugin.json`** (and vice versa) — the two must stay in sync.
- **Don't commit a `documentation-methodology.skill` zip into this repo.** Zips are for sharing one-off via email; in the marketplace, the unpacked folder is what's installed.
- **Don't change a published plugin's `id`.** That breaks every user who installed it. Bump version and deprecate via a `note` if a rename is unavoidable.

## When the human asks for something that doesn't fit

If what they want is a single MCP server config or a one-off hook, it's still a plugin (one item, but still in `plugins/<name>/`). The plugin abstraction is the unit; an "MCP-only plugin" is fine.

If they want to share something with a non-Claude-Code audience, you're outside the scope of this repo — say so and ask where it should go instead.
