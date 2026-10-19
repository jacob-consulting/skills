# Icons

*Available since 0.30.0.* Before 0.30.0 icons were raw CSS classes configured per feature; see
[migration.md](migration.md#0300--icon-registry) for the old settings.

The package names every icon semantically (`detail`, `delete`, `filter`, …). A layered table maps names to icon
values, and a renderer per **library prefix** turns a value into HTML. Module: `crud_views.lib.icons`.

## Icon values

Accepted wherever the package takes an icon: `cv_icon_action`, `cv_icon_header`, `ViewSet(icon_header=...)`, an
object detail group's `"icon"`, `CRUD_VIEWS_ICONS` values. Resolved in this order:

1. **Semantic name**: no colon and present in the icon table (`"detail"`, your own `"person"`). One lookup only; a
   table value pointing to another semantic name is not followed (`crud_views.W352`).
2. **`prefix:name`**: the library's renderer gets `name` (`far:eye`, `fas:truck`, `bi:person`).
3. **Raw CSS class**: anything else without a colon (`"fa-solid fa-truck"`) renders `<i class="…">` as is.

`None`, `""` or whitespace renders nothing (so `CRUD_VIEWS_ICONS = {"field-marker": None}` switches that icon off).
Other non-strings render nothing and raise `crud_views.E356`. A colon always means `prefix:name`, so a raw class
with a colon (Tailwind `hover:…`) needs its own library entry. An unknown prefix renders nothing (W352/W353/W246).
Icons get `aria-hidden="true"`.

**Prefer `prefix:name`.** Bare unknown names are raw classes and are never flagged: `"icon": "truck"` renders an
invisible `<i class="truck">`. Default libraries are free Font Awesome 6, where `far` (regular) has only a small set
of icons (`user`, `eye`, `envelope`, `trash-can`, `file-lines`, …). `book`, `box`, `tag`, `truck` and most others are
solid-only, so use `fas:` when unsure, since `far:box` renders blank.

## Default table

Font Awesome 6 free (`far` / `fas`). **The package does not ship Font Awesome**: load it in the base template.

| Name | Default | Used for |
|---|---|---|
| `list` / `card` | `far:rectangle-list` / `fas:rectangle-list` | list / card list view action |
| `detail` `create` `update` `delete` | `far:eye` `far:square-plus` `far:pen-to-square` `far:trash-can` | view actions |
| `order-up` / `order-down` | `far:circle-up` / `far:circle-down` | ordered views |
| `manage` / `workflow` | `fas:gear` / `fas:diagram-project` | action and header |
| `actions-menu` | `fas:ellipsis` | `⋯` menu toggle |
| `filter` / `filter-close` | `fas:filter` / `fas:filter-circle-xmark` | filter toggle (closed / open) and panel header |
| `language` | `fas:language` | language selector |
| `sort-asc` / `sort-desc` | `fas:arrow-up-short-wide` / `fas:arrow-down-wide-short` | card list ordering |
| `table-sort-asc` / `table-sort-desc` | `fas:angles-up` / `fas:angles-down` | sortable table headers |
| `formset-up` `formset-down` `formset-add` `formset-delete` | `fas:caret-up` `fas:caret-down` `fas:plus` `fas:square-xmark` | formset rows |
| `field-marker` | `fas:angles-right` | detail widgets |
| `boolean-true` / `boolean-false` | `fas:circle-check` / `fas:circle-xmark` | booleans (core widget, object detail) |
| `property-detail` / `text-icon` | `fas:circle-info` / `far:file-lines` | object detail `card-rows` / `list-group-3col` |

## Configuring

```python
CRUD_VIEWS_ICONS = {                   # merged per key over defaults and theme registrations
    "detail": "fas:magnifying-glass",  # override a default
    "actions-menu": "fas:bars",
    "person": "far:user",              # your own name, usable anywhere an icon value is accepted
}

from crud_views.lib.icons import BOOTSTRAP_ICONS   # every default name as bi:…
CRUD_VIEWS_ICONS = {**BOOTSTRAP_ICONS, "detail": "bi:search"}   # load the Bootstrap Icons CSS yourself
```

```python
class AuthorDetailView(DetailViewPermissionRequired):
    cv_icon_action = "person"          # or "far:user"
```

## Rendering in templates and Python

```html+django
{% load crud_views %}            {# also available via {% load crud_views_object_detail %} #}
{% cv_icon "detail" %}
{% cv_icon cv_icon_action css="me-2" %}
```

Python: `crud_views.lib.icons.render_icon(value, css="")` returns a `SafeString`. `get_icons()` / `get_libraries()`
return the resolved, cached dicts; don't mutate them.

The context values `cv_icon_action`, `cv_icon_header` and `cv_menu_icon` hold **icon values**, not classes. In a custom
button/menu template `<i class="{{ cv_icon_action }}">` renders an invisible icon; use `{% cv_icon cv_icon_action %}`.
In `template_code` strings, include `{% load crud_views %}`.

Fixed-width icons in menus use `.cv-icon-fw` from the core asset `crud_views/css/icons.css` (`{% cv_css %}` includes it;
hand-maintained CSS lists must add it).

## Libraries and renderers

`CRUD_VIEWS_ICON_LIBRARIES` maps prefix → config, merged **per prefix** (an entry replaces the whole built-in entry).
Built-ins: `far` = `{"renderer": "font", "class": "fa-regular fa-{name}"}`, `fas` = `fa-solid fa-{name}`,
`bi` = `bi bi-{name}`.

```python
CRUD_VIEWS_ICON_LIBRARIES = {
    "fal": {"renderer": "font", "class": "fa-light fa-{name}"},                       # FA Pro light
    "svg": {"renderer": "myproject.icons.render_svg", "sprite": "/static/icons.svg"},  # custom renderer
}
```

A custom renderer is `renderer(name: str, *, css: str, config: dict) -> SafeString`; extra config keys (`sprite`)
arrive in `config`. It is the only place markup is produced, so escape with `format_html`:

```python
from django.utils.html import format_html

def render_svg(name, *, css, config):
    return format_html('<svg class="icon {}" aria-hidden="true"><use href="{}#{}"/></svg>', css, config["sprite"], name)
```

## Theme apps

```python
# myapp_theme/apps.py
def ready(self):
    from crud_views.lib.icons import register_icon_library, register_icons

    register_icon_library("tabler", renderer="myapp_theme.icons.render")       # "font", dotted path or callable
    register_icon_library("ti", **{"class": "ti ti-{name}"})                   # `class` is a keyword: dict form
    register_icons({"detail": "tabler:eye", "delete": "tabler:trash"})
```

Precedence, later wins per key: package defaults → theme registrations (later in `INSTALLED_APPS` wins) →
`CRUD_VIEWS_ICONS` / `CRUD_VIEWS_ICON_LIBRARIES`.

## System checks

| ID | Meaning |
|---|---|
| `crud_views.E350` | a removed icon setting is still defined; the hint names the replacement |
| `crud_views.E351` | a library's `renderer` dotted path can't be imported |
| `crud_views.E354` | a `font` library has no `class`, or it isn't a valid format string (renders nothing) |
| `crud_views.E355` | a library config isn't a dict, or its `renderer` isn't `font` / dotted path / callable |
| `crud_views.E356` | a `CRUD_VIEWS_ICONS` value, `cv_icon_action` or `cv_icon_header` is neither str nor `None` |
| `crud_views.W352` | a `CRUD_VIEWS_ICONS` entry uses an unregistered prefix, or points to another semantic name |
| `crud_views.W353` | `cv_icon_action` / `cv_icon_header` / `ViewSet.icon_header` uses an unregistered prefix |
| `viewset.W246` | an object detail group `icon` uses an unregistered prefix |
