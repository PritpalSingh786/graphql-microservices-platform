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
        # Get from middleware
        user_id = getattr(info.context, 'user_id', None)
        
        if not user_id:
            raise GraphQLError("Authentication required - No user_id in context")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found")
        
        device_id = getattr(info.context, "device_id", None)
        platform = getattr(info.context, "platform", None)
        
        return AuthenticatedUserType(
            success=True,
            message="Authenticated user",
            user=user,
            device_id=device_id,
            platform=platform,
        )

    def resolve_my_devices(self, info):
        # Get from middleware (same pattern as resolve_me)
        user_id = getattr(info.context, 'user_id', None)
        
        if not user_id:
            raise GraphQLError("Authentication required - No user_id in context")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found")
        
        devices = user.devices.filter(is_active=True)

        return devices

    def resolve_get_user(self, info, user_id):
        # Get current user from middleware
        current_user_id = getattr(info.context, 'user_id', None)
        
        if not current_user_id:
            raise GraphQLError("Authentication required - No user_id in context")
        
        # Optional: Check if current user has permission to view other user
        # For now, allow any authenticated user to view any user
        try:
            user_obj = User.objects.get(id=current_user_id)
            
            return user_obj
        except User.DoesNotExist:
            raise GraphQLError("User not found")