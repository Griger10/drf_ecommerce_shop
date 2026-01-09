from django.urls import path

from backend.apps.sellers.views import (
    SellersView,
    SellerProductsView,
    SellerProductView,
)

urlpatterns = [
    path("", SellersView.as_view()),
    path("products/", SellerProductsView.as_view()),
    path("products/<slug:slug>/", SellerProductView.as_view()),
]
