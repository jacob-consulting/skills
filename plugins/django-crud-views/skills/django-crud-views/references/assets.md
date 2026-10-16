# Static assets, CSP, SRI and django-pipeline

## Static assets, CSP, and SRI

*Available since 0.18.0.*

`{% cv_js %}` and `{% cv_css %}` render the package's own assets plus every bundle registered
by an installed app. They emit external `<script src>` / `<link>` tags — no inline JS or CSS.

Put both in the base template named by `CRUD_VIEWS_EXTENDS` — that is what makes a registered
bundle render:

```html
{% load crud_views %}
{% cv_css %}
{% cv_js %}
```

Core scripts: `viewset.js`, `formset.js`, `list.filter.js`, `modal.js`, `toggle.js` and — since
0.23.0 — `tooltip.js` (initialises the package's own `[data-cv-tooltip]` triggers; call
`cv.initTooltips(root)` after injecting such markup yourself).

The package emits **no inline `<script>` or `<style>` anywhere**, so it needs no
`'unsafe-inline'`. `{% cv_config %}` (the modal shell) is markup only — a hidden `<div>`
carrying `data-` attributes plus an empty modal container — so it needs no nonce. Modal
content is fetched from the view's own URL, so `connect-src 'self'` suffices.

### Contributing your own JS/CSS

Call `register_assets()` from your `AppConfig.ready()` — once per key, or startup raises
`ImproperlyConfigured`. Bundles render *after* core assets, in `INSTALLED_APPS` order.

```python
from django.apps import AppConfig
from crud_views.lib.assets import Asset, register_assets

class MyAppConfig(AppConfig):
    name = "myapp"

    def ready(self):
        register_assets(
            "myapp",                                  # unique key
            js=["myapp/js/widget.js"],                # static paths
            css=["myapp/css/widget.css"],
            # emit=False registers the bundle without rendering it
        )
```

Entries are static paths, external URLs (`http://`, `https://`, `//` — rendered verbatim),
or `Asset` instances. Plain strings are normalized to `Asset` internally.

### Subresource Integrity for CDN assets

```python
register_assets(
    "myapp",
    js=[Asset(
        path="https://cdn.example.com/lib.min.js",
        integrity="sha384-…",       # sha256-/sha384-/sha512- prefixed
        # crossorigin defaults to "anonymous" when integrity is set
    )],
)
```

Two startup checks guard this: `crud_views.E330` (integrity value is not a
`sha256-`/`sha384-`/`sha512-` hash) and `crud_views.W332` (integrity set on a same-origin
static path — it breaks on every asset edit and buys no security).

### Content-Security-Policy nonces

Nonces are automatic — **no configuration needed** in the normal case. `cv_js`/`cv_css`
resolve a nonce in this order and stamp `nonce="…"` on every tag they emit:

1. `request.<CRUD_VIEWS_CSP_NONCE_ATTR>` — default `request.csp_nonce`, the django-csp convention
2. Django 6.0's built-in CSP middleware (`django.middleware.csp.get_nonce`)
3. a `csp_nonce` template-context variable

Output is byte-identical to before when no CSP middleware is present. Only change
`CRUD_VIEWS_CSP_NONCE_ATTR` (default `"csp_nonce"`) if your middleware stores the nonce
under a different request attribute.

### Bundling with django-pipeline

*Available since 0.25.0.*

```python
# settings.py
from crud_views.lib.pipeline import cv_sources

CRUD_VIEWS_ASSETS_BUNDLED = True   # cv_js/cv_css then emit only CDN entries

PIPELINE = {
    "JAVASCRIPT": {"main": {
        "source_filenames": cv_sources("js", before=["js/jquery.js"], after=["js/app.js"]),
        "output_filename": "js/main.js",
    }},
    "STYLESHEETS": {"main": {"source_filenames": cv_sources("css"), "output_filename": "css/main.css"}},
}
```

- `cv_sources()` is **lazy** — pipeline reads it after `AppConfig.ready()`, so core plus every
  registered bundle lands in the package with no hand-maintained list. Never expand it in settings
  (`[*cv_sources(...)]` raises `AppRegistryNotReady`); use `before=`/`after=` or `list + cv_sources(...)`.
- `keys=[...]` / `exclude=[...]` select bundles (`"crud_views"` = core, a reserved key) to split across
  packages; `keys=None` = all, `keys=[]` = none.
- CDN entries cannot be bundled: they stay `{% cv_js %}`/`{% cv_css %}` tags, so keep the tags in
  the base template. Core has none; an extension must be in its vendored mode to be fully bundled
  (W345 warns otherwise). `python manage.py cv_assets --external` lists the CDN entries.
- Checks: W340 (bundled, no `cv_sources()` in `PIPELINE`), W341 (asset in no package), W342 (not
  bundled → double load), W343 (unknown key), W344 (js/css mismatch), W345 (bundle mixes CDN and local).
  Hand-written `source_filenames` strings count as coverage too; globs match per path segment like
  pipeline's own (`*` does not cross `/`).
