import asyncio
import httpx


BASE_URL = "http://localhost:8000/api/v1"

async def verify_backend():
    async with httpx.AsyncClient() as client:
        # 1. Create User
        email = "testuser@example.com"
        password = "testpassword"
        user_data = {
            "email": email,
            "password": password,
            "name": "Test User"
        }
        print(f"Creating user: {email}")
        response = await client.post(f"{BASE_URL}/users", json=user_data)
        if response.status_code == 400 and "already exists" in response.text:
            print("User already exists, proceeding to login.")
        elif response.status_code != 200:
            print(f"Failed to create user: {response.status_code} {response.text}")
            return
        else:
            print("User created successfully.")

        # 2. Login
        print("Logging in...")
        login_data = {
            "username": email,
            "password": password
        }
        response = await client.post(f"{BASE_URL}/auth/login/access-token", data=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} {response.text}")
            return

        token_data = response.json()
        access_token = token_data["access_token"]
        print("Login successful. Token received.")

        # 3. Get User Profile
        print("Getting user profile...")
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await client.get(f"{BASE_URL}/users/me", headers=headers)
        if response.status_code != 200:
            print(f"Failed to get profile: {response.status_code} {response.text}")
            return

        profile = response.json()
        print(f"Profile retrieved: {profile['email']}")

        # 4. Update Profile
        print("Updating profile...")
        update_data = {"name": "Updated Test User"}
        response = await client.put(f"{BASE_URL}/users/me", json=update_data, headers=headers)
        if response.status_code != 200:
            print(f"Failed to update profile: {response.status_code} {response.text}")
            return

        updated_profile = response.json()
        print(f"Profile updated: {updated_profile['name']}")

        print("\nVerification successful!")

if __name__ == "__main__":
    asyncio.run(verify_backend())
