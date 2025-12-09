from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from datetime import datetime
from vehicles.choices import VehicleCategory
from vehicles.models import Brands, Models, Types, Displacements, Years, DisplacementYear
import re

def normalize_whitespace(value):
    if not value:
        return value
    return re.sub(r'\s+', ' ', str(value)).strip()


def parse_date(value):
    if not value or str(value).strip() in ('>', ''):
        return None
    try:
        return datetime.strptime(str(value).strip(), '%m/%y').date()
    except ValueError:
        return None


class BrandsResource(resources.ModelResource):
    sync_id = fields.Field(attribute='sync_id', column_name='brand_id')
    brembo_code = fields.Field(attribute='brembo_code', column_name='brembo_brand_code')
    name = fields.Field(attribute='name', column_name='brand_title')

    class Meta:
        model = Brands
        import_id_fields = ['sync_id']
        fields = ('sync_id', 'brembo_code', 'name')
        skip_unchanged = True

    def before_import_row(self, row, **kwargs):
        if not row.get('brembo_brand_code') or row.get('brembo_brand_code').strip() == '':
            row['brembo_brand_code'] = None


class ModelsResource(resources.ModelResource):
    sync_id = fields.Field(attribute='sync_id', column_name='model_id')
    vehicle_type = fields.Field(attribute='vehicle_type', column_name='vehicle_type')
    brembo_code = fields.Field(attribute='brembo_code', column_name='brembo_model_code')
    name = fields.Field(attribute='name', column_name='model_name')
    brand = fields.Field(
        attribute='brand',
        column_name='brand_id',
        widget=ForeignKeyWidget(Brands, field='sync_id')
    )

    class Meta:
        model = Models
        import_id_fields = ['sync_id']
        fields = ('sync_id', 'brembo_code', 'name', 'brand', 'vehicle_type', 'date_start', 'date_end')
        skip_unchanged = True

    def before_import_row(self, row, **kwargs):
        vehicle_type = row.get('vehicle_type')
        row['vehicle_type'] = VehicleCategory.parse(vehicle_type)

        if vehicle_type == 'Bike':
            name = row.get('model_title')
        else:
            name = row.get('model_name')

        if name: name = normalize_whitespace(name)
        row['model_name'] = name

        row['date_start'] = parse_date(row.get('date_start'))
        row['date_end'] = parse_date(row.get('date_end'))

        if not row.get('brembo_model_code') or row.get('brembo_model_code').strip() == '':
            row['brembo_model_code'] = None


class TypesResource(resources.ModelResource):
    sync_id = fields.Field(attribute='sync_id', column_name='type_id')
    brembo_code = fields.Field(attribute='brembo_code', column_name='brembo_type_code')
    name = fields.Field(attribute='name', column_name='type_name')
    kw = fields.Field(attribute='kw', column_name='kw')
    cv = fields.Field(attribute='cv', column_name='cv')
    model = fields.Field(
        attribute='model',
        column_name='model_id',
        widget=ForeignKeyWidget(Models, field='sync_id')
    )

    class Meta:
        model = Types
        import_id_fields = ['sync_id']
        fields = ('sync_id', 'brembo_code', 'name', 'model', 'kw', 'cv', 'date_start', 'date_end')
        skip_unchanged = True

    def skip_row(self, instance, original, row, import_validation_errors=None):
        kw, cv = row.get('kw'), row.get('cv')
        if not kw or not cv or not str(kw).strip() or not str(cv).strip():
            return True
        return super().skip_row(instance, original, row, import_validation_errors)

    def before_import_row(self, row, **kwargs):
        name = row.get('model_name')
        row['model_name'] = normalize_whitespace(name)
        row['date_start'] = parse_date(row.get('date_start'))
        row['date_end'] = parse_date(row.get('date_end'))

        if not row.get('brembo_type_code') or row.get('brembo_type_code').strip() == '':
            row['brembo_type_code'] = None

    def before_save_instance(self, instance, row, **kwargs):
        if instance.model:
            instance.brand = instance.model.brand


class DisplacementsResource(resources.ModelResource):
    sync_id = fields.Field(attribute='sync_id', column_name='disp_id')
    brembo_code = fields.Field(attribute='brembo_code', column_name='brembo_disp_code')
    value = fields.Field(attribute='value', column_name='value')
    model = fields.Field(
        attribute='model',
        column_name='model_id',
        widget=ForeignKeyWidget(Models, field='sync_id')
    )

    class Meta:
        model = Displacements
        import_id_fields = ['sync_id']
        fields = ('sync_id', 'brembo_code', 'model', 'value')
        skip_unchanged = True

    def before_import_row(self, row, **kwargs):
        if not row.get('brembo_disp_code') or row.get('brembo_disp_code').strip() == '':
            row['brembo_disp_code'] = None

    def before_save_instance(self, instance, row, **kwargs):
        if instance.model:
            instance.brand = instance.model.brand


class YearsResource(resources.ModelResource):
    class Meta:
        model = Years
        import_id_fields = ['value']
        fields = ('sync_id', 'value')
        skip_unchanged = True


class DisplacementYearResource(resources.ModelResource):
    sync_id = fields.Field(attribute='sync_id', column_name='year_id')
    displacement = fields.Field(
        attribute='displacement',
        column_name='disp_id',
        widget=ForeignKeyWidget(Displacements, field='sync_id')
    )

    class Meta:
        model = DisplacementYear
        import_id_fields = ['sync_id']
        fields = ('sync_id', 'displacement')
        skip_unchanged = True

    def before_save_instance(self, instance, row, **kwargs):
        year_value = int(row.get('year_value'))
        year, created = Years.objects.get_or_create(value=year_value)
        instance.year = year
