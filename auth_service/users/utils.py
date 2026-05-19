import jwt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from .redis_token_manager import redis_token_manager

User = get_user_model()

# ============ TOKEN CREATION ============

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
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

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
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

# ============ TOKEN VERIFICATION ============

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
        
        if redis_token_manager.is_blacklisted(payload.get('jti')):
            return None
        
        if payload['exp'] < datetime.utcnow().timestamp():
            return None
        
        if not User.objects.filter(id=payload['user_id'], is_active=True).exists():
            return None
        
        return payload
        
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

async def averify_token(token, token_type='access'):
    """Async version for WebSocket"""
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

# ============ TOKEN STORAGE ============

def store_refresh_token(refresh_token_str, user, device_id=None, platform="web", device_name="", ip_address=""):
    """Store refresh token in Redis"""
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

# ============ BLACKLIST OPERATIONS ============

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

# ============ SESSION MANAGEMENT ============

def get_active_tokens(user):
    """Get all active tokens for user from Redis"""
    return redis_token_manager.get_user_active_tokens(user.id)

def limit_user_sessions(user, max_sessions=5):
    """Limit number of active sessions"""
    return redis_token_manager.limit_user_sessions(user.id, max_sessions)

def refresh_both_tokens(refresh_token_str):
    """Generate new access and refresh tokens (rotation)"""
    payload = verify_token(refresh_token_str, 'refresh')
    
    if not payload:
        return None, None
    
    blacklist_token_by_value(refresh_token_str, reason="rotated")
    
    try:
        user = User.objects.get(id=payload['user_id'])
        device_id = payload.get('device_id')
        platform = payload.get('platform')
        
        new_access = create_access_token(user, device_id, platform)
        new_refresh = create_refresh_token(user, device_id, platform)
        
        store_refresh_token(new_refresh, user, device_id, platform)
        
        return new_access, new_refresh
    except User.DoesNotExist:
        return None, None

def revoke_user_session_by_jti(jti, reason="revoked"):
    """Revoke a specific session by its JTI"""
    try:
        token_data = redis_token_manager.get_refresh_token(jti)
        if token_data:
            user_id = token_data.get('user_id')
            device_id = token_data.get('device_id')
            
            redis_token_manager.blacklist_token(jti, reason)
            redis_token_manager.delete_refresh_token(jti)
            
            if device_id:
                redis_token_manager._send_websocket_notification(
                    user_id, device_id, f"Session terminated. Reason: {reason}"
                )
            return True
        return False
    except Exception as e:
        print(f"Error revoking session: {e}")
        return False