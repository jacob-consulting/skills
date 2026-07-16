# Changelog

All notable changes to the `django-crud-views` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The plugin version is independent of the `django-crud-views` package it documents; per-feature
`Available since X.Y.Z` markers in the skill track the package's release history.

## [0.1.0] — 2026-07-16

Initial published release — the `django-crud-views` skill packaged as a Claude Code plugin.

### Added
- **Skill `django-crud-views`** covering the package end to end:
  - ViewSets and the List / Detail / Create / Update / Delete view classes.
  - Tables (django-tables2), filters (django-filter, incl. pinned filters), and crispy-forms.
  - Nested/child resources via `ParentViewSet`; Child, Sibling, and view-level context buttons.
  - `CardListView` (ordering, pagination, filter coexistence) and `DetailCustomView`.
  - Modal views (`cv_modal`), custom form/action views, and conditional action disabling
    (`cv_action_enabled`).
  - Formsets (`FormSetMixin`), polymorphic models (`crud_views_polymorphic`), and the FSM
    `WorkflowView` with audit history (`crud_views_workflow`).
  - Per-object permissions with django-guardian (`crud_views_guardian`).
  - Non-ORM / non-database data in ViewSets via `Resource` + `ResourceViewMixin`.
- **Reference material** bundled with the skill: API reference, quickstart, workflow guide, and a
  dedicated non-ORM resources reference.
- **Per-feature `Available since X.Y.Z` markers** on every non-original feature section, matching
  the underlying package's releases (0.4.0 through 0.12.0).
- **Plugin packaging**: `plugin.json` manifest and a listing in the `jacob-consulting` marketplace
  (`.claude-plugin/marketplace.json`) so the skill installs via
  `/plugin install django-crud-views@jacob-consulting`.

[0.1.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.1.0
