from django.db import models
from django.utils.translation import gettext_lazy as _

class Axle(models.TextChoices):
    FRONT = "F", _("Front")
    REAR  = "R", _("Rear")
    BOTH  = "B", _("Front and rear")

class AssemblySide(models.TextChoices):
    NONE  = "N", _("None")
    LEFT  = "L", _("Left")
    RIGHT = "R", _("Right")
    BOTH  = "B", _("Left and right")

class DiscType(models.TextChoices):
    SOLID      = "S", _("Solid")
    VENTILATED = "V", _("Ventilated")

class Material(models.TextChoices):
    ALUMINIUM = "A", _("Aluminium")
    CAST_IRON = "C", _("Cast Iron")
    PLASTIC = "P", _("Plastic")
    STEEL = "S", _("Steel")

class CaliperPosition(models.TextChoices):
    LEFT = "L", _("Left")
    RIGHT = "R", _("Right")
    BOTH = "B", _("Left and Right")

class WearIndicator(models.TextChoices):
    WITHOUT = "W", _("Without")
    ACOUSTIC = "A", _("Acoustic")
    ELECTRIC = "E", _("Electric")
    PREPARED = "P", _("Prepared for wear indicator")

class PadAccessoryType(models.TextChoices):
    WEAR_INDICATOR = "W", _("Wear Indicator")
    ASSEMBLY_KIT = "A", _("Assembly Kit")