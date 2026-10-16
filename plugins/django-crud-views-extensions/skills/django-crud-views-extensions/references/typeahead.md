# crud_views_widget_typeahead — reference

*Available since package 0.3.0 (text typeahead, `TypeaheadSelect` popup and endpoint paging).*

A server-backed type-ahead **single** select for large, permission-sensitive model choice sets (thousands of
users), for forms and django-filter filters. Vanilla JS, no jQuery, CSP-safe (no `innerHTML`), ARIA combobox.

Contents: [Setup](#setup) · [Lookups](#lookups) · [Fields & filters](#fields--filters) ·
[Widgets](#widgets) · [Endpoint](#endpoint) · [Security](#security) · [Settings](#settings) ·
[django-pipeline](#django-pipeline) · [Skins](#skins)

## Setup

```python
INSTALLED_APPS = [..., "crud_views", "crud_views_widget_typeahead"]
```

```python
# urls.py — any prefix; the widgets build the URL from the name crud_views_typeahead:lookup
from django.urls import include, path

urlpatterns += [path("_typeahead/", include("crud_views_widget_typeahead.urls"))]
```

Assets come through `{% cv_js %}` / `{% cv_css %}`. No jQuery needed.

## Lookups

A lookup is one registered class per use case. It owns the **allowed set** (including the permission check),
the **search** and the **labels**. Endpoint and form field both resolve the lookup by name, so the restriction is
written once.

### Autodiscovery and registry

Put lookups in your app's `typeahead.py`. At startup the typeahead app imports the `typeahead.py` of every
installed app (like the admin's `admin.py`). Registering a name twice raises `ImproperlyConfigured`; binding to an
unregistered name raises `LookupNotFound` (subclass of `ImproperlyConfigured`). Names are global — namespace them
`"<app>.<use_case>"`.

### `TypeaheadLookup`

```python
from django.core.exceptions import PermissionDenied
from crud_views_widget_typeahead.lookups import TypeaheadLookup, register_lookup

@register_lookup("projects.projects")
class ProjectLookup(TypeaheadLookup):
    search_fields = ["name", "code"]
    ordering = ["name"]

    def get_queryset(self, request, **params):
        if not request.user.has_perm("projects.view_project"):
            raise PermissionDenied
        return Project.objects.filter(archived=False)

    def label(self, obj):
        return f"{obj.code} – {obj.name}"
```

| Attribute | Default | Meaning |
|---|---|---|
| `search_fields` | `[]` | `icontains`-searched; **every word** of the term must match one of them. Searching with none raises `ImproperlyConfigured` |
| `ordering` | `[]` | `order_by()` args; empty keeps the queryset's own ordering (else model `Meta.ordering`) |
| `max_results` | `10` | results per response; also the select popup's page size |
| `min_chars` | `2` | shorter terms return empty without a query. `0` lets the select popup list the first page on open |
| `login_required` | `True` | anonymous requests get `403 login_required` |

| Method | Meaning |
|---|---|
| `get_queryset(self, request, **params)` | **required.** The allowed set for this request and params. Raise `PermissionDenied` / `Http404` to refuse (endpoint answers `403 forbidden` / `404 not_found`) |
| `label(self, obj)` | displayed text; default `str(obj)`. Plain text — the frontend escapes it |

`params` are the keyword arguments given to `bind()`. Search results are made `.distinct()`, so joins in
`get_queryset` don't duplicate rows. Values are always the pk.

### Users: `register_user_lookup`

Decorate a function returning the allowed set:

```python
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from crud_views_widget_typeahead.lookups import register_user_lookup

@register_user_lookup("projects.members")
def members(request, project):
    if not request.user.has_perm("projects.view_project"):
        raise PermissionDenied
    return get_object_or_404(Project, pk=project).members.all()
```

This registers a `UserLookup` subclass whose `get_queryset` calls your function (the function is returned
unchanged). `UserLookup` searches `first_name`, `last_name`, `username`; orders by last name, first name, username
(case-insensitive); labels with `get_full_name()`, falling back to the username. Customise via `base=`:

```python
from crud_views_widget_typeahead.lookups import UserLookup, register_user_lookup

class UserWithUsernameLookup(UserLookup):
    def label(self, obj):
        return f"{obj.get_full_name() or obj.get_username()} ({obj.get_username()})"

@register_user_lookup("projects.members_with_username", base=UserWithUsernameLookup)
def members_with_username(request, project): ...
```

**The endpoint must never reveal more than the pages do:** check in `get_queryset` the same permission the page
using the field checks.

## Fields & filters

`TypeaheadField(lookup=..., **ModelChoiceField kwargs)` is a `ModelChoiceField` whose queryset comes from a
lookup. `TypeaheadFilter(lookup=..., **kwargs)` is a django-filter `ModelChoiceFilter` using it; filter URLs stay
`?assignee=<pk>`.

### `bind(request, **params)`

The single source of truth for a field. From the same lookup + params it:

- sets the field's queryset to `lookup.get_queryset(request, **params)` — used by save-time validation;
- signs `{lookup, params}` into a token for the widget — used by the endpoint.

So suggestions and validation are always the same set. Returns the field / filter.

- Params must be JSON values: pass UUIDs, dates, model instances as `str` (`project=str(project.pk)`). Anything
  else raises `ImproperlyConfigured` at bind time.
- `get_queryset` runs **at bind time**, i.e. while the form / FilterSet is constructed in the view. A
  `PermissionDenied` (or `Http404`) raised there propagates out of the view: the whole create/update/list page
  answers 403 (404), not just the endpoint. That is right when the lookup checks the same permission as the page.
  When the lookup's permission is stricter than the page's (e.g. `add_order` on a form also used for updates),
  either check the permission each page needs (`has_perm("orders.add_order") or has_perm("orders.change_order")`)
  or return `queryset.none()` instead of raising, so the field is merely empty.
- An unbound field raises `ImproperlyConfigured` when it renders or validates — bind in every code path
  (GET and POST) that builds the form.
- Don't pass `queryset=`; `bind()` overwrites it. Put every restriction in the lookup.
- `to_field_name=` raises `ImproperlyConfigured`.

### Plain Django form

```python
class TaskForm(forms.ModelForm):
    assignee = TypeaheadField(lookup="projects.members")

    class Meta:
        model = Task
        fields = ["title", "assignee"]

    def __init__(self, *args, request, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignee"].bind(request, project=str(project.pk))
```

### crud_views forms

`CrispyModelForm` has the view at `self.cv_view`; take the request (and, for child ViewSets, the parent object)
from there:

```python
from crud_views.lib.crispy import CrispyModelForm
from crud_views_widget_typeahead.fields import TypeaheadField

class TaskForm(CrispyModelForm):
    assignee = TypeaheadField(lookup="projects.members", required=False)

    class Meta:
        model = Task
        fields = ["title", "assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        project = self.cv_view.cv_get_parent_object()  # the project from the URL
        self.fields["assignee"].bind(self.cv_view.request, project=str(project.pk))
```

### Filters

Bind in the FilterSet's `__init__` (`self.request` is set by django-filter):

```python
import django_filters
from crud_views_widget_typeahead.filters import TypeaheadFilter

class TaskFilter(django_filters.FilterSet):
    assignee = TypeaheadFilter(lookup="projects.members")
    do_not_call_in_templates = True

    class Meta:
        model = Task
        fields = []

    def __init__(self, *args, project, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request, project=str(project.pk))
```

`TypeaheadFilter` defaults to `TypeaheadInput(submit_on_clear=True)`, so clearing the filter submits the filter
form; pass `widget=` to change that.

**`do_not_call_in_templates = True` is required under crud_views list views.** The crud_views list template tests
`{% if view.filterset_class %}`, and Django templates call callables — so the FilterSet class would be
instantiated there without a request and `bind(self.request)` would fail.

A list-wide filter usually needs its own lookup over every candidate (e.g. all users who are a member of any
team), since there is no parent object to scope by:

```python
@register_user_lookup("teams.any_member")
def any_member(request):
    if not request.user.has_perm("teams.view_team"):
        raise PermissionDenied
    return get_user_model().objects.filter(teams__isnull=False).distinct()
```

### Duplicate rows

If a lookup queryset is not distinct (M2M joins), the same object can appear in several rows; the field
tolerates that (pk is unique, any row is the object).

## Widgets

```python
from crud_views_widget_typeahead.widgets import TypeaheadInput, TypeaheadSelect
```

| Widget | Looks like | Use when |
|---|---|---|
| `TypeaheadInput` (default) | text input with a suggestion list | users know what they're looking for |
| `TypeaheadSelect` | Bootstrap `<select>` look; opens a popup with a search field and a scroll-paged list | users want to browse |

```python
assignee = TypeaheadField(lookup="projects.members", widget=TypeaheadSelect())
assignee = TypeaheadFilter(lookup="projects.members", widget=TypeaheadSelect(submit_on_clear=True))
```

Both take `attrs=None` (visible input / trigger button), `submit_on_clear=False` (`TypeaheadFilter` uses `True`),
`template_name=None` (overrides the settings template). Both can appear on one page.

Rendering:

- The visible input (or trigger button) has **no `name`**; a hidden input carries the field name and the pk.
- `required` is never rendered as an HTML attribute (a required visible input would accept text without a pk);
  `required=True` still validates server-side.
- `aria-describedby` is merged with Django's help-text/error ids.

Text typeahead behaviour: searches after `DEBOUNCE_MS` once `min_chars` are typed, highlights matches; ↓ opens,
↑/↓ preview, Enter selects; Enter never submits while the list is open or the text isn't a selection; Escape
restores the selected label; blur/submit restore it; clearing takes the clear button or fully emptied text; "N
more results – keep typing" when `count > max_results`.

Select popup behaviour: Enter/Space/↑/↓ or typing opens the popup and focuses search; with `min_chars = 0` the
first page lists immediately; scrolling to the end loads the next page (page size = `max_results`); Escape closes
only the popup (a surrounding crud_views modal stays open). The popup renders inside the widget, not at the end
of `<body>`, so it works in Bootstrap 5 modals — but an ancestor with `overflow: hidden` clips it.

### Modals and dynamic content

Both widgets initialise on `DOMContentLoaded` and on crud_views' `cv:modal:loaded` event. For other dynamically
added content (new formset rows, your own AJAX):

```javascript
window.cvTypeahead.init(container);        // text typeahead
window.cvTypeaheadSelect.init(container);  // select popup
```

## Endpoint

`GET <mount>/?t=<token>&q=<term>[&page=<n>]` — `t` the signed token from `bind()`, `q` the term, `page` 1-based
(select popup; missing/invalid/<1 → 1). Never cached; non-GET → `405`.

```json
{"results": [{"value": "42", "label": "Ada Lovelace"}, {"value": "7", "label": "Grace Hopper"}], "count": 57}
```

- `value` = pk as string, `label` = `lookup.label(obj)`, `count` = all matches before paging.
- Ordered by the lookup's `ordering` (else queryset/model ordering) with pk as final tiebreaker, so pages never
  repeat or skip rows.
- Terms shorter than `min_chars` → `{"results": [], "count": 0}` without a query.

Errors are JSON (never a login redirect — `fetch()` must get JSON) and never echo exception messages:

| Status | Body | When |
|---|---|---|
| 400 | `{"error": "bad_token"}` | bad signature, wrong payload shape, or lookup no longer registered |
| 403 | `{"error": "login_required"}` | `login_required = True` and anonymous user |
| 403 | `{"error": "forbidden"}` | `get_queryset` raised `PermissionDenied` |
| 404 | `{"error": "not_found"}` | `get_queryset` raised `Http404` |
| 405 | — | not `GET` |

## Security

- `bind()` signs `{"l": lookup_name, "p": params}` with `SECRET_KEY`, salt `crud_views.typeahead`. The browser
  can read the token but not change it (modified → `400 bad_token`), so it can't widen the search to another
  lookup or other params.
- Signed, **not encrypted**: params are visible in the page source. No secrets in params.
- **No expiry, on purpose:** the endpoint re-checks permission on every request by calling
  `get_queryset(request, **params)` with the current user. Open forms keep working overnight; a leaked token
  grants nothing beyond what the requesting user may see. Rotating `SECRET_KEY` invalidates open forms' tokens.
- Validation uses the same set: a pk outside it (hand-edited hidden input) fails like any invalid
  `ModelChoiceField` choice.

## Settings

```python
CRUD_VIEWS_TYPEAHEAD = {
    "EMIT": True,             # False: suppress the text typeahead's cv_js/cv_css output
    "TEMPLATE": "crud_views_widget_typeahead/typeahead.html",
    "DEBOUNCE_MS": 250,       # both widgets
    "SELECT_EMIT": True,      # False: suppress the select popup's cv_js/cv_css output
    "SELECT_TEMPLATE": "crud_views_widget_typeahead/typeahead_select.html",
}
```

The two widgets are separate asset bundles (`typeahead`, `typeahead_select`). `EMIT` / `SELECT_EMIT` are read
once at startup; templates and `DEBOUNCE_MS` on every render.

## django-pipeline

No third-party plugin, so nothing to vendor and no CDN mode. Add the static files to your bundle and switch off
the app's tag output:

```python
from crud_views_widget_typeahead.assets import select_source_files, source_files

_ta = source_files()
_tas = select_source_files()  # only if you use TypeaheadSelect
PIPELINE = {
    "JAVASCRIPT": {"main": {"source_filenames": [*_ta["js"], *_tas["js"]], "output_filename": "js/main.js"}},
    "STYLESHEETS": {"main": {"source_filenames": [*_ta["css"], *_tas["css"]], "output_filename": "css/main.css"}},
}
CRUD_VIEWS_TYPEAHEAD = {"EMIT": False, "SELECT_EMIT": False}
```

`crud_views_widget_typeahead.assets` is Django-free (safe in `settings.py`). `source_files()` →
`typeahead.js` / `typeahead.css`; `select_source_files()` → `typeahead-select.js` / `typeahead-select.css` (all
under `crud_views_widget_typeahead/`); `bundle()` / `select_bundle()` return the same lists the app registers.

Combined with the datetimepicker, put jQuery and the datetimepicker files in the same bundle; the typeahead files
have no ordering dependency on them.

## Skins

A design-system package can replace either widget's frontend and keep the server core (lookups, fields,
endpoint). Start from the default templates in
`src/crud_views_widget_typeahead/templates/crud_views_widget_typeahead/`.

1. **Template** — `CRUD_VIEWS_TYPEAHEAD["TEMPLATE"]` (or the widget's `template_name`). Context:
   `widget.attrs` (visible input: `id`, `class` incl. `form-control`, `autocomplete="off"`, `role="combobox"`,
   `aria-autocomplete="list"`, `aria-expanded`, `aria-controls`, merged `aria-describedby`) and
   `widget.typeahead`: `url` (endpoint incl. token; append `&q=…`), `label`, `value`, `hidden_name`, `hidden_id`,
   `listbox_id`, `hint_id`, `min_chars`, `debounce`, `submit_on_clear`, `i18n` (`hint`, `more`, `none`, `count`,
   `error`, `clear`, `listbox`; `{n}` = number placeholder).
2. **Assets** — register your own and switch ours off:

   ```python
   class YourSkinConfig(AppConfig):
       name = "your_skin"

       def ready(self):
           from crud_views.lib.assets import register_assets
           register_assets(key="your_skin_typeahead", js=["your_skin/typeahead.js"], css=["your_skin/typeahead.css"])
   ```

   ```python
   CRUD_VIEWS_TYPEAHEAD = {"TEMPLATE": "your_skin/typeahead.html", "EMIT": False}
   ```
3. **Contract** — hidden input carries the field `name` and the pk, `autocomplete="off"`, empty when nothing is
   selected. Visible text is the stored pk's label except while typing (restore on blur and submit). Clear only via
   clear button or fully emptied text. Arrow keys preview only. Enter never submits while the list is open or the
   text isn't a selection. Escape and highlight labels yourself — never insert server text as HTML. Show "N more"
   from `count`. ARIA combobox/listbox with a live result count. Re-initialise on `cv:modal:loaded` and expose an
   `init(root)` like `window.cvTypeahead.init`.

Select popup skin: same three steps with `SELECT_TEMPLATE` and `SELECT_EMIT = False`. `widget.attrs` land on the
trigger button (`class` incl. `form-select text-start`, `aria-haspopup="listbox"`, `aria-expanded`,
`aria-controls`, `aria-labelledby="<id> <id>_label"`); `widget.typeahead` adds `popup_id`, `label_id`,
`search_id`, `page_size`, and `i18n` adds `placeholder`, `search`, `loading`, `type_more`. Keep scroll paging,
Enter-never-submits-while-open, and Escape-closes-only-the-popup.
