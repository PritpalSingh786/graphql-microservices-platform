import jwt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from .redis_token_manager import redis_token_manager
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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
    """Verify and decode JWT token - Uses Redis for blacklist check"""
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
        
        # Redis blacklist check - O(1) operation!
        if redis_token_manager.is_blacklisted(payload.get('jti')):
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
        
        from asgiref.sync import sync_to_async
        
        # Async Redis blacklist check
        if await sync_to_async(redis_token_manager.is_blacklisted)(payload.get('jti')):
            return None
        
        if payload['exp'] < datetime.utcnow().timestamp():
            return None
        
        user_exists = await sync_to_async(User.objects.filter(id=payload['user_id'], is_active=True).exists)()
        if not user_exists:
            return None
        
        return payload
        
    except:
        return None


def store_refresh_token(refresh_token_str, user, device_id=None, platform="web", device_name="", ip_address=""):
    """Store refresh token in Redis (not database!)"""
    try:
        payload = jwt.decode(
            refresh_token_str,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            options={'verify_exp': False}
        )
        
        redis_token_manager.store_refresh_token(
            user_id=user.id,
            jti=payload.get('jti'),
            device_id=str(device_id) if device_id else None,
            platform=platform,
            device_name=device_name,
            ip_address=ip_address
        )
        return True
    except Exception as e:
        print(f"Error storing token in Redis: {e}")
        return False


def is_token_blacklisted(jti):
    """Check if token is blacklisted - Redis O(1)"""
    return redis_token_manager.is_blacklisted(jti)


def blacklist_token(jti, reason=None):
    """Blacklist token in Redis"""
    return redis_token_manager.blacklist_token(jti, reason or "revoked")


def blacklist_token_by_value(token_str, reason=None):
    """Blacklist token by value"""
    try:
        payload = jwt.decode(
            token_str,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_signature": False}
        )
        jti = payload.get('jti')
        if jti:
            return redis_token_manager.blacklist_token(jti, reason or "revoked")
    except:
        pass
    return False


def get_active_tokens(user):
    """Get all active tokens for user from Redis"""
    return redis_token_manager.get_user_active_tokens(user.id)


def limit_user_sessions(user, max_sessions=5):
    """Limit number of active sessions using Redis"""
    return redis_token_manager.limit_user_sessions(user.id, max_sessions)


def refresh_both_tokens(refresh_token_str):
    """Generate new access and refresh tokens (rotate)"""
    payload = verify_token(refresh_token_str, 'refresh')
    
    if not payload:
        return None, None
    
    # Blacklist old refresh token in Redis
    blacklist_token_by_value(refresh_token_str, reason="rotated")
    
    try:
        user = User.objects.get(id=payload['user_id'])
        device_id = payload.get('device_id')
        platform = payload.get('platform')
        
        # Create new tokens
        new_access = create_access_token(user, device_id, platform)
        new_refresh = create_refresh_token(user, device_id, platform)
        
        # Store new refresh token in Redis
        store_refresh_token(new_refresh, user, device_id, platform)
        
        return new_access, new_refresh
    except User.DoesNotExist:
        return None, None


def logout_from_device(user, device_id):
    """Logout from a specific device"""
    return redis_token_manager.revoke_all_user_tokens(user.id, f"logout_device_{device_id}")


def clean_expired_tokens():
    """Redis handles this automatically - function kept for compatibility"""
    return 0