from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Category, CartItem, MenuItem, Order, OrderItem


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "title"]


class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source="category", write_only=True)

    class Meta:
        model = MenuItem
        fields = ["id", "title", "description", "price", "available", "item_of_day", "category", "category_id"]


class CartItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)
    menu_item_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.filter(available=True), source="menu_item", write_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "menu_item", "menu_item_id", "quantity", "added_at", "subtotal"]
        read_only_fields = ["id", "added_at", "subtotal"]


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "quantity", "unit_price", "subtotal"]
        read_only_fields = ["id", "subtotal"]


class OrderSerializer(serializers.ModelSerializer):
    customer = UserSerializer(read_only=True)
    delivery_crew = UserSerializer(read_only=True)
    order_items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "customer", "delivery_crew", "status", "total", "created_at", "order_items"]
        read_only_fields = ["id", "customer", "delivery_crew", "total", "created_at", "order_items"]


class OrderCreateSerializer(serializers.Serializer):
    cart_item_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)

    def validate_cart_item_ids(self, value):
        if not value:
            raise serializers.ValidationError("Please provide at least one cart item ID.")
        return value
