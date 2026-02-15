# catalogue/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q

from .models import (
    Brand, Category, Attribute, AttributeValue,
    Product, ProductImage, ProductCategory, ProductAttribute, ProductVehicleCompatibility, CategoryAttribute,
)

class TimeStampedReadonlyMixin:
    readonly_fields = ("created_at", "updated_at")


@admin.register(Brand)
class BrandAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = ("name", "oem", "is_active", "country", "site_link", "created_at")
    list_filter  = ("is_active", "oem", "country")
    search_fields = ("name", "slug", "country")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "description")}),
        ("Media & Meta", {"fields": ("logo", "website", "country", "oem")}),
        ("Status", {"fields": ("is_active",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

    def site_link(self, obj):
        if obj.website:
            return format_html('<a href="{}" target="_blank">Open</a>', obj.website)
        return "-"
    site_link.short_description = "Website"

class CategoryAttributeInline(admin.TabularInline):
    model = CategoryAttribute
    extra = 0
    fields = ("category", "attribute")
    list_filter = ("category", "attribute")
    # search_fields = ("category__name", "attribute__name")

@admin.register(Category)
class CategoryAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("parent",)
    ordering = ("name",)
    inlines = (CategoryAttributeInline,)
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "description", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )


class AttributeValueInline(admin.TabularInline):
    model = AttributeValue
    extra = 1
    fields = ("value", "slug", "sort_order", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("sort_order", "value")

@admin.register(Attribute)
class AttributeAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "input_type", "is_filterable", "is_required", "sort_order")
    list_filter  = ("input_type", "is_filterable", "is_required")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AttributeValueInline]
    ordering = ("sort_order", "name")
    fieldsets = (
        (None, {"fields": ("name", "slug", "input_type")}),
        ("Usage", {"fields": ("is_required", "is_filterable", "sort_order")}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )

@admin.register(AttributeValue)
class AttributeValueAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = ("attribute", "value", "slug", "sort_order")
    list_filter = ("attribute",)
    search_fields = ("value", "slug", "attribute__name")
    autocomplete_fields = ("attribute",)
    ordering = ("attribute__name", "sort_order", "value")
    prepopulated_fields = {"slug": ("value",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("thumb", "image", "alt_text", "is_primary", "sort_order", "created_at", "updated_at")
    readonly_fields = ("thumb", "created_at", "updated_at")
    ordering = ("sort_order", "-is_primary")

    def thumb(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:60px; border-radius:6px;" />', obj.image.url)
        return "—"
    thumb.short_description = "Preview"

class ProductCategoryInline(admin.TabularInline):
    model = ProductCategory
    extra = 0
    autocomplete_fields = ("category",)
    fields = ("category", "is_primary", "created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")

class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ("attribute",)
    fields = ("attribute", "attribute_value", "value_text")
    ordering = ("attribute__name",)


class InStockFilter(admin.SimpleListFilter):
    title = "Stock"
    parameter_name = "stock_status"

    def lookups(self, request, model_admin):
        return [("in", "In stock"), ("out", "Out of stock")]

    def queryset(self, request, queryset):
        val = self.value()
        if val == "in":
            return queryset.filter(stock_qty__gt=0)
        if val == "out":
            return queryset.filter(stock_qty__lte=0)
        return queryset

class PromoFilter(admin.SimpleListFilter):
    title = "Promo"
    parameter_name = "promo"

    def lookups(self, request, model_admin):
        return [("has", "Has promo price"), ("none", "No promo")]

    def queryset(self, request, queryset):
        if self.value() == "has":
            return queryset.exclude(promo_price__isnull=True)
        if self.value() == "none":
            return queryset.filter(promo_price__isnull=True)
        return queryset


class ProductVehicleCompatibilityInline(admin.TabularInline):
    model = ProductVehicleCompatibility
    extra = 1
    fields = ('vehicle_type', 'displacement_year', 'notes')
    autocomplete_fields = ('vehicle_type', 'displacement_year')

@admin.register(Product)
class ProductAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = (
        "sku", "mpn",  "ean", "brand", "price", "stock_qty",
        "is_active", "visible"
    )
    list_filter = (
        "is_active", "visible",
        InStockFilter, PromoFilter, "brand", "categories",
    )
    search_fields = ("sku", "mpn", "ean")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("brand",)
    inlines = [ProductImageInline, ProductCategoryInline, ProductAttributeInline, ProductVehicleCompatibilityInline]
    ordering = ("-created_at",)
    save_on_top = True

    fieldsets = (
        ("Identity", {"fields": ("name", "slug", "sku", "brand")}),
        ("Content", {"fields": ("description",)}),
        ("Merchandising", {"fields": ("is_active", "visible", "is_featured")}),
        ("Identifiers", {"fields": ("ean", "mpn", "sync_id")}),
        ("Pricing", {
            "fields": (
                "price", "price_compare_at",
                "promo_price", "promo_starts_at", "promo_ends_at", "vat_rate",
            )
        }),
        ("Inventory", {"fields": ("stock_qty",)}),
        ("Shipping", {"fields": ("weight_kg", "length_mm", "width_mm", "height_mm")}),
        ("SEO & Publishing", {"fields": ("published_at", "meta_title", "meta_description")}),
    )

    actions = ["mark_visible", "mark_hidden", "mark_active", "mark_inactive"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("brand")

    # Quick actions
    def mark_visible(self, request, queryset):
        updated = queryset.update(visible=True)
        self.message_user(request, f"Marked {updated} product(s) visible.")
    mark_visible.short_description = "Mark selected products as visible"

    def mark_hidden(self, request, queryset):
        updated = queryset.update(visible=False)
        self.message_user(request, f"Marked {updated} product(s) hidden.")
    mark_hidden.short_description = "Mark selected products as hidden"

    def mark_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Marked {updated} product(s) active.")
    mark_active.short_description = "Mark selected products as active"

    def mark_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Marked {updated} product(s) inactive.")
    mark_inactive.short_description = "Mark selected products as inactive"



@admin.register(ProductImage)
class ProductImageAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = ("product", "thumb", "is_primary", "sort_order", "created_at")
    list_filter  = ("is_primary",)
    search_fields = ("product__sku", "product__name")
    autocomplete_fields = ("product",)
    ordering = ("product__sku", "sort_order")

    readonly_fields = ("created_at", "updated_at", "thumb")

    def thumb(self, obj):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:80px; border-radius:8px;" />', obj.image.url)
        return "—"
    thumb.short_description = "Preview"


@admin.register(ProductCategory)
class ProductCategoryAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = ("product", "category", "is_primary", "created_at")
    list_filter = ("is_primary", "category")
    search_fields = ("product__sku", "product__name", "category__name", "category__slug")
    autocomplete_fields = ("product", "category")
    ordering = ("category__name", "product__sku")


@admin.register(ProductAttribute)
class ProductAttributeAdmin(TimeStampedReadonlyMixin, admin.ModelAdmin):
    list_display = ("product", "attribute", "display_value", "created_at")
    list_filter = ("attribute",)
    search_fields = ("product__sku", "product__name", "attribute__name", "value_text", "attribute_value__value")
    autocomplete_fields = ("product", "attribute")
    ordering = ("product__sku", "attribute__name")

    def display_value(self, obj):
        return obj.attribute_value.value if obj.attribute_value else obj.value_text
    display_value.short_description = "Value"

