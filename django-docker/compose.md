# Docker Compose Reference

## Three Compose Files

| File | Target stage | When used |
|------|-------------|-----------|
| `docker-compose.yml` | `dev` | Local development (`task dc:up`) |
| `docker-compose.test.yml` | `test` | CI / automated tests (`task dc:test`) |
| `docker-compose.prod.yml` | `prod` | Production deployment (`task dc:prod-up`) |

---

## docker-compose.yml (dev)

```yaml
# docker-compose.yml – development environment
#
# Start with:  docker compose up --build

services:

  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: dev
      args:
        # Match UID/GID to the host developer so bind-mounted files are
        # owned correctly on both sides.  Override in .env if needed.
        APP_UID: ${UID:-1000}
        APP_GID: ${GID:-1000}
    environment:
      ENV_FOR_DYNACONF: development
    volumes:
      - ./project:/opt/project/project
      - ./src:/opt/project/src
      - ./db.sqlite3:/opt/project/db.sqlite3
    ports:
      - "8000:8000"
    stdin_open: true
    tty: true
```

---

## docker-compose.test.yml

```yaml
# docker-compose.test.yml – CI / automated test runner
#
# Run with:  docker compose -f docker-compose.test.yml up --build --exit-code-from app

services:

  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: test
    # REQUIRED: explicit image name prevents Docker from reusing the dev image.
    # Without this, compose auto-generates the same name as docker-compose.yml
    # and the cached dev image (missing source) is used for tests.
    image: ${IMAGE_NAME:-myapp}-test:${IMAGE_TAG:-latest}
    environment:
      ENV_FOR_DYNACONF: testing
    command: >
      pytest src/ -v --tb=short
      --cov=src --cov-report=term-missing --cov-report=xml:/reports/coverage.xml
    volumes:
      - ./reports:/reports
```

### Critical: explicit `image:` tag

Without `image:`, Docker Compose generates the image name from the project directory name.
Both `docker-compose.yml` and `docker-compose.test.yml` would produce the same name.
The dev image (built earlier, with bind-mounts — no source baked in) would be reused for tests,
causing `ModuleNotFoundError: No module named 'project'`.

---

## docker-compose.prod.yml

```yaml
# docker-compose.prod.yml – production deployment
#
# REQUIRED env vars:
#   DJANGO_SECRET_KEY – long random string; never commit to VCS

services:

  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: prod
    image: ${IMAGE_NAME:-myapp}-prod:${IMAGE_TAG:-latest}
    restart: unless-stopped
    environment:
      ENV_FOR_DYNACONF: production

      # :? syntax makes compose fail fast with a clear error if SECRET_KEY is unset.
      # Bare ${DJANGO_SECRET_KEY} silently passes an empty string.
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?DJANGO_SECRET_KEY must be set for production}

      # Inject extra allowed hosts at runtime (comma-separated).
      DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:-}

    ports:
      - "8000:8000"

    volumes:
      - ./db.sqlite3:/opt/project/db.sqlite3
```

---

## ENV_FOR_DYNACONF placement

Every compose file sets `ENV_FOR_DYNACONF` in `environment:`. This tells dynaconf which YAML overlay to load:

- dev → `settings.development.yaml`
- testing → `settings.testing.yaml`
- production → `settings.production.yaml`

**Do not use `DJANGO_ENV` — dynaconf looks for `ENV_FOR_DYNACONF`.**
