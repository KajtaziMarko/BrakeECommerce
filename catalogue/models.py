# catalogue/models.py
from django.db.models import Q

from catalogue.choices import (
    DiscType, Axle, AssemblySide, Material, CaliperPosition,
    WearIndicator, PadAccessoryType
)
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation

from django.apps import apps as django_apps
from vehicles.models import Car, MotorBike, CommercialVehicle

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
        null=True, blank=True,
    )
    units_per_box = models.PositiveSmallIntegerField(null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='disc_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.diameter_mm:       specs.append(("Diameter", f"{self.diameter_mm}", "mm"))
        if self.thickness_th_mm:   specs.append(("Thickness TH", f"{self.thickness_th_mm}", "mm"))
        if self.min_thickness_mm:  specs.append(("Min. Thickness TH", f"{self.min_thickness_mm}", "mm"))
        if self.height_mm:         specs.append(("Height", f"{self.height_mm}", "mm"))
        if self.num_holes:         specs.append(("Number of Holes", f"{self.num_holes}", ""))
        if self.disc_type:         specs.append(("Type", self.get_disc_type_display(), ""))
        if self.center_bore_mm:    specs.append(("Centering", f"{self.center_bore_mm}", "mm"))
        if self.tightening_torque: specs.append(("Tightening Torque", f"{self.tightening_torque}", ""))
        if self.axle:              specs.append(("Axle", self.get_axle_display(), ""))
        if self.assembly_side:     specs.append(("Assembly Side", self.get_assembly_side_display(), ""))
        if self.units_per_box:     specs.append(("Units Per Box", f"{self.units_per_box}", ""))
        return specs


class Drum(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    num_holes = models.PositiveSmallIntegerField(null=True, blank=True)
    center_bore_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    max_diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='drum_links',
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="drum_max_diameter_gt_diameter",
                check=(
                        models.Q(max_diameter_mm__isnull=True) |
                        models.Q(diameter_mm__isnull=True) |
                        models.Q(max_diameter_mm__gt=models.F("diameter_mm"))
                ),
            ),
        ]

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.diameter_mm:       specs.append(("Diameter", f"{self.diameter_mm}", "mm"))
        if self.width_mm:          specs.append(("Width", f"{self.width_mm}", "mm"))
        if self.height_mm:         specs.append(("Height", f"{self.height_mm}", "mm"))
        if self.num_holes:         specs.append(("Number of Holes", f"{self.num_holes}", ""))
        if self.center_bore_mm:    specs.append(("Centering", f"{self.center_bore_mm}", "mm"))
        if self.max_diameter_mm:   specs.append(("Max Diameter", f"{self.center_bore_mm}", "mm"))
        if self.axle:              specs.append(("Axle", self.get_axle_display(), ""))
        return specs


class Pad(ProductBase):
    width_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    thickness_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    wva_number = models.CharField(max_length=100, null=True, blank=True)
    wear_indicator = models.CharField(max_length=1, choices=WearIndicator.choices, null=True, blank=True)
    accessories = models.CharField(max_length=100, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    fmsi = models.CharField(max_length=70, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.width_mm:               specs.append(("Width", f"{self.width_mm}", "mm"))
        if self.thickness_mm:           specs.append(("Thickness TH", f"{self.thickness_mm}", "mm"))
        if self.height_mm:              specs.append(("Height", f"{self.height_mm}", "mm"))
        if self.braking_system:         specs.append(("Braking System", self.braking_system, ""))
        if self.wva_number:             specs.append(("WVA", self.wva_number, ""))
        if self.wear_indicator:         specs.append(("Wear Indicator", self.get_wear_indicator_display(), ""))
        if self.accessories:            specs.append(("Accessories", self.accessories, ""))
        if self.axle:                   specs.append(("Axle", self.get_axle_display(), ""))
        if self.fmsi:                   specs.append(("FMSI", self.fmsi, ""))
        return specs


class PadAccessory(ProductBase):
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    accessory_type = models.CharField(max_length=1, choices=PadAccessoryType.choices, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    length_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    assembly_side = models.CharField(max_length=1, choices=AssemblySide.choices, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    class Meta:
        verbose_name_plural = "Pad Accessories"

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.braking_system:         specs.append(("Braking System", self.braking_system, ""))
        if self.accessory_type:         specs.append(("Accessory", self.get_accessory_type_display(), ""))
        if self.axle:                   specs.append(("Axle", self.get_axle_display(), ""))
        if self.length_mm:              specs.append(("Length", f"{self.length_mm}", "mm"))
        if self.assembly_side: specs.append(("Assembly Side", self.assembly_side, ""))
        return specs


class Hose(ProductBase):
    length_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    threading_1 = models.CharField(max_length=30, null=True, blank=True)
    threading_2 = models.CharField(max_length=30, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.length_mm:              specs.append(("Length", f"{self.length_mm}", "mm"))
        if self.threading_1:            specs.append(("Threading 1", self.threading_1, ""))
        if self.threading_2:            specs.append(("Threading 2", self.threading_2, ""))
        if self.axle:                   specs.append(("Axle", self.get_axle_display(), ""))
        return specs


class CylinderBase(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    threading = models.CharField(max_length=100, null=True, blank=True)
    material = models.CharField(max_length=1, choices=Material.choices, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.diameter_mm:               specs.append(("Diameter", f"{self.diameter_mm}", "mm"))
        if self.threading:                 specs.append(("Threading", self.threading, ""))
        if self.material:                  specs.append(("Threading 2", self.get_material_display(), ""))
        if self.braking_system:            specs.append(("Braking System", self.braking_system, ""))
        if self.axle:                      specs.append(("Axle", self.get_axle_display(), ""))
        return specs


class WheelCylinder(CylinderBase):
    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )


class MasterCylinder(CylinderBase):
    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    class Meta:
        constraints = [
            # if you truly want “rear only”
            models.CheckConstraint(
                name="master_cyl_rear_only",
                check=models.Q(axle="R") | models.Q(axle__isnull=True) | models.Q(axle=""),
            ),
        ]


class ClutchCylinder(CylinderBase):
    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )


class ClutchMasterCylinder(CylinderBase):
    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )


class Caliper(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    num_pistons = models.PositiveSmallIntegerField(null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    position = models.CharField(max_length=1, choices=CaliperPosition.choices, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    assembly_side = models.CharField(max_length=1, choices=AssemblySide.choices, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.diameter_mm:               specs.append(("Diameter", f"{self.diameter_mm}", "mm"))
        if self.num_pistons:               specs.append(("Number of Pistons", f"{self.num_pistons}", "mm"))
        if self.braking_system:            specs.append(("Braking System", self.braking_system, ""))
        if self.position:                  specs.append(("Position", self.get_position_display(), ""))
        if self.axle:                      specs.append(("Axle", self.get_axle_display(), ""))
        if self.assembly_side:             specs.append(("Assembly side", self.get_assembly_side_display(), ""))
        return specs



class ShoeKit(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    master_cylinder_diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_pre_assembled = models.BooleanField(default=False)
    braking_system = models.CharField(max_length=30, null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    is_manual_proportioning_valve = models.BooleanField(default=False)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.diameter_mm:                    specs.append(("Diameter", f"{self.diameter_mm}", "mm"))
        if self.width_mm:                       specs.append(("Width", f"{self.width_mm}", "mm"))
        if self.master_cylinder_diameter_mm:    specs.append(("Master Cylinder Diameter", f"{self.master_cylinder_diameter_mm}", "mm"))
        if self.is_pre_assembled:               specs.append(("Pre-assembled", self.is_pre_assembled, ""))
        if self.braking_system:                 specs.append(("Braking System", self.braking_system, ""))
        if self.axle:                           specs.append(("Axle", self.get_axle_display(), ""))
        if self.is_manual_proportioning_valve:  specs.append(("Brake Proportioning Valve", "Manual", ""))
        return specs



class Shoe(ProductBase):
    diameter_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    width_mm = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_parking_brake = models.BooleanField(default=False)
    has_handbrake_lever = models.BooleanField(default=False)
    has_accessories = models.BooleanField(default=False)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.diameter_mm:                    specs.append(("Diameter", f"{self.diameter_mm}", "mm"))
        if self.width_mm:                       specs.append(("Width", f"{self.width_mm}", "mm"))
        if self.is_parking_brake:               specs.append(("Type", "Parking brake", ""))
        if self.has_handbrake_lever:            specs.append(("Parking brake lever", "Handbrake Lever", ""))
        if self.has_accessories:                specs.append(("Accessories", "With Accessories", ""))
        if self.braking_system:                 specs.append(("Braking System", self.braking_system, ""))
        if self.axle:                           specs.append(("Axle", self.get_axle_display(), ""))
        return specs

class ProportioningValve(ProductBase):
    threading = models.CharField(max_length=30, null=True, blank=True)
    material = models.CharField(max_length=1, choices=Material.choices, null=True, blank=True)
    braking_system = models.CharField(max_length=30, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.material:              specs.append(("Material", self.get_material_display(), ""))
        if self.braking_system:        specs.append(("Braking System", self.braking_system, ""))
        return specs


class Kit(ProductBase):
    disc_per_box = models.PositiveSmallIntegerField(null=True, blank=True)
    pad_per_box = models.PositiveSmallIntegerField(null=True, blank=True)
    axle = models.CharField(max_length=1, choices=Axle.choices, null=True, blank=True)

    product_links = GenericRelation(
        'catalogue.ProductVehicle',
        content_type_field='product_ct',
        object_id_field='product_id',
        related_query_name='pad_links',
    )

    @property
    def card_specs(self) -> list[tuple[str, str, str]]:
        specs = []
        if self.disc_per_box:              specs.append(("Disc per box", f"{self.disc_per_box}", ""))
        if self.pad_per_box:                specs.append(("Pad per box", f"{self.pad_per_box}", ""))
        if self.axle:                      specs.append(("Axle", self.axle, ""))
        return specs


def product_ct_limit():
    product_models = [
        m for m in django_apps.get_models()
        if isinstance(m, type)
        and issubclass(m, ProductBase)
        and not m._meta.abstract
    ]
    # get_for_models returns a {model: ContentType} mapping
    cts = ContentType.objects.get_for_models(*product_models).values()
    return Q(pk__in=[ct.pk for ct in cts])


def vehicle_ct_limit():
    cts = ContentType.objects.get_for_models(Car, MotorBike, CommercialVehicle).values()
    return Q(pk__in=[ct.pk for ct in cts])


class ProductVehicle(models.Model):
    product_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="+",
                                   limit_choices_to=product_ct_limit)
    product_id = models.CharField(max_length=30)
    product = GenericForeignKey("product_ct", "product_id")

    vehicle_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name="+",
                                   limit_choices_to=vehicle_ct_limit)
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

        verbose_name_plural = "Product Vehicles"

    def __str__(self):
        return f"{self.product} <-> {self.vehicle}"
