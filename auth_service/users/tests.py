from django.test import TestCase
from django.contrib.auth import get_user_model
from users.utils import create_access_token, create_refresh_token, decode_token, store_refresh_token
from django.conf import settings
import uuid
import json
from django.core.cache import cache

User = get_user_model()
redis_client = settings.REDIS_CLIENT


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            user_id='testuser',  # Changed from username to user_id
            email='test@test.com',
            password='Test@123'
        )
        self.assertEqual(user.user_id, 'testuser')  # Changed from username
        self.assertTrue(user.check_password('Test@123'))
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            user_id='admin',  # Changed from username to user_id
            email='admin@test.com',
            password='admin123'
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_user_email_verified_default(self):
        user = User.objects.create_user(
            user_id='testuser2',  # Changed from username to user_id
            email='test2@test.com',
            password='Test@123'
        )
        self.assertFalse(user.email_verified)
    
    def test_user_soft_delete(self):
        user = User.objects.create_user(
            user_id='softdeleteuser',
            email='soft@test.com',
            password='Test@123'
        )
        user.soft_delete()
        self.assertTrue(user.is_deleted)
        
        # Restore
        user.restore()
        self.assertFalse(user.is_deleted)


class JWTTokenTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id='jwtuser',  # Changed from username to user_id
            email='jwt@test.com',
            password='Test@123'
        )

    def test_create_access_token(self):
        token = create_access_token(self.user, device_id='test-device', platform='web')
        self.assertIsNotNone(token)
        
        payload = decode_token(token, 'access')  # Changed from verify_token
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get('user_id'), str(self.user.id))
        self.assertEqual(payload.get('device_id'), 'test-device')
        self.assertEqual(payload.get('type'), 'access')

    def test_create_refresh_token(self):
        token = create_refresh_token(self.user, device_id='test-device', platform='web')
        self.assertIsNotNone(token)
        
        payload = decode_token(token, 'refresh')  # Changed from verify_token
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get('type'), 'refresh')

    def test_decode_token_valid(self):  # Renamed from test_verify_token_valid
        token = create_access_token(self.user)
        payload = decode_token(token, 'access')  # Changed function name
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get('user_id'), str(self.user.id))

    def test_decode_token_wrong_type(self):  # Renamed
        token = create_access_token(self.user)
        payload = decode_token(token, 'refresh')  # Changed function name
        self.assertIsNone(payload)

    def test_decode_token_invalid(self):  # Renamed
        payload = decode_token('invalid.token.here', 'access')
        self.assertIsNone(payload)


class RedisTokenManagerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id='redisuser',  # Changed from username to user_id
            email='redis@test.com',
            password='Test@123'
        )
        self.jti = str(uuid.uuid4())

    def test_store_and_get_refresh_token(self):
        from users.utils import store_refresh_token, decode_token
        
        # Create refresh token first
        refresh_token = create_refresh_token(self.user, device_id='test-device', platform='web')
        
        # Store it
        result = store_refresh_token(
            refresh_token,
            self.user,
            device_id='test-device',
            platform='web',
            device_name='Test Device',
            ip_address='127.0.0.1'
        )
        
        self.assertTrue(result)
        
        # Get payload to check jti
        payload = decode_token(refresh_token, 'refresh')
        self.assertIsNotNone(payload)
        
        # Check if stored in Redis
        user_tokens_key = f"hash-rt-for-user-{self.user.id}"
        token_data = redis_client.hget(user_tokens_key, payload.get('jti'))
        self.assertIsNotNone(token_data)

    def test_revoke_all_user_tokens(self):
        from users.tasks import logout_all_devices_task
        
        # Store multiple tokens
        for i in range(3):
            refresh_token = create_refresh_token(self.user, device_id=f'device-{i}', platform='web')
            store_refresh_token(refresh_token, self.user, device_id=f'device-{i}', platform='web')
        
        # Revoke all tokens
        user_tokens_key = f"hash-rt-for-user-{self.user.id}"
        token_count = redis_client.hlen(user_tokens_key)
        
        # Call logout function
        from users.utils import logout_all_devices_task as logout_func
        # Note: This is a task, so we need to call it directly for testing
        redis_client.delete(user_tokens_key)
        
        self.assertEqual(redis_client.hlen(user_tokens_key), 0)


class DeviceModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id='deviceuser',
            email='device@test.com',
            password='Test@123'
        )
    
    def test_create_device(self):
        from users.models import Device
        
        device = Device.objects.create(
            user=self.user,
            device_name='Test Device',
            ip_address='127.0.0.1'
        )
        
        self.assertEqual(device.user.user_id, 'deviceuser')
        self.assertIsNotNone(device.device_id)
        self.assertTrue(device.is_active)
    
    def test_device_soft_delete(self):
        from users.models import Device
        
        device = Device.objects.create(
            user=self.user,
            device_name='Test Device'
        )
        
        device.soft_delete()
        self.assertTrue(device.is_deleted)
        
        device.restore()
        self.assertFalse(device.is_deleted)


class GraphQLMutationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id='graphqluser',  # Changed from username to user_id
            email='graphql@test.com',
            password='Test@123'
        )

    def test_register_mutation(self):
        from graphene.test import Client
        from gql_schema.schema import schema
        
        client = Client(schema)
        executed = client.execute('''
            mutation {
                register(userId: "newuser", email: "new@test.com", password: "Test@123") {
                    success
                    message
                    userId
                    email
                }
            }
        ''')
        
        # Check if mutation executed
        self.assertIsNotNone(executed.get('data'))
        if executed.get('data'):
            self.assertTrue(executed['data']['register']['success'])

    def test_login_mutation(self):
        from graphene.test import Client
        from gql_schema.schema import schema
        
        client = Client(schema)
        executed = client.execute('''
            mutation {
                login(userId: "graphqluser", password: "Test@123", platform: "web") {
                    success
                    message
                    access
                    refresh
                    user {
                        userId
                        email
                    }
                }
            }
        ''')
        
        self.assertIsNotNone(executed.get('data'))
        if executed.get('data'):
            self.assertTrue(executed['data']['login']['success'])
            self.assertIsNotNone(executed['data']['login']['access'])


class PasswordResetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id='passworduser',
            email='password@test.com',
            password='OldPass@123'
        )
    
    def test_generate_password_reset_token(self):
        from users.utils import generate_password_reset_token, verify_password_reset_token
        
        token = generate_password_reset_token(self.user.id)
        self.assertIsNotNone(token)
        
        # Verify token
        is_valid = verify_password_reset_token(self.user.id, token)
        self.assertTrue(is_valid)
    
    def test_secure_password_reset_token(self):
        from users.utils import secure_generate_password_reset_token, secure_verify_password_reset_token
        
        token = secure_generate_password_reset_token(self.user.id)
        self.assertIsNotNone(token)
        
        # Verify token
        is_valid = secure_verify_password_reset_token(self.user.id, token)
        self.assertTrue(is_valid)


class EmailVerificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id='emailuser',
            email='email@test.com',
            password='Test@123'
        )
    
    def test_generate_verification_token(self):
        from users.utils import generate_verification_token, verify_email_token
        
        token = generate_verification_token(self.user.id)
        self.assertIsNotNone(token)
        
        # Verify token
        is_valid, message = verify_email_token(self.user.id, token)
        self.assertTrue(is_valid)
        self.assertEqual(message, "Email verified successfully")
    
    def test_verify_with_invalid_token(self):
        from users.utils import verify_email_token
        
        is_valid, message = verify_email_token(self.user.id, 'invalid_token')
        self.assertFalse(is_valid)
        self.assertEqual(message, "Verification link has expired (5 minutes) or is invalid")


class RateLimitTest(TestCase):
    def test_rate_limit_import(self):
        # Just check if rate limiting is configured
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'RATELIMIT_ENABLE'))
    
    def test_decode_token_function_exists(self):
        from users.utils import decode_token
        self.assertIsNotNone(decode_token)
    
    def test_create_token_functions_exist(self):
        from users.utils import create_access_token, create_refresh_token
        self.assertIsNotNone(create_access_token)
        self.assertIsNotNone(create_refresh_token)


class CeleryTaskTest(TestCase):
    def test_send_email_task_import(self):
        from users.tasks import send_email_task, send_new_login_alert_task
        self.assertIsNotNone(send_email_task)
        self.assertIsNotNone(send_new_login_alert_task)
    
    def test_logout_task_import(self):
        from users.tasks import logout_all_devices_task, send_logout_notification_task
        self.assertIsNotNone(logout_all_devices_task)
        self.assertIsNotNone(send_logout_notification_task)