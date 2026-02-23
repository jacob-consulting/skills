---
name: django-crud-views
description: "Build Django CRUD interfaces using the django-crud-views package. Use when creating, reading, updating, or deleting model records with class-based views; when wiring up ViewSets, ListViews, DetailViews, CreateViews, UpdateViews, or DeleteViews; when configuring tables with django-tables2, filters with django-filter, or forms with django-crispy-forms; when implementing nested/child resources with ParentViewSet; when adding permission-required views; when integrating django-fsm state machine transitions with WorkflowView or WorkflowViewPermissionRequired; when adding workflow audit history to models with WorkflowModelMixin; when using formsets with FormSetMixin; when working with polymorphic models; or any time the codebase imports from crud_views.lib, crud_views_workflow, or crud_views_polymorphic."
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

---

## Formsets (Inline Child Records)

Use `FormSetMixin` on Create/Update views to manage nested inline formsets. Configure with `cv_formsets`.

```python
from crud_views.lib.formsets import FormSet, FormSets, FormSetMixin, InlineFormSet
from crispy_forms.layout import Row

class ItemFormSet(InlineFormSet):
    model = Item
    parent_model = Order
    fk_name = "order"
    fields = ["name", "quantity", "price"]
    extra = 1

    def get_helper_layout_fields(self):
        return [Row(Column4("name"), Column4("quantity"), Column4("price"))]

class OrderCreateView(FormSetMixin, CrispyModelViewMixin, CreateViewPermissionRequired):
    cv_viewset = cv_order
    form_class = OrderCreateForm
    cv_formsets = FormSets(formsets={
        "items": FormSet(
            klass=ItemFormSet,
            title="Order Items",
            fields=["name", "quantity", "price"],
            pk_field="id",
        )
    })
```

---

## Polymorphic Models (`crud_views_polymorphic`)

Two-step create flow for polymorphic models (requires `django-polymorphic`).

Install: `pip install django-crud-views[polymorphic]`, add `"crud_views_polymorphic"` to `INSTALLED_APPS`.

```python
from crud_views_polymorphic.lib import (
    PolymorphicCreateSelectViewPermissionRequired,  # step 1: choose subtype
    PolymorphicCreateViewPermissionRequired,         # step 2: fill subtype form
    PolymorphicUpdateViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
)

class AnimalCreateSelectView(PolymorphicCreateSelectViewPermissionRequired):
    cv_viewset = cv_animal
    # cv_polymorphic_include = [Dog, Cat]  # optional whitelist
    # cv_polymorphic_exclude = [...]       # optional blacklist (mutually exclusive with include)

class AnimalCreateView(PolymorphicCreateViewPermissionRequired):
    cv_viewset = cv_animal
    polymorphic_forms = {Dog: DogForm, Cat: CatForm}

class AnimalUpdateView(PolymorphicUpdateViewPermissionRequired):
    cv_viewset = cv_animal
    polymorphic_forms = {Dog: DogForm, Cat: CatForm}

class AnimalDetailView(PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_animal
    cv_property_display = [...]
```

---

## WorkflowView (FSM State Transitions)

Integrates django-fsm-2 state machines with the CRUD framework. Provides transition execution, comment requirements, and a full audit log.

Full reference: see [references/workflow.md](references/workflow.md)

### Quick pattern

```python
# 1. Model: mix in WorkflowModelMixin, define states and @transition methods
from django_fsm import FSMField, transition
from crud_views_workflow.lib.enums import WorkflowComment, BadgeEnum
from crud_views_workflow.lib.mixins import WorkflowModelMixin

class MyModel(WorkflowModelMixin, models.Model):
    STATE_CHOICES = MyState       # TextChoices subclass
    STATE_BADGES = {MyState.NEW: BadgeEnum.LIGHT, MyState.DONE: BadgeEnum.SUCCESS}
    STATE_BADGE_DEFAULT = BadgeEnum.INFO  # fallback for states not in STATE_BADGES
    state = FSMField(default=MyState.NEW, choices=MyState.choices)

    @transition(field=state, source=MyState.NEW, target=MyState.DONE,
                custom={"label": "Complete", "comment": WorkflowComment.OPTIONAL})
    def wf_complete(self, request=None, by=None, comment=None):
        pass

# 2. Form
from crud_views_workflow.lib.forms import WorkflowForm
class MyWorkflowForm(WorkflowForm):
    class Meta(WorkflowForm.Meta):
        model = MyModel

# 3. View
from crud_views_workflow.lib.views import WorkflowViewPermissionRequired
class MyWorkflowView(CrispyModelViewMixin, MessageMixin, WorkflowViewPermissionRequired):
    cv_viewset = cv_my
    form_class = MyWorkflowForm
```

Install: `pip install django-crud-views[workflow]`, add `"crud_views_workflow.apps.CrudViewsWorkflowConfig"` to `INSTALLED_APPS`, run `migrate`.
