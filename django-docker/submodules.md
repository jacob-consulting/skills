# Git Submodule as Editable Package

Use this pattern when developing a library alongside this Django project and you want
import changes to reflect immediately without reinstalling.

## Setup Steps

### 1. Add the submodule

```bash
git submodule add https://github.com/org/my-lib.git submodules/my-lib
git submodule update --init --recursive
```

### 2. Tell uv to use the local editable checkout

In `pyproject.toml`, add a `[tool.uv.sources]` section:

```toml
[tool.uv]
[tool.uv.sources]
my-lib = { path = "./submodules/my-lib", editable = true }
```

Then add `my-lib` to `[project.dependencies]` so it is installed in all stages:

```toml
dependencies = [
    "django>=5.0,<6.0",
    "dynaconf>=3.2",
    "my-lib",               # resolved from submodules/ via uv.sources
]
```

Update the lock file:

```bash
uv lock
```

### 3. Dockerfile: bind-mount submodules in deps-dev

The `deps-dev` stage bind-mounts the submodules directory so that `uv sync --locked` can
resolve the editable path during the build:

```dockerfile
FROM base AS deps-dev

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=submodules,target=submodules \
    uv venv "${VIRTUAL_ENV}" \
 && uv sync --locked --no-install-project
```

The bind-mount is only needed during the build; submodule source is NOT baked into the image.

### 4. Dev compose: bind-mount submodules at runtime

In `docker-compose.yml`, mount the submodule source so changes are picked up by runserver:

```yaml
volumes:
  - ./project:/opt/project/project
  - ./src:/opt/project/src
  - ./submodules/my-lib:/opt/project/submodules/my-lib  # editable source
  - ./db.sqlite3:/opt/project/db.sqlite3
```

### 5. Dev stage: COPY submodules metadata

The dev stage copies submodules/ so that `uv sync --locked` (which runs at build time to
install the project editable) can find the path dependency:

```dockerfile
FROM deps-dev AS dev

COPY --parents uv.lock pyproject.toml manage.py submodules ${APP_DIR}/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked \
 && chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
```

## Checking Submodule Status

```bash
git submodule status          # show current commit for each submodule
git submodule update --remote # pull latest from each submodule's remote
```

## Multiple Submodules

Add each submodule the same way. The `submodules/` directory holds all of them:

```
submodules/
  my-lib/
  another-lib/
```

All are covered by the single bind-mount `--mount=type=bind,source=submodules,target=submodules`
in the Dockerfile.

## Removing a Submodule

```bash
git submodule deinit submodules/my-lib
git rm submodules/my-lib
rm -rf .git/modules/submodules/my-lib
```

Remove the corresponding `[tool.uv.sources]` entry and run `uv lock` again.
