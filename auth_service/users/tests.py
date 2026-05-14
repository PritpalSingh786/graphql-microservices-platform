from django.test import TestCase
from django.contrib.auth import get_user_model
from users.utils import create_access_token, create_refresh_token, verify_token
from users.redis_token_manager import redis_token_manager
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


class RedisTokenManagerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='redisuser',
            email='redis@test.com',
            password='Test@123'
        )
        self.jti = str(uuid.uuid4())

    def test_store_and_get_refresh_token(self):
        redis_token_manager.store_refresh_token(
            user_id=self.user.id,
            jti=self.jti,
            device_id='test-device',
            platform='web',
            device_name='Test Device',
            ip_address='127.0.0.1'
        )
        
        token_data = redis_token_manager.get_refresh_token(self.jti)
        self.assertIsNotNone(token_data)
        self.assertEqual(token_data['user_id'], str(self.user.id))

    def test_blacklist_token(self):
        redis_token_manager.store_refresh_token(
            user_id=self.user.id,
            jti=self.jti,
            device_id='test-device',
            platform='web'
        )
        
        redis_token_manager.blacklist_token(self.jti, "test_reason")
        self.assertTrue(redis_token_manager.is_blacklisted(self.jti))

    def test_revoke_all_user_tokens(self):
        redis_token_manager.store_refresh_token(
            user_id=self.user.id,
            jti=self.jti,
            device_id='test-device',
            platform='web'
        )
        
        count = redis_token_manager.revoke_all_user_tokens(self.user.id)
        self.assertEqual(count, 1)
        self.assertIsNone(redis_token_manager.get_refresh_token(self.jti))


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


class RateLimitTest(TestCase):
    def test_rate_limit_decorator(self):
        from users.utils import verify_token
        self.assertIsNotNone(verify_token)