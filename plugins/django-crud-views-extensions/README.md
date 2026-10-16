# django-crud-views-extensions (Claude Code plugin)

A Claude Code skill for the [django-crud-views-extensions](https://github.com/jacob-consulting/django-crud-views-extensions)
package — form widgets for [django-crud-views](https://github.com/jacob-consulting/django-crud-views):

- `crud_views_widget_datetimepicker` — date, time and datetime pickers wrapping the xdsoft jQuery DateTimePicker,
  with locale-following formats, CDN or vendored assets, and django-pipeline support.
- `crud_views_widget_typeahead` — a server-backed, permission-aware type-ahead single select for large model
  choice sets (thousands of users), for forms and django-filter filters, as a text typeahead or a select popup.

## Install

```
/plugin marketplace add jacob-consulting/skills
/plugin install django-crud-views-extensions@jacob-consulting
```

Start a new Claude Code session afterwards. The skill loads automatically when you work with the
`crud_views_widget_*` apps (see the skill's `description` for the full trigger list). For ViewSets, views,
tables and forms themselves, install the `django-crud-views` plugin from the same marketplace as well.

## What's inside

| Component | Count |
|---|---|
| Skills | 1 — `django-crud-views-extensions` |
| Agents / Hooks / MCP servers | 0 |

The skill lives at [`skills/django-crud-views-extensions/SKILL.md`](skills/django-crud-views-extensions/SKILL.md)
with one reference file per app under `skills/django-crud-views-extensions/references/`. Feature sections carry
`Available since X.Y.Z` markers matching the package's releases.

## Author

Alexander Jacob — <alexander.jacob@jacob-consulting.de>
