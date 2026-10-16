# django-crud-views (Claude Code plugin)

A Claude Code skill for building Django CRUD interfaces with the
[django-crud-views](https://github.com/jacob-consulting/django-crud-views) package — ViewSets,
django-tables2 tables, django-filter filters, crispy-forms, nested/child resources, FSM
workflows, django-guardian per-object permissions, formsets, polymorphic models, and non-ORM
Resource ViewSets.

## Install

```
/plugin marketplace add jacob-consulting/skills
/plugin install django-crud-views@jacob-consulting
```

Start a new Claude Code session afterwards. The skill loads automatically when you work with the
`django-crud-views` package (see the skill's `description` for the full trigger list).

## What's inside

| Component | Count |
|---|---|
| Skills | 1 — `django-crud-views` |
| Agents / Hooks / MCP servers | 0 |

The skill lives at [`skills/django-crud-views/SKILL.md`](skills/django-crud-views/SKILL.md): a short
entry point with the core patterns and a table that routes each feature to a topic file under
`skills/django-crud-views/references/` (detail views, lists and cards, form views, formsets, actions and
buttons, Guardian, polymorphic, workflow, resources, assets, settings, system checks, API reference).
Feature sections carry `Available since X.Y.Z` markers matching the package's releases; upgrade notes
for older package versions are in `references/migration.md`.

## Author

Alexander Jacob — <alexander.jacob@jacob-consulting.de>
