# Settings

Each setting is a flat, module-level Django setting prefixed with `CRUD_VIEWS_` (read via
`getattr(settings, "CRUD_VIEWS_<NAME>", default)`). There is no `CRUD_VIEWS = {...}` dict.
Only `CRUD_VIEWS_EXTENDS` is required; the rest show their defaults.

```python
# Required
CRUD_VIEWS_EXTENDS = "base.html"                       # base template; missing/not found → crud_views.E100

# Manage views
CRUD_VIEWS_MANAGE_VIEWS_ENABLED = "debug_only"         # "yes" | "no" | "debug_only" (crud_views.E101)
CRUD_VIEWS_MANAGE_GROUP = "CRUD_VIEWS_MANAGE"           # group name granting manage access
CRUD_VIEWS_MANAGE_SHOW_USERS = False                   # show Users column in Permission Holders
CRUD_VIEWS_MANAGE_VIEW_CLASS = None                    # dotted path, default manage view for plain ViewSets
CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS = None           # dotted path, default for GuardianViewSets

# Strict mode: unresolvable view keys in template tags / link columns raise instead of
# rendering nothing (logged as a warning). Defaults to DEBUG.
CRUD_VIEWS_STRICT = DEBUG

# Session
CRUD_VIEWS_SESSION_DATA_KEY = "viewset"

# Origin parameter for cv_cancel_keys / cv_success_keys; must match ^[a-z][a-z0-9_]*$ (crud_views.E103)
CRUD_VIEWS_ORIGIN_PARAM = "cv_from"

# Filter
CRUD_VIEWS_FILTER_PERSISTENCE = True                   # store filter state in session
CRUD_VIEWS_FILTER_PINNED = False                       # True = filter always open, toggle hidden
CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS = "btn btn-secondary"

# Inaccessible actions: "hide" | "disable" (crud_views.E104) — see actions-and-buttons.md
CRUD_VIEWS_INACCESSIBLE_ACTIONS = "hide"

# Action menus: keys kept as buttons, the rest folds into a ⋯ dropdown;
# None = no menu, [] = everything in the menu (crud_views.E105) — see actions-and-buttons.md
CRUD_VIEWS_LIST_ACTIONS_INLINE = None
CRUD_VIEWS_CONTEXT_ACTIONS_INLINE = None
CRUD_VIEWS_CARD_ACTIONS_INLINE = None

# Icons (since 0.30.0) — see icons.md. Merged per key over the defaults (Font Awesome 6 free).
CRUD_VIEWS_ICONS = {}            # e.g. {"filter": "fas:magnifying-glass", "actions-menu": "fas:bars"}
CRUD_VIEWS_ICON_LIBRARIES = {}   # prefix -> config; built-ins far, fas, bi

# Default per-row actions for list views
CRUD_VIEWS_LIST_ACTIONS = ["detail", "update", "delete"]

# Default page-level (context) actions per view type
CRUD_VIEWS_LIST_CONTEXT_ACTIONS = ["parent", "list", "filter", "create"]
CRUD_VIEWS_DETAIL_CONTEXT_ACTIONS = ["home", "detail", "update", "delete"]
CRUD_VIEWS_CREATE_CONTEXT_ACTIONS = ["home", "create"]
CRUD_VIEWS_UPDATE_CONTEXT_ACTIONS = ["home", "detail", "update", "delete"]
CRUD_VIEWS_DELETE_CONTEXT_ACTIONS = ["home", "detail", "update", "delete"]
CRUD_VIEWS_MANAGE_CONTEXT_ACTIONS = ["home"]
CRUD_VIEWS_CREATE_SELECT_CONTEXT_ACTIONS = ["home", "create_select"]
CRUD_VIEWS_POLYMORPHIC_CREATE_CONTEXT_ACTIONS = ["home"]   # since 0.29.3; never "create" (needs the content type)

# Breadcrumbs: leading items, e.g. [{"title": "Home", "url_name": "home"}] (crud_views.E102)
CRUD_VIEWS_BREADCRUMB_PREFIX = []

# Assets / CSP — see assets.md
CRUD_VIEWS_CSP_NONCE_ATTR = "csp_nonce"                # request attribute holding the CSP nonce
CRUD_VIEWS_ASSETS_BUNDLED = False                      # True: cv_js/cv_css emit only CDN entries
```

`CRUD_VIEWS_THEME` is not a setting; it is ignored and only triggers warning `crud_views.W110`.

Removed in 0.30.0 (error `crud_views.E350` while still defined): `CRUD_VIEWS_FILTER_ICON`,
`CRUD_VIEWS_ACTIONS_MENU_ICON` (now the `filter` / `actions-menu` entries of `CRUD_VIEWS_ICONS`) and all
`CRUD_VIEWS_OBJECT_DETAIL_ICONS_*` / `CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS` settings.

Manage-view access is granted by `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` ("yes"/"debug_only"/"no") **or** by
membership in the `CRUD_VIEWS_MANAGE` group (name configurable via `CRUD_VIEWS_MANAGE_GROUP`). The group
approach grants selective access without changing deployment settings. Per ViewSet,
`manage_view_class="dotted.path.MyClass"` overrides the global class settings.

## Object-detail settings (`crud_views_object_detail`)

```python
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"  # "accordion", "tabs-vertical",
                                                              # "card-rows", "striped-rows",
                                                              # "table-inline", "list-group-3col"
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"
CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE = "linebreaksbr"   # or "linebreaks"
```

Object detail has no icon settings since 0.30.0: it uses the core registry names `boolean-true`, `boolean-false`,
`property-detail` and `text-icon` (Font Awesome by default). To keep its old Bootstrap Icons look:

```python
from crud_views.lib.icons import BOOTSTRAP_ICONS

CRUD_VIEWS_ICONS = {k: BOOTSTRAP_ICONS[k] for k in ("boolean-true", "boolean-false", "property-detail", "text-icon")}
```

## Reading the settings object

```python
from crud_views.lib.settings import crud_views_settings
crud_views_settings.as_dict
```
