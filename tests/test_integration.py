import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000"


def test_register():
    print("📝 Testing Register...")
    url = f"{BASE_URL}/graphql/auth/"
    payload = {
        "operationName": "register",
        "query": """mutation register($userId: String!, $email: String!, $password: String!) {
            register(userId: $userId, email: $email, password: $password) {
                success 
                message 
                userId 
                email
            }
        }""",
        "variables": {
            "userId": "integrationtest",
            "email": "integration@test.com",
            "password": "Test@123"
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    
    if 'errors' in data:
        print(f"   Warning: {data['errors']}")
    return data


def test_verify_email_direct():
    """Directly verify email using database (for testing only)"""
    print("📧 Directly verifying email in database...")
    
    # For testing, we need to get the verification token from Redis
    # Or we can directly mark user as verified in database
    import subprocess
    import docker
    
    # Option 1: Mark user as verified via Django shell
    cmd = """
    docker compose exec auth_service python manage.py shell -c "
    from users.models import User;
    user = User.objects.get(user_id='integrationtest');
    user.email_verified = True;
    user.is_active = True;
    user.save();
    print('User verified successfully')
    "
    """
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(f"   {result.stdout}")
    return True


def test_login():
    print("🔐 Testing Login...")
    url = f"{BASE_URL}/graphql/auth/"
    payload = {
        "operationName": "login",
        "query": """mutation login($userId: String!, $password: String!, $platform: String!) {
            login(userId: $userId, password: $password, platform: $platform) {
                success 
                message
                access
                refresh
                user {
                    id
                    userId
                    email
                    emailVerified
                }
            }
        }""",
        "variables": {
            "userId": "integrationtest",
            "password": "Test@123",
            "platform": "web"
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    
    if 'errors' in data:
        print(f"   Login error: {data['errors'][0]['message']}")
        return None
    
    if 'data' in data and data['data'] and data['data']['login'] and data['data']['login'].get('access'):
        return data['data']['login']['access']
    else:
        print(f"   Login failed: {data}")
        return None


def test_get_me(token):
    print("👤 Testing Get Me...")
    url = f"{BASE_URL}/graphql/auth/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "operationName": "me",
        "query": """query me { 
            me { 
                success 
                message
                user { 
                    id 
                    userId
                    email 
                    emailVerified
                }
                deviceId
                platform
            } 
        }"""
    }
    response = requests.post(url, json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


def test_refresh_token(token):
    print("🔄 Testing Refresh Token...")
    url = f"{BASE_URL}/graphql/auth/"
    
    # First get refresh token from login
    login_payload = {
        "operationName": "login",
        "query": """mutation login($userId: String!, $password: String!, $platform: String!) {
            login(userId: $userId, password: $password, platform: $platform) {
                success
                refresh
            }
        }""",
        "variables": {
            "userId": "integrationtest",
            "password": "Test@123",
            "platform": "web"
        }
    }
    
    login_response = requests.post(url, json=login_payload)
    login_data = login_response.json()
    
    if 'data' in login_data and login_data['data'] and login_data['data']['login']:
        refresh_token = login_data['data']['login'].get('refresh')
        
        if refresh_token:
            payload = {
                "operationName": "refreshToken",
                "query": """mutation refreshToken($refresh: String!, $platform: String!) {
                    refreshToken(refresh: $refresh, platform: $platform) {
                        success
                        access
                        refresh
                    }
                }""",
                "variables": {
                    "refresh": refresh_token,
                    "platform": "web"
                }
            }
            
            response = requests.post(url, json=payload)
            assert response.status_code == 200
            data = response.json()
            print(f"   Response: {data}")
            return data
    
    print("   Could not get refresh token")
    return None


def test_logout(token):
    print("🚪 Testing Logout...")
    url = f"{BASE_URL}/graphql/auth/"
    
    login_payload = {
        "operationName": "login",
        "query": """mutation login($userId: String!, $password: String!, $platform: String!) {
            login(userId: $userId, password: $password, platform: $platform) {
                success
                refresh
            }
        }""",
        "variables": {
            "userId": "integrationtest",
            "password": "Test@123",
            "platform": "web"
        }
    }
    
    login_response = requests.post(url, json=login_payload)
    login_data = login_response.json()
    
    if 'data' in login_data and login_data['data'] and login_data['data']['login']:
        refresh_token = login_data['data']['login'].get('refresh')
        
        if refresh_token:
            payload = {
                "operationName": "logout",
                "query": """mutation logout($refresh: String!) {
                    logout(refresh: $refresh) {
                        success
                        message
                    }
                }""",
                "variables": {
                    "refresh": refresh_token
                }
            }
            
            response = requests.post(url, json=payload)
            assert response.status_code == 200
            data = response.json()
            print(f"   Response: {data}")
            return data
    
    print("   Could not get refresh token for logout")
    return None


def test_forgot_password():
    print("📧 Testing Forgot Password...")
    url = f"{BASE_URL}/graphql/auth/"
    payload = {
        "operationName": "forgotPassword",
        "query": """mutation forgotPassword($userId: String!) {
            forgotPassword(userId: $userId) {
                success
                message
            }
        }""",
        "variables": {
            "userId": "integrationtest"
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


def test_my_devices(token):
    print("📱 Testing My Devices...")
    url = f"{BASE_URL}/graphql/auth/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "operationName": "myDevices",
        "query": """query myDevices {
            myDevices {
                id
                deviceName
                deviceId
                lastLogin
                ipAddress
                isActive
            }
        }"""
    }
    response = requests.post(url, json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


def test_create_upload(token):
    print("📤 Testing Create Upload...")
    url = f"{BASE_URL}/graphql/blog/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "operationName": "CreateUpload",
        "query": """mutation CreateUpload($title: String!, $description: String!) {
            createUpload(title: $title, description: $description) {
                success message
                upload { id title }
            }
        }""",
        "variables": {
            "title": "Integration Test Blog",
            "description": "Created via integration test"
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


def test_all_uploads():
    print("📋 Testing All Uploads...")
    url = f"{BASE_URL}/graphql/blog/"
    payload = {"query": "query { allUploads { id title } }"}
    response = requests.post(url, json=payload)
    assert response.status_code in [200, 401]
    data = response.json() if response.status_code == 200 else {}
    print(f"   Response: {data}")
    return data


def test_secure_endpoint_without_token():
    print("🔒 Testing Protected Endpoint Without Token (Should Fail)...")
    url = f"{BASE_URL}/graphql/auth/"
    payload = {
        "operationName": "me",
        "query": "query me { me { success message } }"
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 401
    print(f"   ✅ Correctly returned 401: {response.status_code}")
    return response


def test_verify_email_mutation_with_invalid_token():
    print("📧 Testing Verify Email (with invalid token)...")
    url = f"{BASE_URL}/graphql/auth/"
    payload = {
        "operationName": "verifyEmail",
        "query": """mutation verifyEmail($userId: String!, $token: String!) {
            verifyEmail(userId: $userId, token: $token) {
                success
                message
            }
        }""",
        "variables": {
            "userId": "integrationtest",
            "token": "invalid_token_should_fail"
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🧪 RUNNING INTEGRATION TESTS")
    print("=" * 50 + "\n")
    
    try:
        # Register user
        test_register()
        
        # Manually verify email (for testing)
        test_verify_email_direct()
        
        # Now login should work
        token = test_login()
        
        if not token:
            print("   ❌ Login failed even after verification")
            sys.exit(1)
        
        # Run authenticated tests
        test_get_me(token)
        test_refresh_token(token)
        test_my_devices(token)
        test_logout(token)
        
        # Run public tests
        test_forgot_password()
        test_verify_email_mutation_with_invalid_token()
        test_secure_endpoint_without_token()
        
        # Blog Service Tests
        test_create_upload(token)
        test_all_uploads()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)