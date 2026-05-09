import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_register():
    print("📝 Testing Register...")
    url = f"{BASE_URL}/graphql/auth/"
    payload = {
        "operationName": "RegisterUser",
        "query": """mutation RegisterUser($username: String!, $email: String!, $password: String!) {
            register(username: $username, email: $email, password: $password) {
                success message
            }
        }""",
        "variables": {
            "username": "integrationtest",
            "email": "integration@test.com",
            "password": "Test@123"
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


def test_login():
    print("🔐 Testing Login...")
    url = f"{BASE_URL}/graphql/auth/"
    payload = {
        "operationName": "Login",
        "query": """mutation Login($username: String!, $password: String!, $platform: String!, $deviceName: String!) {
            login(username: $username, password: $password, platform: $platform, deviceName: $deviceName) {
                success accessToken refreshToken
            }
        }""",
        "variables": {
            "username": "integrationtest",
            "password": "Test@123",
            "platform": "web",
            "deviceName": "integration-test"
        }
    }
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data['data']['login']['accessToken']


def test_get_me(token):
    print("👤 Testing Get Me...")
    url = f"{BASE_URL}/graphql/auth/"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": "query { me { id username email } }"}
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
    assert response.status_code == 200
    data = response.json()
    print(f"   Response: {data}")
    return data


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🧪 RUNNING INTEGRATION TESTS")
    print("=" * 50 + "\n")
    
    try:
        test_register()
        token = test_login()
        test_get_me(token)
        test_create_upload(token)
        test_all_uploads()
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)