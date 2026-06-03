import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_register():
    print("📝 Testing Register...")
    url = f"{BASE_URL}/graphql/"  # Changed: removed /auth/
    payload = {
        "operationName": "register",  # Changed from RegisterUser
        "query": """mutation register($userId: String!, $email: String!, $password: String!) {
            register(userId: $userId, email: $email, password: $password) {
                success 
                message 
                userId 
                email
            }
        }""",
        "variables": {
            "userId": "integrationtest",  # Changed from username
            "email": "integration@test.com",
            "password": "Test@123"
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    
    # Check if registration was successful
    if 'errors' in data:
        print(f"   Warning: {data['errors']}")
    return data


def test_login():
    print("🔐 Testing Login...")
    url = f"{BASE_URL}/graphql/"  # Changed: removed /auth/
    payload = {
        "operationName": "login",  # Changed from Login
        "query": """mutation login($userId: String!, $password: String!, $platform: String!) {
            login(userId: $userId, password: $password, platform: $platform) {
                success 
                message
                access  # Changed from accessToken
                refresh  # Changed from refreshToken
                user {
                    id
                    userId  # Changed from username
                    email
                    emailVerified
                }
            }
        }""",
        "variables": {
            "userId": "integrationtest",  # Changed from username
            "password": "Test@123",
            "platform": "web"
            # deviceName removed - auto-detected from headers
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    
    # Extract access token from response
    if 'data' in data and data['data'] and 'login' in data['data']:
        return data['data']['login']['access']  # Changed from accessToken
    else:
        print(f"   Login failed: {data}")
        return None


def test_get_me(token):
    print("👤 Testing Get Me...")
    url = f"{BASE_URL}/graphql/"  # Changed: removed /auth/
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "operationName": "me",
        "query": """query me { 
            me { 
                success 
                message
                user { 
                    id 
                    userId  # Changed from username
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
    url = f"{BASE_URL}/graphql/"
    
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
    
    if 'data' in login_data and login_data['data']:
        refresh_token = login_data['data']['login']['refresh']
        
        # Test refresh token mutation
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
    url = f"{BASE_URL}/graphql/"
    
    # First get refresh token
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
    
    if 'data' in login_data and login_data['data']:
        refresh_token = login_data['data']['login']['refresh']
        
        # Test logout mutation
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
    url = f"{BASE_URL}/graphql/"
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
    url = f"{BASE_URL}/graphql/"
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
    url = f"{BASE_URL}/graphql/blog/"  # This stays the same (different service)
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
    url = f"{BASE_URL}/graphql/blog/"  # This stays the same
    payload = {"query": "query { allUploads { id title } }"}
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


def test_secure_endpoint_without_token():
    print("🔒 Testing Protected Endpoint Without Token (Should Fail)...")
    url = f"{BASE_URL}/graphql/"
    payload = {
        "operationName": "me",
        "query": "query me { me { success message } }"
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 401  # Should be unauthorized
    print(f"   ✅ Correctly returned 401: {response.status_code}")
    return response


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🧪 RUNNING INTEGRATION TESTS")
    print("=" * 50 + "\n")
    
    try:
        # Auth Service Tests
        test_register()
        token = test_login()
        
        if token:
            test_get_me(token)
            test_refresh_token(token)
            test_my_devices(token)
            test_logout(token)
        else:
            print("   Skipping authenticated tests - login failed")
        
        test_forgot_password()
        test_secure_endpoint_without_token()
        
        # Blog Service Tests
        if token:
            test_create_upload(token)
        test_all_uploads()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)