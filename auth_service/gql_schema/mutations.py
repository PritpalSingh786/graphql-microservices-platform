import graphene
import datetime
import re
import uuid
import time
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from graphql import GraphQLError
from .types import UserType, DeviceType, SessionType
from users.tasks import send_email_task
from users.models import Device
from users.utils import (
    create_access_token, create_refresh_token, verify_token,
    store_refresh_token, limit_user_sessions, blacklist_token_by_value,
    get_active_tokens, refresh_both_tokens
)
from users.redis_token_manager import redis_token_manager

User = get_user_model()
token_generator = PasswordResetTokenGenerator()


def rate_limit(ip, limit=5, window=60, key_prefix="login"):
    key = f"rate_limit_{key_prefix}_{ip}"
    requests = cache.get(key, [])
    now = time.time()
    requests = [t for t in requests if now - t < window]
    
    if len(requests) >= limit:
        raise GraphQLError(f"Rate limit exceeded. Too many {key_prefix} attempts. Try after {window} seconds.")
    
    requests.append(now)
    cache.set(key, requests, window)
    return True


class RegisterMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, username, email, password):
        ip = info.context.META.get('REMOTE_ADDR', '0.0.0.0')
        rate_limit(ip, limit=3, window=60, key_prefix="register")
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return RegisterMutation(
                success=False,
                message="Invalid email format. Example: user@domain.com"
            )
        if len(username) < 4:
            return RegisterMutation(success=False, message="Username must be at least 4 characters")
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return RegisterMutation(success=False, message="Username can contain only letters, numbers and underscore")
        
        if User.objects.filter(username__iexact=username).exists():
            return RegisterMutation(success=False, message="Username already exists")
        
        if User.objects.filter(email__iexact=email).exists():
            return RegisterMutation(success=False, message="Email already exists")
        
        if len(password) < 6:
            return RegisterMutation(success=False, message="Password must be at least 6 characters")
        
        user = User.objects.create_user(username=username, email=email, password=password)
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
        message = f"Verify your email before {expire} UTC\n\nLink: {link}"
        
        send_email_task.delay("Verify Your Email", message, [email])
        
        return RegisterMutation(success=True, message="User registered successfully! Please check your email.")


class LoginMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        platform = graphene.String(required=True)
        device_name = graphene.String(default_value="Unknown Device")
    
    success = graphene.Boolean()
    message = graphene.String()
    access_token = graphene.String()
    refresh_token = graphene.String()
    user = graphene.Field(UserType)
    
    def mutate(self, info, username, password, platform, device_name):
        ip = info.context.META.get('REMOTE_ADDR', '0.0.0.0')
        rate_limit(ip, limit=5, window=60, key_prefix="login")
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return LoginMutation(success=False, message="Invalid credentials")
        
        if not user.check_password(password):
            return LoginMutation(success=False, message="Invalid credentials")
        
        if not user.email_verified:
            return LoginMutation(success=False, message="Please verify your email first")
        
        # Get or create device
        device, created = Device.objects.get_or_create(
            user=user,
            device_name=device_name,
            defaults={
                "ip_address": info.context.META.get("REMOTE_ADDR"),
                "device_id": uuid.uuid4()
            }
        )
        
        device.ip_address = info.context.META.get("REMOTE_ADDR")
        device.save()
        
        device_id = str(device.device_id)
        
        # Create tokens using pure PyJWT
        access_token = create_access_token(user, device_id, platform)
        refresh_token = create_refresh_token(user, device_id, platform)
        
        # Store refresh token in REDIS (not database!)
        store_refresh_token(
            refresh_token, user, device_id, platform,
            device_name=device_name,
            ip_address=info.context.META.get('REMOTE_ADDR', '')
        )
        
        # Limit sessions using Redis
        limit_user_sessions(user, max_sessions=5)
        
        return LoginMutation(
            success=True,
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            user=user
        )


class VerifyEmailMutation(graphene.Mutation):
    class Arguments:
        uidb64 = graphene.String(required=True)
        token = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, uidb64, token):
        ip = info.context.META.get('REMOTE_ADDR', '0.0.0.0')
        rate_limit(ip, limit=10, window=60, key_prefix="verify_email")
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return VerifyEmailMutation(success=False, message="Invalid verification link")
        
        if token_generator.check_token(user, token):
            user.email_verified = True
            user.save()
            return VerifyEmailMutation(success=True, message="Email verified successfully!")
        
        return VerifyEmailMutation(success=False, message="Invalid or expired verification link")


class RefreshTokenMutation(graphene.Mutation):
    class Arguments:
        refresh_token = graphene.String(required=True)
        platform = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    access_token = graphene.String()
    refresh_token = graphene.String()
    
    def mutate(self, info, refresh_token, platform):
        ip = info.context.META.get('REMOTE_ADDR', '0.0.0.0')
        rate_limit(ip, limit=20, window=60, key_prefix="refresh")
        
        # Verify refresh token (uses Redis blacklist check)
        payload = verify_token(refresh_token, 'refresh')
        if not payload:
            return RefreshTokenMutation(success=False, message="Invalid or expired refresh token")
        
        # Rotate tokens (blacklist old in Redis, create new)
        new_access, new_refresh = refresh_both_tokens(refresh_token)
        
        if not new_access:
            return RefreshTokenMutation(success=False, message="Failed to refresh token")
        
        return RefreshTokenMutation(
            success=True,
            message="Token refreshed successfully",
            access_token=new_access,
            refresh_token=new_refresh
        )


class LogoutMutation(graphene.Mutation):
    class Arguments:
        refresh_token = graphene.String(required=True)
        all_devices = graphene.Boolean(default_value=False)
    
    success = graphene.Boolean()
    message = graphene.String()
    count = graphene.Int()
    
    def mutate(self, info, refresh_token, all_devices=False):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        
        if not user_id:
            raise GraphQLError("Authentication required")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found")
        
        if all_devices:
            # Revoke all tokens from Redis
            count = redis_token_manager.revoke_all_user_tokens(user.id, "logout_all_devices")
            return LogoutMutation(
                success=True,
                message=f"Logged out from {count} devices",
                count=count
            )
        else:
            blacklist_token_by_value(refresh_token, reason="logout")
            return LogoutMutation(
                success=True,
                message="Logged out successfully",
                count=1
            )


class PasswordResetRequestMutation(graphene.Mutation):
    class Arguments:
        email = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, email):
        ip = info.context.META.get('REMOTE_ADDR', '0.0.0.0')
        rate_limit(ip, limit=3, window=60, key_prefix="password_reset")
        
        user = User.objects.filter(email=email).first()
        
        if not user:
            return PasswordResetRequestMutation(success=True, message="If account exists, password reset email sent")
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        expire = datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        message = f"Reset your password before {expire} UTC\n\nLink: {link}"
        
        send_email_task.delay("Password Reset Request", message, [email])
        
        return PasswordResetRequestMutation(success=True, message="If account exists, password reset email sent")


class SetNewPasswordMutation(graphene.Mutation):
    class Arguments:
        uidb64 = graphene.String(required=True)
        token = graphene.String(required=True)
        new_password = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, uidb64, token, new_password):
        ip = info.context.META.get('REMOTE_ADDR', '0.0.0.0')
        rate_limit(ip, limit=5, window=60, key_prefix="set_password")
        
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return SetNewPasswordMutation(success=False, message="Invalid reset link")
        
        if len(new_password) < 6:
            return SetNewPasswordMutation(success=False, message="Password must be at least 6 characters")
        
        if token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            
            # Revoke all sessions from Redis after password change
            redis_token_manager.revoke_all_user_tokens(user.id, "password_changed")
            
            return SetNewPasswordMutation(success=True, message="Password reset successful! Please login again.")
        
        return SetNewPasswordMutation(success=False, message="Invalid or expired reset link")


class ChangePasswordMutation(graphene.Mutation):
    class Arguments:
        old_password = graphene.String(required=True)
        new_password = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, old_password, new_password):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        
        if not user_id:
            raise GraphQLError("Authentication required")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found")
        
        if not user.check_password(old_password):
            return ChangePasswordMutation(success=False, message="Wrong password")
        
        if len(new_password) < 6:
            return ChangePasswordMutation(success=False, message="Password must be at least 6 characters")
        
        user.set_password(new_password)
        user.save()
        
        # Revoke all sessions from Redis after password change
        redis_token_manager.revoke_all_user_tokens(user.id, "password_changed")
        
        return ChangePasswordMutation(success=True, message="Password changed successfully! Please login again.")


class RemoveDeviceMutation(graphene.Mutation):
    class Arguments:
        device_id = graphene.String(required=True)
    
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, device_id):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        
        if not user_id:
            raise GraphQLError("Authentication required")
        
        try:
            user = User.objects.get(id=user_id)
            device = Device.objects.get(device_id=device_id, user=user)
        except (User.DoesNotExist, Device.DoesNotExist):
            raise GraphQLError("Device not found")
        
        # Revoke device tokens from Redis
        redis_token_manager.revoke_all_user_tokens(user.id, f"remove_device_{device_id}")
        
        # Delete device record
        device.delete()
        
        return RemoveDeviceMutation(success=True, message="Device removed successfully")


class RemoveOtherDevicesMutation(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    count = graphene.Int()
    
    def mutate(self, info):
        user_id = info.context.META.get('HTTP_X_USER_ID', '')
        current_device_id = info.context.META.get('HTTP_X_DEVICE_ID', '')
        
        if not user_id:
            raise GraphQLError("Authentication required")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise GraphQLError("User not found")
        
        devices = Device.objects.filter(user=user)
        
        if current_device_id:
            devices = devices.exclude(device_id=current_device_id)
        
        count = devices.count()
        
        for device in devices:
            redis_token_manager.revoke_all_user_tokens(user.id, f"remove_other_devices_{device.device_id}")
            device.delete()
        
        return RemoveOtherDevicesMutation(
            success=True,
            message=f"Removed {count} other devices",
            count=count
        )