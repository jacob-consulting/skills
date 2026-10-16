# Detail views — `DetailView` vs `ObjectDetailView`

## Detail views: `DetailView` vs `ObjectDetailView`

*Available since 0.4.0; restructured in 0.17.0 (see [migration.md](migration.md)).*

There are two detail views, and picking the wrong one is the most common mistake:

| Want | Use | Lives in |
|---|---|---|
| Your own template, full layout control | `DetailViewPermissionRequired` | `crud_views.lib.views` |
| Property grid from `cv_property_display` | `ObjectDetailViewPermissionRequired` | `crud_views_object_detail.lib` |

Both share `cv_key = "detail"` / `cv_path = "detail"`, icons, snippets, and context actions.

### `DetailView` — custom template

```python
from crud_views.lib.views import DetailViewPermissionRequired

class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book
    template_name = "myapp/book_detail.html"
```

Template receives `object`, `view`, and `cv_extends`. Extend `cv_extends` and fill `{% block cv_content %}`.

When hand-building links in the custom template, use `{% cv_context_url "key" as url %}`
to get a permission-gated target URL (`None` when the user has no access or the action is
disabled), then gate your markup with `{% if url %}`. Use `{% cv_context_button "key" %}`
instead when you want the library to render the full button markup. For a POST-only target
(`ActionView`, `up` / `down`) that button submits a hidden form: also render
`{% cv_context_action_form "key" %}` outside any `.btn-group` (since 0.29.0; it renders nothing for GET,
hidden or disabled actions, and the object defaults to the view's object).

Guardian variant: `GuardianDetailViewPermissionRequired`.

### `ObjectDetailView` — property grid

Ships as a **separate app** that must be installed:

```python
INSTALLED_APPS = [..., "crud_views_object_detail", "crud_views", ...]
```

```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired, x

class BookDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_object_detail_layout = "accordion"   # optional per-view layout override

    cv_property_display = [
        {
            "title": "Attributes",
            "icon": "tag",
            "description": "Core book information",
            "properties": [
                "title",                                   # field or @property name
                {"path": "isbn", "title": "ISBN"},         # dict form
                x("author__email", title="Author email"),  # x() helper == PropertyConfig
            ],
        },
    ]
```

Each `properties` entry is a plain string, a dict, or `x()` / `PropertyConfig`. Dict keys:
`path` (required), `title`, `detail` (tooltip), `type`, `template`, `link`, `badge`.
`detail` renders inline in most layout packs; `card-rows` shows it as a tooltip, initialised by the
bundled `tooltip.js` (via `{% cv_js %}`, needs Bootstrap's JS; since 0.23.0).
Use `__` for FK/M2M traversal (`"author__country__name"`, `"tags"`).

`link` and `badge` each accept **either** a string shorthand or the full object:

```python
{"path": "state", "badge": "success"}                     # → BadgeConfig(color="success")
{"path": "state", "badge": BadgeConfig(color_map={...})}  # full control
{"path": "owner", "link": "author-detail"}                # → LinkConfig(url="author-detail")
{"path": "owner", "link": LinkConfig(url="author-detail", kwargs={"pk": "owner.pk"})}
```

Startup checks: `E240` (`cv_property_display` not set), `E241` (set but not a list).

Also exported from `crud_views_object_detail.lib`: `ObjectDetailMixin`, `ObjectDetailView`,
`PropertyConfig`, `PropertyGroupConfig`, `LinkConfig`, `BadgeConfig`, `x`.

**Polymorphic and Guardian detail views do not include the property grid.** Compose
`ObjectDetailMixin` yourself:

```python
from crud_views_object_detail.lib import ObjectDetailMixin
from crud_views_polymorphic.lib import PolymorphicDetailViewPermissionRequired

class VehicleDetailView(ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_property_display = [{"title": "Attributes", "properties": ["name"]}]
```
