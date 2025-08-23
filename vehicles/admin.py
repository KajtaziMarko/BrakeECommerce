from django.contrib import admin
from vehicles.models import Brand, Model, Car, CommercialVehicle, MotorBike
from django.utils.translation import gettext_lazy as _


class ModelFilter(admin.SimpleListFilter):
    title = _('Model')
    parameter_name = 'model'

    def lookups(self, request, model_admin):
        # pull the brand’s PK from the URL
        brand_id = request.GET.get('brand__id__exact')
        if not brand_id:
            return []   # no brand selected → no model choices
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
    list_display = ('brand','model','name','kw','cv','date_start','date_end')
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

@admin.register(CommercialVehicle)
class CVAdmin(admin.ModelAdmin):
    list_display = ('brand','model','name','kw','cv','date_start','date_end')
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

@admin.register(MotorBike)
class MotorBikeAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'displacement', 'years_list')
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

    def years_list(self, obj):
        return ", ".join(str(y.value) for y in obj.years.all())

    years_list.short_description = 'Model Years'