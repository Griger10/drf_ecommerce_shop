from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from adrf.views import APIView as AsyncAPIView

from backend.apps.common.paginations import PageSizedPagination
from backend.apps.profiles.models import OrderItem, Order, ShippingAddress
from backend.apps.sellers.models import Seller
from backend.apps.shop.filters import ProductFilter
from backend.apps.shop.models import Category, Product, Review
from backend.apps.shop.schema_examples import PRODUCT_PARAM_EXAMPLE
from backend.apps.shop.serializers import (
    CategorySerializer,
    ProductSerializer,
    OrderItemSerializer,
    ToggleCartItemSerializer,
    OrderSerializer,
    CheckoutSerializer,
    ReviewSerializer,
)

tags = ["shop"]


class CategoriesView(APIView):
    serializer_class = CategorySerializer

    @extend_schema(
        summary="Categories Fetch",
        description="""
            This endpoint returns all categories.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        serializer = self.serializer_class(categories, many=True)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Category Creating",
        description="""
            This endpoint creates categories.
        """,
        tags=tags,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            new_cat = Category.objects.create(**serializer.validated_data)
            serializer = self.serializer_class(new_cat)
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)


class ProductsByCategoryView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        operation_id="category_products",
        summary="Category Products Fetch",
        description="""
            This endpoint returns all products in a particular category.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        category = Category.objects.get_or_none(slug=kwargs["slug"])
        if not category:
            return Response(
                data={"message": "Category does not exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(category=category)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class ProductsView(AsyncAPIView):
    serializer_class = ProductSerializer
    pagination_class = PageSizedPagination

    @extend_schema(
        operation_id="all_products",
        summary="Product Fetch",
        description="""
            This endpoint returns all products.
        """,
        tags=tags,
        parameters=PRODUCT_PARAM_EXAMPLE,
    )
    async def get(self, request, *args, **kwargs):
        queryset = (
            Product.objects.select_related("category", "seller", "seller__user")
            .order_by("id")
            .all()
        )

        filterset = ProductFilter(request.query_params, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        qs = filterset.qs

        paginator = self.pagination_class()
        page_size = paginator.get_page_size(request) or 10

        try:
            page_number = int(request.query_params.get(paginator.page_query_param, 1))
        except (ValueError, TypeError):
            page_number = 1

        total_count = await qs.acount()

        start = (page_number - 1) * page_size
        end = start + page_size

        if start >= total_count > 0:
            return Response(
                {"detail": "Invalid page."}, status=status.HTTP_404_NOT_FOUND
            )

        page_items = [p async for p in qs[start:end]]

        serializer = self.serializer_class(page_items, many=True)

        return Response(
            {
                "count": total_count,
                "next": self.get_next_link(
                    request, page_number, total_count, page_size
                ),
                "previous": self.get_previous_link(request, page_number),
                "results": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def get_next_link(self, request, page_number, total_count, page_size):
        if (page_number * page_size) >= total_count:
            return None
        url = request.build_absolute_uri()
        return replace_query_param(url, "page", page_number + 1)

    def get_previous_link(self, request, page_number):
        if page_number <= 1:
            return None
        url = request.build_absolute_uri()
        return replace_query_param(url, "page", page_number - 1)


class ProductsBySellerView(APIView):
    serializer_class = ProductSerializer

    @extend_schema(
        summary="Seller Products Fetch",
        description="""
            This endpoint returns all products in a particular seller.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        seller = Seller.objects.get_or_none(slug=kwargs["slug"])
        if not seller:
            return Response(
                data={"message": "Seller does not exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )
        products = Product.objects.select_related(
            "category", "seller", "seller__user"
        ).filter(seller=seller)
        serializer = self.serializer_class(products, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class ProductView(APIView):
    serializer_class = ProductSerializer

    def get_object(self, slug):
        product = Product.objects.get_or_none(slug=slug)
        return product

    @extend_schema(
        operation_id="product_detail",
        summary="Product Details Fetch",
        description="""
            This endpoint returns the details for a product via the slug.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        product = self.get_object(kwargs["slug"])
        if not product:
            return Response(
                data={"message": "Product does not exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = self.serializer_class(product)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class CartView(APIView):
    serializer_class = OrderItemSerializer

    @extend_schema(
        summary="Cart Items Fetch",
        description="""
            This endpoint returns all items in a user cart.
        """,
        tags=tags,
    )
    def get(self, request, *args, **kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None).select_related(
            "product", "product__seller", "product__seller__user"
        )
        serializer = self.serializer_class(orderitems, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Toggle Item in cart",
        description="""
            This endpoint allows a user or guest to add/update/remove an item in cart.
            If quantity is 0, the item is removed from cart
        """,
        tags=tags,
        request=ToggleCartItemSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = ToggleCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        quantity = data["quantity"]

        product = Product.objects.select_related("seller", "seller__user").get_or_none(
            slug=data["slug"]
        )
        if not product:
            return Response({"message": "No Product with that slug"}, status=404)
        orderitem, created = OrderItem.objects.update_or_create(
            user=user,
            order=None,
            product=product,
            defaults={"quantity": quantity},
        )
        resp_message_substring = "Updated In"
        status_code = status.HTTP_200_OK
        if created:
            status_code = status.HTTP_201_CREATED
            resp_message_substring = "Added To"
        if orderitem.quantity == 0:
            resp_message_substring = "Removed From"
            orderitem.delete()
            data = None
        if resp_message_substring != "Removed From":
            serializer = self.serializer_class(orderitem)
            data = serializer.data
        return Response(
            data={"message": f"Item {resp_message_substring} Cart", "item": data},
            status=status_code,
        )


class CheckoutView(APIView):
    serializer_class = CheckoutSerializer

    @extend_schema(
        summary="Checkout",
        description="""
               This endpoint allows a user to create an order through which payment can then be made through.
               """,
        tags=tags,
        request=CheckoutSerializer,
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        orderitems = OrderItem.objects.filter(user=user, order=None)
        if not orderitems.exists():
            return Response(
                {"message": "No Items in Cart"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        shipping_id = data.get("shipping_id")
        shipping = ShippingAddress.objects.get_or_none(id=shipping_id)
        if not shipping:
            return Response(
                {"message": "No shipping address with that ID"},
                status=status.HTTP_404_NOT_FOUND,
            )

        fields_to_update = [
            "full_name",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "zipcode",
        ]
        data = {}
        for field in fields_to_update:
            value = getattr(shipping, field)
            data[field] = value

        order = Order.objects.create(user=user, **data)
        orderitems.update(order=order)

        serializer = OrderSerializer(order)
        return Response(
            data={"message": "Checkout Successful", "item": serializer.data},
            status=status.HTTP_200_OK,
        )


class ReviewsViewSet(ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    queryset = Review.objects.all()
