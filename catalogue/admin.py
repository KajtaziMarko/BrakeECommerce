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

    fields = ("vehicle_bmt",)
    readonly_fields = ("vehicle_bmt",)

    extra = 0
    can_delete = False
    max_num = 0
    show_change_link = False  # just text
    verbose_name = "Compatible vehicle"
    verbose_name_plural = "Compatible vehicles"
    classes = ("collapse",)  # collapsible UI

    def has_add_permission(self, request, obj):
        return False

    def vehicle_bmt(self, obj):
        """
        Show 'Brand Model Type' for the related vehicle (Car / CV / Bike).
        Falls back gracefully if some fields are missing.
        """
        v = getattr(obj, "vehicle", None)
        if not v:
            return "-"

        def display_attr(o, attr_candidates):
            # use get_<field>_display() if available, else attribute value
            for a in attr_candidates:
                disp = getattr(o, f"get_{a}_display", None)
                if callable(disp):
                    val = disp()
                    if val:
                        return val
                val = getattr(o, a, None)
                if val:
                    # if it's a related object, prefer its 'name'/'title' or str()
                    if hasattr(val, "name"):
                        return val.name
                    if hasattr(val, "title"):
                        return val.title
                    return str(val)
            return None

        brand = display_attr(v, ["brand", "make", "manufacturer"])
        model = display_attr(v, ["model", "model_name", "series"])
        vtype = display_attr(v, ["type", "type_name", "variant", "trim", "body_type", "engine", "displacement"])

        parts = [p for p in [brand, model, vtype] if p]
        return " ".join(parts) if parts else str(v)

    vehicle_bmt.short_description = "Vehicle (Brand Model Type)"


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