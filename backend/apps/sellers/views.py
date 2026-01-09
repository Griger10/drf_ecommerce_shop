from django.utils.text import slugify
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.profiles.models import OrderItem, Order
from backend.apps.sellers.models import Seller
from backend.apps.sellers.serializers import SellerSerializer
from backend.apps.shop.models import Category, Product
from backend.apps.shop.serializers import (
    ProductSerializer,
    CreateProductSerializer,
    OrderSerializer,
    CheckItemOrderSerializer,
)

tags = ["sellers"]


class SellersView(APIView):
    serializer_class = SellerSerializer

    @extend_schema(
        summary="Apply to become a seller",
        description="""
            This endpoint allows a buyer to apply to become a seller.
        """,
        tags=tags,
    )
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, partial=False)
        if serializer.is_valid():
            data = serializer.validated_data
            seller, _ = Seller.objects.update_or_create(user=user, defaults=data)
            user.account_type = "SELLER"
            user.save()
            serializer = self.serializer_class(seller)
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SellerProductsView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="""
            This endpoint returns all products from a seller.
            Products can be filtered by name, sizes or colors.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(
                data={"message": "Access is denied"}, status=status.HTTP_403_FORBIDDEN
            )
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create a product",
        description="""
            This endpoint allows a seller to create a product.
        """,
        tags=tags,
        request=CreateProductSerializer,
        responses=ProductSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = CreateProductSerializer(data=request.data)
        seller = Seller.objects.get_or_none(user=request.user, is_approved=True)
        if not seller:
            return Response(
                data={"message": "Access is denied"}, status=status.HTTP_403_FORBIDDEN
            )
        if serializer.is_valid():
            data = serializer.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(
                    data={"message": "Category does not exist!"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            data["category"] = category
            data["seller"] = seller
            new_prod = Product.objects.create(**data)
            serializer = ProductSerializer(new_prod)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SellerProductView(APIView):
    serializer_class = CreateProductSerializer

    @extend_schema(
        summary="Update a product",
        description="Updates a product by slug",
        tags=tags,
    )
    def put(self, request, *args, **kwargs):
        product = Product.objects.get_or_none(slug=slugify(kwargs["slug"]))
        if not product:
            return Response(
                data={"message": "Product does not exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if product.seller != request.user.seller:
            return Response(
                data={"message": "Access is denied"}, status=status.HTTP_403_FORBIDDEN
            )

        new_product_data = self.serializer_class(instance=product, data=request.data)
        if new_product_data.is_valid():
            data = new_product_data.validated_data
            category_slug = data.pop("category_slug", None)
            category = Category.objects.get_or_none(slug=category_slug)
            if not category:
                return Response(
                    data={"message": "Category does not exist!"}, status=404
                )
            data["category"] = category
            new_price = data.get("price_current")
            if new_price is not None and new_price != product.price_current:
                product.price_old = product.price_current
            product.save()
            return Response(data=new_product_data.data, status=status.HTTP_200_OK)

        return Response(
            data=new_product_data.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        summary="Delete a product",
        description="Deletes a product by slug",
        tags=tags,
    )
    def delete(self, request, *args, **kwargs):
        product = Product.objects.get_or_none(slug=slugify(kwargs["slug"]))
        if not product:
            return Response(
                data={"message": "Product does not exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if product.seller != request.user.seller:
            return Response(
                data={"message": "Access is denied"}, status=status.HTTP_403_FORBIDDEN
            )

        product.delete()
        return Response(
            data={"message": "Product deleted"}, status=status.HTTP_204_NO_CONTENT
        )


class SellerOrdersView(APIView):
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id="seller_orders_view",
        summary="Seller Orders Fetch",
        description="""
            This endpoint returns all orders for a particular seller.
        """,
        tags=tags,
    )
    def get(self, request):
        seller = request.user.seller
        orders = (
            Order.objects.filter(orderitems__product__seller=seller)
            .distinct()
            .order_by("-created_at")
        )
        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class SellerOrderItemsView(APIView):
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id="seller_order_items_view",
        summary="Seller Items Order Fetch",
        description="""
            This endpoint returns all items order for a particular seller.
        """,
        tags=tags,
    )
    def get(self, request, **kwargs):
        seller = request.user.seller
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order:
            return Response(
                data={"message": "Order does not exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )
        order_items = OrderItem.objects.filter(order=order, product__seller=seller)
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
