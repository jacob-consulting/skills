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
