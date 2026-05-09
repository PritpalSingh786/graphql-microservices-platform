import jwt
from django.conf import settings

class AuthMiddleware:
    def resolve(self, next, root, info, **kwargs):
        request = info.context
        auth_header = request.headers.get('Authorization', '')
        
        user_id = None
        device_id = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    audience='my-users',
                    issuer='my-app'
                )
                
                user_id = str(payload.get('user_id'))
                device_id = payload.get('device_id', '')
                
            except jwt.ExpiredSignatureError:
                print("Token expired")
            except jwt.InvalidTokenError as e:
                print(f"Invalid token: {e}")
            except Exception as e:
                print(f"Other error: {e}")
        
        # Store in META for resolvers to use
        request.META['HTTP_X_USER_ID'] = user_id if user_id else ''
        request.META['HTTP_X_DEVICE_ID'] = device_id if device_id else ''
        
        return next(root, info, **kwargs)