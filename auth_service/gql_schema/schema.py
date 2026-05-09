import graphene
from .mutations import (
    RegisterMutation,
    LoginMutation,
    VerifyEmailMutation,
    RefreshTokenMutation,
    LogoutMutation,
    PasswordResetRequestMutation,
    SetNewPasswordMutation,
    ChangePasswordMutation,
    RemoveDeviceMutation,
    RemoveOtherDevicesMutation
)
from .queries import Query as BaseQuery


class Mutation(graphene.ObjectType):
    register = RegisterMutation.Field()
    login = LoginMutation.Field()
    verify_email = VerifyEmailMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()
    password_reset_request = PasswordResetRequestMutation.Field()
    set_new_password = SetNewPasswordMutation.Field()
    change_password = ChangePasswordMutation.Field()
    remove_device = RemoveDeviceMutation.Field()
    remove_other_devices = RemoveOtherDevicesMutation.Field()


class Query(BaseQuery):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)