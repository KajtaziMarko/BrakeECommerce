# vehicles/models.py
import code

from django.db import models
from django.db.models import Q
from smart_selects.db_fields import ChainedForeignKey

from vehicles.choices import VehicleCategory

class Brands(models.Model):
    sync_id = models.BigIntegerField(null=True, blank=True)
    name = models.CharField(max_length=50, null=False, blank=False, unique=True)
    slug = models.SlugField(null=False, blank=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Brands"


class Models(models.Model):
    sync_id = models.BigIntegerField(null=True, blank=True)
    brand = models.ForeignKey(Brands, on_delete=models.CASCADE)

    vehicle_type = models.CharField(max_length=1, choices=VehicleCategory.choices, null=False, blank=False, default=VehicleCategory.CAR)
    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.SlugField(null=False, blank=False, unique=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False)

    def __str__(self):
        full_date = f"{self.date_start.strftime("%m/%y")}-{self.date_end.strftime("%m/%y")}" if self.date_start and self.date_end else ""
        return f"{self.name} {full_date} ({VehicleCategory(self.vehicle_type).label})"

    class Meta:
        verbose_name_plural = "Models"
        indexes = [
            models.Index(fields=["vehicle_type", "brand"]),
        ]


class Types(models.Model):
    sync_id = models.BigIntegerField(null=True, blank=True)
    brand = models.ForeignKey(Brands, on_delete=models.CASCADE, blank=False, null=False)
    model = ChainedForeignKey(
        Models, chained_field="brand", chained_model_field="brand",
        show_all=False, auto_choose=True, sort=True, on_delete=models.CASCADE,
        limit_choices_to=Q(vehicle_type__in=[VehicleCategory.CAR, VehicleCategory.CV]),
        null=False, blank=False
    )


    name = models.CharField(max_length=50, null=False, blank=False)
    slug = models.SlugField(null=False, blank=False, unique=True)
    kw = models.IntegerField(null=False, blank=False)
    cv = models.IntegerField(null=False, blank=False)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False)

    def __str__(self):
        start_date = self.date_start.strftime("%m/%y")
        end_date = self.date_end.strftime("%m/%y")
        return f"{self.name} kw: {self.kw} cv: {self.cv} {start_date} - {end_date}"

    class Meta:
        verbose_name_plural = "Types"
        indexes = [
            models.Index(fields=["brand"]),
            models.Index(fields=["model"]),
        ]

class Displacements(models.Model):
    sync_id = models.BigIntegerField(null=True, blank=True)

    brand = models.ForeignKey(Brands, on_delete=models.CASCADE)
    model = ChainedForeignKey(
        Models, chained_field="brand", chained_model_field="brand",
        show_all=False, auto_choose=True, sort=True, on_delete=models.CASCADE,
        limit_choices_to=Q(vehicle_type__in=[VehicleCategory.BIKE]),
        null=False, blank=False
    )

    value = models.IntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False)

    def __str__(self):
        return f"{self.brand} {self.model} {self.value}cc"

    class Meta:
        verbose_name_plural = "Displacements"
        indexes = [
            models.Index(fields=["brand"]),
            models.Index(fields=["model"]),
        ]

class Years(models.Model):
    sync_id = models.BigIntegerField(null=True, blank=True)
    value = models.IntegerField(null=False, blank=False, unique=True)

    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False)

    def __str__(self):
        return str(self.value)

    class Meta:
        verbose_name_plural = "Years"


class DisplacementYear(models.Model):
    sync_id = models.BigIntegerField(null=True, blank=True)
    displacement = models.ForeignKey(Displacements, on_delete=models.CASCADE)
    year = models.ForeignKey(Years, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.displacement.brand} {self.displacement.model} {self.displacement} {self.year}"