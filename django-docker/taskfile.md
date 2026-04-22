# Taskfile Reference

## Directory Structure

```
taskfile.yaml          ← root (includes only, no direct tasks)
tasks/
  docker_compose.yaml  ← dc: namespace
  manage.yaml          ← m: namespace
  uv.yaml              ← uv: namespace
```

## taskfile.yaml (root)

```yaml
# yaml-language-server: $schema=https://taskfile.dev/schema.json

version: '3'

includes:
  dc: ./tasks/docker_compose.yaml
  uv: ./tasks/uv.yaml
  m: ./tasks/manage.yaml

vars:

tasks:
```

## tasks/docker_compose.yaml

```yaml
version: '3'

env:
  DJANGO_SECRET_KEY: "your-secret-key"   # satisfies :? check in prod compose for local use

tasks:

  build:
    desc: Build the docker image(s)
    cmd: docker compose build

  build-no-cache:
    desc: Build the docker image(s) without using the cache
    cmd: docker compose build --no-cache

  bash:
    desc: Run a bash shell inside the app container
    cmd: docker compose run --rm app bash

  logs:
    desc: Show logs from the app container
    cmd: docker compose logs -f app

  logs-all:
    desc: Show logs from all containers
    cmd: docker compose logs -f

  up:
    desc: Start the application in detached mode
    cmd: docker compose up -d --remove-orphans

  down:
    desc: Stop and remove containers, networks, images, and volumes
    cmd: docker compose down --volumes --remove-orphans

  restart:
    desc: Restart the application
    cmds:
      - docker compose down --remove-orphans
      - docker compose up -d --remove-orphans
      - sleep 3
      - docker compose ps

  ps:
    desc: List containers
    cmd: docker compose ps

  test:
    desc: Run tests with coverage inside the test container
    cmds:
      - docker compose -f docker-compose.test.yml build --no-cache
      - docker compose -f docker-compose.test.yml run --rm app

  prod-build:
    desc: Build application in production mode
    cmd: docker compose -f docker-compose.prod.yml build --no-cache

  prod-up:
    desc: Start the application in production mode (detached)
    cmd: docker compose -f docker-compose.prod.yml up -d --remove-orphans

  prod-down:
    desc: Stop and remove production containers
    cmd: docker compose -f docker-compose.prod.yml down --volumes --remove-orphans
```

Note: `dc:test` uses `build --no-cache` to ensure the test image is always fresh.

## tasks/manage.yaml

```yaml
version: '3'

vars:
  MANAGE: docker compose run --rm app python ./manage.py

tasks:

  migrate:
    cmds:
      - "{{ .MANAGE }} migrate"

  makemigrations:
    cmds:
      - "{{ .MANAGE }} makemigrations"

  collectstatic:
    cmds:
      - "{{ .MANAGE }} collectstatic --no-input"

  superuser:
    cmds:
      - "DJANGO_SUPERUSER_PASSWORD=foobar4711 {{ .MANAGE }} createsuperuser --username admin --email admin@example.com --noinput"
    ignore_error: true
```

## tasks/uv.yaml

```yaml
version: '3'

tasks:

  lock:
    desc: Lock dependencies, update uv.lock
    cmd: uv lock

  upgrade:
    desc: Upgrade and lock dependencies, update uv.lock
    cmd: uv lock --upgrade
```

## Common Commands

```bash
task dc:up           # start dev environment
task dc:down         # stop and clean up
task dc:test         # run full test suite in container
task dc:logs         # tail app logs
task dc:bash         # shell into running container
task m:migrate       # run database migrations
task m:makemigrations
task m:superuser     # create admin user (password: foobar4711)
task uv:lock         # update lock file
task uv:upgrade      # upgrade all dependencies
```
