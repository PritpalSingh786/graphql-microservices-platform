import asyncio
import websockets
import json
import requests

BASE_URL = "http://localhost:8000"
WEBSOCKET_URL = "ws://localhost:8001"  # Or your WebSocket port


def get_token():
    """Get access token using updated GraphQL mutation"""
    
    # Updated URL - removed /auth/
    url = f"{BASE_URL}/graphql/"
    
    # Updated payload with new schema
    payload = {
        "operationName": "login",  # Changed from Login
        "query": """mutation login($userId: String!, $password: String!, $platform: String!) {
            login(userId: $userId, password: $password, platform: $platform) {
                success
                access  # Changed from accessToken
                refresh
                user {
                    id
                    userId
                    email
                }
            }
        }""",
        "variables": {
            "userId": "testuser",  # Changed from username
            "password": "Test@123",
            "platform": "web"
            # deviceName removed - auto-detected
        }
    }
    
    try:
        resp = requests.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract access token from response
        if 'data' in data and data['data'] and 'login' in data['data']:
            token = data['data']['login']['access']  # Changed from accessToken
            print(f"   ✅ Token obtained: {token[:50]}...")
            return token
        else:
            print(f"   ❌ Login failed: {data}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error getting token: {e}")
        return None


async def test_websocket_connection(token):
    """Test WebSocket connection with authentication"""
    
    # WebSocket URL with token in query parameter
    uri = f"{WEBSOCKET_URL}/ws/auth/?token={token}"
    
    print(f"🔌 Connecting to {uri}")
    
    try:
        async with websockets.connect(
            uri,
            ping_interval=20,
            ping_timeout=60,
            close_timeout=10
        ) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Test 1: Send ping message
            print("\n📤 Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📥 Received: {response}")
            
            # Test 2: Send test message (if your consumer handles it)
            print("\n📤 Sending test message...")
            test_message = {
                "type": "test",
                "data": {"message": "Hello from WebSocket test"}
            }
            await websocket.send(json.dumps(test_message))
            
            # Try to receive response
            try:
                response2 = await asyncio.wait_for(websocket.recv(), timeout=5)
                print(f"📥 Received: {response2}")
            except asyncio.TimeoutError:
                print("   ⏰ No response to test message (timeout)")
            
            # Test 3: Keep connection alive and listen for notifications
            print("\n👂 Listening for notifications (5 seconds)...")
            try:
                for i in range(5):
                    try:
                        msg = await asyncio.wait_for(websocket.recv(), timeout=1)
                        print(f"   📥 Notification {i+1}: {msg}")
                    except asyncio.TimeoutError:
                        print(f"   ⏰ No message received in second {i+1}")
            except Exception as e:
                print(f"   Listening stopped: {e}")
            
            await websocket.close()
            print("\n🔌 Connection closed gracefully")
            return True
            
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status: {e}")
        return False
    except asyncio.TimeoutError:
        print("❌ Connection timeout")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False


async def test_websocket_multiple_connections():
    """Test multiple WebSocket connections for same user"""
    
    token = get_token()
    if not token:
        print("❌ Cannot test WebSocket without token")
        return False
    
    print("\n📡 Testing multiple connections...")
    
    async def create_connection(connection_id):
        uri = f"{WEBSOCKET_URL}/ws/auth/?token={token}"
        try:
            async with websockets.connect(uri) as websocket:
                print(f"   Connection {connection_id}: Connected")
                await websocket.send(json.dumps({"type": "ping", "id": connection_id}))
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"   Connection {connection_id}: Received {response}")
                return True
        except Exception as e:
            print(f"   Connection {connection_id}: Failed - {e}")
            return False
    
    # Create 3 concurrent connections
    tasks = [create_connection(i) for i in range(3)]
    results = await asyncio.gather(*tasks)
    
    success_count = sum(results)
    print(f"\n   ✅ {success_count}/3 connections successful")
    return success_count > 0


async def test_websocket_invalid_token():
    """Test WebSocket connection with invalid token"""
    
    invalid_token = "invalid.token.here"
    uri = f"{WEBSOCKET_URL}/ws/auth/?token={invalid_token}"
    
    print("\n🔒 Testing with invalid token...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("   ⚠️ Connection succeeded with invalid token (unexpected)")
            await websocket.close()
            return False
    except Exception as e:
        print(f"   ✅ Connection correctly rejected: {e}")
        return True


async def test_websocket_no_token():
    """Test WebSocket connection without token"""
    
    uri = f"{WEBSOCKET_URL}/ws/auth/"
    
    print("\n🔒 Testing without token...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("   ⚠️ Connection succeeded without token (unexpected)")
            await websocket.close()
            return False
    except Exception as e:
        print(f"   ✅ Connection correctly rejected: {e}")
        return True


async def test_websocket_heartbeat():
    """Test WebSocket heartbeat/ping-pong mechanism"""
    
    token = get_token()
    if not token:
        print("❌ Cannot test heartbeat without token")
        return False
    
    uri = f"{WEBSOCKET_URL}/ws/auth/?token={token}"
    
    print("\n💓 Testing WebSocket heartbeat...")
    
    try:
        async with websockets.connect(
            uri,
            ping_interval=5,  # Send ping every 5 seconds
            ping_timeout=10
        ) as websocket:
            print("   Connected, monitoring heartbeat...")
            
            # Wait for 15 seconds to see heartbeats
            for i in range(3):
                await asyncio.sleep(5)
                print(f"   Still connected after {i+1} heartbeats...")
            
            await websocket.close()
            print("   ✅ Heartbeat test passed")
            return True
            
    except Exception as e:
        print(f"   ❌ Heartbeat test failed: {e}")
        return False


def create_test_user_if_not_exists():
    """Helper function to create test user if doesn't exist"""
    
    url = f"{BASE_URL}/graphql/"
    
    # Try to register user (will fail if already exists)
    payload = {
        "operationName": "register",
        "query": """mutation register($userId: String!, $email: String!, $password: String!) {
            register(userId: $userId, email: $email, password: $password) {
                success
                message
            }
        }""",
        "variables": {
            "userId": "testuser",
            "email": "testuser@test.com",
            "password": "Test@123"
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        if 'data' in data and data['data'].get('register', {}).get('success'):
            print("   ✅ Test user created")
        else:
            print("   ℹ️ Test user may already exist")
    except Exception as e:
        print(f"   ⚠️ Could not create test user: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔌 TESTING WEBSOCKET CONNECTIONS")
    print("=" * 60 + "\n")
    
    # Create test user if needed
    create_test_user_if_not_exists()
    
    # Run all tests
    async def run_all_tests():
        results = {}
        
        # Test 1: Basic connection
        print("\n📡 TEST 1: Basic WebSocket Connection")
        token = get_token()
        if token:
            results['basic'] = await test_websocket_connection(token)
        else:
            results['basic'] = False
        
        # Test 2: Multiple connections
        print("\n📡 TEST 2: Multiple Connections")
        results['multiple'] = await test_websocket_multiple_connections()
        
        # Test 3: Invalid token
        print("\n📡 TEST 3: Invalid Token")
        results['invalid_token'] = await test_websocket_invalid_token()
        
        # Test 4: No token
        print("\n📡 TEST 4: No Token")
        results['no_token'] = await test_websocket_no_token()
        
        # Test 5: Heartbeat
        print("\n📡 TEST 5: Heartbeat")
        results['heartbeat'] = await test_websocket_heartbeat()
        
        return results
    
    try:
        results = asyncio.run(run_all_tests())
        
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name:15} : {status}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n🎉 ALL WEBSOCKET TESTS PASSED!")
        else:
            print("\n⚠️ SOME WEBSOCKET TESTS FAILED!")
            
    except Exception as e:
        print(f"\n❌ WEBSOCKET TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()