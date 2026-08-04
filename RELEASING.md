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
