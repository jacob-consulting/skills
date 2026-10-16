---
name: django-crud-views
description: "Build Django CRUD interfaces using the django-crud-views package. Use when wiring up ViewSets or List/Detail/Create/Update/Delete class-based views; configuring tables with django-tables2, filters with django-filter, or forms with django-crispy-forms; building nested/child resources with ParentViewSet; adding permission-required views or per-object permissions with Guardian; integrating django-fsm transitions with WorkflowView or WorkflowModelMixin; using formsets with FormSetMixin or conditional field-groups; rendering property grids with ObjectDetailView and cv_property_display; registering static assets, CSP nonces or SRI hashes (register_assets) or bundling them for django-pipeline (cv_sources); working with polymorphic models; showing non-ORM data (S3, APIs) with Resource; folding actions into a ⋯ menu or showing them disabled; diagnosing system checks such as viewset.W280; or when code imports crud_views, crud_views_object_detail, crud_views_workflow, crud_views_polymorphic, or crud_views_guardian."
---

# django-crud-views

A library that wires together class-based views, django-tables2, django-filter, and django-crispy-forms into a coherent
CRUD framework. A **ViewSet** groups all views for one model and generates their URL patterns; each **CrudView**
subclass registers itself with its ViewSet through `cv_viewset`, and sibling views find each other by **key**
(`"list"`, `"detail"`, `"update"`, …) to render action buttons and redirects.

Supported: Python ≥ 3.12, tested on 3.12–3.15 (3.15 since 0.29.1) with Django 4.2 / 5.2 / 6.0; Django 4.2 only on
Python ≤ 3.13, as Django itself requires. This skill describes package **0.29.1**. If the project pins an older
version, or code mentions names you can't find here, read [references/migration.md](references/migration.md).

## How to use this skill

This file holds the core model and the patterns almost every task needs. Each feature beyond that has its own
reference file with exact import paths, attribute names and the startup checks that guard it. **Read the matching
file before writing code for that feature** — the attribute names are specific (`cv_cancel_keys`, not
`cancel_keys`), many features have non-obvious rules (mixin order, which view types support modals, Guardian's
strict mode), and guessing produces code that silently does nothing or fails `manage.py check`.

| Task | Read |
|---|---|
| First ViewSet, step by step | [quickstart.md](references/quickstart.md) |
| Detail page: own template vs property grid (`cv_property_display`, `ObjectDetailView`) | [detail-views.md](references/detail-views.md) |
| Card grids, filters (django-filter), ordering, up/down reordering | [lists-and-cards.md](references/lists-and-cards.md) |
| Delete protection / cascade display, custom form views, one-click action views, cancel/success redirect targets, modals, transactions and `cv_on_commit` | [form-views.md](references/form-views.md) |
| Inline formsets, conditional field-groups and conditional formsets | [forms-and-formsets.md](references/forms-and-formsets.md) |
| Nested (child) ViewSets, context buttons (child/sibling/view-level), disabling or hiding actions, `⋯` action menus | [actions-and-buttons.md](references/actions-and-buttons.md) |
| Per-object permissions with django-guardian | [guardian.md](references/guardian.md) |
| Polymorphic models (django-polymorphic) | [polymorphic.md](references/polymorphic.md) |
| FSM workflows (django-fsm-2), transitions, audit log | [workflow.md](references/workflow.md) |
| Non-ORM data (S3, REST APIs) via `Resource` | [resources.md](references/resources.md) |
| Static assets, CSP nonces, SRI, django-pipeline bundling | [assets.md](references/assets.md) |
| Base-template override, breadcrumbs | [templates-and-navigation.md](references/templates-and-navigation.md) |
| All `CRUD_VIEWS_*` settings | [settings.md](references/settings.md) |
| A system check fired (`viewset.E255`, `crud_views.W345`, …) | [system-checks.md](references/system-checks.md) |
| Every ViewSet / view attribute, mixins, columns, import cheatsheet | [api-reference.md](references/api-reference.md) |
| Upgrading, or a project on an older version | [migration.md](references/migration.md) |

After wiring views, run `python manage.py check`: most misconfigurations are reported there at startup.

---

## Setup

```python
# pip install django-crud-views   (extras: [guardian], [ordered], [polymorphic], [workflow], [all])
INSTALLED_APPS = [
    ...,
    "django.contrib.humanize",
    "django_bootstrap5",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_tables2",
    "crud_views_object_detail",          # only if you use ObjectDetailView (property grid)
    "crud_views.apps.CrudViewsConfig",
    "myapp",
]
CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRUD_VIEWS_EXTENDS = "myapp/crud_views.html"   # required: your base template (crud_views.E100 if missing)
```

The `CRUD_VIEWS_EXTENDS` template is what every crud_views page extends. It must `{% load crud_views %}`, render
`{% cv_css %}` and `{% cv_js %}` (core JS/CSS and registered bundles) and `{% cv_config %}` (modal shell), and define
the blocks the views fill — at least `{% block cv_content %}`, typically also `cv_header`, `cv_context` (with
`{% cv_context_actions object %}`), `cv_paragraph` and `cv_filter`. All other settings are optional:
[settings.md](references/settings.md).

---

## View classes

| View class | Import from | Use for |
|---|---|---|
| `ListViewPermissionRequired` (+ `ListViewTableMixin`) | `crud_views.lib.views` | Paginated list with a django-tables2 table |
| `DetailViewPermissionRequired` | `crud_views.lib.views` | Single object with your own template |
| `ObjectDetailViewPermissionRequired` | `crud_views_object_detail.lib` | Single object as a property grid |
| `CreateViewPermissionRequired` | `crud_views.lib.views` | New object form |
| `UpdateViewPermissionRequired` | `crud_views.lib.views` | Edit object form |
| `DeleteViewPermissionRequired` | `crud_views.lib.views` | Confirm-delete form (`CrispyDeleteForm`) |
| `CustomFormViewPermissionRequired` | `crud_views.lib.views.form` | Custom form attached to an existing object |
| `ActionViewPermissionRequired` | `crud_views.lib.views` | One-click POST action on an existing object |
| `CardListViewPermissionRequired` | `crud_views.lib.views` | Card grid with action buttons |
| `WorkflowViewPermissionRequired` | `crud_views_workflow.lib.views` | FSM state transitions with audit log |

Every class also exists without `PermissionRequired` (no permission check). Guardian variants
(`Guardian…PermissionRequired` in `crud_views_guardian.lib.views`) exist for list, card, detail, create, update,
delete and action views. The `PermissionRequired` variants check the Django model permission matching the view
(`view_`, `add_`, `change_`, `delete_<model>`) and hide action buttons the user can't use.

**Mixins always go before the base view class:** `CrispyViewMixin, MessageMixin, CreateViewPermissionRequired`.

Buttons are configured by key: `cv_list_actions` (per-row buttons on list/card views), `cv_context_actions`
(page-level toolbar). Custom views register a new key with `cv_key` and `cv_path`.

---

## Core pattern: one model, five views

```python
# myapp/views.py
import django_tables2 as tables
from crispy_forms.layout import Row
from crud_views.lib.crispy import Column4, CrispyDeleteForm, CrispyModelForm, CrispyViewMixin
from crud_views.lib.table import Table, UUIDLinkDetailColumn
from crud_views.lib.views import (
    CreateViewPermissionRequired, DeleteViewPermissionRequired, DetailViewPermissionRequired,
    ListViewPermissionRequired, ListViewTableMixin, MessageMixin, UpdateViewPermissionRequired,
)
from crud_views.lib.viewset import ViewSet

from .models import Author

cv_author = ViewSet(model=Author, name="author", icon_header="fa-regular fa-user")  # pk type auto-detected


class AuthorTable(Table):
    id = UUIDLinkDetailColumn()          # LinkDetailColumn for integer pks
    first_name = tables.Column()
    last_name = tables.Column()


class AuthorForm(CrispyModelForm):
    submit_label = "Save"

    class Meta:
        model = Author
        fields = ["first_name", "last_name", "pseudonym"]

    def get_layout_fields(self):
        return Row(Column4("first_name"), Column4("last_name"), Column4("pseudonym"))


class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    table_class = AuthorTable
    cv_list_actions = ["detail", "update", "delete"]


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    template_name = "myapp/author_detail.html"   # extends cv_extends, fills {% block cv_content %}


class AuthorCreateView(CrispyViewMixin, MessageMixin, CreateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message_template_code = "Created »{{ object }}«"


class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_message_template_code = "Updated »{{ object }}«"


class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    cv_viewset = cv_author
    form_class = CrispyDeleteForm
    cv_message_template_code = "Deleted »{{ object }}«"
```

```python
# urls.py — every ViewSet, including child ViewSets, adds its own patterns
urlpatterns += cv_author.urlpatterns
```

For a property grid instead of a hand-written detail template, see [detail-views.md](references/detail-views.md).

---

## Nested resources (child ViewSets)

```python
from crud_views.lib.table import LinkChildColumn
from crud_views.lib.views import CreateViewParentMixin
from crud_views.lib.viewset import ParentViewSet

cv_book = ViewSet(model=Book, name="book", parent=ParentViewSet(name="author"))  # /author/<author_pk>/book/


class BookCreateView(CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    cv_viewset = cv_book          # CreateViewParentMixin assigns the FK to the parent from the URL
    form_class = BookForm         # don't include the parent FK field in the form


class AuthorTable(Table):
    books = LinkChildColumn(name="book", verbose_name="Books")   # link from parent row to child list
```

`ParentViewSet(attribute=...)` names the FK field when it differs from the parent's name. Child list pages get a
`"parent"` context action automatically. Buttons from a parent detail page down to the children
(`ChildContextButton`) and between siblings: [actions-and-buttons.md](references/actions-and-buttons.md). With
django-guardian, child create views need `GuardianCreateViewPermissionRequired`: [guardian.md](references/guardian.md).

---

## Hooks and side effects

- Form views: override `cv_form_valid(self, context)` (saves the instance; `context["form"]`, `context["object"]`)
  or `cv_form_valid_hook(self, context)` (after save).
- Action views: implement `action(self, context) -> bool` (truthy → success message, falsy → error message).
- The write phase runs inside `transaction.atomic()`. **Put side effects — mail, Celery tasks, webhooks — in
  `cv_on_commit(self, context)`**, which runs after the commit and never after a rollback; in `cv_form_valid_hook`,
  `action()` or a workflow's `on_transition` they would run before the commit. Details:
  [form-views.md](references/form-views.md#transactions--hooks-since-0270).

---

## Common mistakes

| Mistake | Fix | More |
|---|---|---|
| Mixin after the base view class | Mixins come **before**: `CrispyViewMixin, MessageMixin, CreateViewPermissionRequired` | |
| Child ViewSet URLs missing | Every ViewSet needs its own `urlpatterns += cv_book.urlpatterns` | |
| FK not assigned on child create | Add `CreateViewParentMixin` to the child create view | |
| `ViewSet(pk="UUID")` → no URL matches | `pk` is a URL regex; leave it unset (auto-detected) or use `ViewSet.PK.UUID` | api-reference.md |
| Mail / Celery task sent although the save rolled back | Move it from `cv_form_valid_hook` / `action()` / `on_transition` to `cv_on_commit(context)` | form-views.md |
| `cv_property_display` renders nothing | Core `DetailView` has no property grid — use `ObjectDetailView`, or put `ObjectDetailMixin` first on a polymorphic/guardian detail view | detail-views.md |
| `cv_modal = True` raises `viewset.E251` | Modals support only `DeleteView`, `DetailView`, `CustomFormView`, `CustomFormNoObjectView` | form-views.md |
| `cv_modal_size` raises `viewset.E250` | Exact values only: `""`, `"modal-sm"`, `"modal-lg"`, `"modal-xl"` (not `"lg"`, `"large"`) | form-views.md |
| Cascading deletes not shown | `cv_show_related_objects = True` (opt-in); links need `cv_link_related_objects = True` and a `detail` view on the related ViewSet | form-views.md |
| `DeleteView` success to `"detail"` fails `viewset.E254` | The object is gone after delete; send success to a list-type view | form-views.md |
| `cv_cancel_keys` origin lost after a validation error | An overridden `*.content.html` posts to `request.path`; use `action="{{ request.get_full_path }}"` | form-views.md |
| `AttributeError: type object '…FormSet' has no attribute 'can_order'` | `FormSet(klass=...)` needs the result of `inlineformset_factory(..., formset=YourInlineFormSet)`, not the `InlineFormSet` subclass; don't put `model`/`fields` on the subclass | forms-and-formsets.md |
| Formset rows never render | The parent form layout lacks `Formsets()`, or crispy's `form_tag` is still on | forms-and-formsets.md |
| Polymorphic list offers `"create"` | Use `cv_context_actions = ["create_select"]` | polymorphic.md |
| Guardian: users see no objects | Strict mode ignores model-level grants; call `assign_perm`, or set `cv_guardian_accept_global_perms = True` | guardian.md |
| Guardian child create: button always hidden | The child create view uses `CreateViewPermissionRequired` instead of `GuardianCreateViewPermissionRequired` | guardian.md |
| Guardian child create: button always visible | `cv_guardian_parent_create_permission` not set on the child `GuardianViewSet` | guardian.md |
| Hand-placed `{% cv_context_button %}` for a POST key does nothing | Also render `{% cv_context_action_form "key" %}` outside any `.btn-group` | detail-views.md |
| Startup fails `viewset.E110` on a backend-only view | Give it `cv_action_label_template_code` and `cv_action_short_label_template_code`; `cv_backend_only = True` exempts only header/paragraph | system-checks.md |
| Startup fails `viewset.E255` | A context button's target (`key_target`, `child_name`/`child_key`, `sibling_name`) doesn't resolve — fix the name or register the view | actions-and-buttons.md |
| Startup warns `viewset.W280` | A `cv_*` attribute no class recognizes — fix the typo, or allow it via `cv_check_ignore_attributes` | system-checks.md |
| Startup warns `viewset.W290`, or no `⋯` menu appears | A key in the view's own `cv_*_actions_inline` isn't among its actions; or the project overrides `columns/actions.html` / `tags/context_actions.html` / `tags/card.html` without the `{% if group is None %}` branch | actions-and-buttons.md |
| Overriding `tags/list_action.html` / `tags/context_action.html` loses the accessible name | Keep `<span class="visually-hidden">{{ cv_action_label }}</span>` and the icon's `aria-hidden="true"`. Prefer that over `aria-label`: same name, and Sonar's `Web:S7927` misreads `aria-label` next to template tags | |
| `card-rows` detail tooltip never appears | Needs `{% cv_js %}` and Bootstrap's JS; for markup you inject yourself call `cv.initTooltips(root)` | detail-views.md |
| Signed card ordering link `?order=+name` | `+` decodes to a space; ascending is the bare name `?order=name`; in signed mode `dir` is ignored | lists-and-cards.md |
| `ImportError: cannot import name 'PrimaryKeys' ... (circular import)` at startup | A `models.py` imports `crud_views.lib.viewset` / `crud_views.lib.table` (e.g. a `Resource` using `ViewSet.PK`); keep crud_views code in `views.py` | resources.md |
| `ImportError` on `import crud_views` | `django-filter` and `django-crispy-forms` are required dependencies; fix the install | |
| `PIPELINE` built with `[*cv_sources("js"), ...]` → `AppRegistryNotReady` | Keep it lazy: `cv_sources("js", before=[...], after=[...])` or `[...] + cv_sources("js")` | assets.md |
| Extension bundled by pipeline in CDN mode (`W345`) | Switch the extension to vendored mode (e.g. datetimepicker `SOURCE="vendored"` + `cv_vendor_datetimepicker`); list CDN entries with `manage.py cv_assets --external` | assets.md |
