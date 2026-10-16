# Form, delete and action views

## DeleteView: Cascading Deletes & Delete Protection

### Cascading Deletes Display

Show users what related objects will be cascade-deleted (like Django Admin). Opt-in via `cv_show_related_objects`:

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher
    cv_show_related_objects = True       # show cascade-deleted objects
    cv_link_related_objects = True       # link related objects to their detail views
```

When enabled, the delete confirmation page shows a summary by type/count, a nested tree of related objects, and warnings for `PROTECT` relationships. Links are only rendered for models with a registered ViewSet that has a `detail` view.

### Delete Protection

**View hook** — override `cv_check_delete_protection()` to return error messages. Runs on GET — the delete form is **not shown at all** when errors exist:

```python
class PublisherDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_publisher

    def cv_check_delete_protection(self) -> list[str]:
        if self.object.books.filter(is_published=True).exists():
            return ["Cannot delete a publisher with published books."]
        return []
```

**Form hook** — for submit-time validation, use standard Django form validation in a `CrispyDeleteForm` subclass:

```python
class ProtectedDeleteForm(CrispyDeleteForm):
    def clean(self):
        cleaned_data = super().clean()
        if some_condition:
            raise ValidationError("Cannot delete.")
        return cleaned_data
```

Execution order: GET checks `cv_check_delete_protection()` (hides form if errors) → POST validates form → POST re-checks `cv_check_delete_protection()` (defense in depth) → delete or re-render.

---

## Custom Form View

`CustomFormView` attaches a custom form to an existing object — use for contact forms, approval actions, etc.

```python
from crud_views.lib.views import MessageMixin
from crud_views.lib.views.form import CustomFormViewPermissionRequired
from crud_views.lib.crispy import CrispyModelForm, CrispyViewMixin, Column12

class AuthorContactForm(CrispyModelForm):
    submit_label = "Send"
    subject = CharField(label="Subject", required=True)
    body = CharField(label="Body", required=True)
    class Meta:
        model = Author
        fields = ["subject", "body"]
    def get_layout_fields(self):
        return Column12("subject"), Column12("body")

class AuthorContactView(MessageMixin, CrispyViewMixin, CustomFormViewPermissionRequired):
    cv_key = "contact"      # unique key — auto-registers URL with the ViewSet
    cv_path = "contact"     # URL path segment
    cv_icon_action = "fa-solid fa-envelope"
    cv_viewset = cv_author
    form_class = AuthorContactForm
    cv_message_template_code = "Successfully contacted author »{{ object }}«"
    cv_context_actions = ["parent", "detail", "update", "delete", "contact"]
    cv_header_template_code = "Contact Author"
    cv_paragraph_template_code = "Send a message to the Author"

    def cv_form_valid(self, context):
        form = context["form"]
        # process form.cleaned_data here
        pass
```

Use `CustomFormNoObjectViewPermissionRequired` for forms not tied to a specific instance.

---

## Custom Action View

Performs a one-click action on an existing object. Implement `action(context)`. Register with a unique `cv_key`
and `cv_path`. Add that key to `cv_list_actions` on the list view to show a per-row button.

```python
from crud_views.lib.views import ActionViewPermissionRequired

class AuthorArchiveView(ActionViewPermissionRequired):
    cv_key = "archive"
    cv_path = "archive"
    cv_icon_action = "fa-solid fa-box-archive"
    cv_viewset = cv_author
    cv_message_template_code = "Archived »{{ object }}«"
    cv_message_template_error_code = "Could not archive »{{ object }}«"

    def action(self, context):
        obj = context["object"]
        obj.is_archived = True
        obj.save()
        return True  # truthy → success message; falsy → error message

# In list view: cv_list_actions = ["detail", "update", "delete", "archive"]
# MessageMixin is NOT needed — ActionView emits messages built in.
# Disable with cv_action_messages = False or by leaving the templates unset.
```

---

## Cancel and success targets

*Cancel since 0.21.0, success since 0.26.0.*

The cancel button returns to `cv_cancel_key` (`"list"`), a successful submit to `cv_success_key`
(`"list"`). Set `cv_cancel_keys` / `cv_success_keys` to return to the sibling view the user came
from instead:

```python
class AuthorUpdateView(CrispyViewMixin, MessageMixin, UpdateViewPermissionRequired):
    cv_viewset = cv_author
    form_class = AuthorForm
    cv_cancel_keys = ["list", "detail"]   # dynamic; cv_cancel_key stays the fallback
    cv_success_keys = ["list", "detail"]  # dynamic; cv_success_key stays the fallback
```

Links into such a view carry the origin as a view key in the query string
(`/author/<pk>/update/?cv_from=detail`) when the target lists it in either list; the parameter
name is `CRUD_VIEWS_ORIGIN_PARAM` (default `cv_from`; was `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` before
0.26.0). The two lists resolve independently. Values that are malformed, not listed, unregistered,
or that need an object the view lacks (e.g. cancel to `detail` on a create view, success to
`detail` after a delete) fall back to `cv_cancel_key` / `cv_success_key`.
The origin survives validation errors (forms post to `request.get_full_path`) and modal
re-renders; modal success uses it for `X-CV-Redirect`. Works on Create/Update/Delete/CustomForm
views; `cv_success_keys` also on Workflow, Action and ordered up/down views. In custom templates
resolve the cancel target with `{% cv_context_url view.cv_get_cancel_key as url %}`, not
`view.cv_cancel_key`; the success key resolves via `cv_get_success_key()`.
Checks: `crud_views.E103` (bad parameter name), `viewset.E252` / `viewset.E253` (unregistered
key in `cv_cancel_keys` / `cv_success_keys`), `viewset.E254` (object view such as `detail` in a
delete view's `cv_success_key` or `cv_success_keys` — the object is gone after success).

Theme overrides of `view_{create,update,delete,custom_form}.content.html` must use
`action="{{ request.get_full_path }}"` — a form posting to `request.path` drops the origin, so
cancel falls back to `cv_cancel_key` after a validation error. Custom link builders (table
columns, theme tags) call `cv_get_link_url` with the target view class so the link carries the
origin; plain `cv_get_url` never does:

```python
url = view.cv_get_link_url(view.cv_get_cls("update"), "update", obj=record)
```

---

## Modal Views

*Available since 0.11.0.*

Opt a view into Bootstrap 5 modal rendering: its action buttons then open the view in a modal dialog
(fetched in place, submitted without a full page reload) instead of navigating to a full page.

```python
class AuthorDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_author
    cv_modal = True                 # opt in
    cv_modal_size = "modal-lg"      # optional: "" | "modal-sm" | "modal-lg" | "modal-xl"
```

**Supported view types:** `DeleteView`, `DetailView`, `CustomFormView`, `CustomFormNoObjectView` (and
their `*PermissionRequired` and Guardian/extension variants). Setting `cv_modal = True` on any other view
type (create, update, list, …) raises system check `viewset.E251`. An invalid `cv_modal_size` — anything
other than the exact strings `""`, `"modal-sm"`, `"modal-lg"`, `"modal-xl"` — raises `viewset.E250`.

**No template, JS, URL, or settings changes needed.** The shared modal shell is rendered by
`{% cv_config %}` and the transport JS by `{% cv_js %}` — both already present in the Bootstrap 5 base
template. It is the same URL: the view detects the modal request via an `X-CV-Modal: true` request header
and returns just the modal partial (reusing the view's normal content). On POST, success answers `204` +
an `X-CV-Redirect` header (the browser navigates — Django messages and `cv_success_key` work unchanged);
invalid forms and delete protection re-render inside the open modal (status `422`).

**Progressive enhancement:** direct links, middle-click, disabled JavaScript, and non-Bootstrap themes
(`crud_views_plain`) all render the normal full page. `cv_modal = False` (the default) changes nothing.

**Re-init hook:** after each content injection a `cv:modal:loaded` CustomEvent fires on `#cv-modal` — use
it to initialize custom widgets inside modal content.

Full reference: see [api-reference.md](api-reference.md).

---

## Transactions & hooks (since 0.27.0)

Form, delete and action views run their write phase in one transaction:
`cv_form_valid` + `cv_form_valid_hook` (resp. `action()` + `cv_action_success_hook` /
`cv_action_error_hook`) are inside `transaction.atomic(using=cv_get_db_alias())`. Side effects go
in `cv_on_commit(context)`, which runs after the commit and never after a rollback. Workflow views
put the transition record in `context["workflow_info"]`.

- `cv_atomic = False`: no transaction (default on `ResourceViewMixin`; needed for
  `atomic(durable=True)` services).
- Another database: override `cv_get_db_alias()` (the transaction and `cv_on_commit` both use it).
  Override `cv_get_atomic()` only for a custom boundary on that same alias.
- `action()` returning `False` does not roll back; call `transaction.set_rollback(True)`.
- An exception in those hooks rolls back the write. Catching an `IntegrityError` inside `cv_form_valid`
  needs a nested `atomic()` on PostgreSQL.
- Overriding `post()`? Call `cv_form_valid_process(context)` / `cv_action_process(context)` to
  keep the transaction.
