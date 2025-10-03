# catalogue/models.py
from __future__ import annotations
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Brand(TimeStampedModel):
    name = models.CharField(max_length=190, unique=True)
    slug = models.SlugField(max_length=190, unique=True)
    description = models.TextField(blank=True, default="")
    website = models.URLField(blank=True, default="")
    logo = models.ImageField(upload_to="brand-logos/", blank=True, null=True)

    country = models.CharField(max_length=80, blank=True, default="")
    oem = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Category(TimeStampedModel):
    name = models.CharField(max_length=190)
    slug = models.SlugField(max_length=190, unique=True, db_index=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE
    )
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["parent", "is_active"]),
        ]

    def __str__(self) -> str:
        return self.name


class Attribute(TimeStampedModel):
    class InputType(models.TextChoices):
        TEXT = "text", "Text"
        INTEGER = "int", "Integer"
        DECIMAL = "dec", "Decimal"
        BOOLEAN = "bool", "Boolean"
        SELECT = "select", "Select (single)"
        MULTISELECT = "multiselect", "Select (multiple)"

    name = models.CharField(max_length=190)
    slug = models.SlugField(max_length=190, unique=True, db_index=True)
    input_type = models.CharField(max_length=20, choices=InputType.choices, default=InputType.TEXT)
    is_required = models.BooleanField(default=False)
    is_filterable = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["is_filterable", "sort_order"]),
        ]

    def __str__(self) -> str:
        return self.name


class AttributeValue(TimeStampedModel):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="values")
    value = models.CharField(max_length=190)
    slug = models.SlugField(max_length=190, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["attribute_id", "sort_order", "value"]
        unique_together = [("attribute", "value")]
        indexes = [
            models.Index(fields=["attribute", "sort_order"]),
        ]

    def __str__(self) -> str:
        return f"{self.attribute.name}: {self.value}"


class Product(TimeStampedModel):
    # Identity
    name = models.CharField(max_length=190)
    slug = models.SlugField(max_length=190, unique=True, db_index=True)
    sku = models.CharField(max_length=64, unique=True, db_index=True)

    # Associations
    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )

    # Merchandising & content
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)       # can be sold
    visible = models.BooleanField(default=True)         # shown on site / search
    is_featured = models.BooleanField(default=False)

    # Identifiers useful for auto parts
    ean = models.CharField(max_length=14, blank=True, default="", db_index=True)
    mpn = models.CharField(max_length=64, blank=True, default="", db_index=True)

    # Pricing
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    price_compare_at = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    promo_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    promo_starts_at = models.DateTimeField(null=True, blank=True)
    promo_ends_at = models.DateTimeField(null=True, blank=True)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Inventory snapshot (consider StockMovement for audits)
    stock_qty = models.IntegerField(default=0)

    # Shipping/physicals
    weight_kg = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    length_mm = models.PositiveIntegerField(null=True, blank=True)
    width_mm = models.PositiveIntegerField(null=True, blank=True)
    height_mm = models.PositiveIntegerField(null=True, blank=True)

    # SEO / publishing
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)
    meta_title = models.CharField(max_length=190, blank=True, default="")
    meta_description = models.CharField(max_length=255, blank=True, default="")

    # Taxonomy
    categories = models.ManyToManyField(
        Category, through="ProductCategory", related_name="products", blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "visible"]),
            models.Index(fields=["name"]),
            models.Index(fields=["brand", "is_active"]),
            models.Index(fields=["published_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku} · {self.name}"

    @property
    def is_on_promo(self) -> bool:
        if self.promo_price is None:
            return False
        if self.promo_starts_at and self.promo_starts_at > self.updated_at:
            pass
        return True


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="product-images/")
    alt_text = models.CharField(max_length=190, blank=True, default="")
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["product_id", "sort_order", "-is_primary"]
        unique_together = [("product", "sort_order")]
        indexes = [
            models.Index(fields=["product", "is_primary"]),
        ]

    def __str__(self) -> str:
        return f"Image for {self.product.sku} ({'primary' if self.is_primary else 'secondary'})"


class ProductCategory(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = [("product", "category")]
        indexes = [
            models.Index(fields=["category", "product"]),
            models.Index(fields=["is_primary"]),
        ]

    def __str__(self) -> str:
        return f"{self.product.sku} → {self.category.slug}"


class ProductAttribute(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_attributes")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="product_attributes")

    attribute_value = models.ForeignKey(
        AttributeValue, null=True, blank=True, on_delete=models.CASCADE, related_name="product_attributes"
    )
    value_text = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = [("product", "attribute")]
        indexes = [
            models.Index(fields=["product", "attribute"]),
            models.Index(fields=["attribute_value"]),
        ]

    def clean(self):
        if not self.attribute_value and not self.value_text:
            raise ValidationError("Provide either attribute_value or value_text.")

        if self.attribute.input_type in {Attribute.InputType.SELECT, Attribute.InputType.MULTISELECT}:
            if not self.attribute_value:
                raise ValidationError("SELECT attributes must use attribute_value (FK).")
            if self.attribute_value.attribute_id != self.attribute_id:
                raise ValidationError("attribute_value must belong to the same attribute.")
        else:
            if self.attribute_value and self.attribute_value.attribute_id != self.attribute_id:
                raise ValidationError("attribute_value must belong to the same attribute.")

    def __str__(self) -> str:
        v = self.attribute_value.value if self.attribute_value else self.value_text
        return f"{self.product.sku} · {self.attribute.name} = {v}"
