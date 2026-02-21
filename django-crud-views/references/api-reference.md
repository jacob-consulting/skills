# django-crud-views API Reference

## Table of Contents
1. [ViewSet](#viewset)
2. [ParentViewSet](#parentviewset)
3. [View Classes](#view-classes)
4. [Mixins](#mixins)
5. [Table & Columns](#table--columns)
6. [Forms & Crispy](#forms--crispy)
7. [Filtering](#filtering)
8. [Settings](#settings)
9. [Import Paths Cheatsheet](#import-paths-cheatsheet)

---

## ViewSet

```python
from crud_views.lib.viewset import ViewSet

cv_author = ViewSet(
    model=Author,           # required: Django model class
    name="author",          # required: identifier, used in URL names and registry
    prefix="authors",       # URL path prefix (defaults to name)
    app="myapp",            # URL namespace (optional)
    pk="UUID",              # primary key type: "INT" | "UUID" | "STR" (default "UUID")
    pk_name="pk",           # URL parameter name (default "pk")
    parent=ParentViewSet(), # for nested resources
    ordering="-created_dt", # default queryset ordering
    icon_header="fa-regular fa-user",  # Font Awesome icon for the header
    context_buttons=[],     # override default context buttons
)
```

**Key method:** `cv_author.urlpatterns` — include in `urls.py` with `urlpatterns += cv_author.urlpatterns`

---

## ParentViewSet

```python
from crud_views.lib.viewset import ParentViewSet

ParentViewSet(
    name="author",              # name of the parent ViewSet
    attribute="author",         # ForeignKey field name on child model (default: same as name)
    pk_name="author_pk",        # URL param for parent PK (default: f"{name}_pk")
    many_to_many_through_attribute=None,  # for M2M through models
)
```

Child URLs become: `/author/<author_pk>/book/`, `/author/<author_pk>/book/<pk>/detail/`, etc.

---

## View Classes

All views require `cv_viewset` to be set. Permission-required variants enforce Django model permissions automatically.

### ListView / ListViewPermissionRequired

```python
from crud_views.lib.views import ListView, ListViewPermissionRequired

class MyListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_my           # required
    table_class = MyTable        # required when using ListViewTableMixin
    cv_list_actions = ["detail", "update", "delete"]  # per-row action buttons
    cv_context_actions = ["parent", "filter", "create"]  # page-level action buttons
    paginate_by = 10
    cv_filter_persistence = True  # store filter state in session
```

### DetailView / DetailViewPermissionRequired

```python
from crud_views.lib.views import DetailViewPermissionRequired

class MyDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_my
    cv_property_display = [
        {
            "title": "Group Title",   # required
            "icon": "tag",            # optional: icon name
            "description": "...",    # optional: subtitle
            "properties": [
                "field_name",                             # simple field or @property
                {"path": "field", "title": "Label",      # full property config
                 "detail": "tooltip", "type": "str",
                 "link": "url-name", "badge": "success"},
                "fk_field__sub_field",                   # FK traversal with __
                "m2m_field",                             # ManyToMany
            ],
        },
    ]
```

**Available layout packs** (set via `OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT`):
`split-card` (default), `accordion`, `tabs-vertical`, `card-rows`, `striped-rows`, `table-inline`, `list-group-3col`

### CreateView / CreateViewPermissionRequired

```python
from crud_views.lib.views import CreateViewPermissionRequired

class MyCreateView(CrispyModelViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_my
    form_class = MyCreateForm
    cv_message = "Created »{object}«"   # {object} replaced with str(instance)
    cv_success_key = "list"              # redirect after success (default: "list")
    cv_context_actions = ["home"]
```

For nested resources, also inherit `CreateViewParentMixin` to auto-assign the parent FK:

```python
class ChildCreateView(CrispyModelViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    ...
```

### UpdateView / UpdateViewPermissionRequired

```python
from crud_views.lib.views import UpdateViewPermissionRequired

class MyUpdateView(CrispyModelViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_my
    form_class = MyUpdateForm
    cv_message = "Updated »{object}«"
    cv_success_key = "list"
```

### DeleteView / DeleteViewPermissionRequired

```python
from crud_views.lib.views import DeleteViewPermissionRequired
from crud_views.lib.crispy import CrispyDeleteForm

class MyDeleteView(CrispyModelViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_my
    form_class = CrispyDeleteForm   # built-in confirmation form
    cv_message = "Deleted »{object}«"
    cv_success_key = "list"
```

### ActionView / ActionViewPermissionRequired

```python
from crud_views.lib.views import ActionViewPermissionRequired

class MyActionView(MessageMixin, ActionViewPermissionRequired):
    cv_key = "my_action"        # unique key for this view
    cv_path = "my-action"       # URL path segment
    cv_icon_action = "fa-solid fa-bolt"
    cv_viewset = cv_my

    def action(self, context):
        obj = context.object
        # perform action on obj
        obj.save()
```

### OrderedUpView / OrderedDownView (requires django-ordered-model)

```python
from crud_views.lib.views import OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired

class MyUpView(MessageMixin, OrderedUpViewPermissionRequired):
    cv_viewset = cv_my
    cv_message = "Moved »{object}« up"

class MyDownView(MessageMixin, OrderedUpDownPermissionRequired):
    cv_viewset = cv_my
    cv_message = "Moved »{object}« down"
```

Add `"up"` and `"down"` to `cv_list_actions` in the list view.

### RedirectChildView

Adds a per-row button that links to a child viewset's list:

```python
from crud_views.lib.views import RedirectChildView

class RedirectBooksView(RedirectChildView):
    cv_action_label = "Goto Books"
    cv_redirect = "book"         # child viewset name
    cv_redirect_key = "list"
    cv_icon_action = "fa-regular fa-address-book"
    cv_viewset = cv_author
```

Add `"redirect_child"` (or the specific cv_key) to `cv_list_actions`.

---

## Mixins

| Mixin | Purpose | Import |
|-------|---------|--------|
| `ListViewTableMixin` | Render queryset as a django-tables2 table | `crud_views.lib.views` |
| `ListViewTableFilterMixin` | Add django-filter filtering + session persistence | `crud_views.lib.views` |
| `CrispyModelViewMixin` | Render form with crispy-forms | `crud_views.lib.crispy` |
| `MessageMixin` | Show Django messages after actions; set `cv_message` | `crud_views.lib.views` |
| `CreateViewParentMixin` | Auto-assign parent FK on nested create | `crud_views.lib.views` |

### Form Processing Hooks (CrudViewProcessFormMixin)

Override these methods on create/update/delete views:

```python
def cv_post_hook(self, context): ...       # before validation
def cv_form_is_valid(self, context): ...   # custom validation
def cv_form_valid(self, context): ...      # called on valid form (saves instance)
def cv_form_valid_hook(self, context): ... # after save
def cv_form_invalid(self, context): ...    # called on invalid form
def cv_form_invalid_hook(self, context): ...
```

---

## Table & Columns

```python
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkDetailColumn, LinkChildColumn
from crud_views.lib.table.columns import NaturalDayColumn, NaturalTimeColumn
import django_tables2 as tables

class MyTable(Table):
    id = UUIDLinkDetailColumn(attrs=Table.ca.ID)    # UUID PK → links to detail view
    name = tables.Column()
    child_count = LinkChildColumn(name="child", verbose_name="Children", attrs=Table.ca.w10)
    created_dt = NaturalDayColumn()    # "3 days ago"
    modified_dt = NaturalTimeColumn()  # "2 hours ago"
```

**Table column attrs helpers** (shortcuts for Bootstrap column widths):
`Table.ca.ID`, `Table.ca.w10`, `Table.ca.w20`, `Table.ca.w30`, `Table.ca.w40`

---

## Forms & Crispy

```python
from crud_views.lib.crispy import (
    CrispyModelForm,
    CrispyDeleteForm,
    CrispyModelViewMixin,
    Column2, Column4, Column8, Column12,   # Bootstrap grid column helpers
)
from crispy_forms.layout import Row, Layout

class MyForm(CrispyModelForm):
    submit_label = "Save"    # required

    class Meta:
        model = MyModel
        fields = ["field1", "field2", "field3"]

    def get_layout_fields(self):
        # Return crispy-forms layout elements
        return Row(Column4("field1"), Column4("field2"), Column4("field3"))
        # or for full-width: return Column12("field1"), Column12("field2")
```

`CrispyDeleteForm` provides a confirmation checkbox — use it as `form_class` on delete views.

### Column grid reference

| Class | Bootstrap cols | Approx width |
|-------|---------------|-------------|
| `Column2` | 2/12 | ~17% |
| `Column4` | 4/12 | ~33% |
| `Column8` | 8/12 | ~67% |
| `Column12` | 12/12 | 100% |

---

## Filtering

```python
import django_filters
from crud_views.lib.views.list import ListViewFilterFormHelper
from crispy_forms.layout import Layout, Row

class MyFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="icontains")
    status = django_filters.ChoiceFilter(choices=MyModel.STATUS_CHOICES)
    class Meta:
        model = MyModel
        fields = ["name", "status"]

class MyFilterFormHelper(ListViewFilterFormHelper):
    layout = Layout(Row(Column4("name"), Column4("status")))

class MyListView(ListViewTableMixin, ListViewTableFilterMixin, ListViewPermissionRequired):
    cv_viewset = cv_my
    table_class = MyTable
    filterset_class = MyFilter
    formhelper_class = MyFilterFormHelper
```

---

## Settings

All settings go under `CRUD_VIEWS` in `settings.py`:

```python
CRUD_VIEWS = {
    # Required
    "EXTENDS": "base.html",                    # base template to extend

    # Manage view
    "MANAGE_VIEWS_ENABLED": "debug_only",      # "yes" | "no" | "debug_only"

    # Session
    "SESSION_DATA_KEY": "viewset",

    # Filter
    "FILTER_PERSISTENCE": True,
    "FILTER_ICON": "fa-solid fa-filter",
    "FILTER_RESET_BUTTON_CSS_CLASS": "btn btn-secondary",

    # Default per-row actions for list views
    "LIST_ACTIONS": ["detail", "update", "delete"],

    # Default page-level (context) actions per view type
    "LIST_CONTEXT_ACTIONS": ["parent", "filter", "create"],
    "DETAIL_CONTEXT_ACTIONS": ["home", "update", "delete"],
    "CREATE_CONTEXT_ACTIONS": ["home"],
    "UPDATE_CONTEXT_ACTIONS": ["home"],
    "DELETE_CONTEXT_ACTIONS": ["home"],
    "MANAGE_CONTEXT_ACTIONS": ["home"],
}
```

### django-object-detail settings (for DetailView)

```python
OBJECT_DETAIL_TEMPLATE_PACK_LAYOUT = "split-card"  # layout pack
OBJECT_DETAIL_TEMPLATE_PACK_TYPES = "default"
OBJECT_DETAIL_ICONS_LIBRARY = "fontawesome"         # "fontawesome" | "bootstrap"
OBJECT_DETAIL_ICONS_TYPE = "regular"                # "solid" | "regular" (FA only)
```

---

## Import Paths Cheatsheet

```python
# ViewSet
from crud_views.lib.viewset import ViewSet, ParentViewSet

# Views
from crud_views.lib.views import (
    ListView, ListViewPermissionRequired,
    DetailView, DetailViewPermissionRequired,
    CreateView, CreateViewPermissionRequired, CreateViewParentMixin,
    UpdateView, UpdateViewPermissionRequired,
    DeleteView, DeleteViewPermissionRequired,
    ActionView, ActionViewPermissionRequired,
    OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired,
    RedirectChildView,
    MessageMixin,
    ListViewTableMixin, ListViewTableFilterMixin,
)
from crud_views.lib.views.list import ListViewFilterFormHelper
from crud_views.lib.views.form import CustomFormViewPermissionRequired

# Table
from crud_views.lib.table import Table, UUIDLinkDetailColumn, LinkDetailColumn, LinkChildColumn
from crud_views.lib.table.columns import NaturalDayColumn, NaturalTimeColumn

# Forms / Crispy
from crud_views.lib.crispy import (
    CrispyModelForm, CrispyDeleteForm, CrispyModelViewMixin,
    Column2, Column4, Column8, Column12,
)

# Crispy layout helpers (standard crispy-forms)
from crispy_forms.layout import Layout, Row

# Filters (standard django-filter)
import django_filters

# Tables (standard django-tables2)
import django_tables2 as tables
```
