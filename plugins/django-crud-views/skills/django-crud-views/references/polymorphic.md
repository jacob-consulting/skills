# Polymorphic models (`crud_views_polymorphic`)

## Polymorphic Models (`crud_views_polymorphic`)

*Available since 0.5.0.*

Two-step create flow for polymorphic models (requires `django-polymorphic`).

Install: `pip install django-crud-views[polymorphic]`, add `"crud_views_polymorphic.apps.CrudViewsPolymorphicConfig"` to `INSTALLED_APPS`.

```python
from crud_views_polymorphic.lib import (
    PolymorphicCreateSelectViewPermissionRequired,  # step 1: choose subtype
    PolymorphicCreateViewPermissionRequired,         # step 2: fill subtype form
    PolymorphicUpdateViewPermissionRequired,
    PolymorphicDetailViewPermissionRequired,
)
from crud_views_polymorphic.lib.create_select import PolymorphicContentTypeForm
from crud_views_polymorphic.lib.delete import PolymorphicDeleteViewPermissionRequired

class VehicleCreateSelectView(CrispyViewMixin, PolymorphicCreateSelectViewPermissionRequired):
    form_class = PolymorphicContentTypeForm
    cv_viewset = cv_vehicle
    # cv_polymorphic_include = [Car, Truck]  # optional whitelist
    # cv_polymorphic_exclude = [...]         # optional blacklist (mutually exclusive)

class VehicleCreateView(CrispyViewMixin, PolymorphicCreateViewPermissionRequired):
    cv_viewset = cv_vehicle
    polymorphic_forms = {Car: CarForm, Truck: TruckForm}

class VehicleUpdateView(CrispyViewMixin, PolymorphicUpdateViewPermissionRequired):
    cv_viewset = cv_vehicle
    polymorphic_forms = {Car: CarForm, Truck: TruckForm}

class VehicleDeleteView(CrispyViewMixin, PolymorphicDeleteViewPermissionRequired):
    form_class = CrispyDeleteForm
    cv_viewset = cv_vehicle

# property grid on a polymorphic detail view requires ObjectDetailMixin (see Detail views above)
class VehicleDetailView(ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_property_display = [
        {"title": "Attributes", "properties": ["name"]},
    ]
```

List view must use `cv_context_actions = ["create_select"]` instead of `"create"`.

The step-2 create view (URL `<prefix>/create/ct/<content-type id>/`) has its own context actions, default
`["home"]` (`CRUD_VIEWS_POLYMORPHIC_CREATE_CONTEXT_ACTIONS`). Never add `"create"` to them: that button can't be
reversed without the content type, so the page fails with `NoReverseMatch`. Up to package 0.29.2 the view
inherited `["home", "create"]` and needed `cv_context_actions = ["home"]` set by hand ([migration.md](migration.md)).

### Subtype-specific fields in the property grid

Fields are resolved against the real subtype instance, so a Truck can show `payload_tons`. To show **different
groups per subtype**, override the `property_display` property (`ObjectDetailMixin` reads it at render time, after
the object is loaded). Keep a class-level `cv_property_display` for the startup checks:

```python
COMMON = [{"title": "Vehicle", "properties": ["name", "plate"]}]
TYPE_GROUPS = {
    Car: [{"title": "Car", "properties": ["doors", "seats"]}],
    Truck: [{"title": "Truck", "properties": ["payload_tons", "axles"]}],
}


class VehicleDetailView(ObjectDetailMixin, PolymorphicDetailViewPermissionRequired):
    cv_viewset = cv_vehicle
    cv_property_display = COMMON

    @property
    def property_display(self):
        return COMMON + TYPE_GROUPS.get(type(self.object), [])
```

Listing every subtype's fields in one group instead would show the other subtype's fields as empty rows.

For a "type" column in the list: `tables.Column(accessor="polymorphic_ctype__model", verbose_name="Type")`.
