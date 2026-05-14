from users.utils import verify_token

class AuthMiddleware:
    def resolve(self, next, root, info, **kwargs):
        request = info.context
        auth_header = request.headers.get('Authorization', '')
        
        user_id = None
        device_id = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            payload = verify_token(token, 'access')
            
            if payload:
                user_id = str(payload.get('user_id'))
                device_id = payload.get('device_id')
        
        request.META['HTTP_X_USER_ID'] = user_id if user_id else ''
        request.META['HTTP_X_DEVICE_ID'] = device_id if device_id else ''
        
        return next(root, info, **kwargs)