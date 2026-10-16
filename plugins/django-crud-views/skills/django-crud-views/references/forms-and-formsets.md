# Formsets and conditional field-groups

## Formsets (Inline Child Records)

*Available since 0.5.0.*

Edit a parent object together with its child rows on one page and one submit. Four parts, all
required:

1. **Child row form** — a plain `CrispyModelForm`.
2. **`InlineFormSet` subclass** — only holds the row layout (`get_helper_layout_fields`;
   `self.form_control_col4` places the add/delete controls). It is **not** configured with
   `model` / `fields` attributes: bind it to the parent/child pair with Django's
   `inlineformset_factory(..., formset=YourInlineFormSet)` and pass *that* result as `klass`.
   Passing the bare `InlineFormSet` subclass crashes at import
   (`AttributeError: ... has no attribute 'can_order'`).
3. **Parent form** — places a `Formsets()` layout element where the child rows render and
   turns off crispy's `form_tag` (the view template already provides the `<form>`; a nested
   one breaks `formset.js`). Without `Formsets()` the rows never appear.
4. **View** — `FormSetMixin` with `cv_formsets = FormSets(...)` on both create and update views.

```python
from crispy_forms.layout import Row
from django.forms.models import inlineformset_factory

from crud_views.lib.crispy import Column3, Column4, Column6, CrispyModelForm, CrispyViewMixin
from crud_views.lib.formsets import FormSet, FormSetMixin, FormSets, Formsets, InlineFormSet
from crud_views.lib.views import CreateViewPermissionRequired, MessageMixin, UpdateViewPermissionRequired


class OrderForm(CrispyModelForm):                       # 3. parent form
    class Meta:
        model = Order
        fields = ["customer_name", "customer_email"]

    def get_layout_fields(self):
        return [Row(Column6("customer_name"), Column6("customer_email")), Formsets()]

    @property
    def helper(self):
        h = super().helper
        h.form_tag = False
        return h


class OrderItemForm(CrispyModelForm):                   # 1. child row form
    class Meta:
        model = OrderItem
        fields = ["product", "quantity", "price"]


class OrderItemInlineFormSet(InlineFormSet):            # 2. row layout only
    def get_helper_layout_fields(self):
        return [Row(Column3("product"), Column3("quantity"), Column4("price"), self.form_control_col2)]


OrderItemFormSet = inlineformset_factory(
    Order, OrderItem,
    formset=OrderItemInlineFormSet, form=OrderItemForm,
    fields=["product", "quantity", "price"],
    extra=1, can_delete=True, can_delete_extra=True,
)

order_formsets = FormSets(formsets={
    "items": FormSet(
        title="Items",
        klass=OrderItemFormSet,                         # the factory result, not the subclass
        fields=["product", "quantity", "price"],        # used to detect empty rows
        pk_field="id",
        # children={"notes": FormSet(...)}              # optional nested formset per row
    ),
})


class OrderCreateView(CrispyViewMixin, FormSetMixin, MessageMixin, CreateViewPermissionRequired):   # 4.
    cv_viewset = cv_order
    form_class = OrderForm
    cv_formsets = order_formsets


class OrderUpdateView(CrispyViewMixin, FormSetMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_order
    form_class = OrderForm
    cv_formsets = order_formsets
```

The rows are validated with the main form and saved in the same transaction. Adding a row
fetches an empty row via AJAX from the same view URL; `formset.js` (from `{% cv_js %}`) handles
it — no extra wiring. `can_order=True` on the factory needs `django-ordered-model`
(`crud_views.E300` otherwise).

---

## Conditional Field-Groups & Conditional FormSets

A checkbox toggle can hide a group of fields (or an entire **first-level** formset). When off, the group/formset is hidden client-side and — authoritatively **server-side** — skips validation and clears its data. JS is cosmetic only; the server enforces the contract on every submit (tampered/JS-off POSTs included).

Import from `crud_views.lib.conditional`.

**Kind 1 — field-group in a form** (`ConditionalGroupModelForm` + `ToggleGroup`):

```python
from crud_views.lib.conditional import (
    ConditionalGroupModelForm, ConditionalGroup, ToggleGroup, ModelFieldToggle,
)

class RegistrationForm(ConditionalGroupModelForm):
    cv_conditional_groups = [
        ConditionalGroup(
            toggle=ModelFieldToggle("with_company"),   # or UIFieldToggle("...") for a non-model checkbox
            fields=["company_name", "vat_id"],
            required=["company_name"],                  # subset required when toggle is on
        ),
    ]
    class Meta:
        model = Registration
        fields = ["name", "with_company", "company_name", "vat_id"]

    def get_layout_fields(self):
        return [Row(Column6("name")),
                Row(Column6("with_company")),
                ToggleGroup("with_company", Row(Column6("company_name"), Column6("vat_id")),
                            legend="Company details")]  # legend=… renders the group as a titled <fieldset>
```

Off ⇒ group fields are cleared (must be `null=True, blank=True`, or pass `empty_values=`). On ⇒ `required` fields enforced.

**Kind 2 — an entire first-level formset** (`ConditionalFormSet` on a `FormSet`):

```python
from crud_views.lib.conditional import ConditionalFormSet, ModelFieldToggle

sessions=FormSet(
    title="Sessions", klass=SessionFormSet, fields=["title"], pk_field="id",
    conditional=ConditionalFormSet(toggle=ModelFieldToggle("with_sessions"), on_off="skip"),
)
```

The parent-form toggle (`with_sessions`) governs the whole formset. `on_off="skip"` (default) leaves existing rows untouched when off; `on_off="purge"` deletes them on save — permanently, even if the formset sets `can_delete=False`/`edit_only=True` (warned by `W321`); the save flow is transactional, so a failed sibling save rolls a purge back. Only **first-level** formsets may be conditional (nested ⇒ check error `crud_views.E310`).

The form must expose the toggle field itself: **`ConditionalFormSet` toggles are never auto-injected** (only `ConditionalGroup` toggles are, via `ConditionalGroupFormMixin`). Use a model field, declare a `BooleanField(required=False)` on the form, or reuse a group-injected `UIFieldToggle`; a missing toggle is flagged by `E311` and would otherwise be permanently off.

System checks: `crud_views.E310` (conditional on nested formset), `crud_views.E311` (toggle field missing from the form and not group-injected), `crud_views.W320` (cleared field not null/blank), `crud_views.W321` (`purge` on a formset forbidding row deletion).
