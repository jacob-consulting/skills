# crud_views_widget_datetimepicker — reference

*Available since package 0.1.1. Locale-following formats since 0.2.0.*

Contents: [Widgets](#widgets) · [Options](#options) · [Config merge order](#config-merge-order) ·
[Formats & language](#formats--language) · [Settings](#settings) · [Vendored mode](#vendored-mode) ·
[django-pipeline](#django-pipeline) · [System checks](#system-checks) · [How it works](#how-it-works)

## Widgets

```python
from crud_views_widget_datetimepicker.widgets import DateTimePickerInput, DatePickerInput, TimePickerInput
```

| Widget | Form field | Class defaults |
|---|---|---|
| `DateTimePickerInput` | `DateTimeField` | — |
| `DatePickerInput` | `DateField` | `{"timepicker": False}` |
| `TimePickerInput` | `TimeField` | `{"timepicker": True, "datepicker": False}` |

Use them in `Meta.widgets` of a crud_views `CrispyModelForm` or a plain `ModelForm`, or as a widget on any form
field. They also work in django-filter filter forms:

```python
import django_filters
from crud_views_widget_datetimepicker.widgets import DatePickerInput

class EventFilter(django_filters.FilterSet):
    day_from = django_filters.DateFilter(field_name="day", lookup_expr="gte", widget=DatePickerInput())
    day_to = django_filters.DateFilter(field_name="day", lookup_expr="lte", widget=DatePickerInput())

    class Meta:
        model = Event
        fields = []
```

## Options

### `config={...}`

Any [xdsoft option](https://xdsoft.net/jqplugins/datetimepicker/), passed to the picker as-is:

```python
widgets = {
    "quarter_hour": TimePickerInput(config={"step": 15}),
    "no_past": DatePickerInput(config={"minDate": 0}),                     # 0 = today
    "weekdays_only": DatePickerInput(config={"disabledWeekDays": [0, 6]}), # Sunday, Saturday
    "inline_calendar": DatePickerInput(config={"inline": True}),
    "fixed_times": TimePickerInput(config={"allowTimes": ["09:00", "12:00", "15:00"]}),
}
```

### `fix_year=2026` (`DateTimePickerInput` only)

Locks the picker to one calendar year: sets `minDate` to `2026-01-01`, `maxDate` to `2026-12-31`, and
`yearStart` / `yearEnd` to `2026`. These are only defaults: an option passed in `config` wins.

### `format=` (Django's own widget argument)

Pins the format the value is rendered and parsed with; see [Formats & language](#formats--language).

## Config merge order

Lowest to highest priority:

1. the widget class defaults (table above),
2. `lang` (see [Language](#language)),
3. `CRUD_VIEWS_DATETIMEPICKER["DEFAULTS"]` from settings,
4. the per-field `config`.

```python
# settings.py: every week starts on Monday
CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"dayOfWeekStart": 1}}

# forms.py: this field also gets 15-minute steps
widgets = {"starts_at": DateTimePickerInput(config={"step": 15})}
```

## Formats & language

### How the format is chosen

Unless pinned, the picker format follows the **active request language**. Resolution order, highest first:

1. an explicit picker `format`, from settings `DEFAULTS` or the per-field `config`;
2. Django's `format=` widget argument;
3. the first of the active locale's `DATETIME_INPUT_FORMATS` / `DATE_INPUT_FORMATS` / `TIME_INPUT_FORMATS`
   that the picker can reproduce (see the token table);
4. a fallback every Django locale accepts: `%Y-%m-%d %H:%M` (datetime), `%Y-%m-%d` (date), `%H:%M` (time).

Datetime and time widgets prefer a locale format **without seconds** (the picker offers hours and minutes only
and would fill in the current seconds).

The widget renders the value with that same format and parses submitted values with it, so whatever the picker
writes is accepted on submit, in every locale — `2026-10-15 19:00` under `en`, `15.10.2026 19:00` under `de`. A
submitted value that doesn't match is passed on to the field's own validation unchanged.

So a multi-language site needs only `USE_I18N`, `LocaleMiddleware` (or whatever activates the language) and the
widgets — no `input_formats`, no `format`.

### Pinning a format

Picker side (PHP-style tokens) or Django side (strftime tokens):

```python
DatePickerInput(config={"format": "d.m.Y"})
DatePickerInput(format="%d.%m.%Y")
```

or for every widget: `CRUD_VIEWS_DATETIMEPICKER = {"DEFAULTS": {"format": "d.m.Y"}}`. The widget renders and
parses a pinned format itself, so it works in every locale.

### Token table

Only tokens both sides share are supported:

| strftime (Django) | PHP (picker) | Meaning |
|---|---|---|
| `%d` | `d` | day, 2 digits |
| `%m` | `m` | month, 2 digits |
| `%Y` | `Y` | year, 4 digits |
| `%y` | `y` | year, 2 digits |
| `%H` | `H` | hour 00–23 |
| `%M` | `i` | minute |
| `%S` | `s` | second |

A format with any other token (`%f`, `%b`, `%p`, …) or a letter in its literal text cannot be reproduced:

- such a locale format is skipped;
- a pinned picker `format` with other tokens is passed to the picker unchanged — the field's `input_formats`
  must then accept what the picker writes;
- a Django `format=` the picker can't reproduce leaves the picker on its own default format, while Django renders
  with `format`; submitted values are then parsed by the field's `input_formats`, which must accept both.

### Language

The picker language is the active request language (first segment: `de-at` → `de`) unless set explicitly:

- for every widget with settings `LANG`, e.g. `CRUD_VIEWS_DATETIMEPICKER = {"LANG": "de"}`;
- per field with `config={"lang": "de"}`.

Without an active language, the first segment of `LANGUAGE_CODE` is used.

**Warning:** the plugin's language is page-global (`jQuery.datetimepicker.setLocale`): one field with its own
`lang` switches every picker on that page.

## Settings

One optional dict; every key is optional:

```python
CRUD_VIEWS_DATETIMEPICKER = {
    "SOURCE": "cdn",        # "cdn" (default) | "vendored"
    "VERSION": "2.5.21",    # pinned upstream jquery-datetimepicker version, used by both modes
    "CDN_BASE": "https://cdn.jsdelivr.net/npm/jquery-datetimepicker@{version}/build/",
    "VENDOR_DIR": None,     # required for vendored mode; must be on STATICFILES_DIRS
    "EMIT": True,           # False: keep registered but let a bundler deliver the files
    "LANG": None,           # None: the active request language
    "DEFAULTS": {},         # merged into every widget's picker config
}
```

| Key | Default | Meaning |
|---|---|---|
| `SOURCE` | `"cdn"` | `"cdn"` or `"vendored"`; anything else → `crud_views.E333` |
| `VERSION` | `"2.5.21"` | upstream version, used by both modes |
| `CDN_BASE` | jsDelivr template | `{version}` is replaced with `VERSION`; also the download source of vendored mode |
| `VENDOR_DIR` | `None` | required for vendored mode; must be listed in `STATICFILES_DIRS` |
| `EMIT` | `True` | `False` keeps the assets registered but suppresses their `{% cv_js %}` / `{% cv_css %}` output |
| `LANG` | `None` | picker language; `None` = active request language |
| `DEFAULTS` | `{}` | merged into every widget's picker config |

`SOURCE`, `VERSION`, `CDN_BASE` and `EMIT` are read once at startup (asset registration) — changing them needs a
restart. `LANG` and `DEFAULTS` are read each time a widget renders.

## Vendored mode

By default the plugin loads from jsDelivr. In production you usually want it served from your own static files:
no third-party request from users' browsers (GDPR), no CDN outage, simpler Content Security Policy. Vendored mode
is also required for django-pipeline.

```python
# settings.py
CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": BASE_DIR / "vendored_static"}
STATICFILES_DIRS = [BASE_DIR / "vendored_static"]
```

```bash
python manage.py cv_vendor_datetimepicker
```

The command takes no options; everything comes from settings. It downloads the four file variants of the pinned
`VERSION` from `CDN_BASE` (`jquery.datetimepicker.full.js`, `.full.min.js`, `.css`, `.min.css`) into
`VENDOR_DIR/crud_views_widget_datetimepicker/<VERSION>/` and writes a `.vendored` version stamp next to them. It
fails with `CommandError` when `VENDOR_DIR` is not set.

Re-run it after changing `VERSION`. Either commit the vendored directory or run the command in the deployment
build, **before `collectstatic`**.

## django-pipeline

CDN mode cannot be bundled. Use vendored mode, build the bundle from the same path list the app uses internally,
and switch off the app's own tag output with `EMIT: False`:

```python
# settings.py
from crud_views_widget_datetimepicker.assets import source_files

_dtp = source_files("2.5.21", minified=False)   # pipeline minifies itself; keep in sync with VERSION
PIPELINE = {
    "JAVASCRIPT": {
        "main": {
            "source_filenames": ["js/jquery.min.js", *_dtp["js"]],  # jQuery first
            "output_filename": "js/main.js",
        }
    },
    "STYLESHEETS": {"main": {"source_filenames": [*_dtp["css"]], "output_filename": "css/main.css"}},
}
CRUD_VIEWS_DATETIMEPICKER = {"SOURCE": "vendored", "VENDOR_DIR": BASE_DIR / "vendored_static", "EMIT": False}
```

`crud_views_widget_datetimepicker.assets` is **Django-free**, so importing it from `settings.py` is safe. It is
the single source of truth for asset paths (asset registration, vendoring command, your pipeline config).

| Function | Returns |
|---|---|
| `source_files(version, minified=True)` | static paths for vendored mode / pipeline: `{"js": ["crud_views_widget_datetimepicker/<v>/jquery.datetimepicker.full.min.js", "crud_views_widget_datetimepicker/init.js"], "css": ["crud_views_widget_datetimepicker/<v>/jquery.datetimepicker.min.css"]}`; `minified=False` → `jquery.datetimepicker.full.js` / `jquery.datetimepicker.css` |
| `cdn_files(cdn_base, version, minified=True)` | the CDN URLs of the plugin files only (`init.js` is always static) |
| `bundle(source, version, cdn_base, minified=True)` | what the app registers: CDN plugin files + static `init.js` for `"cdn"`, else `source_files(...)` |

**Load order is load-bearing:** jQuery → plugin → `init.js`. `source_files()` already orders plugin before
`init.js`; jQuery is yours to put first.

## System checks

Registered under the `crud_views` tag (`python manage.py check --tag crud_views`).

| ID | Level | When | Fix |
|---|---|---|---|
| `crud_views.E333` | Error | `SOURCE` is neither `"cdn"` nor `"vendored"` | set `SOURCE` to `"cdn"` or `"vendored"` |
| `crud_views.E332` | Error | `SOURCE` is `"vendored"` but `VENDOR_DIR` is not set | set `VENDOR_DIR` and list it in `STATICFILES_DIRS` |
| `crud_views.W330` | Warning | vendored mode, no vendored files found at `<VENDOR_DIR>/crud_views_widget_datetimepicker/<VERSION>` | run `python manage.py cv_vendor_datetimepicker` |
| `crud_views.W331` | Warning | the `.vendored` stamp names another version than `VERSION` (e.g. files copied by hand) | re-run `python manage.py cv_vendor_datetimepicker` |

`E333` is checked in every mode, the others only in vendored mode. Files live in a directory per version, so W330
also appears right after changing `VERSION`. `W330`/`W331` come from django-crud-views core
(`crud_views.lib.vendor.check_vendored`); `E332`/`E333` are this app's own. Core's `W345` (a CDN extension
bundled by pipeline) is fixed by switching to vendored mode.

## How it works

- No `Media` class. The plugin and a small `init.js` are registered with the django-crud-views asset registry
  (key `datetimepicker`), so `{% cv_css %}` / `{% cv_js %}` deliver them on every page.
- At render time (per request) each widget serialises its merged config to JSON in an `xdsoft-datetime-config`
  attribute on the `<input>`.
- `init.js` activates every `input[xdsoft-datetime-config]` on document ready, and again whenever
  django-crud-views dispatches `cv:modal:loaded` on `#cv-modal` after injecting modal content — pickers work in
  crud-views modals without extra code.
- jQuery must be loaded in the base template before `{% cv_js %}` (same rule as django-crud-views core).
