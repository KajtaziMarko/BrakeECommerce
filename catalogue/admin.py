from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from catalogue.models import Disc

@admin.register(Disc)
class DiscAdmin(admin.ModelAdmin):
    list_display = ("code", "ean", "type_label", "price", "available", "quantity")
    search_fields = ("code", "ean")
    list_filter = ("available", "type_label", "axle", "assembly_side")

    fieldsets = (
        ("Basic Info", {"fields": (
        "code", "ean", "price", "available", "quantity", "type_label", "image_url", "technical_image_url")}),
        ("Dimensions",
         {"fields": ("diameter_mm", "thickness_th_mm", "min_thickness_mm", "height_mm", "center_bore_mm")}),
        ("Mounting / Fitment", {"fields": ("num_holes", "tightening_torque", "axle", "assembly_side", "disc_type")}),
        ("Packaging", {"fields": ("units_per_box",)}),
    )
