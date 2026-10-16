# List views, card views, filtering and ordering

## CardListView

*Available since 0.4.0 (ordering, pagination, and filter coexistence since 0.6.0).*

Render objects as cards instead of table rows. Uses `CardAction` for per-button config and `cv_card_template` for
per-view card body overrides.

```python
from crud_views.lib.view import CardAction
from crud_views.lib.views import CardListViewPermissionRequired, ListViewTableFilterMixin

class AuthorCardListView(ListViewTableFilterMixin, CardListViewPermissionRequired):
    cv_viewset = cv_author
    filterset_class = AuthorFilter
    formhelper_class = AuthorFilterFormHelper
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(key="delete", no_label=True, variant="tertiary"),
    ]
```

URLs auto-register at `/<prefix>/card/`. `cv_card_actions` declares per-button rendering: `key` maps to a view in the
ViewSet, `label` overrides the default short label, `variant` sets the button style (`primary`/`secondary`/`tertiary`),
`flex` makes the button fill available space, and `no_label` renders an icon-only button.

A `CardAction` whose `key` targets a POST-only view (ordered up/down or any custom `ActionView`) or a modal-enabled
view works automatically — the button renders a POST form / modal trigger derived from the target view, exactly like
table-list actions. No extra `CardAction` config is needed (requires crud_views ≥ 0.15.0).

Card views support ordering (`cv_order_fields`), Django pagination (`paginate_by`), and
django-filter filtering — all coexisting and session-persistable. See [api-reference.md](api-reference.md)
for attributes.

### Card ordering: signed choices vs direction buttons

`cv_order_fields` has two shapes. Plain names render a combo plus asc/desc buttons
(`?order=name&dir=desc`). Prefix an entry with `-` / `+` and the direction becomes part of the
choice: one combo, no buttons, submits on change, `?order=-created` (available since 0.22.0):

```python
class RecipeCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_recipe
    cv_order_fields = [
        ("-created_dt", "Newest first"),
        ("created_dt", "Oldest first"),   # plain name in a signed list == ascending
        "-title",                         # auto-label: "Title (descending)" (translated)
    ]
    cv_order_default = "-created_dt"
```

Rules: one signed entry switches the whole list to signed mode; ascending is emitted as the bare
name (never `+name` — a `+` in a query string decodes to a space); `dir` is ignored; the whitelist
is exact per signed value (`?order=created_dt` is rejected when only `-created_dt` is declared);
the combo preselects the active choice including the default.

### Card Container Class

Override `cv_card_container_class` to control the Bootstrap grid width of each card wrapper. Default is `"col-md-6"` (two cards per row). Set to `"col-md-12"` for full-width or `"col-md-4"` for three per row.

### List Key Fallback

ViewSets with only a `CardListView` (no `ListView`) automatically resolve `"list"` keys to `"card"`. No need to
override `cv_success_key` or `cv_cancel_key` on sibling views.

### Custom Card Template

Override `cv_card_template` for model-specific card content:

```python
class ProjektCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_projekt
    cv_card_template = "myapp/tags/projekt_card.html"
    cv_card_actions = [...]
```

The template receives `object`, `view`, and `request`. Use `{% cv_card_action action object %}` for buttons:

```html
{% load crud_views %}
<div class="card mb-3">
    <div class="card-body">
        <h5 class="card-title">{{ object.name }}</h5>
        <p>{{ object.description|truncatewords:20 }}</p>
        <div class="d-flex gap-2">
            {% for action in view.cv_card_actions %}
                {% cv_card_action action object %}
            {% endfor %}
        </div>
    </div>
</div>
```

Guardian variant: `GuardianCardListViewPermissionRequired` filters the queryset by per-object view permissions.

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

To show a filter always-open with no toggle button, set `cv_filter_pinned = True` (or the `CRUD_VIEWS_FILTER_PINNED` setting).

---

## Ordered Actions (move up/down)

```python
from crud_views.lib.views import OrderedUpViewPermissionRequired, OrderedUpDownPermissionRequired

class AuthorUpView(OrderedUpViewPermissionRequired):
    cv_viewset = cv_author

class AuthorDownView(OrderedUpDownPermissionRequired):
    cv_viewset = cv_author

# Add "up" and "down" to cv_list_actions in the list view
# Move messages are emitted automatically — no MessageMixin needed.
# Override cv_message_template_code to customize, or set cv_action_messages = False to disable.
```
