import graphene
from .mutations import (
    RegisterMutation,
    LoginMutation,
    VerifyEmailMutation,
    RefreshTokenMutation,
    LogoutMutation,
    ForgotPasswordMutation,
    PasswordChangeMutation,
    SecurePasswordChangeMutation,
)
from .queries import Query as BaseQuery


class Mutation(graphene.ObjectType):
    register = RegisterMutation.Field()
    login = LoginMutation.Field()
    verify_email = VerifyEmailMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()
    forgot_password = ForgotPasswordMutation.Field()
    change_password = PasswordChangeMutation.Field()
    secure_change_password = SecurePasswordChangeMutation.Field()


class Query(BaseQuery):
    pass


# Create schema instance
schema = graphene.Schema(query=Query, mutation=Mutation)

# Also export Schema class for compatibility (optional)
Schema = schema  # This allows both 'schema' and 'Schema' imports