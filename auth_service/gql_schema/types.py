import graphene
from graphene_django import DjangoObjectType
from users.models import User, Device


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "email_verified", "date_joined")


class DeviceType(DjangoObjectType):
    class Meta:
        model = Device
        fields = ("id", "device_name", "device_id", "last_login", "ip_address")


class SessionType(graphene.ObjectType):
    device_id = graphene.String()
    platform = graphene.String()
    created_at = graphene.String()
    device_name = graphene.String()
    ip_address = graphene.String()


class TokenType(graphene.ObjectType):
    access_token = graphene.String()
    refresh_token = graphene.String()