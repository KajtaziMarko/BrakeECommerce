from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from django.utils.text import capfirst

from catalogue.models import ProductVehicle
from vehicles.models import Brand, Model, Car, CommercialVehicle, MotorBike
from django.utils.translation import gettext_lazy as _


class CompatibleProductInline(GenericTabularInline):
    """
    Shows all ProductVehicle rows where the *vehicle* is this object,
    i.e. every compatible product (Disc/Pad/Drum/...).
    """
    model = ProductVehicle
    ct_field = "vehicle_ct"
    ct_fk_field = "vehicle_id"

    fields = ("product_type", "product_info", "price", "available")
    readonly_fields = ("product_type", "product_info", "price", "available")

    extra = 0
    can_delete = False
    max_num = 0
    show_change_link = False  # links to ProductVehicle; we’ll link to the product ourselves
    verbose_name = "Compatible product"
    verbose_name_plural = "Compatible products"
    classes = ("collapse",)

    def has_add_permission(self, request, obj):
        return False

    # Minor perf: pull content types in one go
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("product_ct", "vehicle_ct")

    def product_type(self, obj):
        """
        Human model name from ContentType (e.g. 'Disc', 'Pad Accessory').
        """
        if not obj.product_ct_id:
            return "-"
        return capfirst(obj.product_ct.name)
    product_type.short_description = "Type"

    def product_info(self, obj):
        """
        Clickable label to the product’s admin page: "<type_label or name> · CODE · EAN"
        Falls back gracefully if fields are missing.
        """
        p = getattr(obj, "product", None)
        if not p:
            return "-"

        # build a nice label
        label = getattr(p, "type_label", "") or getattr(p, "name", "") or self.product_type(obj)
        bits = [label]
        if getattr(p, "code", None):
            bits.append(str(p.code))
        if getattr(p, "ean", None):
            bits.append(str(p.ean))
        text = " · ".join(bits)

        # link to the product change view
        try:
            # admin url pattern: admin:<app_label>_<model>_change
            from django.urls import reverse
            ct = obj.product_ct
            url = reverse(f"admin:{ct.app_label}_{ct.model}_change", args=[p.pk])
            return format_html('<a href="{}">{}</a>', url, text)
        except Exception:
            return text
    product_info.short_description = "Product"

    def price(self, obj):
        p = getattr(obj, "product", None)
        return getattr(p, "price", None)
    price.admin_order_field = "product__price"

    def available(self, obj):
        p = getattr(obj, "product", None)
        val = getattr(p, "available", None)
        return "Yes" if val else ("No" if val is not None else "-")
    available.boolean = False
    available.short_description = "Available"

class ModelFilter(admin.SimpleListFilter):
    title = _('Model')
    parameter_name = 'model'

    def lookups(self, request, model_admin):
        brand_id = request.GET.get('brand__id__exact')
        if not brand_id:
            return []
        qs = Model.objects.filter(brand_id=brand_id)
        return [(m.pk, str(m)) for m in qs]

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            return queryset.filter(model_id=val)
        return queryset

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle_type')
    search_fields = ('name',)
    list_filter = ('vehicle_type',)
    ordering = ('name', 'vehicle_type')

@admin.register(Model)
class ModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'date_start', 'date_end')
    search_fields = ('name', 'brand__name')
    ordering = ('brand__name', 'name')

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand','model','name','kw','cv','date_start','date_end')
    fieldsets = (
        ('Vehicle Info', {
            'fields': ('brand', 'model', 'name')
        }),
        ('Performance', {
            'fields': ('kw', 'cv')
        }),
        ('Production Dates', {
            'fields': ('date_start', 'date_end')
        }),
    )
    search_fields = ('brand__name','model__name','name')
    list_filter = ('brand', ModelFilter,)
    ordering = ('brand__name',)
    inlines = [CompatibleProductInline]

@admin.register(CommercialVehicle)
class CVAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand','model','name','kw','cv','date_start','date_end')
    fieldsets = (
        ('Vehicle Info', {
            'fields': ('brand', 'model', 'name')
        }),
        ('Performance', {
            'fields': ('kw', 'cv')
        }),
        ('Production Dates', {
            'fields': ('date_start', 'date_end')
        }),
    )
    search_fields = ('brand__name','model__name','name')
    autocomplete_fields = ['brand', 'model']
    list_filter = ('brand', ModelFilter,)
    ordering = ('brand__name',)
    inlines = [CompatibleProductInline]

@admin.register(MotorBike)
class MotorBikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'brand', 'model', 'displacement', 'years_list')
    fieldsets = (
        ('Vehicle Info', {
            'fields': ('brand', 'model')
        }),
        ('Performance', {
            'fields': ('displacement',)
        }),
        ('Production Dates', {
            'fields': ('years',)
        }),
    )
    filter_horizontal = ('years',)
    search_fields = ('brand__name', 'model__name', 'displacement')
    list_filter = ('brand', ModelFilter,)
    ordering = ('brand__name',)
    inlines = [CompatibleProductInline]

    def years_list(self, obj):
        return ", ".join(str(y.value) for y in obj.years.all())

    years_list.short_description = 'Model Years'