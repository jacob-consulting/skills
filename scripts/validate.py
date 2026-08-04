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
        if not isinstance(version, str):
            error(manifest_path, f"version {version!r} is not a string")
        elif not SEMVER.match(version):
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
        elif not isinstance(version, str):
            error(MARKETPLACE, f"metadata.version {version!r} is not a string")
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
            if isinstance(source, dict):
                # A remote source (e.g. git-subdir): the plugin's files aren't in this
                # repo, so the local-directory checks below don't apply. The
                # no-'version'-key check above still ran.
                continue
            if not isinstance(source, str):
                error(MARKETPLACE, f"plugin entry {name!r} source {source!r} is not a string")
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
