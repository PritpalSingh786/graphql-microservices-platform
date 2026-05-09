import asyncio
import websockets
import json
import requests

BASE_URL = "http://localhost:8000"


def get_token():
    resp = requests.post(
        f"{BASE_URL}/graphql/auth/",
        json={
            "operationName": "Login",
            "query": "mutation Login($username: String!, $password: String!, $platform: String!, $deviceName: String!) { login(username: $username, password: $password, platform: $platform, deviceName: $deviceName) { accessToken } }",
            "variables": {
                "username": "testuser",
                "password": "Test@123",
                "platform": "web",
                "deviceName": "websocket-test"
            }
        }
    )
    return resp.json()['data']['login']['accessToken']


async def test_websocket():
    token = get_token()
    uri = f"ws://localhost:8001/ws/auth/?token={token}"
    
    print(f"🔌 Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            
            await websocket.send(json.dumps({"type": "ping"}))
            print("📤 Sent: ping")
            
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            await websocket.close()
            print("🔌 Connection closed")
            return True
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔌 TESTING WEBSOCKET")
    print("=" * 50 + "\n")
    
    success = asyncio.run(test_websocket())
    
    if success:
        print("\n✅ WEBSOCKET TEST PASSED!")
    else:
        print("\n❌ WEBSOCKET TEST FAILED!")