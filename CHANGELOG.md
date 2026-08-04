# Changelog

All notable changes to the `jacob-consulting` marketplace are documented here — plugins added or
removed, and marketplace-level metadata. Each plugin keeps its own changelog under
`plugins/<name>/CHANGELOG.md`, versioned independently of this one.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `scripts/validate.py` — checks manifests, changelogs, and skill frontmatter. Read-only.
- `scripts/release.sh` — bumps a version, rolls the changelog, commits, and tags. Never pushes.

## [1.0.0] — 2026-08-04

First versioned release of the marketplace itself.

### Added
- `metadata.version` and this changelog, so the marketplace is versioned independently of the
  plugins it lists.

### Changed
- Plugin entries no longer carry a `version` field. A plugin's version lives solely in its own
  `.claude-plugin/plugin.json`. The previous arrangement required bumping two files in lockstep
  and had already drifted once.

[1.0.0]: https://github.com/jacob-consulting/skills/releases/tag/marketplace--v1.0.0
