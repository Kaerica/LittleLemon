from django.conf import settings
from django.db import models


class Category(models.Model):
    title = models.CharField(max_length=120, unique=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class MenuItem(models.Model):
    title = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    category = models.ForeignKey(Category, related_name="menu_items", on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    item_of_day = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="cart_items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, related_name="cart_items", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "menu_item")

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.title}"

    @property
    def subtotal(self):
        return self.quantity * self.menu_item.price


class Order(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_ASSIGNED = "ASSIGNED"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_ASSIGNED, "Assigned"),
        (STATUS_DELIVERED, "Delivered"),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="assigned_orders", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="order_items", on_delete=models.CASCADE)
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.menu_item.title}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
