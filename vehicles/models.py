# vehicles/models.py
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from smart_selects.db_fields import ChainedForeignKey
from .choices import VehicleCategory

class Brand(models.Model):
    name = models.CharField(max_length=50)
    vehicle_type = models.CharField(max_length=1, choices=VehicleCategory.choices)

    def __str__(self):
        return f"{self.name} ({self.get_vehicle_type_display()})"

class Model(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date_start = models.DateField(null=True, blank=True)
    date_end   = models.DateField(null=True, blank=True)

    def __str__(self):
        start = self.date_start.strftime('%m/%Y') if self.date_start else '?'
        end   = self.date_end.strftime('%m/%Y')   if self.date_end   else '>'
        return f"{self.name} ({start}–{end})"

class PoweredVehicle(models.Model):
    kw = models.PositiveIntegerField()
    cv = models.PositiveIntegerField()
    class Meta: abstract = True

class DatedVehicle(models.Model):
    date_start = models.DateField(null=True, blank=True)
    date_end   = models.DateField(null=True, blank=True)
    class Meta: abstract = True

class Car(PoweredVehicle, DatedVehicle):
    TYPE_CODE = VehicleCategory.CAR
    brand = models.ForeignKey(
        Brand,
        related_name='cars',
        on_delete=models.CASCADE,
        limit_choices_to={'vehicle_type': TYPE_CODE},
    )
    model = ChainedForeignKey(
        Model, chained_field="brand", chained_model_field="brand",
        show_all=False, auto_choose=True, sort=True, on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100)
    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='vehicle_ct',
        object_id_field='vehicle_id',
        related_query_name='car_links',
    )

    class Meta: verbose_name = "Car"

    def __str__(self):
        start = self.date_start.strftime('%m/%y') if self.date_start else '?'
        end   = self.date_end.strftime('%m/%y')   if self.date_end   else '?'
        return f"{self.brand.name} {self.model.name} {self.name} ({start}–{end}) – {self.kw} KW/{self.cv} CV"

class CommercialVehicle(PoweredVehicle, DatedVehicle):
    TYPE_CODE = VehicleCategory.CV
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE,
        limit_choices_to={'vehicle_type': TYPE_CODE},
    )
    model = ChainedForeignKey(
        Model, chained_field="brand", chained_model_field="brand",
        show_all=False, auto_choose=True, sort=True, on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=100)

    class Meta: verbose_name = "Commercial Vehicle"

    def __str__(self):
        start = self.date_start.strftime('%Y') if self.date_start else '?'
        end   = self.date_end.strftime('%Y')   if self.date_end   else '?'
        return f"{self.brand.name} {self.model.name} {self.name} ({start}–{end}) – {self.kw} KW/{self.cv} CV"

class Year(models.Model):
    value = models.PositiveSmallIntegerField(unique=True)
    class Meta:
        ordering = ['value']
        verbose_name = 'Model Year'
        verbose_name_plural = 'Model Years'
    def __str__(self): return f"{self.value}"

class MotorBike(models.Model):
    TYPE_CODE = VehicleCategory.BIKE
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE,
        limit_choices_to={'vehicle_type': TYPE_CODE},
    )
    model = ChainedForeignKey(
        Model, chained_field="brand", chained_model_field="brand",
        show_all=False, auto_choose=True, sort=True, on_delete=models.CASCADE,
    )
    displacement = models.IntegerField()
    years = models.ManyToManyField(Year, related_name='motorbikes', blank=True)

    class Meta: verbose_name = 'Motor Bike'

    def __str__(self):
        return f"{self.brand.name} {self.displacement}"
