from django.contrib import admin

from .models import CartItem, Category, MenuItem, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "title"]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "category", "price", "item_of_day", "available"]
    list_filter = ["category", "item_of_day", "available"]


class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "menu_item", "quantity", "added_at"]
    list_select_related = ["user", "menu_item"]


admin.site.register(CartItem, CartItemAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
