# Versioning and Release Process Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the plugin version single-sourced in `plugin.json`, version the marketplace itself, and add a scripted, CI-guarded release process.

**Architecture:** A read-only checker (`scripts/validate.py`) owns every invariant and is the single place that knows what "valid" means. A release script (`scripts/release.sh`) calls the checker as a preflight, then mutates a version field and a changelog, commits, and tags — never pushing. CI runs only the checker.

**Tech Stack:** Python 3 + PyYAML (checker), Bash + jq + perl + git (release script), GitHub Actions (CI). No build system, no package manager, no test framework.

**Spec:** `docs/superpowers/specs/2026-08-04-versioning-design.md`

## Global Constraints

- A plugin's version lives **only** in `plugins/<name>/.claude-plugin/plugin.json`. Plugin entries in `marketplace.json` must never carry a `version` key.
- The marketplace's own version lives in `.claude-plugin/marketplace.json` → `metadata.version`.
- Tag format: `<plugin-name>--vX.Y.Z` for plugins, `marketplace--vX.Y.Z` for the marketplace.
- Changelog release headings use an em dash: `## [X.Y.Z] — YYYY-MM-DD`. Match this exactly; `validate.py` matches only the `## [X.Y.Z]` prefix, but the existing file uses em dashes and consistency matters.
- Today's date for changelog entries: **2026-08-04**.
- `release.sh` never runs `git push`. It prints the command and stops.
- `release.sh` does **not** require any particular branch. It does require a clean working tree.
- Releases URL base: `https://github.com/jacob-consulting/skills/releases/tag`
- Skill `description` frontmatter limit: **1024** characters.
- `validate.py` is read-only: it never writes files and never calls git.

---

### Task 1: The invariant checker

**Files:**
- Create: `scripts/validate.py`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: a CLI contract that Task 3 and Task 4 depend on — `python3 scripts/validate.py`, run from anywhere, exits `0` when all invariants hold and `1` otherwise, printing `error: <path>: <message>` lines to stderr. It locates the repo root from its own file path (`Path(__file__).resolve().parent.parent`), not from the working directory.

- [ ] **Step 1: Write the checker**

Create `scripts/validate.py`:

```python
#!/usr/bin/env python3
"""Validate marketplace and plugin manifests, changelogs, and skill frontmatter.

Read-only: never writes a file, never calls git. Exits 0 when every invariant
holds, 1 otherwise, printing one line per violation to stderr.

Run by CI, by scripts/release.sh as a preflight, and by hand.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    sys.exit("validate.py requires PyYAML. Install it with:  pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
MAX_DESCRIPTION = 1024

errors: list[str] = []


def error(path: Path, message: str) -> None:
    try:
        where = path.relative_to(REPO_ROOT)
    except ValueError:
        where = path
    errors.append(f"{where}: {message}")


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        error(path, "missing")
    except json.JSONDecodeError as exc:
        error(path, f"invalid JSON: {exc}")
    return None


def check_changelog(path: Path, version: str) -> None:
    """The changelog must document the version currently being shipped."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        error(path, "missing")
        return
    if not re.search(rf"^## \[{re.escape(version)}\]", text, re.MULTILINE):
        error(path, f"no '## [{version}]' section for the version being shipped")


def check_skill(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        error(path, "no YAML frontmatter")
        return
    end = text.find("\n---", 3)
    if end == -1:
        error(path, "frontmatter is not terminated by '---'")
        return
    try:
        meta = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        error(path, f"frontmatter is not valid YAML: {exc}")
        return
    if not isinstance(meta, dict):
        error(path, "frontmatter is not a mapping")
        return
    if not meta.get("name"):
        error(path, "frontmatter has no 'name'")
    description = meta.get("description")
    if not description:
        error(path, "frontmatter has no 'description'")
    elif not isinstance(description, str):
        error(path, "frontmatter 'description' is not a string")
    elif len(description) > MAX_DESCRIPTION:
        error(
            path,
            f"description is {len(description)} characters, limit is {MAX_DESCRIPTION}",
        )


def check_plugin(directory: Path):
    """Validate one plugin directory. Returns its manifest dict, or None."""
    manifest_path = directory / ".claude-plugin" / "plugin.json"
    manifest = load_json(manifest_path)
    if manifest is None:
        return None
    for field in ("name", "description", "version"):
        if not manifest.get(field):
            error(manifest_path, f"missing required field {field!r}")
    version = manifest.get("version")
    if version:
        if not SEMVER.match(version):
            error(manifest_path, f"version {version!r} is not semver (X.Y.Z)")
        else:
            check_changelog(directory / "CHANGELOG.md", version)
    for skill in sorted(directory.glob("skills/*/SKILL.md")):
        check_skill(skill)
    return manifest


def main() -> int:
    marketplace = load_json(MARKETPLACE)
    listed: set[Path] = set()

    if marketplace is not None:
        metadata = marketplace.get("metadata") or {}
        version = metadata.get("version")
        if not version:
            error(MARKETPLACE, "metadata.version is missing")
        elif not SEMVER.match(version):
            error(MARKETPLACE, f"metadata.version {version!r} is not semver (X.Y.Z)")
        else:
            check_changelog(REPO_ROOT / "CHANGELOG.md", version)

        for entry in marketplace.get("plugins", []):
            name = entry.get("name", "<unnamed>")
            if "version" in entry:
                error(
                    MARKETPLACE,
                    f"plugin entry {name!r} has a 'version' key; a plugin's version "
                    f"belongs only in its own plugin.json",
                )
            source = entry.get("source")
            if not source:
                error(MARKETPLACE, f"plugin entry {name!r} has no 'source'")
                continue
            directory = (REPO_ROOT / source).resolve()
            if not (directory / ".claude-plugin" / "plugin.json").is_file():
                error(
                    MARKETPLACE,
                    f"plugin entry {name!r} source {source!r} has no "
                    f".claude-plugin/plugin.json",
                )
                continue
            listed.add(directory)
            manifest = check_plugin(directory)
            if manifest and manifest.get("name") != name:
                error(
                    MARKETPLACE,
                    f"plugin entry {name!r} does not match its plugin.json name "
                    f"{manifest.get('name')!r}",
                )

    for manifest_path in sorted((REPO_ROOT / "plugins").glob("*/.claude-plugin/plugin.json")):
        directory = manifest_path.parent.parent.resolve()
        if directory not in listed:
            error(manifest_path, "plugin is not listed in .claude-plugin/marketplace.json")
            check_plugin(directory)

    for line in errors:
        print(f"error: {line}", file=sys.stderr)
    if errors:
        print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x scripts/validate.py
```

- [ ] **Step 3: Run it against the current repo and confirm it fails correctly**

Run: `python3 scripts/validate.py; echo "exit=$?"`

Expected: exit=1, with exactly these two errors (order may vary):

```
error: .claude-plugin/marketplace.json: metadata.version is missing
error: .claude-plugin/marketplace.json: plugin entry 'django-crud-views' has a 'version' key; a plugin's version belongs only in its own plugin.json
```

This is the point of running it now: the checker independently rediscovers the drift the spec describes. If it reports anything else — especially a `SKILL.md` or plugin `CHANGELOG.md` error — stop and investigate before continuing, because Task 2 only fixes these two.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate.py
git commit -m "feat: add validate.py invariant checker"
```

---

### Task 2: Fix the drift and cut marketplace 1.0.0

**Files:**
- Modify: `.claude-plugin/marketplace.json`
- Modify: `plugins/django-crud-views/CHANGELOG.md`
- Create: `CHANGELOG.md` (repo root)

**Interfaces:**
- Consumes: `python3 scripts/validate.py` from Task 1, as the acceptance check.
- Produces: a repo state where `validate.py` exits 0. Task 3's `release.sh` preflight depends on this, and on `.metadata.version` existing at the jq path `.metadata.version`.

- [ ] **Step 1: Remove the entry version and add the marketplace version**

Edit `.claude-plugin/marketplace.json`. Delete the `"version": "0.2.0",` line from the plugin entry, and add `"version": "1.0.0"` to `metadata`. The result:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "jacob-consulting",
  "owner": { "name": "Alexander Jacob", "email": "alexander.jacob@jacob-consulting.de" },
  "metadata": {
    "description": "Skills and plugins by Jacob Consulting",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "django-crud-views",
      "source": "./plugins/django-crud-views",
      "description": "Build Django CRUD interfaces with the django-crud-views package — ViewSets, tables, filters, forms, workflows, per-object permissions, and non-ORM resources.",
      "author": { "name": "Alexander Jacob", "email": "alexander.jacob@jacob-consulting.de" },
      "category": "development",
      "homepage": "https://github.com/jacob-consulting/skills"
    }
  ]
}
```

Note `metadata` is now a multi-line object. That is deliberate — it is the one object in this file that will keep changing, and `release.sh` rewrites its `version` in place.

- [ ] **Step 2: Create the marketplace changelog**

Create `CHANGELOG.md` at the repo root:

```markdown
# Changelog

All notable changes to the `jacob-consulting` marketplace are documented here — plugins added or
removed, and marketplace-level metadata. Each plugin keeps its own changelog under
`plugins/<name>/CHANGELOG.md`, versioned independently of this one.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
```

- [ ] **Step 3: Add `[Unreleased]` and the missing 0.2.0 link to the plugin changelog**

In `plugins/django-crud-views/CHANGELOG.md`, insert an `## [Unreleased]` section between the preamble and the 0.2.0 heading. Find:

```markdown
`Available since X.Y.Z` markers in the skill track the package's release history.

## [0.2.0] — 2026-08-04
```

Replace with:

```markdown
`Available since X.Y.Z` markers in the skill track the package's release history.

## [Unreleased]

## [0.2.0] — 2026-08-04
```

Then at the end of the file, find:

```markdown
[0.1.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.1.0
```

Replace with:

```markdown
[0.2.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.2.0
[0.1.0]: https://github.com/jacob-consulting/skills/releases/tag/django-crud-views--v0.1.0
```

- [ ] **Step 4: Run the checker and confirm it now passes**

Run: `python3 scripts/validate.py; echo "exit=$?"`

Expected:

```
All checks passed.
exit=0
```

- [ ] **Step 5: Commit**

```bash
git add .claude-plugin/marketplace.json CHANGELOG.md plugins/django-crud-views/CHANGELOG.md
git commit -m "feat: single-source plugin versions, version the marketplace at 1.0.0"
```

- [ ] **Step 6: Tag the two releases that already shipped**

`django-crud-views` 0.2.0 shipped in commit `88a2814` but was never tagged. Tag it where it actually landed, and tag the marketplace at the commit just made:

```bash
git tag -a django-crud-views--v0.2.0 88a2814 -m "django-crud-views v0.2.0"
git tag -a marketplace--v1.0.0 -m "jacob-consulting marketplace v1.0.0"
git tag --list
```

Expected: three tags — `django-crud-views--v0.1.0`, `django-crud-views--v0.2.0`, `marketplace--v1.0.0`.

Do **not** push. Pushing tags is the repo owner's call, and is listed at the end of this plan.

---

### Task 3: The release script

**Files:**
- Create: `scripts/release.sh`

**Interfaces:**
- Consumes: `python3 scripts/validate.py` (exit 0 = valid) from Task 1; the repo state from Task 2 (`.metadata.version` present, `## [Unreleased]` sections present in both changelogs).
- Produces: `scripts/release.sh <target> <version> [--dry-run]`, referenced by `RELEASING.md` and `README.md` in Task 4.

- [ ] **Step 1: Write the release script**

Create `scripts/release.sh`:

```bash
#!/usr/bin/env bash
#
# Cut a release: bump the version, roll the changelog, commit, and tag.
# Never pushes — publishing stays an explicit human action.
#
# usage: scripts/release.sh <target> <version> [--dry-run]
#
set -euo pipefail

usage() {
    cat <<'EOF'
usage: scripts/release.sh <target> <version> [--dry-run]

  target    a plugin name (e.g. django-crud-views), or the literal "marketplace"
  version   the new version, as semver (X.Y.Z)
  --dry-run apply every change, show the diff, then revert without committing
EOF
}

die() { echo "release: $*" >&2; exit 1; }

TARGET="${1:-}"
VERSION="${2:-}"
DRY_RUN=false

if [[ -z "$TARGET" || -z "$VERSION" ]]; then usage >&2; exit 2; fi
if [[ -n "${3:-}" ]]; then
    [[ "$3" == "--dry-run" ]] || { echo "release: unknown argument: $3" >&2; usage >&2; exit 2; }
    DRY_RUN=true
fi

command -v jq   >/dev/null || die "jq is required but not on PATH"
command -v perl >/dev/null || die "perl is required but not on PATH"

cd "$(git rev-parse --show-toplevel)"

RELEASES_URL="https://github.com/jacob-consulting/skills/releases/tag"

if [[ "$TARGET" == "marketplace" ]]; then
    MANIFEST=".claude-plugin/marketplace.json"
    CHANGELOG="CHANGELOG.md"
    TAG="marketplace--v${VERSION}"
    VERSION_PATH=".metadata.version"
else
    MANIFEST="plugins/${TARGET}/.claude-plugin/plugin.json"
    CHANGELOG="plugins/${TARGET}/CHANGELOG.md"
    TAG="${TARGET}--v${VERSION}"
    VERSION_PATH=".version"
    [[ -f "$MANIFEST" ]] || die "no such plugin: ${TARGET} (expected ${MANIFEST})"
fi

# ---- preflight -------------------------------------------------------------

[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "version '${VERSION}' is not semver (X.Y.Z)"

git diff --quiet && git diff --cached --quiet \
    || die "working tree is not clean; commit or stash first"

echo "==> validating"
python3 scripts/validate.py || die "validate.py failed; fix the problems above first"

CURRENT="$(jq -r "${VERSION_PATH}" "$MANIFEST")"
[[ "$CURRENT" != "null" ]] || die "${MANIFEST} has no ${VERSION_PATH}"

if [[ "$CURRENT" == "$VERSION" ]]; then
    die "${TARGET} is already at ${VERSION}"
fi
if [[ "$(printf '%s\n%s\n' "$CURRENT" "$VERSION" | sort -V | tail -n1)" != "$VERSION" ]]; then
    die "${VERSION} is not greater than the current version ${CURRENT}"
fi

git rev-parse -q --verify "refs/tags/${TAG}" >/dev/null \
    && die "tag ${TAG} already exists"

awk '
    /^## \[Unreleased\]/ { inside = 1; next }
    /^## \[/            { inside = 0 }
    inside && NF        { found = 1 }
    END                 { exit !found }
' "$CHANGELOG" || die "${CHANGELOG} has no '## [Unreleased]' section with content to release"

# ---- mutate ----------------------------------------------------------------

# Rewrite the version with a key-anchored substitution rather than `jq`, which
# would reflow the hand-formatted inline objects in these manifests and bury a
# one-line release under cosmetic churn. Assert the key is unique first.
occurrences="$(grep -c '"version"[[:space:]]*:' "$MANIFEST" || true)"
[[ "$occurrences" -eq 1 ]] \
    || die "expected exactly one \"version\" key in ${MANIFEST}, found ${occurrences}"

NEW_VERSION="$VERSION" perl -pi -e 's/("version"\s*:\s*")[^"]*(")/$1$ENV{NEW_VERSION}$2/' "$MANIFEST"

WROTE="$(jq -r "${VERSION_PATH}" "$MANIFEST")"
[[ "$WROTE" == "$VERSION" ]] \
    || die "failed to write the version into ${MANIFEST} (found '${WROTE}')"

# Roll [Unreleased] into a dated release section, leaving a fresh empty one.
NEW_VERSION="$VERSION" TODAY="$(date +%F)" perl -pi -e '
    if (!$seen && s/^## \[Unreleased\].*$/## [Unreleased]\n\n## [$ENV{NEW_VERSION}] \x{2014} $ENV{TODAY}/) {
        $seen = 1;
    }
' "$CHANGELOG"

printf '[%s]: %s/%s\n' "$VERSION" "$RELEASES_URL" "$TAG" >> "$CHANGELOG"

echo "==> re-validating"
python3 scripts/validate.py || die "the release left the repo invalid (see above); run 'git checkout -- .' to undo"

# ---- report ----------------------------------------------------------------

echo
echo "==> ${TARGET}: ${CURRENT} -> ${VERSION}   (tag ${TAG})"
echo
git --no-pager diff -- "$MANIFEST" "$CHANGELOG"
echo

if [[ "$DRY_RUN" == true ]]; then
    git checkout -- "$MANIFEST" "$CHANGELOG"
    echo "==> dry run: reverted, nothing committed"
    exit 0
fi

git add -- "$MANIFEST" "$CHANGELOG"
git commit -q -m "release(${TARGET}): v${VERSION}"
git tag -a "$TAG" -m "${TARGET} v${VERSION}"

echo "==> committed and tagged"
echo
echo "    next:  git push origin $(git rev-parse --abbrev-ref HEAD) --follow-tags"
```

Two details worth understanding before running it:

- `\x{2014}` in the perl substitution is the em dash, written as an escape so the script file stays pure ASCII and cannot be corrupted by an editor re-encoding it.
- The dry run works by making the real changes, showing the real diff, then running `git checkout --` on exactly the two files it touched. This is safe *because* the preflight already refused to run on a dirty tree — there is nothing else to lose.

- [ ] **Step 2: Make it executable**

```bash
chmod +x scripts/release.sh
```

- [ ] **Step 3: Commit the script**

Commit before exercising the guards. The script's own preflight refuses to run on a dirty tree, so
an uncommitted `release.sh` would make every check below fail with "working tree is not clean"
rather than the message being tested.

```bash
git add scripts/release.sh
git commit -m "feat: add release.sh"
```

- [ ] **Step 4: Verify the preflight rejects a version that isn't an increase**

Run: `scripts/release.sh django-crud-views 0.1.0; echo "exit=$?"`

Expected: exit=1 with

```
release: 0.1.0 is not greater than the current version 0.2.0
```

- [ ] **Step 5: Verify the preflight rejects an empty Unreleased section**

The plugin's `[Unreleased]` section is empty right now, which is exactly the case this check exists
for.

Run: `scripts/release.sh django-crud-views 0.3.0; echo "exit=$?"`

Expected: exit=1 with

```
release: plugins/django-crud-views/CHANGELOG.md has no '## [Unreleased]' section with content to release
```

- [ ] **Step 6: Verify the preflight rejects a dirty working tree**

Dirty the tree, confirm the guard fires, then revert:

```bash
printf '\n' >> CHANGELOG.md
scripts/release.sh marketplace 1.1.0 --dry-run; echo "exit=$?"
git checkout -- CHANGELOG.md
git status --porcelain
```

Expected: exit=1 with `release: working tree is not clean; commit or stash first`, then
`git status --porcelain` prints nothing.

- [ ] **Step 7: Record the tooling in the marketplace changelog**

The script and checker are marketplace-level changes, so they belong in the root changelog's `[Unreleased]` section. Edit `CHANGELOG.md`, replacing:

```markdown
## [Unreleased]
```

with:

```markdown
## [Unreleased]

### Added
- `scripts/validate.py` — checks manifests, changelogs, and skill frontmatter. Read-only.
- `scripts/release.sh` — bumps a version, rolls the changelog, commits, and tags. Never pushes.
```

- [ ] **Step 8: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: record release tooling in the marketplace changelog"
```

---

### Task 4: CI, RELEASING.md, and the stale README instruction

**Files:**
- Create: `.github/workflows/validate.yml`
- Create: `RELEASING.md`
- Modify: `README.md` (the "Adding a new plugin" section, steps 3 and 4)

**Interfaces:**
- Consumes: `scripts/validate.py` (Task 1) and `scripts/release.sh` (Task 3), by path and CLI signature.
- Produces: no code interface. This is the last task before the final release.

- [ ] **Step 1: Add the CI workflow**

Create `.github/workflows/validate.yml`:

```yaml
name: validate

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install pyyaml
      - run: python3 scripts/validate.py
```

- [ ] **Step 2: Write RELEASING.md**

Create `RELEASING.md`:

````markdown
# Releasing

Two things in this repo are versioned, on their own schedules.

| Thing | Version lives in | Changelog | Tag |
|---|---|---|---|
| A plugin | `plugins/<name>/.claude-plugin/plugin.json` → `version` | `plugins/<name>/CHANGELOG.md` | `<name>--vX.Y.Z` |
| The marketplace | `.claude-plugin/marketplace.json` → `metadata.version` | `CHANGELOG.md` | `marketplace--vX.Y.Z` |

A plugin release does not bump the marketplace version, and vice versa.

**A plugin's version appears in exactly one file.** Plugin entries in `marketplace.json` carry no
`version` key — `scripts/validate.py` fails if one appears. This mirrors Anthropic's
`claude-plugins-official` marketplace, whose plugin entries are versionless.

## Cutting a release

Write what changed into the `## [Unreleased]` section of the relevant changelog as you work, then:

```bash
scripts/release.sh <target> <version> --dry-run   # inspect the diff
scripts/release.sh <target> <version>             # commit and tag
git push origin <branch> --follow-tags            # publish
```

`<target>` is a plugin name or the literal `marketplace`. For example:

```bash
scripts/release.sh django-crud-views 0.3.0 --dry-run
scripts/release.sh marketplace 1.1.0 --dry-run
```

**Always dry-run first.** There is no test suite for the release script; the dry run is the
verification step. It applies every change, prints the exact diff, then reverts — so what you
review is what you would have committed.

The script refuses to run unless the working tree is clean, `validate.py` passes, the new version
is greater than the current one, the tag is free, and the changelog has unreleased content. It
does not care which branch you are on. It never pushes.

## What the release script does

1. Rewrites the version in the manifest.
2. Turns `## [Unreleased]` into `## [X.Y.Z] — <today>` and opens a fresh empty `## [Unreleased]`.
3. Appends the `[X.Y.Z]:` link reference pointing at the release tag.
4. Commits as `release(<target>): v<version>` and creates an annotated tag.
5. Prints the push command and stops.

## What CI checks

`.github/workflows/validate.yml` runs `scripts/validate.py` on every pull request and every push
to `main`. It verifies that:

- every `plugin.json` parses and has a `name`, `description`, and semver `version`
- every marketplace entry resolves to a real plugin directory, its name matches that plugin's
  manifest, and it carries no `version` key
- every plugin on disk is listed in the marketplace
- each changelog has a section for the version currently shipping
- `metadata.version` is semver and the root changelog documents it
- every `SKILL.md` has valid YAML frontmatter with a `name` and a `description` of at most 1024
  characters

Run it locally the same way CI does:

```bash
pip install pyyaml      # once
python3 scripts/validate.py
```

## Recovering from drift

`validate.py` names the file and the problem for anything it can detect. Two things it cannot see,
because they live in git rather than in a file:

- **A release that was never tagged.** Compare `git tag --list` against the changelog headings.
  Tag the commit where the version actually landed: `git tag -a <name>--vX.Y.Z <sha> -m "..."`.
- **A tag that was never pushed.** `git push origin --follow-tags` pushes tags reachable from the
  branch you are pushing; a tag on an older commit needs `git push origin <tag>` explicitly.
````

- [ ] **Step 3: Fix the stale README instructions**

`README.md` currently tells the reader to duplicate the version, which is now wrong and would be
caught by CI. In the "Adding a new plugin" section, find steps 3 and 4:

```markdown
3. Add an entry to `plugins` in `.claude-plugin/marketplace.json` with a
   `source: "./plugins/<name>"` (a plugin in another repo can instead use a `git-subdir` source).
4. Bump the plugin's `version` in both `plugin.json` and the marketplace entry on each release.
```

Replace them with:

```markdown
3. Add an entry to `plugins` in `.claude-plugin/marketplace.json` with a
   `source: "./plugins/<name>"` (a plugin in another repo can instead use a `git-subdir` source).
   Do **not** put a `version` in the entry — it belongs only in the plugin's own `plugin.json`.
4. Add a `plugins/<name>/CHANGELOG.md` with a section for the plugin's current version.
5. Run `python3 scripts/validate.py` to check all of the above, and see
   [RELEASING.md](RELEASING.md) for how to cut releases.
```

- [ ] **Step 4: Verify everything still passes**

Run: `python3 scripts/validate.py; echo "exit=$?"`

Expected:

```
All checks passed.
exit=0
```

- [ ] **Step 5: Record the docs and CI in the marketplace changelog**

Edit `CHANGELOG.md`, extending the `[Unreleased]` section written in Task 3 to read:

```markdown
## [Unreleased]

### Added
- `scripts/validate.py` — checks manifests, changelogs, and skill frontmatter. Read-only.
- `scripts/release.sh` — bumps a version, rolls the changelog, commits, and tags. Never pushes.
- `RELEASING.md` documenting the version topology and the release procedure.
- A `validate` GitHub Actions workflow running the checker on pull requests and pushes to `main`.

### Changed
- `README.md` no longer instructs bumping the version in two files.
```

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/validate.yml RELEASING.md README.md CHANGELOG.md
git commit -m "ci: validate manifests on PRs; document the release process"
```

---

### Task 5: Use the script to release the marketplace

The first real use of `release.sh` is releasing the tooling it is part of. If it works here, it works.

**Files:**
- Modify: `.claude-plugin/marketplace.json` (by script)
- Modify: `CHANGELOG.md` (by script)

**Interfaces:**
- Consumes: `scripts/release.sh` from Task 3, and the `[Unreleased]` content written in Task 4.
- Produces: the final repo state.

- [ ] **Step 1: Dry-run the release**

Run: `scripts/release.sh marketplace 1.1.0 --dry-run`

Expected: a diff showing `metadata.version` going `1.0.0` → `1.1.0`, the `## [Unreleased]` heading
becoming `## [1.1.0] — 2026-08-04` with a fresh empty `## [Unreleased]` above it, and a
`[1.1.0]:` link reference appended — followed by `==> dry run: reverted, nothing committed`.

Then confirm nothing survived: `git status --porcelain` should print nothing.

- [ ] **Step 2: Cut the release for real**

Run: `scripts/release.sh marketplace 1.1.0`

Expected: the same diff, then `==> committed and tagged` and a printed push command.

- [ ] **Step 3: Verify the result**

```bash
python3 scripts/validate.py
git log --oneline -1
git tag --list
```

Expected: `All checks passed.`; a `release(marketplace): v1.1.0` commit; four tags —
`django-crud-views--v0.1.0`, `django-crud-views--v0.2.0`, `marketplace--v1.0.0`,
`marketplace--v1.1.0`.

- [ ] **Step 4: Hand the push to the repo owner**

Nothing in this plan pushes. Report the exact commands and stop:

```bash
git push origin main --follow-tags
git push origin django-crud-views--v0.2.0    # on an older commit; --follow-tags misses it
```

The second command is needed because `--follow-tags` only pushes annotated tags reachable from the
commits being pushed, and `django-crud-views--v0.2.0` sits on `88a2814`, which is already on the
remote.

---

## Verification summary

After all five tasks:

| Check | Command | Expected |
|---|---|---|
| Invariants hold | `python3 scripts/validate.py` | `All checks passed.` |
| Version is single-sourced | `jq '.plugins[0] \| has("version")' .claude-plugin/marketplace.json` | `false` |
| Marketplace is versioned | `jq -r '.metadata.version' .claude-plugin/marketplace.json` | `1.1.0` |
| Plugin version untouched | `jq -r '.version' plugins/django-crud-views/.claude-plugin/plugin.json` | `0.2.0` |
| Releases are tagged | `git tag --list` | 4 tags |
| Release script guards work | `scripts/release.sh django-crud-views 0.1.0` | exits 1, "not greater than" |
