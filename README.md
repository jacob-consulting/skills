# jacob-consulting — Claude Code plugin marketplace

A [Claude Code](https://github.com/anthropics/claude-code) plugin marketplace of skills that
extend Claude with domain-specific knowledge and workflows.

## Install

Add this marketplace, then install the plugin:

```
/plugin marketplace add jacob-consulting/skills
/plugin install django-crud-views@jacob-consulting
```

Then start a new Claude Code session. Update later with `/plugin update django-crud-views@jacob-consulting`.

> **Official directory** (pending review): once accepted into Anthropic's
> [`claude-plugins-official`](https://github.com/anthropics/claude-plugins-official) marketplace,
> the plugin can also be installed without adding this marketplace first:
> ```
> /plugin install django-crud-views@claude-plugins-official
> ```
> Same plugin — pick whichever marketplace you already have added.

### Available plugins

| Plugin | Description |
|---|---|
| `django-crud-views` | Build Django CRUD interfaces with the django-crud-views package — ViewSets, tables, filters, forms, workflows, per-object permissions, and non-ORM resources. |

## Repository structure

This repo *is* the marketplace. Its root `.claude-plugin/marketplace.json` lists the plugins;
each plugin lives under `plugins/` and bundles its skill(s) under its own `skills/` directory:

```
.claude-plugin/
  marketplace.json                     # lists all plugins
plugins/
  django-crud-views/                   # a plugin
    .claude-plugin/
      plugin.json                      # name, version, description, author
    skills/
      django-crud-views/               # the skill Claude loads
        SKILL.md                       # main skill file (required)
        references/                    # supporting reference files
```

## Adding a new plugin

1. Create `plugins/<name>/` with a `.claude-plugin/plugin.json`
   (`name`, `description`, `version`, `author`).
2. Put the skill under `plugins/<name>/skills/<skill-name>/SKILL.md` (plus any `references/`).
3. Add an entry to `plugins` in `.claude-plugin/marketplace.json` with a
   `source: "./plugins/<name>"` (a plugin in another repo can instead use a `git-subdir` source).
   Do **not** put a `version` in the entry — it belongs only in the plugin's own `plugin.json`.
4. Add a `plugins/<name>/CHANGELOG.md` with a section for the plugin's current version.
5. Run `python3 scripts/validate.py` to check all of the above, and see
   [RELEASING.md](RELEASING.md) for how to cut releases.

## Local development

To edit a skill and see changes live without reinstalling, symlink it into your skills directory:

```bash
ln -sfn "$(pwd)/plugins/django-crud-views/skills/django-crud-views" \
        ~/.claude/skills/django-crud-views
```

Restart Claude Code or start a new session to pick up changes.
