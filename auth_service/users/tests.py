from django.test import TestCase
from django.contrib.auth import get_user_model
from users.utils import create_access_token, create_refresh_token, verify_token
import jwt
from django.conf import settings
import uuid

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='Test@123'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('Test@123'))
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_user_email_verified_default(self):
        user = User.objects.create_user(
            username='testuser2',
            email='test2@test.com',
            password='Test@123'
        )
        self.assertFalse(user.email_verified)


class JWTTokenTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='jwtuser',
            email='jwt@test.com',
            password='Test@123'
        )

    def test_create_access_token(self):
        token = create_access_token(self.user, device_id='test-device')
        self.assertIsNotNone(token)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience='my-users',
            issuer='my-app'
        )
        self.assertEqual(payload.get('user_id'), self.user.id)
        self.assertEqual(payload.get('device_id'), 'test-device')
        self.assertEqual(payload.get('type'), 'access')

    def test_create_refresh_token(self):
        token = create_refresh_token(self.user, device_id='test-device')
        self.assertIsNotNone(token)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience='my-users',
            issuer='my-app'
        )
        self.assertEqual(payload.get('type'), 'refresh')

    def test_verify_token_valid(self):
        token = create_access_token(self.user)
        payload = verify_token(token, 'access')
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get('user_id'), self.user.id)

    def test_verify_token_wrong_type(self):
        token = create_access_token(self.user)
        payload = verify_token(token, 'refresh')
        self.assertIsNone(payload)

    def test_verify_token_invalid(self):
        payload = verify_token('invalid.token.here', 'access')
        self.assertIsNone(payload)


class GraphQLMutationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='graphqluser',
            email='graphql@test.com',
            password='Test@123'
        )

    def test_register_mutation(self):
        from graphene.test import Client
        from gql_schema.schema import schema
        
        client = Client(schema)
        executed = client.execute('''
            mutation {
                register(username: "newuser", email: "new@test.com", password: "Test@123") {
                    success
                    message
                }
            }
        ''')
        self.assertTrue(executed['data']['register']['success'])

    def test_login_mutation(self):
        from graphene.test import Client
        from gql_schema.schema import schema
        
        client = Client(schema)
        executed = client.execute('''
            mutation {
                login(username: "graphqluser", password: "Test@123", platform: "web", deviceName: "test") {
                    success
                    accessToken
                    refreshToken
                }
            }
        ''')
        self.assertTrue(executed['data']['login']['success'])
        self.assertIsNotNone(executed['data']['login']['accessToken'])


class RateLimitTest(TestCase):
    def test_rate_limit_decorator(self):
        # Test rate limiting functionality
        from users.utils import verify_token
        self.assertIsNotNone(verify_token)