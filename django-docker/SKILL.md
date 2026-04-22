---
name: django-docker
description: Use when creating a Django project from scratch with Docker, migrating an existing Django project to this multi-stage Docker blueprint, adding dynaconf for environment-specific settings, adding git submodule libraries as editable packages, or adding default Taskfile tasks
---

# Django Docker Blueprint

## Overview

A multi-stage Django Dockerfile blueprint using `uv` for dependency management and `dynaconf` for environment-specific settings. Produces minimal, reproducible images for dev, test, and prod.

## Reference Files

- `dockerfile.md` — complete Dockerfile (5 stages) + non-obvious decisions
- `compose.md` — docker-compose.yml (dev), docker-compose.test.yml, docker-compose.prod.yml
- `settings.md` — dynaconf integration in settings.py + YAML overlay files
- `pyproject.md` — pyproject.toml with PEP 735 dependency groups
- `taskfile.md` — taskfile.yaml + tasks/ directory
- `submodules.md` — git submodule as editable package

## Critical Non-Obvious Rules

**Always check these first — they cause silent failures:**

1. **`ENV_FOR_DYNACONF`** is the environment selector (not `DJANGO_ENV`, `DJANGO_ENVIRONMENT`, or any other name). Set it in every Compose `environment:` block.

2. **dynaconf settings_files use SHORT paths** — `"settings.yaml"` not `"project/settings.yaml"`. DjangoDynaconf uses the calling `settings.py` file's directory as `root_path`, so the YAML files sit alongside `settings.py`.

3. **`environments=False`** in DjangoDynaconf — YAML files are flat (no `[default]`/`[production]` sections). One file per environment.

4. **Test compose needs an explicit `image:` tag** — without it, Docker auto-generates the same image name as dev compose and reuses the dev image for tests, causing "No module named 'project'" or stale code errors.

5. **`.secrets.yaml` in BOTH `.gitignore` AND `.dockerignore`** — gitignore prevents committing it; dockerignore prevents baking it into the image layer.

6. **`${DJANGO_SECRET_KEY:?message}`** in prod compose (not bare `${DJANGO_SECRET_KEY}`) — the `:?` syntax makes Compose fail fast with a clear error when the variable is unset.

7. **uwsgi goes in the `prod` dependency group only** — it requires gcc to compile; other stages don't install it and must not have gcc installed.
