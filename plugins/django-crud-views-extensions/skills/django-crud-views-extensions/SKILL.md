---
name: django-crud-views-extensions
description: "Add date/time pickers and server-backed type-ahead selects to Django forms and django-filter filters with the django-crud-views-extensions package (apps crud_views_widget_datetimepicker and crud_views_widget_typeahead). Use when adding DateTimePickerInput / DatePickerInput / TimePickerInput or an xdsoft jQuery DateTimePicker to a form; making date formats follow the request locale; serving the picker from vendored static files instead of a CDN (GDPR, cv_vendor_datetimepicker); replacing a ModelChoiceField or filter dropdown over thousands of rows (users, members, customers) with an autocomplete / type-ahead / searchable select; writing typeahead lookups (TypeaheadLookup, register_lookup, register_user_lookup), binding TypeaheadField / TypeaheadFilter with bind(), using TypeaheadSelect; skinning the typeahead; bundling either app with django-pipeline; configuring CRUD_VIEWS_DATETIMEPICKER or CRUD_VIEWS_TYPEAHEAD; diagnosing checks crud_views.E332/E333/W330/W331; or when code imports crud_views_widget_*."
---

# django-crud-views-extensions

Form widgets for [django-crud-views](https://github.com/jacob-consulting/django-crud-views), shipped as the PyPI
package `django-crud-views-extensions`. Two independent Django apps:

| App | Gives you | Use when |
|---|---|---|
| `crud_views_widget_datetimepicker` | `DateTimePickerInput`, `DatePickerInput`, `TimePickerInput` (xdsoft jQuery DateTimePicker) | a date / time / datetime field should get a picker |
| `crud_views_widget_typeahead` | `TypeaheadField`, `TypeaheadFilter`, lookups, one JSON endpoint; widgets `TypeaheadInput` and `TypeaheadSelect` | a foreign-key choice is too large for a `<select>` (thousands of users) and/or must be restricted by permission |

The apps are named as if they lived in django-crud-views itself: import paths (`crud_views_widget_<name>.<module>`)
and settings keys (`CRUD_VIEWS_<NAME>`) stay stable if an app moves into the core package. Don't invent other
import paths.

Requirements: Python ≥ 3.12, django-crud-views ≥ 0.29, jQuery (datetimepicker only). For ViewSets, views, tables
and forms themselves, see the **django-crud-views** skill; this skill covers only the widgets.

Read the reference for the app you're working with — it has the full API, settings, and edge cases:

- Datetimepicker → [references/datetimepicker.md](references/datetimepicker.md)
- Typeahead → [references/typeahead.md](references/typeahead.md)

Docs: <https://django-crud-views-extensions.readthedocs.io/en/stable/> · Live demo (log in `admin`/`admin`):
<https://django-crud-views-extensions-demo.onrender.com/>

---

## Install

```bash
pip install django-crud-views-extensions   # or: uv add django-crud-views-extensions
```

```python
INSTALLED_APPS = [
    # ...
    "crud_views",
    "crud_views_widget_datetimepicker",  # only the apps you use
    "crud_views_widget_typeahead",
]
```

**No `Media` class, no extra template tags.** Both apps register their JS/CSS with the django-crud-views asset
registry in `AppConfig.ready()`, so the `{% cv_css %}` / `{% cv_js %}` tags the base template already has deliver
them on every page — including content loaded into crud-views modals. Don't add `{{ form.media }}` or `<script>`
tags for these widgets. The datetimepicker is a jQuery plugin: jQuery must load **before** `{% cv_js %}`.

The typeahead needs its endpoint mounted (any prefix; the widgets resolve the URL name
`crud_views_typeahead:lookup` themselves). The datetimepicker needs no URLs.

```python
urlpatterns += [path("_typeahead/", include("crud_views_widget_typeahead.urls"))]
```

---

## Datetimepicker in one screen

*Available since 0.1.1; locale-following formats since 0.2.0.*

```python
from crud_views.lib.crispy import CrispyModelForm
from crud_views_widget_datetimepicker.widgets import DatePickerInput, DateTimePickerInput, TimePickerInput

class EventForm(CrispyModelForm):
    class Meta:
        model = Event
        fields = ["title", "day", "doors_open", "starts_at"]
        widgets = {
            "day": DatePickerInput(config={"minDate": 0}),        # any xdsoft option goes in config
            "doors_open": TimePickerInput(config={"step": 15}),
            "starts_at": DateTimePickerInput(),
        }
```

- **Formats follow the active request language** (`15.10.2026 19:00` under `de`, `2026-10-15 19:00` under `en`),
  and the widget parses submitted values with the same format. Don't hand-set `input_formats` or a picker
  `format` to "make German work" — it already does. Pin a format only when the product needs one fixed format.
- Config merge order, low → high: widget class defaults → `lang` → `CRUD_VIEWS_DATETIMEPICKER["DEFAULTS"]` →
  per-field `config`.
- Default source is the jsDelivr CDN. For production / GDPR / CSP / django-pipeline, use **vendored mode**:
  `{"SOURCE": "vendored", "VENDOR_DIR": BASE_DIR / "vendored_static"}`, put `VENDOR_DIR` in `STATICFILES_DIRS`,
  run `python manage.py cv_vendor_datetimepicker` (before `collectstatic`).

Details, all settings, format tokens, pipeline and checks: [references/datetimepicker.md](references/datetimepicker.md)

---

## Typeahead in one screen

*Available since 0.3.0.*

The pieces, and why there are this many: the **lookup** is the single place that defines the allowed set
(including the permission check). `bind()` derives both the save-time validation queryset and a signed token for
the endpoint from that one lookup + params, so what the user can find and what the form accepts can never drift.

```python
# <app>/typeahead.py — autodiscovered at startup, like admin.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from crud_views_widget_typeahead.lookups import register_user_lookup

@register_user_lookup("teams.members")
def team_members(request, team):
    if not request.user.has_perm("teams.view_team"):   # same permission as the pages using it
        raise PermissionDenied
    return get_object_or_404(Team, pk=team).members.all()
```

```python
# forms.py
from crud_views.lib.crispy import CrispyModelForm
from crud_views_widget_typeahead.fields import TypeaheadField

class TaskForm(CrispyModelForm):
    assignee = TypeaheadField(lookup="teams.members", required=False)

    class Meta:
        model = Task
        fields = ["title", "assignee"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        team = self.cv_view.cv_get_parent_object()
        self.fields["assignee"].bind(self.cv_view.request, team=str(team.pk))  # params: JSON values only
```

```python
# filters.py
import django_filters
from crud_views_widget_typeahead.filters import TypeaheadFilter

class TaskFilter(django_filters.FilterSet):
    assignee = TypeaheadFilter(lookup="teams.any_member")
    do_not_call_in_templates = True   # required under crud_views list views — see Common Mistakes

    class Meta:
        model = Task
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters["assignee"].bind(self.request)
```

- For non-user models subclass `TypeaheadLookup` with `@register_lookup("name")`, set `search_fields`
  (required for searching), optionally `ordering`, `max_results`, `min_chars`, `label(obj)`.
- `TypeaheadSelect` (`widget=TypeaheadSelect()`) gives a browse-style select popup with scroll paging; pair it
  with `min_chars = 0` on the lookup so it lists entries as soon as it opens.
- Tokens are signed, not encrypted, and never expire — permission is re-checked on every request.
- `bind()` calls the lookup's `get_queryset` while the form / FilterSet is built, so a `PermissionDenied` there
  turns the **whole page** (create, update, list) into a 403 — not just the search. Use the page's own permission;
  if the field should merely be empty for some users, return `.none()` instead of raising.

Lookups, widgets, endpoint, security, skins, pipeline: [references/typeahead.md](references/typeahead.md)

---

## Common Mistakes

| Mistake | Fix |
|---|---|
| Adding `{{ form.media }}`, a `Media` class or `<script>` tags for these widgets | Nothing to add: assets come through `{% cv_js %}` / `{% cv_css %}` |
| jQuery loaded after `{% cv_js %}` — pickers never appear | Load jQuery before `{% cv_js %}` in the base template |
| Hand-written `input_formats` / picker `format` to support a locale | Remove them; the widget derives and parses the locale format itself |
| Per-field `config={"lang": ...}` on one field | The plugin language is page-global — it switches every picker on the page. Use settings `LANG` or leave it to the request language |
| Pinned picker `format` with tokens outside `d m Y y H i s` | Only those tokens map to strftime; otherwise the field's `input_formats` must accept what the picker writes |
| `SOURCE: "vendored"` without `VENDOR_DIR` (E332) or `VENDOR_DIR` missing from `STATICFILES_DIRS` | Set both; run `cv_vendor_datetimepicker` |
| W330 / W331 after deploying or changing `VERSION` | Run `python manage.py cv_vendor_datetimepicker` (in the build, before `collectstatic`) or commit the vendored dir |
| Bundling the datetimepicker with django-pipeline in CDN mode | Use vendored mode, build the bundle from `assets.source_files()`, set `EMIT: False` |
| A `TypeaheadField` / `TypeaheadFilter` that is never `bind()`-ed | `ImproperlyConfigured` on render/validate: always bind in the form's / FilterSet's `__init__` |
| `bind(request, team=team)` or `team=team.pk` with a UUID | Params must be JSON values: `team=str(team.pk)` |
| FilterSet that binds in `__init__` without `do_not_call_in_templates = True` | crud_views' list template evaluates `view.filterset_class`, instantiating it without a request — set the flag |
| Lookup without a permission check, or a looser one than the page | The endpoint must never reveal more than the pages: raise `PermissionDenied` in `get_queryset` using the page's permission |
| Lookup raises `PermissionDenied` for a permission the page's users don't all have (e.g. `add_order` on an update form) | `bind()` runs `get_queryset` at form build time → the whole page 403s. Check the permission that page requires (or either of add/change), or return `.none()` to just empty the field |
| Setting `queryset=` on `TypeaheadField`, or filtering choices separately from the lookup | The lookup is the single source of truth: put all restrictions into `get_queryset(request, **params)` |
| `TypeaheadField(to_field_name=...)` | Not supported (`ImproperlyConfigured`); values are always the pk |
| Custom `TypeaheadLookup` without `search_fields` | Searching raises `ImproperlyConfigured`: list the fields to `icontains`-search |
| Lookup defined outside `<app>/typeahead.py` and never imported | Put it in `typeahead.py` (autodiscovered) or import it from `AppConfig.ready()` |
| Registering the same lookup name twice | `ImproperlyConfigured`; names are global — namespace them `"<app>.<use_case>"` |
| Secrets in `bind()` params | Tokens are signed, not encrypted — params are visible in the page source |
| Typeahead in content added by your own JS stays inert | Call `window.cvTypeahead.init(container)` / `window.cvTypeaheadSelect.init(container)`; crud-views modals and crud-views formset rows (≥ 0.3.3 with django-crud-views ≥ 0.29.4) are handled automatically |
| Picker / typeahead dead in a formset row added with the add button | Upgrade to django-crud-views ≥ 0.29.4 and this package ≥ 0.3.3 (`cv:formset:row-added`); on older versions call the `init` functions yourself |
| `TypeaheadSelect` popup cut off | It renders inside the widget (so it works in Bootstrap modals); an ancestor with `overflow: hidden` clips it |
