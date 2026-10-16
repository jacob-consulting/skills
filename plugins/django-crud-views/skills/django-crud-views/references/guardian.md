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

### Grant the creator access to what they create

Nothing grants per-object permissions automatically. In strict mode a user who just created an object
**cannot see it**: the success redirect lands on a list that filters it out, and its detail page returns 403.
Grant the creator their permissions in `cv_form_valid`, after `super()` has saved the object. This is a DB write,
so it belongs inside the transaction (not in `cv_on_commit`): if the save rolls back, so do the grants.

```python
class PublisherCreateView(CrispyViewMixin, MessageMixin, GuardianCreateViewPermissionRequired):
    cv_viewset = cv_publisher
    form_class = PublisherForm

    def cv_form_valid(self, context):
        super().cv_form_valid(context)                  # saves; self.object is set
        for perm in ("view", "change", "delete"):
            cv_publisher.assign_perm(perm, self.request.user, self.object)
```

Do the same on child create views (with the child ViewSet's `assign_perm`), unless child rows inherit access
from the parent (next section).

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

### Do children inherit the parent's grant? (No, by default)

A child view on `Guardian*ViewPermissionRequired` checks **two** things: the parent check above *and* the
per-object permission on the child row itself. So a user with `view` on a publisher, but no grants on its books,
gets an **empty** book list and 403 on each book. Every book needs its own grant (or a group grant).

When the parent grant should cover the children ("whoever may see the publisher sees all its books"), keep the
parent check and drop only the per-row check. The parent check in `dispatch()` is then the only gate:

- **List:** stay on `GuardianListViewPermissionRequired` and skip only its per-row queryset filter. Don't switch
  to the plain list view: the guardian list is what resolves the parent for the child **create** button. On a plain
  list that button is always hidden.
- **Detail:** `GuardianParentPermissionMixin` plus the **plain** detail view, with `cv_has_access` opened up.
  Without that, the plain view checks the model-level `view_book` permission and hides the row buttons.

```python
from crud_views_guardian.lib.mixins import GuardianParentPermissionMixin, GuardianQuerysetMixin


class BookListView(ListViewTableMixin, GuardianListViewPermissionRequired):
    cv_viewset = cv_book
    table_class = BookTable
    cv_list_actions = ["detail"]

    def get_queryset(self):
        # skip GuardianQuerysetMixin's per-row filter; still only this publisher's books
        return super(GuardianQuerysetMixin, self).get_queryset()


class ParentGrantAccess(GuardianParentPermissionMixin):
    @classmethod
    def cv_has_access(cls, user, obj=None):
        return True   # button visibility only; dispatch() still enforces the parent grant


class BookDetailView(ParentGrantAccess, DetailViewPermissionRequired):
    cv_viewset = cv_book
    template_name = "catalog/book_detail.html"
```

Verified behaviour: with only `view` on publisher P1, the user sees all of P1's books (none of P2's) and can open
them, P2's book pages return 403, and P1's "create" button appears only once the user also has P1's
`cv_guardian_parent_create_permission`.

All non-create child views share `cv_guardian_parent_permission`. If you also put update/delete on
`ParentGrantAccess`, anyone with `view` on the parent could edit its children. Keep those on
`GuardianUpdateViewPermissionRequired` / `GuardianDeleteViewPermissionRequired` (per-row grants), or give them their own
access rule.

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
