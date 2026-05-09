import graphene
from users.models import User, Device, OutstandingToken
from users.utils import get_active_tokens
from .types import UserType, DeviceType, SessionType


class Query(graphene.ObjectType):
    hello = graphene.String()
    me = graphene.Field(UserType)
    my_devices = graphene.List(DeviceType)
    my_sessions = graphene.List(SessionType)
    user = graphene.Field(UserType, id=graphene.ID(required=True))
    
    def resolve_hello(self, info):
        return "Welcome to GraphQL Auth API with Pure JWT!"
    
    def resolve_me(self, info):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        if not user_id:
            return None
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    def resolve_my_devices(self, info):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        if not user_id:
            return []
        return Device.objects.filter(user_id=user_id)
    
    def resolve_my_sessions(self, info):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        if not user_id:
            return []
        try:
            user = User.objects.get(id=user_id)
            return get_active_tokens(user)
        except User.DoesNotExist:
            return []
    
    def resolve_user(self, info, id):
        try:
            return User.objects.get(id=id)
        except User.DoesNotExist:
            return None