# Per-object permissions (`crud_views_guardian`)

## Per-Object Permissions (`crud_views_guardian`)

*Available since 0.4.0 (strict mode became the default in 0.6.0).*

Integrates [django-guardian](https://django-guardian.readthedocs.io/) for per-object permission checking and queryset filtering. Swap `ViewSet` → `GuardianViewSet` and `*ViewPermissionRequired` → `Guardian*ViewPermissionRequired`.

Install: `pip install django-crud-views[guardian]`, add `"guardian"` and `"crud_views_guardian.apps.CrudViewsGuardianConfig"` to `INSTALLED_APPS`, add `"guardian.backends.ObjectPermissionBackend"` to `AUTHENTICATION_BACKENDS`, set `ANONYMOUS_USER_NAME = None`, run `migrate`.

```python
from crud_views_guardian.lib.viewset import GuardianViewSet
from crud_views_guardian.lib.views import (
    GuardianListViewPermissionRequired,
    GuardianDetailViewPermissionRequired,
    GuardianCreateViewPermissionRequired,
    GuardianUpdateViewPermissionRequired,
    GuardianDeleteViewPermissionRequired,
)

cv_author = GuardianViewSet(model=Author, name="author")

class AuthorListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_author

class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
```

### Assigning permissions

```python
cv_author.assign_perm("view", user, author_instance)   # grant
cv_author.remove_perm("view", user, author_instance)   # revoke
cv_author.assign_perm("change", group, author_instance)
qs = cv_author.get_objects_for_user(user, "view")
```

### Strict mode (default)

`cv_guardian_accept_global_perms = False` by default — model-level Django permissions are **not** a fallback. Only explicit per-object grants count. Override per view:

```python
class AuthorDetailView(GuardianDetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_guardian_accept_global_perms = True  # allow model-level perms as fallback
```

On a child view the flag also covers the **parent** check: a model-level permission on the parent
model (e.g. `app.view_author`) is accepted as a fallback for the per-object grant — *since 0.23.0*;
before, the parent check ignored the flag and returned 403.

### Create views

- **Top-level creates** (no parent): standard model-level `add_<model>` permission is checked.
- **Child creates** (with parent viewset): guardian checks per-object permission on the parent using `cv_guardian_parent_create_permission`. Child create views **must** use `GuardianCreateViewPermissionRequired` — using plain `CreateViewPermissionRequired` hides the button permanently and blocks the form page.

### Child create button visibility

`cv_has_access` is a classmethod — it has no access to request or URL kwargs. When the "create" button is rendered from a child list page, `obj=None` and the parent cannot be determined inside `cv_has_access` alone.

`GuardianListViewPermissionRequired` solves this: its `cv_get_context` override resolves the parent from the URL via `cv_get_parent_object()` and calls `cv_create_has_access(user, rendering_view, parent_obj)` on the create view class. The default implementation checks `cv_guardian_parent_create_permission` on the parent. Override `cv_create_has_access` on the create view class for custom logic (e.g. role-based checks that go beyond a single guardian perm):

```python
class BookCreateView(CreateViewParentMixin, GuardianCreateViewPermissionRequired):
    cv_viewset = cv_book
    form_class = BookCreateForm

    @classmethod
    def cv_create_has_access(cls, user, rendering_view, parent_obj):
        # rendering_view is the list view instance — has .request, .kwargs, etc.
        if parent_obj is None:
            return False
        from guardian.core import ObjectPermissionChecker
        return ObjectPermissionChecker(user).has_perm("change_publisher", parent_obj)
```

### Parent viewsets

```python
cv_book = GuardianViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    cv_guardian_parent_permission="view",           # for list/detail/update/delete
    cv_guardian_parent_create_permission="change",  # for create (None = use above)
)
```

Setting either to `None` disables the parent check for that view type.

### Cascading Deletes with Per-Object Permissions

When `cv_show_related_objects = True` on a Guardian delete view, related objects are filtered using per-object `view` permissions (via `guardian.shortcuts.get_objects_for_user`) instead of model-level permissions:

```python
class PublisherDeleteView(CrispyViewMixin, GuardianDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True
```

Objects the user has per-object `view` permission for are shown with full details; others appear as aggregated counts.

### GuardianManageView

GuardianManageView: auto-wired by `GuardianViewSet.register()`. Extends ManageView with a Guardian Configuration section, per-object permission holder counts (Group → Permission → N objects), and a Guardian Mixin column in the Views table. No manual configuration required — just enable manage views or add users to CRUD_VIEWS_MANAGE group.
To customise the manage view class for a specific viewset, pass `manage_view_class="dotted.path.MyClass"` to `GuardianViewSet(...)` (or plain `ViewSet(...)`). Global defaults: `CRUD_VIEWS_GUARDIAN_MANAGE_VIEW_CLASS` for guardian viewsets, `CRUD_VIEWS_MANAGE_VIEW_CLASS` for plain viewsets. Per-viewset field takes priority over the global setting.
