from django.contrib import admin

from vehicles.choices import VehicleCategory
from vehicles.models import Brands, Models, Types, Years, DisplacementYear, Displacements
from django.utils.translation import gettext_lazy as _


class DisplacementYearInline(admin.TabularInline):
    model = DisplacementYear
    exclude = ('sync_id',)
    extra = 0

class ModelFilter(admin.SimpleListFilter):
    title = _('Model')
    parameter_name = 'model'

    def lookups(self, request, model_admin):
        brand_id = request.GET.get('brand__id__exact')
        if not brand_id:
            return []

        allowed_vehicle_types = getattr(model_admin, 'model_vehicle_types', None)

        qs = Models.objects.filter(brand_id=brand_id)
        if allowed_vehicle_types:
            qs = qs.filter(vehicle_type__in=allowed_vehicle_types)

        return [(m.pk, str(m)) for m in qs]

    def queryset(self, request, queryset):
        val = self.value()
        if val:
            return queryset.filter(model_id=val)
        return queryset

@admin.register(Brands)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)
    plural = "brands"

    exclude = ("created_at", "updated_at", "sync_id")

@admin.register(Models)
class ModelAdmin(admin.ModelAdmin):
    list_display = ("brand", "name", "vehicle_type", "date_start", "date_end")
    search_fields = ("name",)
    ordering = ("name",)
    list_filter = ("brand", "vehicle_type")
    plural = "models"

    exclude = ("created_at", "updated_at", "sync_id")

@admin.register(Types)
class TypeAdmin(admin.ModelAdmin):
    model_vehicle_types = [VehicleCategory.CAR, VehicleCategory.CV]

    list_display = ("brand", "model", "name", "kw", "cv", "date_start", "date_end")
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

    list_filter = ("brand", ModelFilter)
    exclude = ("created_at", "updated_at", "sync_id")

@admin.register(Displacements)
class DisplacementsAdmin(admin.ModelAdmin):
    model_vehicle_types = [VehicleCategory.BIKE]

    list_display = ("brand", "model", "value")
    exclude = ("created_at", "updated_at", "sync_id")
    fieldsets = (
        ('Vehicle Info', {
            'fields': ('brand', 'model')
        }),
        ('Performance', {
            'fields': ('value',)
        }),
    )

    list_filter = ("brand", ModelFilter)
    inlines = (DisplacementYearInline, )

@admin.register(Years)
class YearsAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)

    exclude = ("created_at", "updated_at", "sync_id")