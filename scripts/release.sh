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

[[ "$VERSION" =~ ^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]] || die "version '${VERSION}' is not semver (X.Y.Z)"

[[ -z "$(git status --porcelain)" ]] || die "working tree is not clean; commit or stash first"

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
    if (!$seen && s/^## \[Unreleased\].*$/## [Unreleased]\n\n## [$ENV{NEW_VERSION}] \xe2\x80\x94 $ENV{TODAY}/) {
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
