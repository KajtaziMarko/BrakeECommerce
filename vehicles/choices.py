from django.db import models
from django.utils.translation import gettext_lazy as _

class VehicleCategory(models.TextChoices):
    CAR  = 'c', _('Car')
    CV   = 't', _('Commercial Vehicle')
    BIKE = 'b', _('Motorbike')

    @classmethod
    def parse(cls, value: str | None):
        """
        Accept 'c'/'t'/'b', or labels ('Car', 'Commercial Vehicle', 'Motor Bike'),
        or names ('CAR','CV','BIKE'). Return the canonical code or None.
        """
        if not value:
            return None
        if value in cls.values:
            return value
        for m in cls:
            if m.label.lower() == value.lower():
                return m.value
        name = value.upper()
        if name in cls.names:
            return cls[name].value
        return None
