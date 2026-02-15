# catalogue/models.py
from __future__ import annotations
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from smart_selects.db_fields import ChainedForeignKey

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

class CategoryAttribute(TimeStampedModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="category_attributes")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="category_attributes")
    required = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("category", "attribute")
        ordering = ["sort_order", "attribute__name"]

    def __str__(self) -> str:
        req = " (required)" if self.required else ""
        return f"{self.category.name} → {self.attribute.name}{req}"



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

    def clean(self):
        input_type = self.attribute.input_type

        if input_type == Attribute.InputType.INTEGER:
            try:
                int(self.value)
            except ValueError:
                raise ValidationError(f"Value '{self.value}' is not a valid integer.")

        elif input_type == Attribute.InputType.DECIMAL:
            try:
                Decimal(self.value)
            except Exception:
                raise ValidationError(f"Value '{self.value}' is not a valid decimal.")

        elif input_type == Attribute.InputType.BOOLEAN:
            valid_booleans = {'true', 'false', '1', '0', 'yes', 'no'}
            if self.value.lower() not in valid_booleans:
                raise ValidationError(
                    f"Value '{self.value}' is not a valid boolean. "
                    f"Use: true, false, 1, 0, yes, or no."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.attribute.name}: {self.value}"


class ProductVehicleCompatibility(TimeStampedModel):
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='vehicle_compatibilities'
    )

    vehicle_type = models.ForeignKey(
        'vehicles.Types',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='product_compatibilities',
        help_text="For cars/CVs"
    )

    displacement_year = models.ForeignKey(
        'vehicles.DisplacementYear',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='product_compatibilities',
        help_text="For bikes"
    )

    notes = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['vehicle_type']),
            models.Index(fields=['displacement_year']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                        models.Q(vehicle_type__isnull=False, displacement_year__isnull=True) |
                        models.Q(vehicle_type__isnull=True, displacement_year__isnull=False)
                ),
                name='exactly_one_vehicle_reference'
            ),

            models.UniqueConstraint(
                fields=['product', 'vehicle_type'],
                name='unique_product_type',
                condition=models.Q(vehicle_type__isnull=False)
            ),

            models.UniqueConstraint(
                fields=['product', 'displacement_year'],
                name='unique_product_displacement',
                condition=models.Q(displacement_year__isnull=False)
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        # Ensure exactly one vehicle reference
        has_type = self.vehicle_type is not None
        has_dy = self.displacement_year is not None

        if not has_type and not has_dy:
            raise ValidationError("Must specify either vehicle_type or displacement_year")

        if has_type and has_dy:
            raise ValidationError("Cannot specify both vehicle_type and displacement_year")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def vehicle(self):
        """Returns the actual vehicle object regardless of type"""
        return self.vehicle_type or self.displacement_year

    def __str__(self):
        vehicle = self.vehicle_type or self.displacement_year
        return f"{self.product.sku} → {vehicle}"



class Product(TimeStampedModel):
    # compatability type CAR, CV or BIKE
    # Identity
    sync_id = models.CharField(unique=True, null=True, blank=True, max_length=255)
    name = models.CharField(max_length=190)
    slug = models.SlugField(max_length=190, unique=True, db_index=True)
    sku = models.CharField(max_length=64, unique=True, db_index=True)

    # Associations
    brand = models.ForeignKey(
        Brand, null=True, blank=True, on_delete=models.SET_NULL, related_name="products"
    )

    # Merchandising & content
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)  # can be sold
    visible = models.BooleanField(default=True)  # shown on site / search
    is_featured = models.BooleanField(default=False) # front page section featured

    # Identifiers useful for auto parts
    ean = models.CharField(max_length=14, blank=True, default="", db_index=True)
    mpn = models.CharField(max_length=64, blank=True, default="", db_index=True)

    # Pricing
    price = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    price_compare_at = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # pokazano od kolku e namalena cena (pogolema od price)
    promo_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    promo_starts_at = models.DateTimeField(null=True, blank=True)
    promo_ends_at = models.DateTimeField(null=True, blank=True)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    # Inventory snapshot
    stock_qty = models.IntegerField(default=0)
    reserved_qty = models.PositiveIntegerField(default=0)

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

    @property
    def available_stock(self):
        return max(0, self.stock_qty - self.reserved_qty)

    def get_missing_required_attributes(self, category=None):
        if not self.pk:
            existing_attr_ids = set()
        else:
            existing_attr_ids = set(
                self.product_attributes.values_list('attribute_id', flat=True)
            )

        if category:
            required_attrs = Attribute.objects.filter(
                category_attributes__category=category,
                category_attributes__required=True
            )
        else:
            if not self.pk:
                return []
            category_ids = self.categories.values_list('id', flat=True)
            required_attrs = Attribute.objects.filter(
                category_attributes__category_id__in=category_ids,
                category_attributes__required=True
            ).distinct()

        # Return attributes that are required but not present
        return list(required_attrs.exclude(id__in=existing_attr_ids))


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    name = models.CharField(max_length=190)
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

    def clean(self):
        if not self.pk:
            return

        missing_attrs = self.product.get_missing_required_attributes(category=self.category)
        if missing_attrs:
            attr_names = ", ".join(attr.name for attr in missing_attrs)
            raise ValidationError(
                f"Product is missing required attributes for category "
                f"'{self.category.name}': {attr_names}"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.product.sku} → {self.category.slug}"


class ProductAttribute(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="product_attributes")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name="product_attributes")

    attribute_value = ChainedForeignKey(
        AttributeValue,
        chained_field="attribute",
        chained_model_field="attribute",
        show_all=False,
        auto_choose=True,
        sort=True,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="product_attributes"
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

        # Validate value_text matches the expected input_type
        value_to_check = self.attribute_value.value if self.attribute_value else self.value_text
        if value_to_check:
            input_type = self.attribute.input_type

            if input_type == Attribute.InputType.INTEGER:
                try:
                    int(value_to_check)
                except ValueError:
                    raise ValidationError(f"Value '{value_to_check}' is not a valid integer.")

            elif input_type == Attribute.InputType.DECIMAL:
                try:
                    Decimal(value_to_check)
                except Exception:
                    raise ValidationError(f"Value '{value_to_check}' is not a valid decimal.")

            elif input_type == Attribute.InputType.BOOLEAN:
                valid_booleans = {'true', 'false', '1', '0', 'yes', 'no'}
                if value_to_check.lower() not in valid_booleans:
                    raise ValidationError(
                        f"Value '{value_to_check}' is not a valid boolean. "
                        f"Use: true, false, 1, 0, yes, or no."
                    )

    def save(self, *args, **kwargs):
        if self.attribute_value:
            self.value_text = self.attribute_value.value

        self.full_clean()

        super().save(*args, **kwargs)

    def __str__(self) -> str:
        v = self.attribute_value.value if self.attribute_value else self.value_text
        return f"{self.product.sku} · {self.attribute.name} = {v}"