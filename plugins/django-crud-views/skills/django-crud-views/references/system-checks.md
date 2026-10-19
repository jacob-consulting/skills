# System checks

django-crud-views validates ViewSets, views and settings at startup (`manage.py check`, `runserver`).
View and ViewSet checks are reported as `viewset.<ID>`; setting and integration checks as
`crud_views.<ID>`. Run `python manage.py check` after wiring views — most misconfigurations surface
there rather than at request time.

## Index

| ID | Meaning | Details |
|---|---|---|
| `crud_views.E100` | `CRUD_VIEWS_EXTENDS` not set, or its template not found | [settings.md](settings.md) |
| `crud_views.E101` | `CRUD_VIEWS_MANAGE_VIEWS_ENABLED` not `"yes"`/`"no"`/`"debug_only"` | [settings.md](settings.md) |
| `crud_views.E102` | malformed `CRUD_VIEWS_BREADCRUMB_PREFIX` entry | [templates-and-navigation.md](templates-and-navigation.md) |
| `crud_views.E103` | `CRUD_VIEWS_ORIGIN_PARAM` not matching `^[a-z][a-z0-9_]*$` | [form-views.md](form-views.md) |
| `crud_views.E104` | `CRUD_VIEWS_INACCESSIBLE_ACTIONS` not `"hide"`/`"disable"` | [actions-and-buttons.md](actions-and-buttons.md) |
| `crud_views.E105` | `CRUD_VIEWS_*_ACTIONS_INLINE` not `None` or a list of strings | [actions-and-buttons.md](actions-and-buttons.md) |
| `crud_views.E350` | a removed icon setting (`CRUD_VIEWS_FILTER_ICON`, `…_ACTIONS_MENU_ICON`, `…_OBJECT_DETAIL_ICONS_*`) is still defined | [migration.md](migration.md) |
| `crud_views.E351` / `E354` / `E355` | icon library misconfigured: renderer not importable / `font` library without valid `class` / config not a dict or bad renderer | [icons.md](icons.md) |
| `crud_views.E356` | icon value (`CRUD_VIEWS_ICONS`, `cv_icon_action`, `cv_icon_header`) neither str nor `None` | [icons.md](icons.md) |
| `crud_views.W352` / `W353` | icon value uses an unregistered library prefix (`CRUD_VIEWS_ICONS` / view or ViewSet icon); W352 also flags a name pointing to a name | [icons.md](icons.md) |
| `crud_views.W110` | `CRUD_VIEWS_THEME` is set — it has no effect | [settings.md](settings.md) |
| `viewset.E002` / `E003` | ViewSet `name` / `prefix` has an invalid format | — |
| `viewset.E110` | a view needs a template or `*_template_code` it doesn't have (header, paragraph, action labels — backend-only views still need action labels) | [form-views.md](form-views.md) |
| `viewset.E111` | `extends` / `cv_extends_template` template missing or misconfigured (e.g. it re-extends `cv_extends`) | [templates-and-navigation.md](templates-and-navigation.md) |
| `viewset.E200` / `E201` | view `cv_key` / `cv_path` has an invalid format | — |
| `viewset.E202` | permission-required view without `cv_permission` | — |
| `viewset.E204` | `cv_formsets` is not a `FormSets` instance | [forms-and-formsets.md](forms-and-formsets.md) |
| `viewset.E205` | `cv_polymorphic_formsets` is not a `{Model: FormSets}` mapping | [polymorphic.md](polymorphic.md) |
| `viewset.E206` | `cv_formsets_required` not set | [forms-and-formsets.md](forms-and-formsets.md) |
| `viewset.E207` | `cv_inaccessible_actions` not `None`/`"hide"`/`"disable"` | [actions-and-buttons.md](actions-and-buttons.md) |
| `viewset.E208` | `cv_*_actions_inline` not `None` or a list of strings | [actions-and-buttons.md](actions-and-buttons.md) |
| `viewset.E220` | both `cv_polymorphic_include` and `cv_polymorphic_exclude` set | [polymorphic.md](polymorphic.md) |
| `viewset.E230`–`E235` | workflow view/model misconfigured (`form_class`, labels, `WorkflowModelMixin`, `STATE_CHOICES`, `STATE_BADGES`) | [workflow.md](workflow.md) |
| `viewset.E240`–`E245` | `cv_property_display` missing or malformed (list of dicts with `title` and `properties`) | [detail-views.md](detail-views.md) |
| `viewset.W246` | object detail group `icon` uses an unregistered library prefix | [icons.md](icons.md) |
| `viewset.E250` | `cv_modal_size` not `""`/`"modal-sm"`/`"modal-lg"`/`"modal-xl"` | [form-views.md](form-views.md) |
| `viewset.E251` | `cv_modal = True` on an unsupported view type | [form-views.md](form-views.md) |
| `viewset.E252` / `E253` | unregistered key in `cv_cancel_keys` / `cv_success_keys` | [form-views.md](form-views.md) |
| `viewset.E254` | delete view's success target is an object view (the object is gone) | [form-views.md](form-views.md) |
| `viewset.E255` | a context button's target view or ViewSet does not resolve | [actions-and-buttons.md](actions-and-buttons.md) |
| `viewset.E260` | Resource ViewSet: `cv_permission` missing from `resource_permissions` | [resources.md](resources.md) |
| `viewset.E261` | Resource ViewSet used as a parent (Resources are leaf-only) | [resources.md](resources.md) |
| `viewset.E262` | Create/Update/Delete view on a Resource ViewSet | [resources.md](resources.md) |
| `viewset.W270` | `cv_breadcrumb_key_object` names no registered view | [templates-and-navigation.md](templates-and-navigation.md) |
| `viewset.W280` | unknown `cv_*` data attribute (typo or removed name) | below |
| `viewset.W290` | a view's own `cv_*_actions_inline` key is not among that location's actions | [actions-and-buttons.md](actions-and-buttons.md) |
| `crud_views.E300` | ordered view or `can_order` formset without `django-ordered-model` installed | [lists-and-cards.md](lists-and-cards.md) |
| `crud_views.E310` / `E311` | conditional formset nested / its toggle field missing from the form | [forms-and-formsets.md](forms-and-formsets.md) |
| `crud_views.W320` / `W321` | cleared conditional field not null/blank / `purge` on a formset forbidding deletion | [forms-and-formsets.md](forms-and-formsets.md) |
| `crud_views.E330` / `W332` | invalid SRI `integrity` / integrity on a same-origin static path | [assets.md](assets.md) |
| `crud_views.W330` / `W331` | vendored asset bundle missing / version drift | [assets.md](assets.md) |
| `crud_views.W340`–`W345` | django-pipeline bundling coverage problems | [assets.md](assets.md) |
| `crud_views_workflow.E001` / `E002` | `django-fsm-2` / `django-fsm-2-admin` not installed | [workflow.md](workflow.md) |

---

## Unknown `cv_*` attributes (W280)

*Available since 0.19.0.*

`viewset.W280` warns when a view declares a `cv_*` data attribute that no `crud_views` class
recognizes — a typo or an attribute left behind by a rename — with a "Did you mean …?" hint.

```
viewset.W280: cv_message on <class 'myapp.views.BookCreateView'> is not a known
crud_views attribute — it is silently ignored (dead attribute or typo).
Did you mean cv_message_template_code?
```

Only non-callable data attributes are flagged, so your own `cv_*` methods and properties are
safe. To keep an intentional custom data attribute, exempt it explicitly:

```python
class BookCreateView(CreateViewPermissionRequired):
    cv_viewset = cv_book
    cv_check_ignore_attributes = frozenset({"cv_my_custom_flag"})
    cv_my_custom_flag = True
```

The allowlist is unioned across the MRO, so a mixin and the leaf view can each exempt their own.
