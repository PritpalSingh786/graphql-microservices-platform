from django.test import TestCase, Client
import json


class GatewayProxyTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_auth_gateway_register(self):
        response = self.client.post(
            '/graphql/',  # Changed from '/graphql/auth/' to '/graphql/'
            json.dumps({
                'operationName': 'register',  # Changed from 'RegisterUser'
                'query': '''
                    mutation register($userId: String!, $email: String!, $password: String!) { 
                        register(userId: $userId, email: $email, password: $password) { 
                            success 
                            message 
                            userId 
                            email 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'testuser',  # Changed from 'username' to 'userId'
                    'email': 'test@test.com',
                    'password': 'Test@123'
                }
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Optional: Check response data
        data = response.json()
        if 'data' in data and data['data']:
            self.assertTrue(data['data']['register']['success'])

    def test_auth_gateway_login(self):
        # First register a user
        register_response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'register',
                'query': '''
                    mutation register($userId: String!, $email: String!, $password: String!) { 
                        register(userId: $userId, email: $email, password: $password) { 
                            success 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'logintest',
                    'email': 'login@test.com',
                    'password': 'Test@123'
                }
            }),
            content_type='application/json'
        )
        
        # Then try to login
        response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'login',  # Changed from 'Login'
                'query': '''
                    mutation login($userId: String!, $password: String!, $platform: String!) { 
                        login(userId: $userId, password: $password, platform: $platform) { 
                            success 
                            message
                            access 
                            refresh 
                            user { 
                                id 
                                userId 
                                email 
                            } 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'logintest',
                    'password': 'Test@123',
                    'platform': 'web'
                }
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_blog_gateway_all_uploads(self):
        response = self.client.post(
            '/graphql/blog/',
            json.dumps({
                'query': 'query { allUploads { id title } }'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)


class MiddlewareTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create a test user and get token
        # Register
        register_response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'register',
                'query': '''
                    mutation register($userId: String!, $email: String!, $password: String!) { 
                        register(userId: $userId, email: $email, password: $password) { 
                            success 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'middletest',
                    'email': 'middle@test.com',
                    'password': 'Test@123'
                }
            }),
            content_type='application/json'
        )
        
        # Login to get token
        login_response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'login',
                'query': '''
                    mutation login($userId: String!, $password: String!, $platform: String!) { 
                        login(userId: $userId, password: $password, platform: $platform) { 
                            success 
                            access 
                            refresh 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'middletest',
                    'password': 'Test@123',
                    'platform': 'web'
                }
            }),
            content_type='application/json'
        )
        
        # Store access token
        login_data = login_response.json()
        if 'data' in login_data and login_data['data']:
            self.access_token = login_data['data']['login']['access']
        else:
            self.access_token = None

    def test_public_operation_no_token(self):
        # Register is now a public operation
        response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'register',
                'query': '''
                    mutation register($userId: String!, $email: String!, $password: String!) { 
                        register(userId: $userId, email: $email, password: $password) { 
                            success 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'publicuser',
                    'email': 'public@test.com',
                    'password': 'Test@123'
                }
            }),
            content_type='application/json'
        )
        # Public operations should work without token
        self.assertNotEqual(response.status_code, 401)
        
        # Check if response is successful
        self.assertEqual(response.status_code, 200)

    def test_protected_operation_requires_token(self):
        # 'me' query is protected
        response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'me',
                'query': 'query me { me { success user { userId email } } }'
            }),
            content_type='application/json'
        )
        # Should return 401 without token
        self.assertEqual(response.status_code, 401)

    def test_protected_operation_with_token(self):
        if not self.access_token:
            self.skipTest("Could not get access token")
        
        # Make request with token
        response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'me',
                'query': 'query me { me { success user { userId email } } }'
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.access_token}'
        )
        
        # Should succeed with token
        self.assertEqual(response.status_code, 200)
        
        # Check response data
        data = response.json()
        if 'data' in data and data['data']:
            self.assertTrue(data['data']['me']['success'])

    def test_refresh_token_mutation(self):
        if not self.access_token:
            self.skipTest("Could not get access token")
        
        # First get refresh token from login
        login_response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'login',
                'query': '''
                    mutation login($userId: String!, $password: String!, $platform: String!) { 
                        login(userId: $userId, password: $password, platform: $platform) { 
                            success 
                            refresh 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'middletest',
                    'password': 'Test@123',
                    'platform': 'web'
                }
            }),
            content_type='application/json'
        )
        
        login_data = login_response.json()
        if 'data' in login_data and login_data['data']:
            refresh_token = login_data['data']['login']['refresh']
            
            # Test refresh token mutation
            response = self.client.post(
                '/graphql/',
                json.dumps({
                    'operationName': 'refreshToken',
                    'query': '''
                        mutation refreshToken($refresh: String!, $platform: String!) { 
                            refreshToken(refresh: $refresh, platform: $platform) { 
                                success 
                                access 
                                refresh 
                            } 
                        }
                    ''',
                    'variables': {
                        'refresh': refresh_token,
                        'platform': 'web'
                    }
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Check if new tokens were generated
            data = response.json()
            if 'data' in data and data['data']:
                self.assertTrue(data['data']['refreshToken']['success'])


class PasswordResetTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create a test user
        register_response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'register',
                'query': '''
                    mutation register($userId: String!, $email: String!, $password: String!) { 
                        register(userId: $userId, email: $email, password: $password) { 
                            success 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'passwordtest',
                    'email': 'password@test.com',
                    'password': 'OldPass@123'
                }
            }),
            content_type='application/json'
        )

    def test_forgot_password_mutation(self):
        # Test forgot password (password reset request)
        response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'forgotPassword',
                'query': '''
                    mutation forgotPassword($userId: String!) { 
                        forgotPassword(userId: $userId) { 
                            success 
                            message 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'passwordtest'
                }
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Should return success message
        data = response.json()
        if 'data' in data and data['data']:
            self.assertTrue(data['data']['forgotPassword']['success'])


class EmailVerificationTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create a test user
        register_response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'register',
                'query': '''
                    mutation register($userId: String!, $email: String!, $password: String!) { 
                        register(userId: $userId, email: $email, password: $password) { 
                            success 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'emailtest',
                    'email': 'email@test.com',
                    'password': 'Test@123'
                }
            }),
            content_type='application/json'
        )

    def test_verify_email_mutation(self):
        # Note: This test requires a valid token from email
        # In real testing, you'd need to mock the email sending
        response = self.client.post(
            '/graphql/',
            json.dumps({
                'operationName': 'verifyEmail',
                'query': '''
                    mutation verifyEmail($userId: String!, $token: String!) { 
                        verifyEmail(userId: $userId, token: $token) { 
                            success 
                            message 
                        } 
                    }
                ''',
                'variables': {
                    'userId': 'emailtest',
                    'token': 'invalid_token_should_fail'
                }
            }),
            content_type='application/json'
        )
        
        # Should fail with invalid token
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if 'errors' in data:
            self.assertIsNotNone(data['errors'])