import graphene
from graphql import GraphQLError
from django.contrib.auth import get_user_model
from .types import UserType, DeviceType, AuthenticatedUserType

User = get_user_model()


class Query(graphene.ObjectType):
    # Authenticated queries
    me = graphene.Field(AuthenticatedUserType)
    my_devices = graphene.List(DeviceType)
    get_user = graphene.Field(
        UserType,
        user_id=graphene.String(required=True)
    )

    def resolve_me(self, info):
        user = info.context.user

        if not user or not user.is_authenticated:
            raise GraphQLError("Authentication required")

        device_id = getattr(info.context, "device_id", None)
        platform = getattr(info.context, "platform", None)

        return AuthenticatedUserType(
            success=True,
            message="Authenticated user",
            user=UserType(
                id=user.id,
                user_id=user.user_id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                email_verified=user.email_verified,
                is_active=user.is_active,
                date_joined=user.date_joined,
                last_login=user.last_login,
            ),
            device_id=device_id,
            platform=platform,
        )

    def resolve_my_devices(self, info):
        user = info.context.user

        if not user or not user.is_authenticated:
            raise GraphQLError("Authentication required")

        devices = user.devices.filter(is_active=True)

        return [
            DeviceType(
                id=device.id,
                device_name=device.device_name,
                device_id=str(device.device_id),
                last_login=device.last_login,
                ip_address=device.ip_address,
                user_agent=device.user_agent,
                is_active=device.is_active,
            )
            for device in devices
        ]

    def resolve_get_user(self, info, user_id):
        user = info.context.user

        if not user or not user.is_authenticated:
            raise GraphQLError("Authentication required")

        try:
            user_obj = User.objects.get(user_id=user_id)

            return UserType(
                id=user_obj.id,
                user_id=user_obj.user_id,
                email=user_obj.email,
                first_name=user_obj.first_name,
                last_name=user_obj.last_name,
                email_verified=user_obj.email_verified,
                is_active=user_obj.is_active,
                date_joined=user_obj.date_joined,
                last_login=user_obj.last_login,
            )

        except User.DoesNotExist:
            raise GraphQLError("User not found")