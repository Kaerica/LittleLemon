from django.contrib.auth.models import Group, User
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import filters, mixins, permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response

from .models import CartItem, Category, MenuItem, Order, OrderItem
from .permissions import IsAdminOrManager, IsAdminOrReadOnly, IsDeliveryCrew, IsManager
from .serializers import (
    CartItemSerializer,
    CategorySerializer,
    MenuItemSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    UserSerializer,
)


class CategoryViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["price", "title"]
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset().filter(available=True)
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    @action(detail=True, methods=["post"], permission_classes=[IsManager])
    def set_item_of_day(self, request, pk=None):
        menu_item = self.get_object()
        with transaction.atomic():
            MenuItem.objects.filter(item_of_day=True).update(item_of_day=False)
            menu_item.item_of_day = True
            menu_item.save()
        serializer = self.get_serializer(menu_item)
        return Response(serializer.data)


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related("menu_item", "menu_item__category")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        menu_item = get_object_or_404(MenuItem, id=request.data.get("menu_item_id"), available=True)
        cart_item, created = CartItem.objects.get_or_create(user=request.user, menu_item=menu_item)
        quantity = int(request.data.get("quantity", 1))
        cart_item.quantity = quantity
        cart_item.save()
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class OrderViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.groups.filter(name="Delivery crew").exists():
            return Order.objects.filter(delivery_crew=user)
        if user.groups.filter(name="Manager").exists() or user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(customer=user)

    @action(detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def place(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart_item_ids = serializer.validated_data["cart_item_ids"]
        cart_items = CartItem.objects.filter(user=request.user, id__in=cart_item_ids).select_related("menu_item")
        if not cart_items:
            return Response({"detail": "No valid cart items found."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            order = Order.objects.create(customer=request.user)
            total = 0
            for cart_item in cart_items:
                item_total = cart_item.quantity * cart_item.menu_item.price
                OrderItem.objects.create(
                    order=order,
                    menu_item=cart_item.menu_item,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.menu_item.price,
                )
                total += item_total
            order.total = total
            order.save()
            cart_items.delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminOrManager])
    def assign_delivery(self, request, pk=None):
        order = self.get_object()
        crew_id = request.data.get("delivery_crew_id")
        if not crew_id:
            return Response({"detail": "delivery_crew_id is required."}, status=status.HTTP_400_BAD_REQUEST)
        crew = get_object_or_404(User, id=crew_id, groups__name="Delivery crew")
        order.delivery_crew = crew
        order.status = Order.STATUS_ASSIGNED
        order.save()
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["post"], permission_classes=[IsDeliveryCrew])
    def delivered(self, request, pk=None):
        order = self.get_object()
        if order.delivery_crew != request.user:
            return Response({"detail": "You are not assigned to this order."}, status=status.HTTP_403_FORBIDDEN)
        order.status = Order.STATUS_DELIVERED
        order.save()
        return Response(OrderSerializer(order).data)

    @action(detail=False, methods=["get"], url_path="my-orders")
    def my_orders(self, request):
        orders = Order.objects.filter(customer=request.user)
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAdminUser])
def assign_manager(request):
    user_id = request.data.get("user_id")
    if not user_id:
        return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(User, id=user_id)
    manager_group, _ = Group.objects.get_or_create(name="Manager")
    user.groups.add(manager_group)
    return Response({"detail": f"User {user.username} assigned to Manager group."})


@api_view(["POST"])
@permission_classes([IsManager])
def assign_delivery_crew(request):
    user_id = request.data.get("user_id")
    if not user_id:
        return Response({"detail": "user_id is required."}, status=status.HTTP_400_BAD_REQUEST)
    user = get_object_or_404(User, id=user_id)
    delivery_group, _ = Group.objects.get_or_create(name="Delivery crew")
    user.groups.add(delivery_group)
    return Response({"detail": f"User {user.username} assigned to Delivery crew group."})
