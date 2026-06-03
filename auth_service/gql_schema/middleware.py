from users.utils import decode_token  # Change: use decode_token instead of verify_token

class AuthMiddleware:
    def resolve(self, next, root, info, **kwargs):
        request = info.context
        auth_header = request.headers.get('Authorization', '')
        
        user_id = None
        device_id = None
        
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            # Use decode_token with 'access' type
            payload = decode_token(token, 'access')
            
            if payload:
                user_id = str(payload.get('user_id'))
                device_id = payload.get('device_id')
        
        # Attach to request for GraphQL context
        request.user_id = user_id
        request.device_id = device_id
        
        # For microservice headers
        request.META['HTTP_X_USER_ID'] = user_id if user_id else ''
        request.META['HTTP_X_DEVICE_ID'] = device_id if device_id else ''
        
        return next(root, info, **kwargs)