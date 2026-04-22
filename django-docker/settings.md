# Dynaconf Settings Reference

## File Layout

```
project/
  settings.py            ← Django settings + DjangoDynaconf hook
  settings.yaml          ← shared defaults (committed, no secrets)
  settings.development.yaml
  settings.testing.yaml
  settings.production.yaml
  .secrets.yaml          ← GITIGNORED + DOCKERIGNORED (never committed)
  .secrets.yaml.example  ← template (committed, no real secrets)
```

## settings.py

```python
import os
from pathlib import Path

from dynaconf import DjangoDynaconf  # noqa: F401 – imported for side effects

BASE_DIR = Path(__file__).resolve().parent.parent

# Safety-net placeholders – dynaconf overwrites these from YAML / env vars.
SECRET_KEY = "django-insecure-placeholder-replaced-by-dynaconf"
DEBUG = False
ALLOWED_HOSTS: list[str] = []

# ... INSTALLED_APPS, MIDDLEWARE, TEMPLATES, etc. ...

_env = os.environ.get("ENV_FOR_DYNACONF", "development").lower()

DjangoDynaconf(
    django_settings_module=__name__,
    settings_files=[
        "settings.yaml",            # shared defaults
        f"settings.{_env}.yaml",    # environment overlay
        ".secrets.yaml",            # local secrets (git-ignored)
    ],
    envvar_prefix="DJANGO",
    environments=False,
    load_dotenv=False,
)
```

### Critical: SHORT settings_files paths

DjangoDynaconf uses the **calling file's directory** as `root_path`.
Since `settings.py` lives in `project/`, write `"settings.yaml"` — not `"project/settings.yaml"`.
Using the longer path causes FileNotFoundError silently (dynaconf may ignore missing files).

### `environments=False`

The YAML files are flat — no `[default]` / `[production]` section headers.
`environments=False` tells dynaconf to read the file as a flat key-value store.
Without it, dynaconf expects sectioned TOML-style blocks and silently loads nothing.

## settings.yaml (shared defaults)

```yaml
debug: false
secret_key: "django-insecure-change-me-in-production"
allowed_hosts:
  - "localhost"
  - "127.0.0.1"
databases:
  default:
    ENGINE: "django.db.backends.sqlite3"
    NAME: "@format {this.BASE_DIR}/db.sqlite3"
email_backend: "django.core.mail.backends.console.EmailBackend"
caches:
  default:
    BACKEND: "django.core.cache.backends.locmem.LocMemCache"
```

## settings.development.yaml

```yaml
debug: true
secret_key: "django-insecure-dev-only-do-not-use-in-production"
allowed_hosts:
  - "*"
logging:
  version: 1
  disable_existing_loggers: false
  handlers:
    console:
      class: "logging.StreamHandler"
  root:
    handlers: ["console"]
    level: "DEBUG"
  loggers:
    django.db.backends:
      handlers: ["console"]
      level: "DEBUG"
      propagate: false
```

## settings.testing.yaml

```yaml
debug: false
secret_key: "django-insecure-test-fixed-key-do-not-use-elsewhere"
allowed_hosts:
  - "localhost"
  - "127.0.0.1"
  - "testserver"           # Django test client uses this hostname
databases:
  default:
    ENGINE: "django.db.backends.sqlite3"
    NAME: ":memory:"       # fresh DB each run, no disk I/O
caches:
  default:
    BACKEND: "django.core.cache.backends.dummy.DummyCache"
email_backend: "django.core.mail.backends.locmem.EmailBackend"
password_hashers:
  - "django.contrib.auth.hashers.MD5PasswordHasher"  # ~100x faster than bcrypt
```

## settings.production.yaml

```yaml
debug: false
allowed_hosts:
  - "your-domain.com"
  - "www.your-domain.com"
secure_ssl_redirect: true
secure_hsts_seconds: 31536000
secure_hsts_include_subdomains: true
secure_hsts_preload: true
session_cookie_secure: true
csrf_cookie_secure: true
secure_proxy_ssl_header:
  - "HTTP_X_FORWARDED_PROTO"
  - "https"
```

## .secrets.yaml (gitignored)

```yaml
secret_key: "actual-long-random-hex-token-here"
```

Generate a key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

## .secrets.yaml.example (committed)

```yaml
# Copy this file to .secrets.yaml and fill in real values.
# .secrets.yaml is git-ignored and docker-ignored — never commit it.
secret_key: "replace-with-output-of: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'"
```

## .dockerignore entry (required)

```
project/.secrets.yaml
```

Without this entry, `COPY . ${APP_DIR}` in the prod and test stages bakes the secrets file
into the image layer, where it can be read by anyone with image access.

## .gitignore entry (required)

```
project/.secrets.yaml
```

## Testing dynaconf settings

```python
# src/demo/tests/test_settings.py
from django.conf import settings

def test_allowed_hosts_does_not_contain_wildcard_in_testing():
    # pytest-django does not override ALLOWED_HOSTS — genuine dynaconf signal
    assert "*" not in settings.ALLOWED_HOSTS

def test_debug_is_false_in_testing():
    # pytest-django forces DEBUG=False — this always passes; prefer ALLOWED_HOSTS test
    assert settings.DEBUG is False

def test_secret_key_is_not_placeholder():
    assert settings.SECRET_KEY != "django-insecure-placeholder-replaced-by-dynaconf"
```

Note: `pytest-django` unconditionally forces `DEBUG=False`, so testing DEBUG is a vacuous assertion.
`ALLOWED_HOSTS` is the meaningful signal that dynaconf loaded the testing overlay.

## Environment variable overrides

Any setting in the YAML files can be overridden at runtime with a `DJANGO_`-prefixed env var:

```bash
DJANGO_SECRET_KEY=abc123 docker compose up
DJANGO_ALLOWED_HOSTS=mysite.com docker compose up
DJANGO_DEBUG=true docker compose up
```

Keys are case-insensitive in dynaconf; `DJANGO_SECRET_KEY` sets `SECRET_KEY`.
