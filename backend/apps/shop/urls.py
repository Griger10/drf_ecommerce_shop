from django.urls import path

from backend.apps.shop.views import (
    CategoriesView,
    ProductsByCategoryView,
    ProductsBySellerView,
    ProductsView,
    ProductView,
    CartView,
    CheckoutView,
)

urlpatterns = [
    path("categories/", CategoriesView.as_view()),
    path("categories/<slug:slug>/", ProductsByCategoryView.as_view()),
    path("sellers/<slug:slug>/", ProductsBySellerView.as_view()),
    path("products/", ProductsView.as_view()),
    path("products/<slug:slug>/", ProductView.as_view()),
    path("cart/", CartView.as_view()),
    path("checkout/", CheckoutView.as_view()),
]
