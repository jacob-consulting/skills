---
name: django-crud-views
description: "Build Django CRUD interfaces using the django-crud-views package. Use when creating, reading, updating, or deleting model records with class-based views; when wiring up ViewSets, ListViews, DetailViews, CreateViews, UpdateViews, or DeleteViews; when configuring tables with django-tables2, filters with django-filter, or forms with django-crispy-forms; when implementing nested/child resources with ParentViewSet; when adding permission-required views; or any time the codebase imports from crud_views.lib."
---

# django-crud-views

A library that wires together class-based views, django-tables2, django-filter, and django-crispy-forms into a coherent
CRUD framework. Key concepts: a **ViewSet** groups all views for a model and auto-generates URL patterns; each
**CrudView** subclass registers itself with the ViewSet via the `cv_viewset` attribute.

Full API reference: see [references/api-reference.md](references/api-reference.md)

---

## Quick Start — Simple CRUD

### 1. Define the ViewSet

```python
# views/author.py
from crud_views.lib.viewset import ViewSet
from .models import Author

cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")
```

### 2. Add URL patterns

```python
# urls.py
from app.views.author import cv_author

urlpatterns += cv_author.urlpatterns
```

### 3. List view with table

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

### 4. Create / Update views

```python
from crispy_forms.layout import Row
from crud_views.lib.crispy import Column4, CrispyModelForm, CrispyModelViewMixin
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

class AuthorCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    form_class = AuthorCreateForm
    cv_viewset = cv_author
    cv_message = "Created author »{object}«"

class AuthorUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    form_class = AuthorUpdateForm
    cv_viewset = cv_author
    cv_message = "Updated author »{object}«"
```

### 5. Delete view

```python
from crud_views.lib.crispy import CrispyDeleteForm
from crud_views.lib.views import DeleteViewPermissionRequired

class AuthorDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_message = "Deleted author »{object}«"
```

### 6. Detail view

```python
from crud_views.lib.views import DetailViewPermissionRequired

class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_property_display = [
        {
            "title": "Attributes",
            "icon": "tag",
            "properties": ["first_name", "last_name", "pseudonym"],
        },
    ]
```

---

## Nested Resources (Child ViewSet)

Add `parent=ParentViewSet(name="author")` to the child ViewSet. Use `CreateViewParentMixin` on the child's create
view to auto-assign the FK. Add `LinkChildColumn` to the parent table to link through.

```python
# views/book.py
from crud_views.lib.viewset import ViewSet, ParentViewSet
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkChildColumn
from crud_views.lib.views import CreateViewParentMixin, CreateViewPermissionRequired

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),  # URL: /author/<author_pk>/book/
)

class BookCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    form_class = BookCreateForm
    cv_viewset = cv_book

# In the parent AuthorTable, add:
# books = LinkChildColumn(name="book", verbose_name="Books")
```

URLs for `cv_book` must also be added: `urlpatterns += cv_book.urlpatterns`

---

## Filtering

```python
import django_filters
from crud_views.lib.views import ListViewTableFilterMixin
from crud_views.lib.views.list import ListViewFilterFormHelper
from crispy_forms.layout import Layout, Row

class AuthorFilter(django_filters.FilterSet):
    first_name = django_filters.CharFilter(lookup_expr="icontains")
    last_name = django_filters.CharFilter(lookup_expr="icontains")
    class Meta:
        model = Author
        fields = ["first_name", "last_name"]

class AuthorFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("first_name"), Column4("last_name")))

class AuthorListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    table_class = AuthorTable
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
    cv_viewset = cv_author
```

---

## Ordered Actions (move up/down)

```python
from crud_views.lib.views import OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired

class AuthorUpView(MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_author
    cv_message = "Moved »{object}« up"

class AuthorDownView(MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_author
    cv_message = "Moved »{object}« down"

# Add "up" and "down" to cv_list_actions in the list view
```

---

## Custom Action View

Subclass `ActionViewPermissionRequired` and implement `action(context)`. Register with a unique `cv_key` and
`cv_path`. Add that key to `cv_list_actions` on the list view to show a per-row button.

---

## Settings (Django `settings.py`)

```python
CRUD_VIEWS = {
    "EXTENDS": "base.html",                    # required: base template
    "MANAGE_VIEWS_ENABLED": "debug_only",      # "yes" | "no" | "debug_only"
    "FILTER_PERSISTENCE": True,
    "LIST_ACTIONS": ["detail", "update", "delete"],
    "LIST_CONTEXT_ACTIONS": ["parent", "filter", "create"],
}
```

See [references/api-reference.md](references/api-reference.md) for full settings and all ViewSet/view attributes.
