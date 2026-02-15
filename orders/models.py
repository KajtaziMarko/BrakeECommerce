import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Cart(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    session_key = models.CharField(max_length=40, null=True, blank=True,
                                   db_index=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) |
                      models.Q(session_key__isnull=False),
                name='cart_user_or_session'
            )
        ]

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.email}"
        return f"Cart (session: {self.session_key[:8]}...)"


class  StockReservation(TimeStampedModel):
    class ReservationType(models.TextChoices):
        CART = 'cart', 'In Cart'
        CHECKOUT = 'checkout', 'In Checkout'

    product = models.ForeignKey(
        'catalogue.Product',
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    quantity = models.PositiveIntegerField()
    reservation_type = models.CharField(max_length=10, choices=ReservationType.choices)
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'expires_at']),
        ]

    def __str__(self):
        return f"{self.quantity}x {self.product.sku} ({self.reservation_type})"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalogue.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    reservation = models.OneToOneField(
        StockReservation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        unique_together = [('cart', 'product')]

    def __str__(self):
        return f"{self.quantity}x {self.product.sku}"


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        DECLINE = 'decline', 'Declined'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='orders'
    )
    email = models.EmailField(db_index=True)
    order_number = models.CharField(max_length=32, unique=True, db_index=True)

    # Status & totals
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    grand_total = models.DecimalField(max_digits=20, decimal_places=6)
    item_count = models.PositiveIntegerField()

    # Payment
    payment_status = models.BooleanField(default=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, default="")  # For bank gateway reference

    # Shipping info
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    address = models.TextField()
    city = models.CharField(max_length=150)
    country = models.CharField(max_length=150)
    post_code = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20)

    # Notes
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(user__isnull=False) | models.Q(email__isnull=False),
                name='order_user_or_email'
            )
        ]

    def __str__(self):
        return f"Order {self.order_number}"

    @classmethod
    def generate_order_number(cls):
        """Generate unique order number: BRK-{timestamp}-{random}"""
        timestamp = int(timezone.now().timestamp())
        random_suffix = uuid.uuid4().hex[:4].upper()
        return f"BRK-{timestamp}-{random_suffix}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalogue.Product', on_delete=models.PROTECT)
    product_name = models.CharField(max_length=190)
    product_sku = models.CharField(max_length=64)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=20, decimal_places=6)
    total_price = models.DecimalField(max_digits=20, decimal_places=6)

    def __str__(self):
        return f"{self.quantity}x {self.product_sku}"
