import graphene
from graphene_django import DjangoObjectType
from users.models import User, Device


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "user_id", "email", "first_name", "last_name", 
                 "email_verified", "is_active", "date_joined", "last_login")


class DeviceType(DjangoObjectType):
    class Meta:
        model = Device
        fields = ("id", "device_name", "device_id", "last_login", 
                 "ip_address", "user_agent", "is_active")


class LoginResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    access = graphene.String()
    refresh = graphene.String()
    user = graphene.Field(UserType)


class TokenResultType(graphene.ObjectType):
    success = graphene.Boolean()
    access = graphene.String()
    refresh = graphene.String()


class LogoutResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()


class PasswordChangeResultType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    redirect = graphene.String()


class AuthenticatedUserType(graphene.ObjectType):
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)
    device_id = graphene.String()
    platform = graphene.String()