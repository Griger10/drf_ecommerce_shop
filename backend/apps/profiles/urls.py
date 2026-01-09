from django.urls import path, include
from rest_framework.routers import DefaultRouter

from backend.apps.profiles.views import (
    ProfileView,
    ShippingAddressesViewSet,
    OrdersView,
    OrderItemsView,
)

router = DefaultRouter()
router.register(
    "shipping-addresses", ShippingAddressesViewSet, basename="shipping-addresses"
)

urlpatterns = [
    path("", ProfileView.as_view()),
    path("shipping_addresses/", include(router.urls)),
    path("orders/", OrdersView.as_view()),
    path("orders/<str:tx_ref>/", OrderItemsView.as_view()),
]
