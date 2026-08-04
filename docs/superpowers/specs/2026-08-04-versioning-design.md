# Versioning and release process — design

**Date:** 2026-08-04
**Repo:** `jacob-consulting/skills` (Claude Code plugin marketplace)
**Status:** approved

## Problem

The repo already has the *artifacts* of versioning — semver in two manifests, a
Keep-a-Changelog `CHANGELOG.md`, one git tag — but no process holding them together. The
consequences are already visible:

- Plugin `0.2.0` shipped in commit `88a2814` but was never tagged; only
  `django-crud-views--v0.1.0` exists.
- The plugin CHANGELOG has a `[0.1.0]` link reference at the bottom but no `[0.2.0]` one.
- The version is written in two files that must be bumped together by hand.
  `README.md` step 4 documents this as a thing to remember.
- Nothing checks any of it.

## Decisions

Two decisions shape everything below.

**1. `plugin.json` is the single source of truth for a plugin's version.** The `version` key is
removed from the plugin's entry in `marketplace.json`. This matches Anthropic's
`claude-plugins-official` marketplace, whose 278 plugin entries carry no `version` field at all.
Drift between the two files becomes structurally impossible rather than machine-checked.

**2. The marketplace is versioned separately, with semver.** `metadata.version` in
`marketplace.json`, a root `CHANGELOG.md`, and `marketplace--vX.Y.Z` tags. It moves on its own
rhythm — a plugin added, a description changed — which no per-plugin version captures.

## Version topology

| Thing | Version lives in | CHANGELOG | Tag |
|---|---|---|---|
| Plugin `django-crud-views` | `plugins/django-crud-views/.claude-plugin/plugin.json` → `version` | `plugins/django-crud-views/CHANGELOG.md` | `django-crud-views--v0.2.0` |
| Marketplace `jacob-consulting` | `.claude-plugin/marketplace.json` → `metadata.version` | `CHANGELOG.md` (repo root) | `marketplace--v1.0.0` |

A plugin release does not bump the marketplace version, and vice versa.

## Components

### `scripts/validate.py`

The shared invariant checker. Python 3, with **PyYAML as its only dependency** (needed by check 5
— frontmatter is YAML, and YAML is not in the stdlib). Everything else it reads is JSON. Run by
CI, by `release.sh` as a preflight, and directly by a human. Exits non-zero with one line per
violation.

The dependency is installed with `pip install pyyaml` — one step in CI, and it is already present
in the maintainer's local environment. There is no requirements file or lockfile; a single
unpinned dependency on a library this stable does not warrant one. If the import fails,
`validate.py` exits with a clear message naming the install command rather than a traceback.

Checks:

1. Every `plugins/*/.claude-plugin/plugin.json` parses, and has `name`, `description`, and a
   semver `version`.
2. `marketplace.json` parses, and for each entry in `plugins`:
   - `source` resolves to an existing directory containing `.claude-plugin/plugin.json`
   - entry `name` equals the manifest's `name`
   - **the entry has no `version` key** — enforcing decision 1 against copy-paste regression
3. Each plugin's `CHANGELOG.md` contains a `## [<version>]` section matching its `plugin.json`
   version.
4. `metadata.version` is semver, and the root `CHANGELOG.md` has a matching section.
5. Every `SKILL.md` has YAML frontmatter that parses, with `name` and `description` present, and
   the description ≤ 1024 characters. (The plugin's own 0.2.0 changelog records this limit being
   exceeded once in a shipped release — it is worth checking mechanically.)

Check 5 parses the frontmatter with PyYAML rather than extracting it with a regex or with `awk`
between the `---` markers. Text extraction handles the current file — a flat block with a
single-line quoted `description` — but silently misreads a folded (`>`) or literal (`|`) block
scalar, which skill frontmatter commonly uses. A length check that quietly under-reports on the
exact construct that produces long descriptions would be worse than no check at all.

Boundary: `validate.py` only reads and reports. It never writes, and knows nothing about git.

### `scripts/release.sh`

```
scripts/release.sh <target> <version> [--dry-run]

  target    a plugin name (e.g. django-crud-views), or the literal "marketplace"
  version   the new semver version
  --dry-run print every change without touching the working tree
```

Resolves `target` to a manifest path, a CHANGELOG path, and a tag prefix, then:

**Preflight** — all failures are fatal, and all run before any mutation:

- `jq` is on PATH
- the working tree is clean
- `validate.py` passes
- `version` is valid semver and strictly greater than the current version
- the target tag does not already exist
- the CHANGELOG has an `## [Unreleased]` section with non-empty content

The current branch is deliberately *not* checked. Releasing from a branch is allowed.

**Mutate:**

- Write the new version into the manifest.
- Rewrite the CHANGELOG's `## [Unreleased]` heading as `## [X.Y.Z] — YYYY-MM-DD` (today's date),
  insert a fresh empty `## [Unreleased]` above it, and append the `[X.Y.Z]:` link reference at
  the bottom, pointing at the release tag URL.
- Commit as `release(<target>): v<version>`.
- Create an annotated tag.
- Print the `git push origin <branch> --follow-tags` command.

**The script never pushes.** Publishing stays an explicit human action.

Implementation note: version fields are rewritten with a key-anchored `perl -pi -e`, not with
`jq`. `jq` reflows the hand-formatted inline objects in these manifests (`"owner": { "name": …,
"email": … }`) onto multiple lines, burying a one-line release under cosmetic churn. To keep the
regex honest, the script asserts the `"version"` key occurs exactly once in the target file
before substituting, then re-parses the file and confirms the new value took. Both manifests
satisfy the once-only precondition after decision 1 removes the entry-level versions.

### `.github/workflows/validate.yml`

On pull requests and pushes to `main`: check out, set up Python, `pip install pyyaml`, run
`scripts/validate.py`. No secrets, no write permissions, no repo mutation — it is purely a gate.

### `RELEASING.md`

Documents the version topology, how to cut a plugin release, how to cut a marketplace release,
what CI enforces, and how to recover from drift.

## Testing

No automated test suite. `--dry-run` is the verification mechanism: it runs the full preflight
and prints every intended change without touching the working tree, so a release is always
inspected before it happens. `RELEASING.md` presents `--dry-run` as the first step of the normal
procedure, not as an optional extra.

This is a deliberate trade-off. The risk it accepts is that a bug in the CHANGELOG-rewriting
logic is caught by reading a diff rather than by an assertion. The mitigations are that
`release.sh` refuses to run on a dirty tree (so `git checkout .` always fully undoes a bad
release before the commit), and that `validate.py` runs both before the change and in CI after.

## One-time drift fix

Distinct from building the tooling, and done once:

1. Add an `## [Unreleased]` section and the missing `[0.2.0]` link reference to
   `plugins/django-crud-views/CHANGELOG.md`.
2. Tag `django-crud-views--v0.2.0` at commit `88a2814`, where 0.2.0 actually shipped.
3. Remove `version` from the plugin's `marketplace.json` entry.
4. Add `metadata.version: "1.0.0"` and create the root `CHANGELOG.md`.
5. Tag `marketplace--v1.0.0` at the resulting commit.

Tags are created locally and pushed by the repo owner, not automatically.

## Files

**New**

- `scripts/validate.py`
- `scripts/release.sh`
- `.github/workflows/validate.yml`
- `RELEASING.md`
- `CHANGELOG.md` (root, marketplace-level)

**Modified**

- `.claude-plugin/marketplace.json` — drop entry `version`, add `metadata.version`
- `plugins/django-crud-views/CHANGELOG.md` — add `[Unreleased]`, add `[0.2.0]` link
- `README.md` — step 4 of "Adding a new plugin" currently instructs bumping both manifests, which
  decision 1 makes wrong; replace it with a pointer to `RELEASING.md`

## Out of scope

- Publishing GitHub Releases from tags.
- Any automation that pushes to the remote.
- Versioning individual skills within a plugin. Per-feature `Available since X.Y.Z` markers in
  `SKILL.md` track the *upstream package's* releases and are unrelated to plugin versioning.
