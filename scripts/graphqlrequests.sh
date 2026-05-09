POST http://localhost:8000/graphql/auth/

Body-raw-JSON

{
  "query": "mutation { register(username: \"duniakegyan\", email: \"duniakegyan@gmail.com\", password: \"admin@123\") { success message } }"
}
In JSON, double quotes inside a string must be escaped with a backslash (\) — 
otherwise the JSON parser can't distinguish between the string delimiter and 
the quote character itself.

2nd way of making request body:-

{
    "operationName": "RegisterUser",
    "query": "mutation RegisterUser($username: String!, $email: String!, $password: String!) { register(username: $username, email: $email, password: $password) { success message } }",
    "variables": {
        "username": "testuser1",
        "email": "test1@test.com",
        "password": "Test@123"
    }
}

{
  "operationName": "VerifyEmail",
  "query": "mutation VerifyEmail($uidb64: String!, $token: String!) { verifyEmail(uidb64: $uidb64, token: $token) { success message } }",
  "variables": {
    "uidb64": "MTA",
    "token": "d88cqu-eba1eda18c73265dc82feb6c57497040"
  }
}


{
  "operationName": "Login",
  "query": "mutation Login($username: String!, $password: String!, $platform: String!, $deviceName: String!) { login(username: $username, password: $password, platform: $platform, deviceName: $deviceName) { success accessToken refreshToken user { id username email } } }",
  "variables": {
    "username": "duniakegyan",
    "password": "admin@123",
    "platform": "web",
    "deviceName": "Postman"
  }
}


{
  "operationName": "GetMe",
  "query": "query GetMe { me { id username email emailVerified dateJoined } }"
}


{
  "operationName": "RefreshToken",
  "query": "mutation RefreshToken($refreshToken: String!, $platform: String!) { refreshToken(refreshToken: $refreshToken, platform: $platform) { success accessToken refreshToken } }",
  "variables": {
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwiZGV2aWNlX2lkIjoiNjg2YmUyMWQtNjlmNi00MTE4LThkZmQtNzYyOGUwZDZlZmI5IiwicGxhdGZvcm0iOiJ3ZWIiLCJ0eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3ODgzMjg3NSwiaWF0IjoxNzc4MjI4MDc1LCJpc3MiOiJteS1hcHAiLCJhdWQiOiJteS11c2VycyIsImp0aSI6IjM5ZTcwMGRjLTUxNzMtNDU3ZS05Nzc2LTZiZTQyY2JlNDBlOSJ9.2g16pvLUujzyx7ExQX3U6lIuLQIPc683UieSN1WiC7s",
    "platform": "web"
  }
}

{
  "operationName": "Logout",
  "query": "mutation Logout($refreshToken: String!) { logout(refreshToken: $refreshToken) { success message } }",
  "variables": {
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwiZGV2aWNlX2lkIjoiNjg2YmUyMWQtNjlmNi00MTE4LThkZmQtNzYyOGUwZDZlZmI5IiwicGxhdGZvcm0iOiJ3ZWIiLCJ0eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3ODgzNTAxMywiaWF0IjoxNzc4MjMwMjEzLCJpc3MiOiJteS1hcHAiLCJhdWQiOiJteS11c2VycyIsImp0aSI6ImVlN2MzMWRmLTIyMDAtNDZhYi1hZWUyLWU5Zjg5NzRiOTZlMiJ9.nCxe7XsMX8VAjGq_yiy51B1265aWL-fSSGPw5xMVqI4"
  }
}

{
  "operationName": "ChangePassword",
  "query": "mutation ChangePassword($oldPassword: String!, $newPassword: String!) { changePassword(oldPassword: $oldPassword, newPassword: $newPassword) { success message } }",
  "variables": {
    "oldPassword": "admin@123",
    "newPassword": "NewPass@123"
  }
}

{
  "operationName": "GetMyDevices",
  "query": "query GetMyDevices { myDevices { id deviceName deviceId lastLogin ipAddress } }"
}

{
  "operationName": "RemoveDevice",
  "query": "mutation RemoveDevice($deviceId: String!) { removeDevice(deviceId: $deviceId) { success message } }",
  "variables": {
    "deviceId": "DEVICE_ID_HERE"
  }
}

{
  "operationName": "RemoveOtherDevices",
  "query": "mutation RemoveOtherDevices { removeOtherDevices { success message count } }"
}

{
  "operationName": "GetMySessions",
  "query": "query GetMySessions { mySessions { deviceId platform createdAt lastAccessed expiresAt } }"
}


{
  "operationName": "PasswordResetRequest",
  "query": "mutation PasswordResetRequest($email: String!) { passwordResetRequest(email: $email) { success message } }",
  "variables": {
    "email": "duniakegyan@gmail.com"
  }
}


{
  "operationName": "SetNewPassword",
  "query": "mutation SetNewPassword($uidb64: String!, $token: String!, $newPassword: String!) { setNewPassword(uidb64: $uidb64, token: $token, newPassword: $newPassword) { success message } }",
  "variables": {
    "uidb64": "YOUR_UID_FROM_EMAIL",
    "token": "YOUR_TOKEN_FROM_EMAIL",
    "newPassword": "NewPass@123"
  }
}


## 🟢 1. CREATE Upload (POST with form-data)

> Mutation must exist in your GraphQL schema (`createUpload`)

**Postman** → `POST` → `Body` → `raw` → `JSON`

```json
{
  "query": "mutation { createUpload(title: "My First Upload" description: "This is a test upload") {upload {id title description images createdAt } } }"
}
```

**Postman** → `POST` → `Body` → `form-data`

| Key        | Type | Value                                                                                                                                                                                               |
| ---------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| operations | text | {"query":"mutation($file: Upload!){ createUpload(title:\"My First Upload\", description:\"Test via Postman\", uploadedImages:[$file]){ upload { id title images } } }","variables":{"file":null}} |
| map        | text | {"0":["variables.file"]}                                                                                                                                                                       |
| 0          | file | *(choose an image file from your system)*                                                                                                                                                           |
                                                                                                                                                                                                                                                                                                             | File |

---

## 🔵 2. READ ALL Uploads (GET all)

**Postman** → `POST` → `Body` → `raw` → `JSON`

```json
{
  "query": "query {  allUploads { id title description images createdAt } }"
}
```

---

## 🔵 3. READ Upload by ID

**Postman** → `POST` → `Body` → `raw` → `JSON`

```json
{
  "query": "query {upload(id: 1) {id title description images createdAt}}",

}
```
---

## ✏️ 4. UPDATE Upload by ID (title and description)

> Mutation must exist in your GraphQL schema (`updateUpload`)

**Postman** → `POST` → `Body` → `raw` → `JSON`

```json
{
  "query": "mutation { updateUpload( id: 1 title: "Updated Title" description: "Updated description here") { upload { id title description images createdAt } } }"
}
```
**Postman** → `POST` → `Body` → `form-data`

| Key        | Type | Value                                                                                                                                                                       |
| ---------- | ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| operations | text | {"query":"mutation($file: Upload!){ updateUpload(id:1, title:\"Updated via Postman\", uploadedImages:[$file]){ upload { id title images } } }","variables":{"file":null}} |
| map        | text | {"0":["variables.file"]}                                                                                                                                                 |
| 0          | file | *(choose an image file from your system)*                                                                                                                                   |


---

## ❌ 5. DELETE Upload by ID

> Mutation must exist in your GraphQL schema (`deleteUpload`)

**Postman** → `POST` → `Body` → `raw` → `JSON`

```json
{
  "query": "mutation deleteUpload($id: ID!) { deleteUpload(id: $id) { success message } }",
  "variables": {
    "id": "1"
  }
}
'''