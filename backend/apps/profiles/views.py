from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from backend.apps.common.permissions import IsOwner
from backend.apps.common.utils import set_dict_attr
from backend.apps.profiles.models import ShippingAddress, Order, OrderItem
from backend.apps.profiles.serializers import ProfileSerializer
from backend.apps.profiles.serializers import ShippingAddressSerializer
from backend.apps.shop.serializers import CheckItemOrderSerializer, OrderSerializer

tags = ["profiles"]


class ProfileView(APIView):
    serializer_class = ProfileSerializer
    permission_classes = [IsOwner]

    @extend_schema(
        summary="Retrieve Profile",
        description="""
                This endpoint allows a user to retrieve his/her profile.
            """,
        tags=tags,
    )
    def get(self, request):
        user = request.user
        serializer = self.serializer_class(user)
        return Response(data=serializer.data, status=200)

    @extend_schema(
        summary="Update Profile",
        description="""
                    This endpoint allows a user to update his/her profile.
                """,
        tags=tags,
        request={"multipart/form-data": serializer_class},
    )
    def put(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = set_dict_attr(user, serializer.validated_data)
        user.save()
        serializer = self.serializer_class(user)
        return Response(data=serializer.data)

    @extend_schema(
        summary="Deactivate account",
        description="""
                This endpoint allows a user to deactivate his/her account.
            """,
        tags=tags,
    )
    def delete(self, request):
        user = request.user
        user.is_active = False
        user.save()
        return Response(data={"message": "User Account Deactivated"})


@extend_schema_view(
    list=extend_schema(
        summary="Shipping Addresses Fetch",
        description="Returns all shipping addresses associated with the authenticated user.",
        tags=tags,
    ),
    create=extend_schema(
        summary="Create Shipping Address",
        description="Create a new shipping address for the authenticated user.",
        tags=tags,
    ),
)
class ShippingAddressesViewSet(ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [IsOwner]

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrdersView(APIView):
    serializer_class = OrderSerializer

    @extend_schema(
        operation_id="orders_view",
        summary="Orders Fetch",
        description="""
            This endpoint returns all orders for a particular user.
        """,
        tags=tags,
    )
    def get(self, request):
        user = request.user
        orders = (
            Order.objects.filter(user=user)
            .select_related("user")
            .prefetch_related("orderitems", "orderitems__product")
            .order_by("-created_at")
        )
        serializer = self.serializer_class(orders, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class OrderItemsView(APIView):
    serializer_class = CheckItemOrderSerializer

    @extend_schema(
        operation_id="order_items_view",
        summary="Items Order Fetch",
        description="""
            This endpoint returns all items order for a particular user.
        """,
        tags=tags,
    )
    def get(self, request, **kwargs):
        order = Order.objects.get_or_none(tx_ref=kwargs["tx_ref"])
        if not order or order.user != request.user:
            return Response(
                data={"message": "Order does not exist!"},
                status=status.HTTP_404_NOT_FOUND,
            )
        order_items = OrderItem.objects.filter(order=order).select_related(
            "product", "product__seller", "product__seller__user"
        )
        serializer = self.serializer_class(order_items, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
