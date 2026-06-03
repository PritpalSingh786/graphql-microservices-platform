import graphene
import uuid
import re
from datetime import datetime
from django.contrib.auth import get_user_model
from django.conf import settings
from graphql import GraphQLError
from users.models import Device
from users.utils import (
    create_access_token,
    create_refresh_token,
    delete_email_token,
    store_refresh_token,
    decode_token,
    verify_email_token,
    generate_verification_token,
    generate_password_reset_token,
    verify_password_reset_token,
    delete_password_reset_token,
    secure_generate_password_reset_token,
    secure_verify_password_reset_token,
    delete_secure_password_reset_token,
    change_user_password,
    generate_password_reset_token as gen_pwd_token
)
from users.tasks import (
    send_email_task,
    send_new_login_alert_task,
    send_password_changed_email_task,
    logout_all_devices_task,
    send_forgot_password_email_task
)
from .types import UserType

User = get_user_model()
redis_client = settings.REDIS_CLIENT


class RegisterMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    user_id = graphene.String()
    email = graphene.String()

    def mutate(self, info, user_id, email, password):
        # Validate user_id
        if len(user_id) < 4:
            raise GraphQLError("userId must be at least 4 characters long")
        
        if not re.match(r"^[a-zA-Z0-9_]+$", user_id):
            raise GraphQLError("userId can contain only letters, numbers and underscore")
        
        if User.objects.filter(user_id__iexact=user_id).exists():
            raise GraphQLError("userId already exists")
        
        # Validate email
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            raise GraphQLError("Enter a valid email address")
        
        if User.objects.filter(email__iexact=email).exists():
            raise GraphQLError("Email already exists")
        
        try:
            user = User.objects.create_user(
                user_id=user_id,
                email=email,
                password=password,
                is_active=False,
                email_verified=False
            )
            
            # Send verification email
            token = generate_verification_token(user.user_id)
            verification_link = f"{settings.DOMAIN_URL}/verify-email?user_id={user.user_id}&token={token}"
            
            message = f"""
            Hello {user.user_id},

            Thank you for registering!

            Please verify your email address by clicking the link below:

            🔗 {verification_link}

            ⏰ This link will expire in 5 minutes.

            If you did not create this account, please ignore this email.

            Best regards,
            Your Team
            """
            
            send_email_task.delay(
                "Verify Your Email - 5 Minutes Expiry",
                message,
                [user.email]
            )
            
            return RegisterMutation(
                success=True,
                message="Registration successful. Please check your email for verification link (expires in 5 minutes).",
                user_id=user.user_id,
                email=user.email
            )
            
        except Exception as e:
            raise GraphQLError(f"Error creating user: {str(e)}")


class LoginMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.String(required=True)
        password = graphene.String(required=True)
        platform = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    access = graphene.String()
    refresh = graphene.String()
    user = graphene.Field(UserType)

    def mutate(self, info, user_id, password, platform):
        request = info.context
        
        # Authenticate user
        try:
            user = User.objects.get(user_id=user_id)
            if not user.check_password(password):
                raise User.DoesNotExist
        except User.DoesNotExist:
            raise GraphQLError("Invalid credentials")
        
        # Check email verification
        if not user.email_verified:
            # Resend verification email
            token = generate_verification_token(user.user_id)
            verification_link = f"{settings.DOMAIN_URL}/verify-email?user_id={user.user_id}&token={token}"
            
            message = f"""
            Hello {user.user_id},

            Please verify your email address by clicking the link below:

            🔗 {verification_link}

            ⏰ This link will expire in 5 minutes.
            """
            
            send_email_task.delay(
                "Verify Your Email",
                message,
                [user.email]
            )
            
            raise GraphQLError("Email not verified. A verification link has been sent to your email.")
        
        # Get device info
        device_name = request.headers.get("User-Agent", "Unknown")
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        # Create or update device
        device, created = Device.objects.get_or_create(
            user=user,
            device_name=device_name,
            defaults={
                "ip_address": ip_address,
                "device_id": uuid.uuid4()
            }
        )
        
        device.ip_address = ip_address
        device.save()
        device_id = str(device.device_id)
        
        # Send alert for new login
        reset_token = secure_generate_password_reset_token(user.id)
        send_new_login_alert_task.delay(
            user_email=user.email,
            id=user.id,
            userId=user.user_id,
            device_name=device_name,
            ip_address=ip_address,
            platform=platform,
            reset_token=reset_token
        )
        
        # Create tokens
        access_token = create_access_token(user, device_id, platform)
        refresh_token = create_refresh_token(user, device_id, platform)
        
        # Store refresh token
        store_refresh_token(
            refresh_token,
            user,
            device_id,
            platform,
            device_name=device_name,
            ip_address=ip_address
        )
        
        return LoginMutation(
            success=True,
            message="Login successful",
            access=access_token,
            refresh=refresh_token,
            user=user
        )


class RefreshTokenMutation(graphene.Mutation):
    class Arguments:
        refresh = graphene.String(required=True)
        platform = graphene.String(required=True)

    success = graphene.Boolean()
    access = graphene.String()
    refresh = graphene.String()

    def mutate(self, info, refresh, platform):
        payload = decode_token(refresh, "refresh")
        
        if not payload:
            raise GraphQLError("Invalid or expired refresh token")
        
        user_id = payload.get("user_id")
        jti = payload.get("jti")
        
        redis_key = f"hash-rt-for-user-{user_id}"
        token_data = redis_client.hget(redis_key, jti)
        
        if not token_data:
            raise GraphQLError("Session expired. Please login again.")
        
        import json
        token_info = json.loads(token_data)
        
        created_at = datetime.fromisoformat(token_info["created_at"])
        token_age = (datetime.utcnow() - created_at).days
        
        if token_age >= settings.REFRESH_TOKEN_LIFETIME:
            redis_client.hdel(redis_key, jti)
            raise GraphQLError("Session expired. Please login again.")
        
        # Remove old token and create new ones
        redis_client.hdel(redis_key, jti)
        
        user = User.objects.get(id=user_id)
        device_id = payload.get("device_id")
        
        access_token = create_access_token(user, device_id, platform)
        refresh_token = create_refresh_token(user, device_id, platform)
        
        store_refresh_token(refresh_token, user, device_id, platform)
        
        return RefreshTokenMutation(
            success=True,
            access=access_token,
            refresh=refresh_token
        )


class LogoutMutation(graphene.Mutation):
    class Arguments:
        refresh = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, refresh):
        payload = decode_token(refresh, "refresh")
        
        if not payload:
            raise GraphQLError("Invalid or expired refresh token")
        
        user_id = payload.get("user_id")
        jti = payload.get("jti")
        
        redis_key = f"hash-rt-for-user-{user_id}"
        
        if not redis_client.hexists(redis_key, jti):
            raise GraphQLError("Session already expired")
        
        redis_client.hdel(redis_key, jti)
        
        return LogoutMutation(
            success=True,
            message="Logout successful"
        )


class ForgotPasswordMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, user_id):
        try:
            print(user_id, "userIdddd")
            user = User.objects.get(user_id=user_id)
            print(user, "userrr")
        except User.DoesNotExist:
            raise GraphQLError("Invalid User ID.")
        
        token = generate_password_reset_token(user.id)
        reset_link = f"{settings.DOMAIN_URL}/password-change-template/{user.id}/{token}/"
        
        message = f"""
        Hello {user.user_id},

        We received a request to reset your password.

        Click the link below to reset it:

        🔗 {reset_link}

        This link will expire in 5 minutes.

        If you did not request a password reset,
        please ignore this email.

        Regards,
        Your Team
        """
        
        send_forgot_password_email_task.delay(
            "Reset Your Password",
            message,
            [user.email]
        )
        
        return ForgotPasswordMutation(
            success=True,
            message="Password reset link sent successfully."
        )


class PasswordChangeMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.String(required=True)
        token = graphene.String(required=True)
        new_password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, user_id, token, new_password, confirm_password):
        # Validate token
        if not verify_password_reset_token(user_id, token):
            raise GraphQLError("Invalid or expired link.")
        
        if new_password != confirm_password:
            raise GraphQLError("Passwords do not match.")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found.")
        
        user.set_password(new_password)
        user.save()
        
        delete_password_reset_token(user.id, token)
        
        return PasswordChangeMutation(
            success=True,
            message="Password changed successfully. Now you can login."
        )


class SecurePasswordChangeMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.String(required=True)
        token = graphene.String(required=True)
        current_password = graphene.String(required=True)
        new_password = graphene.String(required=True)
        confirm_password = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    redirect = graphene.String()

    def mutate(self, info, user_id, token, current_password, new_password, confirm_password):
        # Validate all fields
        if not all([user_id, token, current_password, new_password, confirm_password]):
            raise GraphQLError("All fields are required")
        
        # Validate passwords match
        if new_password != confirm_password:
            raise GraphQLError("New passwords do not match")
        
        # Verify token
        if not secure_verify_password_reset_token(user_id, token):
            raise GraphQLError("Invalid or expired link.")
        
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found")
        
        # Verify current password
        if not user.check_password(current_password):
            raise GraphQLError("Current password is incorrect")
        
        # Change password
        change_user_password(user, new_password)
        
        # Send email notification
        send_password_changed_email_task.delay(
            user_email=user.email,
            user_name=user.user_id
        )
        
        # Logout from all devices
        logout_all_devices_task.delay(user.id)
        
        # Delete token
        delete_secure_password_reset_token(user_id, token)
        
        return SecurePasswordChangeMutation(
            success=True,
            message="Password changed successfully! You have been logged out from all devices.",
            redirect="/login/"
        )


class VerifyEmailMutation(graphene.Mutation):
    class Arguments:
        user_id = graphene.String(required=True)
        token = graphene.String(required=True)

    success = graphene.Boolean()
    message = graphene.String()
    user_id = graphene.String()
    email = graphene.String()

    def mutate(self, info, user_id, token):
        # Validate parameters
        if not user_id or not token:
            raise GraphQLError("Invalid verification link. Missing required parameters.")
        
        # Get user
        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found. The verification link may be invalid.")
        
        # Verify token
        is_valid, message = verify_email_token(user.user_id, token)
        
        if not is_valid:
            raise GraphQLError(message)
        
        # Activate user
        user.email_verified = True
        user.is_active = True
        user.save()
        delete_email_token(user_id, token)
        
        return VerifyEmailMutation(
            success=True,
            message="Email verified successfully",
            user_id=user.user_id,
            email=user.email
        )


class Mutation(graphene.ObjectType):
    register = RegisterMutation.Field()
    login = LoginMutation.Field()
    refresh_token = RefreshTokenMutation.Field()
    logout = LogoutMutation.Field()
    forgot_password = ForgotPasswordMutation.Field()
    change_password = PasswordChangeMutation.Field()
    secure_change_password = SecurePasswordChangeMutation.Field()
    verify_email = VerifyEmailMutation.Field()