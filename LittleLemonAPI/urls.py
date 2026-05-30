from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CartItemViewSet,
    CategoryViewSet,
    MenuItemViewSet,
    OrderViewSet,
    assign_delivery_crew,
    assign_manager,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"menu-items", MenuItemViewSet, basename="menuitem")
router.register(r"cart", CartItemViewSet, basename="cartitem")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("manager/assign-user/", assign_manager, name="assign-manager"),
    path("manager/assign-delivery/", assign_delivery_crew, name="assign-delivery-crew"),
]
