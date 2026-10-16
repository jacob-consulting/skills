# Changelog

All notable changes to the `django-crud-views` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The plugin version is independent of the `django-crud-views` package it documents; per-feature
`Available since X.Y.Z` markers in the skill track the package's release history.

## [Unreleased]

### Changed
- Package 0.29.3: the polymorphic create view defaults to `["home"]` context actions (new setting
  `CRUD_VIEWS_POLYMORPHIC_CREATE_CONTEXT_ACTIONS`) and its URL loses the double slash (`create/ct/<id>/`). The
  `cv_context_actions = ["home"]` workaround becomes a 0.29.2-and-older note in `references/migration.md`, and the
  skill now describes package 0.29.3.

## [0.15.0] — 2026-10-16

### Added
- `references/guardian.md`: granting the creator per-object permissions in `cv_form_valid` (strict mode otherwise
  hides what a user just created), and how child rows relate to the parent grant: by default they are checked
  per row as well, plus a verified recipe for children that inherit the parent's grant without losing the child
  create button.
- `references/polymorphic.md`: per-subtype property-grid groups (override `property_display`), and a "type" list
  column.
- Common Mistakes rows for the two guardian cases and the polymorphic create-page `NoReverseMatch`.

### Fixed
- `references/polymorphic.md`: the polymorphic create view needs its own `cv_context_actions` (e.g. `["home"]`).
  The inherited `"create"` button can't be reversed without the content type, so the step-2 form page crashed with
  `NoReverseMatch`.
- `references/workflow.md`: the `on_transition` example sent a notification inside the transition's transaction.
  It now does a DB follow-up there and sends the notification from `cv_on_commit` (`context["workflow_info"]`).

## [0.14.1] — 2026-10-16

### Changed
- Package 0.29.2 notes: the circular `ImportError` when `crud_views.lib.viewset` / `crud_views.lib.table` is imported
  first (e.g. a `Resource` with `ViewSet.PK` in `models.py`) is fixed upstream; the warning becomes a 0.29.1-and-older
  note in `references/migration.md`, and the skill now describes package 0.29.2.

## [0.14.0] — 2026-10-16

### Changed
- Restructured the skill: `SKILL.md` shrinks from 1,499 to ~250 lines (74 KB → 17 KB loaded per trigger) and holds
  the core model, setup, the five-view pattern, nesting, hooks, a routing table and the current-version Common
  Mistakes. Feature sections moved verbatim into topic references (`detail-views`, `lists-and-cards`, `form-views`,
  `forms-and-formsets`, `actions-and-buttons`, `guardian`, `polymorphic`, `assets`, `templates-and-navigation`,
  `settings`, `system-checks`). The skill description is unchanged.
- Version history ("before 0.x", renamed settings/classes, upgrade-only fixes) moved to `references/migration.md`.
- `references/settings.md` replaces the two partial settings lists and is checked against the package's defaults.

### Added
- `references/system-checks.md`: index of every check ID the package defines (several were undocumented, e.g.
  `crud_views.E100`, `viewset.E262`, `crud_views.E300`), each pointing at its reference.
- `CRUD_VIEWS_STRICT` (raise instead of swallowing unresolvable view keys; defaults to `DEBUG`).
- Note that Resources belong in `views.py`: importing `crud_views.lib.viewset` / `crud_views.lib.table` from
  `models.py` raises a circular `ImportError` in package 0.29.1.

### Fixed
- Formsets example: `FormSet(klass=...)` takes the result of `inlineformset_factory(..., formset=<InlineFormSet
  subclass>)`, and the parent form needs a `Formsets()` layout element plus `form_tag = False`. The previous example
  (`model`/`fields` on the `InlineFormSet` subclass) crashed at import.
- `ViewSet(pk=...)` is a URL regex, auto-detected from the model by default; the API reference claimed a default of
  the string `"UUID"`.

## [0.13.0] — 2026-10-15

### Changed
- Package 0.29.1 notes: supported Python / Django versions stated in the intro; Python 3.15 is tested and
  declared since 0.29.1 (Django 5.2 and 6.0; Django 4.2 stays on Python ≤ 3.13).

## [0.12.0] — 2026-10-12

### Changed
- Package 0.29.0 notes: `viewset.E110` requires action label templates on backend-only views (#179); POST
  actions work in the context toolbar, inline and in its menu, and the new tag `{% cv_context_action_form %}` pairs
  with a hand-placed `{% cv_context_button %}` for POST keys (#178).

## [0.11.0] — 2026-10-12

### Added
- Package 0.28.0 notes: hide or disable inaccessible actions (`CRUD_VIEWS_INACCESSIBLE_ACTIONS`,
  `inaccessible_actions`, `cv_inaccessible_actions`, checks `crud_views.E104` / `viewset.E207`) and action menus
  (`CRUD_VIEWS_*_ACTIONS_INLINE`, `*_actions_inline`, `cv_*_actions_inline`, `CRUD_VIEWS_ACTIONS_MENU_ICON`, group
  methods, menu templates, checks `crud_views.E105` / `viewset.E208` / `viewset.W290`); Common Mistakes rows for
  overridden containers, POST actions in the context toolbar, W290, hide-mode placeholders and `ActionView`
  buttons without label templates.

## [0.10.0] — 2026-10-09

### Added
- Package 0.27.1 notes: system check `viewset.E255` for context buttons whose target view or
  ViewSet does not resolve, `ContextButton.cv_check_target(viewset)`; Common Mistakes row for
  silently missing context buttons.

## [0.9.0] — 2026-10-09

### Added
- Package 0.27.0 notes: transactions around every write (`cv_atomic`, `cv_get_atomic()`,
  `cv_get_db_alias()`, `cv_form_valid_process()` / `cv_action_process()`), the `cv_on_commit(context)`
  hook with `context["workflow_info"]` on workflow views, and the 0.26 migration notes; Common Mistakes
  row for side effects in hooks that now run before the commit.

### Changed
- `CrudView.cv_parent_key` removed (package 0.27.0); Common Mistakes row for `viewset.W280` flagging it.

## [0.8.0] — 2026-10-08

### Added
- Package 0.26.0 notes: `cv_success_keys` / `cv_get_success_key()` (dynamic success target sharing
  the origin parameter with `cv_cancel_keys`), checks `viewset.E253` / `viewset.E254`,
  `cv_origin_keys_registered(keys)`.

### Changed
- `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` → `CRUD_VIEWS_ORIGIN_PARAM` (package 0.26.0); Common Mistakes rows
  for the rename and for an object-view `cv_success_key` on a `DeleteView`.

## [0.7.0] — 2026-10-08

### Added
- Package 0.25.0 notes: bundling registry assets into django-pipeline with the lazy `cv_sources()`,
  `CRUD_VIEWS_ASSETS_BUNDLED`, checks W340–W345, the `cv_assets` listing command; Common Mistakes
  rows for eager `cv_sources()` expansion and bundling an extension in CDN mode.

## [0.6.0] — 2026-09-28

### Added
- Package 0.23.0 notes: the core script `tooltip.js` (sixth `{% cv_js %}` asset) initialises the
  `card-rows` detail tooltip (`[data-cv-tooltip]`, `cv.initTooltips(root)`); where `detail` shows
  per layout pack; guardian `cv_guardian_accept_global_perms` now also covers the parent check;
  `Table.ca` presets combine safely with `|` (full preset list incl. `w5`…`w100`, `action`).
- Common Mistakes rows for 0.23.0: POST list actions and the filter toggle are `<button>`s
  (tag selectors break), overridden action templates must keep the visually hidden label, the
  never-initialised tooltip, the guardian parent 403 and the `Table.ca` preset bleed (both
  fixed in 0.23.0).

## [0.5.0] — 2026-09-14

### Added
- **Signed card ordering** (package 0.22.0): `cv_order_fields` entries prefixed with `-` / `+`
  encode the direction, render a single auto-submitting combo without asc/desc buttons and use
  `?order=-field`; new SKILL.md section "Card ordering: signed choices vs direction buttons",
  api-reference notes incl. the `data-cv-action="submit-on-change"` handler, two Common
  Mistakes rows (`+` in query strings, `dir` ignored in signed mode).

## [0.4.0] — 2026-09-14

### Added
- **Dynamic cancel target** (package 0.21.0): `cv_cancel_keys`, `cv_get_cancel_key()`,
  `CRUD_VIEWS_CANCEL_ORIGIN_PARAM`, checks `crud_views.E103` / `viewset.E252`; new SKILL.md
  section "Cancel button target" and an api-reference table.
- Package 0.21.0 notes: theme overrides of the form content templates must post to
  `request.get_full_path`; a `cv_get_link_url(view.cv_get_cls(key), key, obj)` example for custom
  link builders; `CustomFormNoObjectView` now defaults to `CRUD_VIEWS_CREATE_CONTEXT_ACTIONS` (its
  GET crash is fixed); the crispy cancel button on a `CustomFormView` targets the view's object.
  Three new Common Mistakes rows.

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
[0.4.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.4.0
[0.5.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.5.0
[0.6.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.6.0
[0.7.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.7.0
[0.8.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.8.0
[0.9.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.9.0
[0.10.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.10.0
[0.11.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.11.0
[0.12.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.12.0
[0.13.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.13.0
[0.14.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.14.0
[0.14.1]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.14.1
[0.15.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.15.0
