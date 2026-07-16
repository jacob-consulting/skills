# jacob-consulting — Claude Code plugin marketplace

A [Claude Code](https://github.com/anthropics/claude-code) plugin marketplace of skills that
extend Claude with domain-specific knowledge and workflows.

## Install

```
/plugin marketplace add jacob-consulting/skills
/plugin install django-crud-views@jacob-consulting
```

Then start a new Claude Code session. Update later with `/plugin update django-crud-views@jacob-consulting`.

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
4. Bump the plugin's `version` in both `plugin.json` and the marketplace entry on each release.

## Local development

To edit a skill and see changes live without reinstalling, symlink it into your skills directory:

```bash
ln -sfn "$(pwd)/plugins/django-crud-views/skills/django-crud-views" \
        ~/.claude/skills/django-crud-views
```

Restart Claude Code or start a new session to pick up changes.
