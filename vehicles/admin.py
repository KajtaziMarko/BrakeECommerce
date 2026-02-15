from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from vehicles.choices import VehicleCategory
from vehicles.models import Brands, Models, Types, Years, DisplacementYear, Displacements
from django.utils.translation import gettext_lazy as _

from vehicles.resources import BrandsResource, ModelsResource, TypesResource, DisplacementsResource, YearsResource, \
    DisplacementYearResource


class DisplacementYearInline(admin.TabularInline):
    model = DisplacementYear
    exclude = ('sync_id', 'slug')
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
class BrandAdmin(ImportExportModelAdmin):
    resource_class = BrandsResource
    list_display = ("name", "slug")
    search_fields = ("name",)
    ordering = ("name",)
    plural = "brands"
    exclude = ("created_at", "updated_at", "sync_id", "slug")

    fieldsets = (
        ('Brand Info', {
            'fields': ('name',)
        }),
    )


@admin.register(Models)
class ModelAdmin(ImportExportModelAdmin):
    resource_class = ModelsResource
    list_display = ("brand", "name", "slug", "vehicle_type", "date_start", "date_end")
    search_fields = ("name",)
    ordering = ("name",)
    list_filter = ("brand", "vehicle_type")
    plural = "models"
    exclude = ("created_at", "updated_at", "sync_id", "slug")

    fieldsets = (
        ('Model Info', {
            'fields': ('brand', 'name','vehicle_type')
        }),
        ('Production Dates', {
            'fields': ('date_start', 'date_end')
        }),
    )

@admin.register(Types)
class TypeAdmin(ImportExportModelAdmin):
    resource_class = TypesResource
    model_vehicle_types = [VehicleCategory.CAR, VehicleCategory.CV]

    search_fields = ('name', 'slug', 'brand__name', 'model__name')
    list_display = ("brand", "model", "name", "slug", "kw", "cv", "date_start", "date_end")
    fieldsets = (
        ('Vehicle Info', {
            'fields': ('brand', 'model', 'name', 'sync_id')
        }),
        ('Performance', {
            'fields': ('kw', 'cv')
        }),
        ('Production Dates', {
            'fields': ('date_start', 'date_end')
        }),
    )
    list_filter = ("brand", ModelFilter)
    exclude = ("created_at", "updated_at", "slug")

@admin.register(Displacements)
class DisplacementsAdmin(ImportExportModelAdmin):
    resource_class = DisplacementsResource
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
class YearsAdmin(ImportExportModelAdmin):
    resource_class = YearsResource
    list_display = ('value',)
    search_fields = ('value',)

    exclude = ("created_at", "updated_at", "sync_id")

@admin.register(DisplacementYear)
class DisplacementYearAdmin(ImportExportModelAdmin):
    resource_class = DisplacementYearResource

    search_fields = ('slug', 'displacement__brand__name', 'displacement__model__name', 'year__value')
    list_display = ('displacement', 'year', 'slug')
    list_filter = ('year',)
    search_fields = ('displacement__brand__name',)