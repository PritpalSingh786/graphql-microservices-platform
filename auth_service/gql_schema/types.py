import graphene
from graphene_django import DjangoObjectType
from users.models import User, Device, OutstandingToken


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "email_verified", "date_joined")


class DeviceType(DjangoObjectType):
    class Meta:
        model = Device
        fields = ("id", "device_name", "device_id", "last_login", "ip_address")


class SessionType(DjangoObjectType):
    class Meta:
        model = OutstandingToken
        fields = ("device_id", "platform", "created_at", "last_accessed", "expires_at")


class TokenType(graphene.ObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()