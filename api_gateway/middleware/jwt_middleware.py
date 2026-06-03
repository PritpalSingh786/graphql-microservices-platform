import jwt
import json
from django.conf import settings
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin


# Public GraphQL operations (no auth required)
PUBLIC_OPERATIONS = [
    'register',
    'login', 
    'verifyEmail',
    'forgotPassword',
    'changePassword',
    'secureChangePassword',
    'refreshToken',
    'changePassword',
    'secureChangePassword',
    'verifyResetToken',
    'verifyEmailTokenValid',
    '__schema',
    '__typename'
]


class JWTAuthMiddleware(MiddlewareMixin):

    def process_request(self, request):

        # ✅ Allow GET requests (GraphQL Playground / browser)
        if request.method == 'GET':
            return None

        # ✅ Only handle GraphQL POST requests
        if request.method == 'POST' and request.path.startswith('/graphql/'):

            try:
                body = json.loads(request.body or '{}')
                query = body.get('query', '')
                operation_name = body.get('operationName', '')

                # ✅ Check public operations (by operationName OR query match)
                if (
                    operation_name in PUBLIC_OPERATIONS or
                    any(op in query for op in PUBLIC_OPERATIONS)
                ):
                    return None  # 🔓 skip auth

            except Exception:
                # If body parsing fails → treat as protected
                pass

        # ✅ JWT Authentication for protected routes
        auth_header = request.headers.get('Authorization', '')

        print(auth_header, "authhhhh")

        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {
                    'errors': [
                        {'message': 'Authentication required. Please provide valid JWT token.'}
                    ]
                },
                status=401
            )

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience='my-users',
                issuer='my-app'
            )

            # ✅ Attach user info to request headers (for microservices)
            request.META['HTTP_X_USER_ID'] = str(payload.get('user_id'))
            request.META['HTTP_X_DEVICE_ID'] = payload.get('device_id', '')

        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {'errors': [{'message': 'Token has expired. Please login again.'}]},
                status=401
            )

        except jwt.InvalidTokenError as e:
            return JsonResponse(
                {'errors': [{'message': f'Invalid token: {str(e)}'}]},
                status=401
            )

        return None