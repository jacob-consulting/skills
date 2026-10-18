# Upgrading and older package versions

The rest of this skill describes the current package (0.29.4). Read this file when a project pins an
older `django-crud-views`, when you are upgrading one, or when code or errors mention names that no
longer exist. Newest first.

## 0.29.4

| Symptom on older versions | Change |
|---|---|
| Date pickers, select widgets, tooltips or conditional field-groups are dead in a formset row added with the add button (up to 0.29.3) | Since 0.29.4 `formset.js` dispatches `cv:formset:row-added` on each new row and core scripts re-initialize on it (#197). On older versions initialize widgets yourself after the row is inserted |

## 0.29.3

| Symptom on older versions | Change |
|---|---|
| Polymorphic create form page (step 2) fails with `NoReverseMatch: Reverse for '<name>-create' with no arguments not found` (up to 0.29.2) | `PolymorphicCreateView` inherited the create view's `["home", "create"]` actions, and `"create"` can't be reversed without the content type. Since 0.29.3 it defaults to `["home"]` (`CRUD_VIEWS_POLYMORPHIC_CREATE_CONTEXT_ACTIONS`) (#193). On older versions set `cv_context_actions = ["home"]` on the view |
| Polymorphic create URL is `<prefix>/create//ct/<id>/` (up to 0.29.2) | Since 0.29.3 it is `<prefix>/create/ct/<id>/`; the double-slash form still resolves. Code that reverses by name is unaffected; update hardcoded URLs in tests |

## 0.29.2

| Symptom on older versions | Change |
|---|---|
| `ImportError: cannot import name 'PrimaryKeys' from partially initialized module 'crud_views.lib.viewset'` at startup (up to 0.29.1) | Importing `crud_views.lib.viewset` or `crud_views.lib.table` before any other crud_views module — typically from a `models.py`, e.g. a `Resource` using `ViewSet.PK` — hit a circular import. Fixed in 0.29.2; on older versions keep that code in `views.py` |

## 0.29.0

| Symptom on older versions | Change |
|---|---|
| POST `ActionView` in `cv_context_actions` answers 405 when clicked (up to 0.28.0) | The toolbar rendered POST actions as GET links; fixed in 0.29.0 (#178). Upgrade. A hand-placed `{% cv_context_button %}` for a POST key also needs `{% cv_context_action_form "key" %}` |
| Backend-only view: button raised `CrudViewError: no template or template_code provided` at request time (up to 0.28.0) | Since 0.29.0 this is startup check `viewset.E110` (#179). Give the view `cv_action_label_template_code` and `cv_action_short_label_template_code` |

## 0.28.0

| Symptom | Change |
|---|---|
| Custom `list_action.html` / `card_action.html` placeholder for `not cv_access` vanished | In the default hide mode the tags pass an empty context; set the target view's `cv_inaccessible_actions = "disable"` and use the `cv_disabled` branch |
| Child card actions (`CardAction(child_name=...)`) always rendered and the target answered 403 | Since 0.28.0 they check the child view's permission, like `ChildContextButton` |
| Overridden `columns/actions.html`, `tags/context_actions.html` or `tags/card.html` show no `⋯` menu | Adopt the package's `{% if group is None %} … {% else %} … {% endif %}` structure |

## 0.27.x

| Symptom | Change |
|---|---|
| Context button silently missing (0.24.2–0.27.0) | An unresolvable target (`child_key="lsit"`) was skipped at render time; since 0.27.1 `viewset.E255` reports it at startup. Customizing a default (`home` with its own label) on a ViewSet without `list` now fails E255: drop it there |
| `viewset.W280` flags `cv_parent_key` (0.27.0) | It was never read and is removed; the parent link's target is `ParentContextButton(key="parent", key_target=...)` |
| Hooks behave differently after upgrading from 0.26 | Since 0.27.0 the write phase runs in `transaction.atomic()`: an exception in `cv_form_valid_hook` / `action()` / their hooks now rolls back the write; a caught `IntegrityError` inside `cv_form_valid` needs a nested `atomic()` on PostgreSQL; `atomic(durable=True)` in the write phase raises `RuntimeError` (set `cv_atomic = False`). Move mail/Celery side effects to `cv_on_commit(context)` |

## 0.26.0

| Symptom | Change |
|---|---|
| `CRUD_VIEWS_CANCEL_ORIGIN_PARAM` silently ignored | Renamed to `CRUD_VIEWS_ORIGIN_PARAM` (shared by `cv_cancel_keys` and `cv_success_keys`) |
| `cv_cancel_keys_registered()` missing | Replaced by `cv_origin_keys_registered(keys)` |
| `DeleteView` with `cv_success_key = "detail"` → `NoReverseMatch` | Since 0.26.0 startup check `viewset.E254`; send success to a list-type view |

## 0.23.0

| Symptom | Change |
|---|---|
| CSS/test selectors for list or filter actions broke | List actions that POST (`ActionView`s such as `up`/`down`) and the filter toggle `#cv-filter-toggle` are `<button type="button">` now, not `<a href="#">`; navigating actions are plain `<a>` without `role="button"`. Select by class/id/`cv-key`, not by tag |
| `card-rows` detail tooltip never appears | Before 0.23.0 nothing initialised it — upgrade |
| Guardian child routes 403 although the user has the model-level parent perm and `cv_guardian_accept_global_perms = True` | Before 0.23.0 the parent check ignored the flag — upgrade |
| `Table.ca.w10 \| …` adds classes to other columns too | `ColumnAttrs.__or__` modified the shared preset; fixed in 0.23.0 — upgrade, no code change |

## 0.21.0

| Symptom | Change |
|---|---|
| `CustomFormNoObjectView` crashes on GET | It inherited the detail actions, which need an object; 0.21.0 defaults to `CRUD_VIEWS_CREATE_CONTEXT_ACTIONS`. Upgrade — a `cv_context_actions` set only to dodge the crash can go |
| Crispy cancel on a `CustomFormView` with `CrispyModelForm` links to a non-existent object | It used the form's unsaved `instance`; fixed in 0.21.0 to use the view's object — upgrade, no code change |
| `cv_cancel_keys` origin lost after a validation error | Package templates switched to `action="{{ request.get_full_path }}"` in 0.21.0; overridden templates must do the same |

## 0.20.0

| Symptom | Change |
|---|---|
| Action-column CSS/test selectors broke | The `th`/`td` class changed from `d-flex justify-content-end` to `cv-col-action` (flex broke the row separator); the shipped `table.css` right-aligns with `text-align` |
| `crud_views_settings.dict` missing | Renamed to `.as_dict` (the old name shadowed the `dict` builtin and broke annotations under PEP 649 on Python 3.14) |
| `ImportError` on `import crud_views` | Since 0.20.0 a missing `django-filter` or `django-crispy-forms` fails immediately instead of later — both are required |

## 0.18.0

`AssetBundle.js` / `.css` hold `Asset` instances, not strings. Code doing
`bundle.js[0].startswith(...)` must use `bundle.js[0].path`.

## 0.17.0 — detail views restructured

| Removed / renamed | Replacement |
|---|---|
| `DetailCustomView` / `DetailCustomViewPermissionRequired` | `DetailView` / `DetailViewPermissionRequired` |
| `GuardianDetailCustomViewPermissionRequired` | `GuardianDetailViewPermissionRequired` |
| `DetailView` + `cv_property_display` | `ObjectDetailView` (add `crud_views_object_detail` to `INSTALLED_APPS`) |
| external `django-object-detail` package / `django_object_detail` app (`ImportError: No module named 'django_object_detail'`) | vendored in-tree; import from `crud_views_object_detail.lib` |
| `OBJECT_DETAIL_*` settings | `CRUD_VIEWS_OBJECT_DETAIL_*` — the old names are no longer read and fail silently |

## Feature availability

Feature sections in the other reference files carry `Available since X.Y.Z` markers. Before using a
feature in a project, compare the marker with the installed version (`pip show django-crud-views`).
