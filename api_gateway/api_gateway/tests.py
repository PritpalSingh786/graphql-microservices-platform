from django.test import TestCase, Client
import json


class GatewayProxyTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_auth_gateway_register(self):
        response = self.client.post(
            '/graphql/auth/',
            json.dumps({
                'operationName': 'RegisterUser',
                'query': 'mutation RegisterUser($username: String!, $email: String!, $password: String!) { register(username: $username, email: $email, password: $password) { success message } }',
                'variables': {
                    'username': 'testuser',
                    'email': 'test@test.com',
                    'password': 'Test@123'
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
    def test_public_operation_no_token(self):
        client = Client()
        response = client.post(
            '/graphql/auth/',
            json.dumps({
                'operationName': 'RegisterUser',
                'query': 'mutation RegisterUser($username: String!, $email: String!, $password: String!) { register(username: $username, email: $email, password: $password) { success } }',
                'variables': {
                    'username': 'newuser',
                    'email': 'new@test.com',
                    'password': 'Test@123'
                }
            }),
            content_type='application/json'
        )
        self.assertNotEqual(response.status_code, 401)

    def test_protected_operation_requires_token(self):
        client = Client()
        response = client.post(
            '/graphql/auth/',
            json.dumps({
                'query': 'query { me { id username } }'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)