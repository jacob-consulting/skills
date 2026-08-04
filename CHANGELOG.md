# Changelog

All notable changes to the `jacob-consulting` marketplace are documented here — plugins added or
removed, and marketplace-level metadata. Each plugin keeps its own changelog under
`plugins/<name>/CHANGELOG.md`, versioned independently of this one.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] — 2026-08-04

### Changed
- The `validate` workflow now uses `actions/checkout@v5` and `actions/setup-python@v6`. The
  previous pins were forced onto Node 24 with a deprecation warning, since Node 20 is no longer
  supported on GitHub Actions runners.

### Fixed
- `scripts/release.sh` no longer corrupts the changelog when it lacks a trailing newline; it now
  ensures a trailing newline before appending the `[X.Y.Z]:` link reference.
- `scripts/validate.py` now accepts a marketplace entry whose `source` is a `git-subdir` object
  (as documented in `README.md`) instead of hard-erroring on it. Local-directory checks are
  skipped for such entries, but the "no `version` key" check still applies to them; non-string,
  non-object sources are still a clean error.
- `RELEASING.md` documents the bootstrap flow for a new plugin's first release (0.1.0), which
  `scripts/release.sh` cannot cut, and lists the two steps its "What the release script does"
  section had omitted (re-running `validate.py` before committing, and printing the diff).

## [1.1.0] — 2026-08-04

### Added
- `scripts/validate.py` — checks manifests, changelogs, and skill frontmatter. Read-only.
- `scripts/release.sh` — bumps a version, rolls the changelog, commits, and tags. Never pushes.
- `RELEASING.md` documenting the version topology and the release procedure.
- A `validate` GitHub Actions workflow running the checker on pull requests and pushes to `main`.

### Changed
- `README.md` no longer instructs bumping the version in two files.

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
[1.1.0]: https://github.com/jacob-consulting/skills/releases/tag/marketplace--v1.1.0
[1.2.0]: https://github.com/jacob-consulting/skills/releases/tag/marketplace--v1.2.0
