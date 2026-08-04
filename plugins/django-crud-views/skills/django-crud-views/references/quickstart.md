# django-crud-views Quick Start

## 1. Define the ViewSet

```python
# views/author.py
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

## 2. Add URL patterns

```python
# urls.py
from app.views.author import cv_author

urlpatterns += cv_author.urlpatterns
```

## 3. List view with table

```python
import django_tables2 as tables
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.table.columns import NaturalDayColumn, NaturalTimeColumn
from crud_views.lib.views import ListViewTableMixin, ListViewPermissionRequired

class AuthorTable(Table):
    id = UUIDLinkDetailColumn()
    first_name = tables.Column()
    last_name = tables.Column()
    created_dt = NaturalDayColumn()

class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete"]  # per-row buttons
```

## 4. Create / Update views

```python
from crispy_forms.layout import Row
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyViewMixin
from crud_views.lib.views import CreateViewPermissionRequired, UpdateViewPermissionRequired, MessageMixin

class AuthorCreateForm(CrispyModelForm):
    submit_label = "Create"
    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]
    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))

class AuthorUpdateForm(AuthorCreateForm):
    submit_label = "Update"

class AuthorCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    form_class = AuthorCreateForm
    cv_viewset = cv_author
    cv_message_template_code = "Created author »{{ object }}«"

class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message_template_code = "Updated author »{{ object }}«"
```

## 5. Delete view

```python
from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired

class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message_template_code = "Deleted author »{{ object }}«"
```

## 6. Detail view

```python
from crud_views_object_detail.lib import ObjectDetailViewPermissionRequired

class AuthorDetailView(ObjectDetailViewPermissionRequired):
    cv_viewset = cv_author

    cv_property_display = [
        {
            "title": "Attributes",
            "icon": "tag",
            "description": "Core author information",
            "properties": [
                "first_name",
                "last_name",
                {"path": "full_name", "detail": "Computed from first and last name"},
                {"path": "id", "title": "UUID"},
            ],
        },
    ]
```

Each entry in `properties` can be a plain string (field or `@property` name), a dict, or the `x()`
helper from `crud_views_object_detail.lib`. Dict keys: `path` (required), `title`, `detail` (tooltip),
`type`, `template`, `link`, `badge`. Use `__` for FK/M2M traversal: `"author__email"`, `"tags"`.

The property grid lives in the separate `crud_views_object_detail` app (vendored in-tree since
0.17.0 — there is no external `django-object-detail` dependency and no `django_object_detail` app):

```python
INSTALLED_APPS = [..., "crud_views_object_detail", "crud_views", ...]

# Layout pack: "split-card" (default), "accordion", "tabs-vertical", "card-rows",
#              "striped-rows", "table-inline", "list-group-3col"
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"
CRUD_VIEWS_OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"

# Icon library: "bootstrap" (default) or "fontawesome"
CRUD_VIEWS_OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"
# Class/type/prefix default per library (bootstrap: bi / none / bi;
# fontawesome: fa / regular / fa). Override only if needed:
# CRUD_VIEWS_OBJECT_DETAIL_ICONS_TYPE = "solid"   # renders fa-solid
```

Per-view layout override: `cv_object_detail_layout = "accordion"`.
