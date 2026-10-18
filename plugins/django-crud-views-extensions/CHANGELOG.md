# Changelog

All notable changes to the `django-crud-views-extensions` plugin are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The plugin version is independent of the `django-crud-views-extensions` package it documents; per-feature
`Available since X.Y.Z` markers in the skill track the package's release history.

## [Unreleased]

## [0.1.1] — 2026-10-18

### Added
- Package 0.3.3: pickers and typeaheads initialise in formset rows added after page load (django-crud-views
  ≥ 0.29.4 `cv:formset:row-added`). The Common Mistakes row about "new formset rows stay inert" now applies only
  to content added by your own JavaScript, plus a new row for older versions.

## [0.1.0] — 2026-10-16

### Added
- Initial release, covering package 0.3.2: `crud_views_widget_datetimepicker` (widgets, locale-following
  formats, settings, vendored mode, django-pipeline, system checks) and `crud_views_widget_typeahead` (lookups,
  `bind()`, fields and filters, text and select-popup widgets, endpoint, security model, skins, django-pipeline).

[0.1.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views-extensions--v0.1.0
[0.1.1]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views-extensions--v0.1.1
