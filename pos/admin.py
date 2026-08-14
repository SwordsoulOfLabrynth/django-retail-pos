from django.contrib import admin

from .models import Category, Product, Sale, SaleItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "sku", "category", "selling_price", "stock_quantity", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "sku")


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ("product_name", "product_sku", "quantity", "unit_price", "line_total")
    can_delete = False


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("sale_number", "cashier", "payment_method", "total", "created_at")
    list_filter = ("payment_method", "created_at")
    search_fields = ("sale_number", "cashier__username")
    readonly_fields = ("sale_number", "cashier", "payment_method", "total", "cash_received", "change", "created_at")
    inlines = [SaleItemInline]

    def has_add_permission(self, request):
        return False
