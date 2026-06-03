import graphene
from graphene_django import DjangoObjectType
from users.models import User


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "user_id", "email", "first_name", "last_name", 
                 "email_verified", "is_active", "date_joined", "last_login")
