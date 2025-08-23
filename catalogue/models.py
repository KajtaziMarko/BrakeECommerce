from django.db import models


# Create your models here.
class Product(models.Model):
    code = models.CharField(max_length=30, unique=True)
    ean = models.CharField(max_length=13, unique=True, null=True, blank=True)
    price = models.DecimalField()
    available = models.BooleanField(default=False)


    class Meta:
        abstract = True
        unique_together = (('code', 'ean'),)