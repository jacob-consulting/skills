# Changelog

All notable changes to the `django-crud-views` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The plugin version is independent of the `django-crud-views` package it documents; per-feature
`Available since X.Y.Z` markers in the skill track the package's release history.

## [Unreleased]

## [0.3.0] — 2026-08-04

### Changed
- Administrative version bump. The skill's content is unchanged from 0.2.0: `SKILL.md` and every
  file under `references/` are byte-identical, and no guidance, API coverage, or `Available since`
  marker differs. Nothing about the plugin's behaviour changes for anyone who installs or updates
  it.

## [0.2.0] — 2026-08-04

Brings the skill up to date with `django-crud-views` 0.20.0. The 0.17.0 object-detail split had
never been reflected, so the property-grid guidance produced a project that could not start.

### Fixed
- **`CrispyModelViewMixin` → `CrispyViewMixin`** throughout. The mixin was renamed in package
  0.14.0; the skill had shipped the dead name in all five files since its first release.
- **Object-detail split (package 0.17.0)**, previously undocumented in full:
  - `DetailCustomView*` / `GuardianDetailCustomViewPermissionRequired` removed — now
    `DetailView*` / `GuardianDetailViewPermissionRequired`.
  - `cv_property_display` no longer works on core `DetailView`; it moved to
    `ObjectDetailView` in the new `crud_views_object_detail` app.
  - The external `django-object-detail` dependency and its `django_object_detail`
    `INSTALLED_APPS` entry are gone (vendored in-tree).
  - `OBJECT_DETAIL_*` settings renamed to `CRUD_VIEWS_OBJECT_DETAIL_*`.
  - Polymorphic and Guardian detail views need `ObjectDetailMixin` composed in for a property grid.
- Contradictory icon-setting documentation between `quickstart.md` and `api-reference.md`
  resolved against the package defaults (library defaults to `bootstrap`; Font Awesome's
  default type is `regular`; the type is a free-form class suffix, not a fixed value set).
- Frontmatter trimmed to 1008 characters — it had exceeded the 1024-character limit.

### Added
- **Static assets, CSP, and SRI** (package 0.18.0): `register_assets()`, the `Asset` dataclass,
  `AssetBundle` now holding `Asset` instances rather than strings, automatic CSP-nonce detection,
  `CRUD_VIEWS_CSP_NONCE_ATTR`, and checks `crud_views.E330` / `crud_views.W332`.
- **System check `viewset.W280`** (package 0.19.0) for unknown/dead `cv_*` attributes, and the
  `cv_check_ignore_attributes` allowlist.
- Package 0.20.0 notes: the action column's `cv-col-action` class (replacing
  `d-flex justify-content-end`, which broke the row separator), the
  `crud_views_settings.dict` → `.as_dict` rename, and the now-immediate `ImportError` when
  `django-filter` or `django-crispy-forms` is missing.
- `PolymorphicDeleteView`, `ObjectDetailMixin`, `CrudViewBreadcrumbMixin`, and the
  `crud_views_object_detail.lib` exports added to the reference cheatsheets; seven new
  "Common Mistakes" rows covering the migrations above.

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

[0.2.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.2.0
[0.1.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.1.0
[0.3.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.3.0
