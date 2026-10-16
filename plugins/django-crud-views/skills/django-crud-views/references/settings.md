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
CRUD_VIEWS_FILTER_ICON = "fa-solid fa-filter"
CRUD_VIEWS_FILTER_RESET_BUTTON_CSS_CLASS = "btn btn-secondary"

# Inaccessible actions: "hide" | "disable" (crud_views.E104) — see actions-and-buttons.md
CRUD_VIEWS_INACCESSIBLE_ACTIONS = "hide"

# Action menus: keys kept as buttons, the rest folds into a ⋯ dropdown;
# None = no menu, [] = everything in the menu (crud_views.E105) — see actions-and-buttons.md
CRUD_VIEWS_LIST_ACTIONS_INLINE = None
CRUD_VIEWS_CONTEXT_ACTIONS_INLINE = None
CRUD_VIEWS_CARD_ACTIONS_INLINE = None
CRUD_VIEWS_ACTIONS_MENU_ICON = "fa-solid fa-ellipsis"

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

# Breadcrumbs: leading items, e.g. [{"title": "Home", "url_name": "home"}] (crud_views.E102)
CRUD_VIEWS_BREADCRUMB_PREFIX = []

# Assets / CSP — see assets.md
CRUD_VIEWS_CSP_NONCE_ATTR = "csp_nonce"                # request attribute holding the CSP nonce
CRUD_VIEWS_ASSETS_BUNDLED = False                      # True: cv_js/cv_css emit only CDN entries
```

`CRUD_VIEWS_THEME` is not a setting; it is ignored and only triggers warning `crud_views.W110`.

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
CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY = "bootstrap"          # default; or "fontawesome"
CRUD_VIEWS_OBJECT_DETAIL_PROPERTY_TEXT_NEWLINE = "linebreaksbr"

# The three below default per library — bootstrap: class "bi", no type, prefix "bi";
# fontawesome: class "fa", type "regular", prefix "fa". Set only to override.
# CRUD_VIEWS_OBJECT_DETAIL_ICONS_CLASS = "fa"
# CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE = "solid"               # suffix: fa-solid, fa-regular, ...
# CRUD_VIEWS_OBJECT_DETAIL_ICONS_PREFIX = "fa"
# CRUD_VIEWS_OBJECT_DETAIL_NAMED_ICONS = {...}                # override the named-icon map
```

The icon class is built as `{class}-{type} {prefix}-{name}` (type omitted when None), so
`ICONS_TYPE` accepts any Font Awesome style suffix.

## Reading the settings object

```python
from crud_views.lib.settings import crud_views_settings
crud_views_settings.as_dict
```
