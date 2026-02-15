import os
from django.conf import settings
from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import StockReservation, Order


@receiver(post_save, sender=StockReservation)
def reservation_created(sender, instance, created, **kwargs):
    if created:
        instance.product.reserved_qty = F('reserved_qty') + instance.quantity
        instance.product.save(update_fields=['reserved_qty'])


@receiver(post_delete, sender=StockReservation)
def reservation_deleted(sender, instance, **kwargs):
    instance.product.reserved_qty = F('reserved_qty') - instance.quantity
    instance.product.save(update_fields=['reserved_qty'])


@receiver(post_save, sender=Order)
def save_order_to_file(sender, instance, created, **kwargs):
    filename = f"order_{instance.order_number}.txt"
    filepath = os.path.join("/Volumes/SHARE za Marko", filename)

    # Write order data
    with open(filepath, 'w') as f:
        f.write(f"Order Number: {instance.order_number}\n")
        f.write(f"Status: {instance.status}\n")
        f.write(f"Created: {instance.created_at}\n")
        f.write(f"Grand Total: {instance.grand_total}\n")
        f.write(f"\nShipping Info:\n")
        f.write(f"  {instance.first_name} {instance.last_name}\n")
        f.write(f"  {instance.address}\n")
        f.write(f"  {instance.city}, {instance.post_code}\n")
        f.write(f"  {instance.country}\n")
        f.write(f"  Phone: {instance.phone_number}\n")

        f.write(f"\nItems:\n")
        for item in instance.items.all():
            f.write(f"  - {item.quantity}x {item.product_name} ({item.product_sku}) @ {item.unit_price}\n")
