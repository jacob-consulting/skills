# Nesting, context buttons and action visibility

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

class BookCreateView(CrispyViewMixin, MessageMixin, CreateViewParentMixin, CreateViewPermissionRequired):
    form_class = BookCreateForm
    cv_viewset = cv_book

# In the parent AuthorTable, add:
# books = LinkChildColumn(name="book", verbose_name="Books")
```

URLs for `cv_book` must also be added: `urlpatterns += cv_book.urlpatterns`

### Child Context Button

Use `ChildContextButton` to add a context action on a parent's detail view that links to a child viewset (e.g. a
"Books" button on the author detail page). This is the inverse of `ParentContextButton` (which navigates up).

```python
from crud_views.lib.view import ChildContextButton
from crud_views.lib.viewset import ViewSet, context_buttons_default

cv_author = ViewSet(
    model=Author,
    name="author",
    context_buttons=context_buttons_default() + [
        ChildContextButton(key="books", child_name="book", label_template_code="Books"),
    ],
)

# Then reference the key in cv_context_actions on the detail view:
class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_context_actions = ["update", "delete", "books"]
```

`ChildContextButton` parameters:
- `key` — the action key referenced in `cv_context_actions`
- `child_name` — name of the child viewset to link to
- `child_key` — target view in the child viewset (default: `"list"`)
- `label_template_code` — Django template string for the button label (optional)
- `label_template` — path to a Django template for the button label (optional)

Access control is handled automatically via the child view's `cv_has_access()`. For Guardian-based views, this
checks object-level permissions on the parent object.

### SiblingContextButton

*Available since 0.7.0.*

Use `SiblingContextButton` on a **child** view to link sideways to a **sibling** collection —
another child of the same parent. It reuses the parent PK from the current URL. Pair it with
`ChildContextButton`: `ChildContextButton` on the parent (go down), `SiblingContextButton` on the
children (go sideways).

```python
from crud_views.lib.view import SiblingContextButton
from crud_views.lib.viewset import ViewSet, ParentViewSet, context_buttons_default

cv_book = ViewSet(
    model=Book,
    name="book",
    parent=ParentViewSet(name="author"),
    context_buttons=context_buttons_default() + [
        SiblingContextButton(key="articles", sibling_name="article", label_template_code="Articles"),
    ],
)

# Then reference the key in cv_context_actions on the child's view:
class BookListView(ListViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["parent", "create", "articles"]
```

`SiblingContextButton` parameters:
- `key` — the action key referenced in `cv_context_actions`
- `sibling_name` — registry name of the sibling viewset (must share the same parent)
- `sibling_key` — target view key in the sibling viewset (default `"list"`)

Renders nothing on a view without a parent. Access is checked model-level on the sibling
view (no parent object is consulted).

### View-level context buttons (cv_context_buttons)

*Available since 0.7.0.*

Context buttons are normally defined on the ViewSet and shared by all its views. To define a
button on a single view, set `cv_context_buttons` on the `CrudView`:

```python
from crud_views.lib.view import ChildContextButton


class BookDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_book
    cv_context_actions = ["update", "delete", "reviews"]   # list the key to render it
    cv_context_buttons = [
        ChildContextButton(key="reviews", child_name="review", label_template_code="Reviews"),
    ]
```

- A button renders only when its `key` is in `cv_context_actions` (definition vs. rendering
  stay separate).
- A view-level button overrides a ViewSet-level button with the same `key`, for that view only.

**Target check `viewset.E255` (since 0.27.1):** every configured button (ViewSet `context_buttons`
and `cv_context_buttons`) must resolve at startup — `key_target` on the own ViewSet
(`ContextButton`) or the parent (`ParentContextButton`, which also needs a parent), `child_name`
being a child plus `child_key`, `sibling_name` plus `sibling_key`; `list` may fall back to `card`.
Buttons equal to a `context_buttons_default()` entry and subclasses overriding `get_context()` are
skipped; a custom button type can override `cv_check_target(viewset)` (returns a message or `None`).

---

## Conditionally Disabling an Action

*Available since 0.6.0.*

`cv_has_access` answers "may this user perform this action at all?" (permission check). `cv_action_enabled` is a
secondary state gate that runs only after `cv_has_access` has passed — it answers "is this action currently
applicable to this specific object?" When it returns `False`, the action button is **hidden** (or, since 0.28.0, rendered disabled — see
[Hide or disable inaccessible actions](#hide-or-disable-inaccessible-actions-since-0280)) and a direct
request to the URL returns 403 for an authenticated user. Override it as a classmethod; `obj` is the target
instance for object views (delete/update/detail/action) or the **parent** instance for a child-create view.

```python
class PersonDeleteView(CrispyViewMixin, MessageMixin, DeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_person

    @classmethod
    def cv_action_enabled(cls, user, obj=None):
        # obj is the Person row; members of a locked group cannot be removed.
        return not (obj and obj.group.filter(locked=True).exists())
```

Full API and enforcement details: [api-reference.md](api-reference.md).

---

## Hide or disable inaccessible actions (since 0.28.0)

An action is **inaccessible** when the user fails `cv_has_access` for its target view, or the target's
`cv_action_enabled` returns `False`. By default such actions are **hidden**; mode `"disable"` renders them greyed
out instead, so users see that the action exists.

| Where | Attribute | Values |
|---|---|---|
| Django settings | `CRUD_VIEWS_INACCESSIBLE_ACTIONS` | `"hide"` (default), `"disable"` |
| `ViewSet` | `inaccessible_actions` | `None` (use the setting), `"hide"`, `"disable"` |
| `CrudView` | `cv_inaccessible_actions` | `None` (use the ViewSet), `"hide"`, `"disable"` |

The mode resolves on the action's **target** view (the view the button links to), not on the page showing it —
`cv_get_inaccessible_actions()` returns the result:

```python
class PublisherDeleteView(DeleteViewPermissionRequired):
    cv_viewset = cv_publisher
    cv_inaccessible_actions = "disable"  # greyed out on list rows, cards and the detail toolbar
```

- Applies everywhere an action renders: the context toolbar, list rows, cards (child card actions too), action
  menus, and the manual tags. `cv_get_context_buttons()` includes disabled entries (`cv_disabled=True`,
  `cv_url=None`); `{% cv_context_url %}` returns `None` for every inaccessible action in **both** modes.
- A disabled action is a native `<button type="button" disabled data-cv-disabled="permission|state">` — no URL,
  no `data-cv-action` / `data-cv-modal`, and no hidden POST form. Templates get `cv_disabled` and
  `cv_disabled_reason` (`"permission"` | `"state"`).
- Child card actions (`CardAction(child_name=...)`) check the **child** view's permission, like
  `ChildContextButton` (before 0.28.0 they always rendered and the target answered 403).
- Checks: `crud_views.E104` (invalid setting), `viewset.E207` (invalid `cv_inaccessible_actions`); the ViewSet
  field is validated by pydantic.

---

## Action menus (since 0.28.0)

Fold the less common actions of a list row, the context toolbar or a card into one Bootstrap dropdown (`⋯`).
Each location has an **inline keys** list: named actions stay buttons, all others go into the menu.

| Level | List rows | Context toolbar | Cards |
|---|---|---|---|
| Django settings | `CRUD_VIEWS_LIST_ACTIONS_INLINE` | `CRUD_VIEWS_CONTEXT_ACTIONS_INLINE` | `CRUD_VIEWS_CARD_ACTIONS_INLINE` |
| `ViewSet` | `list_actions_inline` | `context_actions_inline` | `card_actions_inline` |
| `CrudView` | `cv_list_actions_inline` | `cv_context_actions_inline` | `cv_card_actions_inline` (card views) |

- `None` (default): no menu — the markup is exactly the pre-0.28 markup
- `[]`: every action goes into the menu
- `["detail"]`: `detail` stays a button, the rest go into the menu

```python
class AuthorListView(ListViewTableMixin, ListViewPermissionRequired):
    cv_viewset = cv_author
    cv_list_actions = ["detail", "update", "delete", "up", "down"]
    cv_list_actions_inline = ["detail", "up", "down"]  # update and delete go into the menu


class AuthorDetailView(DetailViewPermissionRequired):
    cv_viewset = cv_author
    cv_context_actions_inline = ["update"]  # the active "detail" shows inside the menu, marked aria-current


class AuthorCardListView(CardListViewPermissionRequired):
    cv_viewset = cv_author
    cv_card_actions = [
        CardAction(key="detail", label="Details", variant="primary", flex=True),
        CardAction(key="update", label="Edit"),
        CardAction(child_name="book", label="Books"),
    ]
    cv_card_actions_inline = ["detail"]  # cards match CardAction.key, or child_name for child actions
```

- **Resolution:** `CrudView` → `ViewSet` → setting, first value that **is not `None`** (so `[]` on a view beats a
  list on the ViewSet). It resolves on the view that **renders** the group — unlike hide/disable, which resolves on
  the target. Getters: `cv_get_list_actions_inline()`, `cv_get_context_actions_inline()`,
  `cv_get_card_actions_inline()`.
- **Matching:** list rows and the toolbar match the key as written in `cv_list_actions` / `cv_context_actions`
  (`"home"`, not its target `"list"`). Order is kept on both sides; new actions land in the menu automatically.
- **Never folded:** context buttons with their own `template=` / `template_code=` (incl. the filter toggle).
  `up` / `down` can be folded but belong inline.
- **Hide/disable:** hidden actions appear nowhere; a menu with only hidden actions renders no toggle. Disabled items
  are `<button class="dropdown-item" disabled data-cv-disabled="…">`; a menu with only disabled items still renders.
- **POST and modal** items work from the menu (hidden forms stay outside it), in list rows, cards and — since
  0.29.0 — the context toolbar too, inline and in its menu (also for a `ContextButton` whose `key_target` is POST).
  Up to 0.28.0 the toolbar rendered POST actions as GET links (405).
- **Labels:** menu items show the target's icon (`cv-icon-fw`, since 0.30.0; `fa-fw` before) and short label
  (`cv_action_short_label`; `CardAction.label` on cards). A context button's own `label_template[_code]` also sets its short label, so it
  labels the menu item too. `CardAction.variant` / `flex` / `no_label` apply to inline card buttons only.
- **Toggle icon:** the `actions-menu` icon (default `fas:ellipsis`): `CRUD_VIEWS_ICONS = {"actions-menu": "fas:bars"}`
  ([icons.md](icons.md); before 0.30.0 `CRUD_VIEWS_ACTIONS_MENU_ICON`). Row menus use Popper's fixed
  strategy, so `.table-responsive` does not clip them. Needs the Bootstrap JS **bundle** (Popper included).
- **Templates** (overridable): `crud_views/tags/actions_menu.html` (wrapper + list), `actions_menu_toggle.html`
  (toggle only — override it for a split-style caret), `actions_menu_item.html`, `actions_menu_item_label.html`.
  Projects that override `columns/actions.html`, `tags/context_actions.html` or `tags/card.html` don't get the menu
  until they adopt the package's `{% if group is None %} … {% else %} … {% endif %}` structure.
- **Custom loops:** `view.cv_get_list_action_group(obj)`, `cv_get_context_action_group(obj)`,
  `cv_get_card_action_group(obj)` return an `ActionGroup` (`inline`, `menu`, `all`) or `None` when off.
- **Checks:** `crud_views.E105` (setting not `None`/list of strings), `viewset.E208` (same for the view attribute),
  `viewset.W290` (a view's **own** inline key isn't among that location's actions — typo; ViewSet and setting
  values are shared defaults and never checked).
