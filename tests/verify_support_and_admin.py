import asyncio
import httpx
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8001/api/v1"

async def verify_support_and_admin():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Test Support Endpoint
        print("Testing Support Endpoint...")
        support_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "message": "I need help with my account."
        }
        response = await client.post(f"{BASE_URL}/support/", json=support_data)
        if response.status_code != 200:
            print(f"Failed to create support ticket: {response.status_code} {response.text}")
        else:
            print(f"Support ticket created: {response.json()['id']}")

        # 2. Login as Admin
        print("Logging in as admin...")
        response = await client.post(
            f"{BASE_URL}/auth/login/admin/access-token",
            data={"username": "admin@example.com", "password": "adminsecret"},
        )
        if response.status_code != 200:
            print(f"Failed to login admin: {response.status_code} {response.text}")
            return
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("Admin login successful.")

        # 3. Test Admin Get Transactions
        print("Testing Admin Get Transactions...")
        response = await client.get(f"{BASE_URL}/admin/transactions", headers=admin_headers)
        if response.status_code != 200:
            print(f"Failed to get transactions: {response.status_code} {response.text}")
        else:
            print(f"Transactions retrieved: {len(response.json())}")

        # 4. Test Admin Get Prop Firms
        print("Testing Admin Get Prop Firms...")
        response = await client.get(f"{BASE_URL}/admin/prop-firms", headers=admin_headers)
        if response.status_code != 200:
            print(f"Failed to get prop firms: {response.status_code} {response.text}")
        else:
            print(f"Prop firms retrieved: {len(response.json())}")

        # 5. Test Admin Update User
        # First get all users to find one to update
        print("Getting users to find one to update...")
        response = await client.get(f"{BASE_URL}/admin/users", headers=admin_headers)
        if response.status_code != 200:
            print(f"Failed to get users: {response.status_code} {response.text}")
            return

        users = response.json()
        if not users:
            print("No users found to update.")
        else:
            user_to_update = users[0]
            user_id = user_to_update["id"]
            print(f"Updating user {user_id}...")

            update_data = {"name": "Updated Name"}
            response = await client.put(f"{BASE_URL}/admin/users/{user_id}", json=update_data, headers=admin_headers)
            if response.status_code != 200:
                print(f"Failed to update user: {response.status_code} {response.text}")
            else:
                print(f"User updated: {response.json()['name']}")

        print("\nVerification successful!")

if __name__ == "__main__":
    asyncio.run(verify_support_and_admin())
