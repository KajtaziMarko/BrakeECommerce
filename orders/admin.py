from django.contrib import admin
from .models import Cart, CartItem, StockReservation, Order, OrderItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'reservation', 'created_at')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'reservation_type', 'expires_at', 'is_expired')
    list_filter = ('reservation_type', 'expires_at')
    search_fields = ('product__sku', 'product__name')
    readonly_fields = ('created_at', 'updated_at')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    # readonly_fields = ('product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'total_price')
    fields = ('product', 'product_name', 'product_sku', 'quantity', 'unit_price', 'total_price')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'email', 'status', 'grand_total', 'item_count', 'payment_status', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__email', 'first_name', 'last_name', 'phone_number', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Info', {
            'fields': ('user', 'email', 'status', 'grand_total', 'item_count')
        }),
        ('Payment', {
            'fields': ('payment_status', 'payment_method', 'transaction_id')
        }),
        ('Shipping', {
            'fields': ('first_name', 'last_name', 'address', 'city', 'country', 'post_code', 'phone_number')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_sku', 'product_name', 'quantity', 'unit_price', 'total_price')
    search_fields = ('order__order_number', 'product_sku', 'product_name')
    readonly_fields = ('created_at', 'updated_at')