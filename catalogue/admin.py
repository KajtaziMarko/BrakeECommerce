from django.utils.text import capfirst
from import_export.admin import ImportExportModelAdmin
from catalogue.import_recources import DiscResource, DrumResource, PadResource, PadAccessoryResource, HoseResource, WheelCylinderResource, MasterCylinderResource, ClutchCylinderResource, ClutchMasterCylinderResource, CaliperResource, ShoeKitResource, ShoeResource, ProportioningValveResource, KitResource
from catalogue.models import Disc, ProductVehicle, product_ct_limit, vehicle_ct_limit, Drum, Pad, PadAccessory, Hose, WheelCylinder, MasterCylinder, ClutchCylinder, ClutchMasterCylinder, Caliper, ShoeKit, Shoe, ProportioningValve, Kit
from django.contrib.contenttypes.admin import GenericStackedInline, GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.utils.html import format_html
from django.contrib import admin
from django.urls import reverse

@admin.register(ProductVehicle)
class ProductVehicleAdmin(admin.ModelAdmin):
    search_fields = ('product_id',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product_ct":
            kwargs["queryset"] = ContentType.objects.filter(product_ct_limit())
        elif db_field.name == "vehicle_ct":
            kwargs["queryset"] = ContentType.objects.filter(vehicle_ct_limit())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class CompatibleVehicleInline(GenericTabularInline):
    model = ProductVehicle
    ct_field = "product_ct"
    ct_fk_field = "product_id"

    fields = ("vehicle_type", "vehicle_bmt")
    readonly_fields = ("vehicle_type", "vehicle_bmt")

    extra = 0
    can_delete = False
    max_num = 0
    show_change_link = False
    verbose_name = "Compatible vehicle"
    verbose_name_plural = "Compatible vehicles"
    classes = ("collapse",)

    def has_add_permission(self, request, obj):
        return False

    def vehicle_type(self, obj):
        """
        'Car', 'Commercial Vehicle', or 'Motor Bike' from the row's ContentType.
        """
        if not obj.vehicle_ct_id:
            return "-"
        return capfirst(obj.vehicle_ct.name)
    vehicle_type.short_description = "Type"

    def vehicle_bmt(self, obj):
        """
        Render a readable line depending on whether the row points to a Car, CV, or Bike.
        """
        v = getattr(obj, "vehicle", None)
        if not v:
            return "-"

        model_label = (obj.vehicle_ct.model or "").lower()

        # Helpers
        def ym(d, fmt="%m/%y", fallback="?"):
            return d.strftime(fmt) if d else fallback

        if model_label == "car":
            return f"{v.brand.name} {v.model.name} {getattr(v, 'name', '')} ({ym(getattr(v,'date_start',None))}–{ym(getattr(v,'date_end',None))}) – {getattr(v,'kw','?')} kW/{getattr(v,'cv','?')} CV".strip()
        elif model_label == "commercialvehicle":
            return f"{v.brand.name} {v.model.name} {getattr(v, 'name', '')} ({ym(getattr(v,'date_start',None), fmt='%Y')}–{ym(getattr(v,'date_end',None), fmt='%Y')}) – {getattr(v,'kw','?')} kW/{getattr(v,'cv','?')} CV".strip()
        elif model_label == "motorbike":
            years = list(v.years.values_list('value', flat=True))
            years_txt = f" ({min(years)}–{max(years)})" if years else ""
            return f"{v.brand.name} {v.model.name} {v.displacement}cc{years_txt}"

        parts = []
        for attr in ("brand", "model", "name"):
            val = getattr(v, attr, None)
            if hasattr(val, "name"):
                parts.append(val.name)
            elif val:
                parts.append(str(val))
        return " ".join(parts) or str(v)

    vehicle_bmt.short_description = "Vehicle (Brand / Model / Details)"


@admin.register(Disc)
class DiscAdmin(ImportExportModelAdmin):
    resource_classes = [DiscResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle", "assembly_side")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": (
        "code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url")}),
        ("Dimensions",
         {"fields": ("diameter_mm", "thickness_th_mm", "min_thickness_mm", "height_mm", "center_bore_mm")}),
        ("Mounting / Fitment", {"fields": ("num_holes", "tightening_torque", "axle", "assembly_side", "disc_type")}),
        ("Packaging", {"fields": ("units_per_box",)}),
    )


@admin.register(Drum)
class DrumAdmin(ImportExportModelAdmin):
    resource_classes = [DrumResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle",)
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": (
        "code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url")}),
        ("Dimensions",
         {"fields": ("diameter_mm", "max_diameter_mm", "width_mm", "height_mm", "center_bore_mm")}),
        ("Mounting / Fitment", {"fields": ("num_holes", "axle")}),
    )

@admin.register(Pad)
class PadAdmin(ImportExportModelAdmin):
    resource_classes = [PadResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url")}),
        ("Dimensions", {"fields": ("width_mm", "thickness_mm", "height_mm")}),
        ("Mounting / Fitment", {"fields": ("axle", "wva_number",)}),
        ("Packaging", {"fields": ("accessories", "braking_system", "wear_indicator", "fmsi")}),
    )

@admin.register(PadAccessory)
class PadAccessoryAdmin(ImportExportModelAdmin):
    resource_classes = [PadAccessoryResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle", "assembly_side")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url", "accessory_type")}),
        ("Dimensions", {"fields": ("length_mm",)}),
        ("Mounting / Fitment", {"fields": ("axle", "assembly_side")}),
    )

@admin.register(Hose)
class HoseAdmin(ImportExportModelAdmin):
    resource_classes = [HoseResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url")}),
        ("Threading", {"fields": ("threading_1", "threading_2")}),
        ("Mounting / Fitment", {"fields": ("axle",)})
    )

class CylinderAdminBase(ImportExportModelAdmin):
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url")}),
        ("Dimensions", {"fields": ("diameter_mm", "threading")}),
        ("Mounting / Fitment", {"fields": ("axle",)}),
        ("Packaging", {"fields": ("braking_system", "material")}),
    )

@admin.register(WheelCylinder)
class WheelCylinderAdmin(CylinderAdminBase):
    resource_classes = [WheelCylinderResource]

@admin.register(MasterCylinder)
class MasterCylinderAdmin(CylinderAdminBase):
    resource_classes = [MasterCylinderResource]

@admin.register(ClutchCylinder)
class ClutchCylinderAdmin(CylinderAdminBase):
    resource_classes = [ClutchCylinderResource]

@admin.register(ClutchMasterCylinder)
class ClutchMasterCylinderAdmin(CylinderAdminBase):
    resource_classes = [ClutchMasterCylinderResource]
    
@admin.register(Caliper)
class CaliperAdmin(ImportExportModelAdmin):
    resource_classes = [CaliperResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle", "assembly_side")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url")}),
        ("Dimensions", {"fields": ("diameter_mm",)}),
        ("Mounting / Fitment", {"fields": ("axle", "assembly_side", "position")}),
        ("Packaging", {"fields": ("braking_system", "num_pistons",)}),
    )

@admin.register(ShoeKit)
class ShoeKitAdmin(ImportExportModelAdmin):
    resource_classes = [ShoeKitResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle", "is_manual_proportioning_valve")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url", "is_manual_proportioning_valve")}),
        ("Dimensions", {"fields": ("diameter_mm", "master_cylinder_diameter_mm", "width_mm")}),
        ("Mounting / Fitment", {"fields": ("axle",)}),
        ("Packaging", {"fields": ("braking_system", "is_pre_assembled")}),
    )

@admin.register(Shoe)
class ShoeAdmin(ImportExportModelAdmin):
    resource_classes = [ShoeResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url", "is_parking_brake", "has_handbrake_lever")}),
        ("Dimensions", {"fields": ("diameter_mm", "width_mm")}),
        ("Mounting / Fitment", {"fields": ("axle",)}),
        ("Packaging", {"fields": ("braking_system", "has_accessories")}),
    )

@admin.register(ProportioningValve)
class ProportioningValveAdmin(ImportExportModelAdmin):
    resource_classes = [ProportioningValveResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url",)}),
        ("Threading", {"fields": ("threading",)}),
        ("Packaging", {"fields": ("braking_system", "material")}),
    )

@admin.register(Kit)
class KitAdmin(ImportExportModelAdmin):
    resource_classes = [KitResource]
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label")
    inlines = [CompatibleVehicleInline]

    fieldsets = (
        ("Basic Info", {"fields": ("code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url",)}),
        ("Packaging", {"fields": ("disc_per_box", "pad_per_box", "axle")}),
    )