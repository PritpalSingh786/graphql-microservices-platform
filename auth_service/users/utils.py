import jwt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import OutstandingToken, BlacklistedToken
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async

User = get_user_model()


def create_access_token(user, device_id=None, platform="web"):
    """Create access token using pure PyJWT"""
    payload = {
        'user_id': user.id,
        'device_id': str(device_id) if device_id else None,
        'platform': platform,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME),
        'iat': datetime.utcnow(),
        'iss': settings.JWT_ISSUER,
        'aud': settings.JWT_AUDIENCE,
        'jti': str(uuid.uuid4())
    }
    
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def create_refresh_token(user, device_id=None, platform="web"):
    """Create refresh token using pure PyJWT"""
    payload = {
        'user_id': user.id,
        'device_id': str(device_id) if device_id else None,
        'platform': platform,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_LIFETIME),
        'iat': datetime.utcnow(),
        'iss': settings.JWT_ISSUER,
        'aud': settings.JWT_AUDIENCE,
        'jti': str(uuid.uuid4())
    }
    
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return token


def verify_token(token, token_type='access'):
    """Verify and decode JWT token - Sync version (for GraphQL)"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={'require': ['exp', 'iat', 'jti', 'type']}
        )
        
        if payload.get('type') != token_type:
            return None
        
        if BlacklistedToken.objects.filter(jti=payload.get('jti')).exists():
            return None
        
        if payload['exp'] < datetime.utcnow().timestamp():
            return None
        
        if not User.objects.filter(id=payload['user_id'], is_active=True).exists():
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


async def averify_token(token, token_type='access'):
    """Verify and decode JWT token - Async version (for WebSocket)"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={'require': ['exp', 'iat', 'jti', 'type']}
        )
        
        if payload.get('type') != token_type:
            return None
        
        # Async database call
        exists = await sync_to_async(BlacklistedToken.objects.filter(jti=payload.get('jti')).exists)()
        if exists:
            return None
        
        if payload['exp'] < datetime.utcnow().timestamp():
            return None
        
        user_exists = await sync_to_async(User.objects.filter(id=payload['user_id'], is_active=True).exists)()
        if not user_exists:
            return None
        
        return payload
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def is_token_blacklisted(jti):
    """Check if a token by JTI is blacklisted"""
    return BlacklistedToken.objects.filter(jti=jti).exists()


def blacklist_token(jti, reason=None):
    """Blacklist a token by its JTI"""
    BlacklistedToken.objects.get_or_create(
        jti=jti,
        defaults={'reason': reason}
    )
    return True


def blacklist_token_by_value(token_str, reason=None):
    """Blacklist token by its value"""
    try:
        payload = jwt.decode(
            token_str,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        jti = payload.get('jti')
        if jti:
            return blacklist_token(jti, reason)
    except:
        pass
    return False


def store_refresh_token(refresh_token_str, user, device_id=None, platform="web"):
    """Store refresh token in OutstandingToken table"""
    try:
        payload = verify_token(refresh_token_str, 'refresh')
        if not payload:
            return False
        
        OutstandingToken.objects.create(
            user=user,
            token=refresh_token_str,
            jti=payload.get('jti'),
            device_id=device_id,
            platform=platform,
            expires_at=datetime.fromtimestamp(payload['exp']),
            is_active=True
        )
        return True
    except Exception as e:
        print(f"Error storing token: {e}")
        return False


def get_active_tokens(user):
    """Get all active tokens for user"""
    now = datetime.utcnow()
    
    active_outstanding = OutstandingToken.objects.filter(
        user=user,
        expires_at__gt=now,
        is_active=True
    )
    
    active_tokens = []
    for token in active_outstanding:
        if not is_token_blacklisted(token.jti):
            active_tokens.append(token)
    
    return active_tokens


def limit_user_sessions(user, max_sessions=5):
    """Limit number of active sessions"""
    active_tokens = get_active_tokens(user)
    
    if len(active_tokens) >= max_sessions:
        tokens_to_remove = active_tokens[max_sessions - 1:]
        channel_layer = get_channel_layer()
        
        for token_obj in tokens_to_remove:
            blacklist_token(token_obj.jti, reason="session_limit")
            token_obj.is_active = False
            token_obj.save()
            
            if token_obj.device_id and channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"user_{user.id}_{token_obj.device_id}",
                    {
                        "type": "session_killed",
                        "message": "Session limit exceeded. You have been logged out."
                    }
                )
        
        return len(tokens_to_remove)
    
    return 0


def clean_expired_tokens():
    """Delete expired tokens from database"""
    now = datetime.utcnow()
    
    expired = OutstandingToken.objects.filter(expires_at__lt=now)
    count = expired.count()
    
    for token in expired:
        BlacklistedToken.objects.filter(jti=token.jti).delete()
    
    expired.delete()
    return count


def refresh_access_token(refresh_token_str):
    """Generate new access token using refresh token"""
    payload = verify_token(refresh_token_str, 'refresh')
    
    if not payload:
        return None
    
    user = User.objects.get(id=payload['user_id'])
    new_access = create_access_token(
        user,
        payload.get('device_id'),
        payload.get('platform')
    )
    
    return new_access


def refresh_both_tokens(refresh_token_str):
    """Generate new access and refresh tokens (rotate)"""
    payload = verify_token(refresh_token_str, 'refresh')
    
    if not payload:
        return None, None
    
    # Blacklist old refresh token
    blacklist_token_by_value(refresh_token_str, reason="rotated")
    
    user = User.objects.get(id=payload['user_id'])
    device_id = payload.get('device_id')
    platform = payload.get('platform')
    
    # Create new tokens
    new_access = create_access_token(user, device_id, platform)
    new_refresh = create_refresh_token(user, device_id, platform)
    
    # Store new refresh token
    store_refresh_token(new_refresh, user, device_id, platform)
    
    return new_access, new_refresh


def logout_from_device(user, device_id):
    """Logout from a specific device"""
    tokens = OutstandingToken.objects.filter(
        user=user,
        device_id=device_id,
        expires_at__gt=datetime.utcnow(),
        is_active=True
    )
    count = 0
    
    for token in tokens:
        blacklist_token(token.jti, reason="manual_logout_from_device")
        token.is_active = False
        token.save()
        count += 1
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}_{device_id}",
                {
                    "type": "session_killed",
                    "message": "You have been logged out from this device"
                }
            )
    
    return count