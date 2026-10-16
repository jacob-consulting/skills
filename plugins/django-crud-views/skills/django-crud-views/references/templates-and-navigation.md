# Base templates and breadcrumbs

## Base template override

The base template each view extends (`cv_extends` in templates) resolves:
view `cv_extends_template` → ViewSet `extends` → global `CRUD_VIEWS_EXTENDS`.

```python
# all views in this ViewSet extend a custom base:
cv_author = ViewSet(model=Author, name="author", extends="myapp/author_base.html")

# or a single view:
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_extends_template = "myapp/author_list_base.html"
```

**Caveat:** the override template MUST NOT contain `{% extends cv_extends %}`
— it is itself the base being extended, so re-extending `cv_extends` makes it
extend itself and raises `TemplateDoesNotExist`. Point it at a real base
template instead. Misconfigured templates are caught at startup as
`crud_views.viewset.E111`.

---

## Breadcrumbs

`CrudViewBreadcrumbMixin` (import from `crud_views.lib.breadcrumb`) adds a Bootstrap 5.3
breadcrumb to any CrudView. The trail follows the ViewSet hierarchy —
`[prefix] › (ancestors …) › container › object › action` — and walks nested ViewSets:
an Employee update page under Company › Department shows
`Companies › ACME › Departments › Sales › Employees › Jane Doe › Edit`.

```python
from crud_views.lib.breadcrumb import BreadcrumbItem, CrudViewBreadcrumbMixin

# adopt once in a project-wide mixin, then put it FIRST in every view's MRO
class BreadcrumbMixin(CrudViewBreadcrumbMixin):
    pass

class EmployeeDetailView(BreadcrumbMixin, DetailViewPermissionRequired):
    cv_viewset = cv_employee
```

Render it in the `CRUD_VIEWS_EXTENDS` base template — safe to place unconditionally,
the tag renders nothing for views without the mixin:

```html
{% load crud_views %}
{% cv_breadcrumb %}
```

Hook into the host site's navigation with the `CRUD_VIEWS_BREADCRUMB_PREFIX` setting
(static, global) and/or a `cv_breadcrumb_prefix()` override (dynamic, per request):

```python
CRUD_VIEWS_BREADCRUMB_PREFIX = [{"title": "Home", "url_name": "home"}]  # settings.py

class HostNavBreadcrumbMixin(CrudViewBreadcrumbMixin):
    def cv_breadcrumb_prefix(self):
        return super().cv_breadcrumb_prefix() + [BreadcrumbItem(title="Admin area", url_name="admin-dashboard")]
```

Key attributes / behavior:

- `cv_breadcrumb_key_object = "detail"` — view key object items link to; a typo'd
  override triggers check `viewset.W270`. Viewsets without a detail view render object
  items unlinked; card-only viewsets use the card view as container.
- `cv_breadcrumb_container_label` — overrides the container (list/card) label; set it on
  the container view class (applies also when the viewset appears as an ancestor).
- `cv_breadcrumb_object_label(obj)` — defaults to `str(obj)`; override for expensive `__str__`.
- The last item is always rendered `active` + `aria-current="page"` and never a link.
- One scoped DB query per ancestor level (memoized per request); a tampered parent pk in
  the URL yields 404, so cross-tenant labels never leak.
- Malformed `CRUD_VIEWS_BREADCRUMB_PREFIX` entries fail system check `crud_views.E102`.
