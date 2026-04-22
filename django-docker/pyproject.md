# pyproject.toml Reference

## Complete Template

```toml
[project]
name = "my-django-project"
version = "0.1.0"
requires-python = ">=3.12"
# Core runtime dependencies – installed in every image target.
# dynaconf is a runtime dep (used in settings.py).
dependencies = [
    "django>=5.0,<6.0",
    "dynaconf>=3.2",
]

# ---------------------------------------------------------------------------
# Dependency groups (PEP 735)
#
# Each group maps to one Dockerfile stage:
#   prod  → deps-prod  (WSGI server; compiled from source with gcc)
#   test  → deps-test  (pytest + plugins)
#   dev   → deps-dev   (linters, debugger; includes test group)
# ---------------------------------------------------------------------------

[dependency-groups]

prod = [
    # uwsgi is compiled from source in deps-prod (gcc+libpcre3-dev available).
    # Only libpcre3 runtime lib is needed in the final prod image.
    "uwsgi>=2.0",
]

test = [
    "pytest>=8.0",
    "pytest-django>=4.8",
    "pytest-cov>=5.0",
    "factory-boy>=3.3",
]

dev = [
    { include-group = "test" },   # developers can also run tests
    "django-debug-toolbar>=4.3",
    "ipython>=8.0",
    "ruff>=0.5",
    "mypy>=1.10",
    "django-stubs>=5.0",
]

# ---------------------------------------------------------------------------
# uv configuration
# ---------------------------------------------------------------------------

[tool.uv]
# Uncomment to use a local checkout as an editable install (see submodules.md):
# [tool.uv.sources]
# my-lib = { path = "./submodules/my-lib", editable = true }

# ---------------------------------------------------------------------------
# pytest
# ---------------------------------------------------------------------------

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "project.settings"
# Restrict discovery to src/ to avoid recursing into submodules/
testpaths = ["src"]
pythonpath = ["src"]

# ---------------------------------------------------------------------------
# ruff
# ---------------------------------------------------------------------------

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["project"]

# ---------------------------------------------------------------------------
# mypy
# ---------------------------------------------------------------------------

[tool.mypy]
plugins = ["mypy_django_plugin.main"]
python_version = "3.12"
strict = true
ignore_missing_imports = true

[tool.django-stubs]
django_settings_module = "project.settings"
```

## Key Points

### uwsgi in prod group only
uwsgi requires gcc to compile. It belongs in the `prod` dependency group, which is installed
in the `deps-prod` stage where gcc and libpcre3-dev are available.
Adding uwsgi to `[project.dependencies]` would cause `deps-dev` and `deps-test` to try to
compile it without gcc — causing build failures.

### dev group includes test group
`{ include-group = "test" }` in the dev group means `uv sync --locked` installs all test
tools for developers. In the `deps-test` stage, `--no-default-groups --group test` installs
only the test group (no dev tools).

### testpaths = ["src"]
Prevents pytest from recursing into `submodules/` (which may contain their own test suites)
or `project/` (Django project config — not app code).
