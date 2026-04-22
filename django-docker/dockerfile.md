# Dockerfile Reference

## Stage overview

```
uv          ← pinned uv binary carrier (never used directly)
base        ← shared OS + uv + user + env vars
deps-prod   ← venv with prod group only (has gcc, builds uwsgi)
deps-test   ← venv with test group only (no gcc)
deps-dev    ← venv with ALL groups (bind-mounts submodules)
prod        ← final production image (libpcre3 runtime, no gcc)
test        ← runs pytest non-interactively
dev         ← bind-mounted source, runserver
```

## Complete Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.4.29

# ---------------------------------------------------------------------------
# Stage: uv binary carrier
# ---------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------------------------------------------------------------------------
# Stage: base
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bookworm AS base

COPY --from=uv /uv /uvx /usr/local/bin/

ARG APP_USER=app
ARG APP_UID=10001
ARG APP_GID=10001

RUN groupadd --system --gid "${APP_GID}" "${APP_USER}" \
 && useradd  --system --uid "${APP_UID}" --gid "${APP_GID}" \
             --create-home --shell /usr/sbin/nologin "${APP_USER}"

ARG APP_DIR=/opt/project
ARG VIRTUAL_ENV=/opt/venv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV} \
    VIRTUAL_ENV=${VIRTUAL_ENV} \
    PATH=${VIRTUAL_ENV}/bin:$PATH \
    PYTHONPATH=${APP_DIR}:${APP_DIR}/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR ${APP_DIR}

# ---------------------------------------------------------------------------
# Stage: deps-prod
# Compiles uwsgi (needs gcc + libpcre3-dev). Build tools stay in this stage.
# ---------------------------------------------------------------------------
FROM base AS deps-prod

RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpcre3-dev \
 && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv venv "${VIRTUAL_ENV}" \
 && uv sync --locked --no-install-project --no-default-groups --group prod

# ---------------------------------------------------------------------------
# Stage: deps-test
# ---------------------------------------------------------------------------
FROM base AS deps-test

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv venv "${VIRTUAL_ENV}" \
 && uv sync --locked --no-install-project --no-default-groups --group test

# ---------------------------------------------------------------------------
# Stage: deps-dev
# All dependency groups; bind-mounts submodules so editable paths resolve.
# ---------------------------------------------------------------------------
FROM base AS deps-dev

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=submodules,target=submodules \
    uv venv "${VIRTUAL_ENV}" \
 && uv sync --locked --no-install-project

# ---------------------------------------------------------------------------
# Stage: prod
# ---------------------------------------------------------------------------
FROM base AS prod

# Only the shared C runtime library; no compiler.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libpcre3 \
 && rm -rf /var/lib/apt/lists/*

COPY --from=deps-prod ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY . ${APP_DIR}

# ENV_FOR_DYNACONF selects the production overlay for collectstatic.
RUN ENV_FOR_DYNACONF=production python manage.py collectstatic --no-input

RUN chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
USER ${APP_USER}

EXPOSE 8000

CMD ["uwsgi", \
     "--http", "0.0.0.0:8000", \
     "--module", "project.wsgi", \
     "--processes", "4", \
     "--threads", "2", \
     "--static-map", "/static/=/opt/project/staticfiles"]

# ---------------------------------------------------------------------------
# Stage: test
# ---------------------------------------------------------------------------
FROM deps-test AS test

COPY . ${APP_DIR}

# Install the project package itself (not just its deps).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-default-groups --group test

RUN chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
USER ${APP_USER}

CMD ["pytest", "src/", "-v", "--tb=short", "--cov=src", "--cov-report=term-missing"]

# ---------------------------------------------------------------------------
# Stage: dev
# ---------------------------------------------------------------------------
FROM deps-dev AS dev

# Only metadata — actual src/ and project/ are bind-mounted by compose.
COPY --parents uv.lock pyproject.toml manage.py submodules ${APP_DIR}/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked \
 && chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

USER ${APP_USER}

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## Non-Obvious Decisions

### gcc only in deps-prod
`uwsgi` must be compiled from source. gcc and libpcre3-dev exist in `deps-prod` only.
The `prod` final image copies the pre-built venv and installs only `libpcre3` (runtime).

### `--no-install-project` in deps stages
The project package itself (your app code) isn't present yet when the venv is built.
`--no-install-project` prevents uv from trying to install it — the source arrives later via COPY or bind-mount.

### `--no-default-groups` in prod and test
Without this flag, uv installs all dependency groups. `--no-default-groups --group prod` installs ONLY prod (uwsgi). Same for test.

### No source copy in dev
Dev stage COPY only the metadata files needed for `uv sync --locked`.
The actual `src/` and `project/` directories are bind-mounted by compose so hot-reload works without rebuilding.

### Bind-mount submodules in deps-dev
`uv sync --locked` for the dev group resolves editable path dependencies (e.g., `./submodules/my-lib`).
The bind-mount makes the submodule source available during the build; it is NOT baked into the image.

### collectstatic before chown
`collectstatic` runs as root so it can write `staticfiles/`. The `chown` runs after, then the image drops to the non-root user.
