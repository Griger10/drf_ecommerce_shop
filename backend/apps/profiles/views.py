from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from backend.apps.common.utils import set_dict_attr
from backend.apps.profiles.models import ShippingAddress
from backend.apps.profiles.serializers import ProfileSerializer
from backend.apps.profiles.serializers import ShippingAddressSerializer

profile_tags = ["profiles"]
shipping_address_tags = ["shipping_addresses"]


class ProfileView(APIView):
    serializer_class = ProfileSerializer

    @extend_schema(
        summary="Retrieve Profile",
        description="""
                This endpoint allows a user to retrieve his/her profile.
            """,
        tags=profile_tags,
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
        tags=profile_tags,
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
        tags=profile_tags,
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
        tags=shipping_address_tags,
    ),
    create=extend_schema(
        summary="Create Shipping Address",
        description="Create a new shipping address for the authenticated user.",
        tags=shipping_address_tags,
    ),
    put=extend_schema(
        summary="Update Shipping Address",
        description="Update a shipping address for the authenticated user.",
        tags=shipping_address_tags,
    ),
    patch=extend_schema(
        summary="Patch Shipping Address",
        description="Patch a shipping address for the authenticated user.",
        tags=shipping_address_tags,
    ),
    delete=extend_schema(
        summary="Delete Shipping Address",
        description="Delete a shipping address for the authenticated user.",
        tags=shipping_address_tags,
    ),
)
class ShippingAddressesViewSet(ModelViewSet):
    serializer_class = ShippingAddressSerializer

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
