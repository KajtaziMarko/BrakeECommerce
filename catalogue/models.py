# catalogue/models.py
from catalogue.choices import (
    DiscType, Axle, AssemblySide, Material, CaliperPosition,
    WearIndicator, PadAccessoryType
)
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation


class ProductBase(models.Model):
    code = models.CharField(max_length=30, unique=True, primary_key=True)
    ean = models.CharField(max_length=13, unique=True, null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal("0"))],
    )
    available = models.BooleanField(default=False)

    type_label = models.CharField(max_length=100, blank=True, default="")
    image_url = models.URLField(blank=True, default="")
    technical_image_url = models.URLField(blank=True, default="")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True  # removed unique_together

    def __str__(self):
        return f"{self.code} - {self.ean or ''}".strip(" -")


class Disc(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    thickness_th_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    min_thickness_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    num_holes = models.PositiveSmallIntegerField(null=True, blank=True)
    disc_type = models.CharField(max_length=1, choices=DiscType.choices, null=True, blank=True)
    center_bore_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    tightening_torque = models.PositiveIntegerField(null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    assembly_side = models.CharField(
        max_length=1, choices=AssemblySide.choices,
        null=False, blank=False,
        default=AssemblySide.NONE
    )
    units_per_box = models.PositiveSmallIntegerField(null=True, blank=True)

    fitments = GenericRelation(
        "ProductVehicle",
        content_type_field="product_ct",
        object_id_field="product_id",
        related_query_name="discs",
    )


class Pad(ProductBase):
    width_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    thickness_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    wva_number = models.CharField(max_length=30, null=True, blank=True)
    wear_indicator = models.CharField(max_length=1, choices=WearIndicator.choices, null=True, blank=True)
    accessories = models.CharField(max_length=100, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    fmsi = models.CharField(max_length=70, null=True, blank=True)


class PadAccessory(ProductBase):  # singular model name
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    accessory_type = models.CharField(max_length=1, choices=PadAccessoryType.choices, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    length_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    assembly_side = models.CharField(max_length=1, choices=AssemblySide.choices, null=False, blank=False, default=AssemblySide.NONE)


class Hose(ProductBase):
    length_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    threading_1 = models.CharField(max_length=30, null=True, blank=True)
    threading_2 = models.CharField(max_length=30, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)


class CylinderBase(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    threading = models.CharField(max_length=30, null=True, blank=True)
    material = models.CharField(max_length=1, choices=Material.choices, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)

    class Meta:
        abstract = True


class WheelCylinder(CylinderBase):
    pass


class MasterCylinder(CylinderBase):
    class Meta:
        constraints = [
            # if you truly want “rear only”
            models.CheckConstraint(
                name="master_cyl_rear_only",
                check=models.Q(axle="R") | models.Q(axle__isnull=True) | models.Q(axle=""),
            ),
        ]


class ClutchCylinder(CylinderBase):
    pass


class ClutchMasterCylinder(CylinderBase):
    pass


class Caliper(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    num_pistons = models.PositiveSmallIntegerField(null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    position = models.CharField(max_length=1, choices=CaliperPosition.choices, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    assembly_side = models.CharField(max_length=1, choices=AssemblySide.choices, null=False, blank=False, default=AssemblySide.NONE)


class ShoeKit(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    master_cylinder_diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_pre_assembled = models.BooleanField(default=False)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    is_manual_proportioning_valve = models.BooleanField(default=False)  # fixed “manuel”


class Shoe(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_parking_brake = models.BooleanField(default=False)
    has_handbrake_lever = models.BooleanField(default=False)  # “lever”, not “level”
    has_accessories = models.BooleanField(default=False)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)


class ProportioningValve(ProductBase):
    threading = models.CharField(max_length=30, null=True, blank=True)
    material = models.CharField(max_length=1, choices=Material.choices, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)


class Kit(ProductBase):
    disc_per_box = models.PositiveSmallIntegerField(null=True, blank=True)
    pad_per_box = models.PositiveSmallIntegerField(null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)


class ProductVehicle(models.Model):
    product_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="+")
    product_id = models.CharField(max_length=30)
    product = GenericForeignKey("product_ct", "product_id")

    vehicle_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="+")
    vehicle_id = models.PositiveIntegerField()
    vehicle = GenericForeignKey("vehicle_ct", "vehicle_id")


    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product_ct", "product_id", "vehicle_ct", "vehicle_id"],
                name="uniq_product_vehicle",
            ),
        ]
        indexes = [
            models.Index(fields=["product_ct", "product_id"]),
            models.Index(fields=["vehicle_ct", "vehicle_id"]),
        ]

    def __str__(self):
        return f"{self.product} -> {self.vehicle}"