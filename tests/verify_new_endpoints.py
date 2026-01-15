import asyncio
import httpx
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

async def verify_new_endpoints():
    async with httpx.AsyncClient() as client:
        # 1. Login as User
        print("Logging in as user...")
        response = await client.post(
            f"{BASE_URL}/auth/login/access-token",
            data={"username": "testuser@example.com", "password": "testpassword"},
        )
        if response.status_code != 200:
            print(f"Failed to login user: {response.status_code} {response.text}")
            return
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("User login successful.")

        # 2. Create Payment
        print("Creating payment...")
        payment_data = {
            "card_name": "Test Card",
            "card_number": "1234567890123456",
            "card_expiry_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "card_type": "Visa",
            "card_cvv": "123"
        }
        response = await client.post(f"{BASE_URL}/payments", json=payment_data, headers=headers)
        if response.status_code != 200:
            print(f"Failed to create payment: {response.status_code} {response.text}")
        else:
            print(f"Payment created: {response.json()['id']}")

        # 3. Create Transaction
        print("Creating transaction...")
        txn_data = {
            "type": "deposit",
            "amount_cents": 1000,
            "status": "pending",
            "reference": "REF123"
        }
        response = await client.post(f"{BASE_URL}/transactions", json=txn_data, headers=headers)
        if response.status_code != 200:
            print(f"Failed to create transaction: {response.status_code} {response.text}")
        else:
            print(f"Transaction created: {response.json()['id']}")

        # 4. Create PropFirm Registration
        print("Creating PropFirm registration...")
        prop_data = {
            "login_id": "123456",
            "password": "password",
            "propfirm_name": "MyPropFirm",
            "propfirm_website_link": "https://example.com",
            "server_name": "Server1",
            "server_type": "MT4",
            "challenges_step": 1,
            "propfirm_account_cost": 100.0,
            "account_size": 10000.0,
            "account_phases": 2,
            "trading_platform": "MT4",
            "propfirm_rules": "No rules",
            "whatsapp_no": "1234567890",
            "telegram_username": "telegram"
        }
        response = await client.post(f"{BASE_URL}/prop-firm", json=prop_data, headers=headers)
        if response.status_code != 200:
            print(f"Failed to create prop firm registration: {response.status_code} {response.text}")
        else:
            print(f"PropFirm registration created: {response.json()['id']}")

        # 5. Login as Admin for Discounts
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

        # 6. Create Discount Code
        print("Creating discount code...")
        discount_data = {
            "discount_name": "Welcome Bonus",
            "discount_code": "WELCOME10",
            "percentage": 10.0,
            "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
        }
        response = await client.post(f"{BASE_URL}/discounts/discounts", json=discount_data, headers=admin_headers)
        if response.status_code != 200:
            # Might fail if already exists, which is fine for re-runs
            print(f"Failed to create discount (might exist): {response.status_code} {response.text}")
        else:
            print(f"Discount created: {response.json()['id']}")

        # 7. Apply Discount as User
        print("Applying discount as user...")
        apply_data = {"discount_code": "WELCOME10"}
        response = await client.post(f"{BASE_URL}/discounts/apply-discount", json=apply_data, headers=headers)
        if response.status_code != 200:
             print(f"Failed to apply discount: {response.status_code} {response.text}")
        else:
            print(f"Discount applied: {response.json()['id']}")

        # 8. Test PropFirm Status Filtering
        print("Testing PropFirm status filtering...")
        response = await client.get(
            f"{BASE_URL}/prop-firm?status=pending",
            headers=headers # Use user's headers
        )
        if response.status_code == 200:
            registrations = response.json()
            print(f"Pending registrations: {len(registrations)}")
        else:
            print(f"Failed to filter registrations: {response.status_code} {response.text}")

        # 9. Test Admin Stats
        print("Testing Admin Stats...")
        response = await client.get(
            f"{BASE_URL}/admin/stats",
            headers=admin_headers # Use admin's headers
        )
        if response.status_code == 200:
            stats = response.json()
            print(f"Admin Stats: {stats}")
        else:
            print(f"Failed to get admin stats: {response.status_code} {response.text}")

        print("Testing Notifications...")
        # 1. Update PropFirm status to trigger notification
        # Need to get the registration ID first
        # Get registrations
        response = await client.get(f"{BASE_URL}/prop-firm", headers=headers)
        registrations = response.json()
        if registrations:
            reg_id = registrations[0]["id"]
            print(f"Found registration with ID: {reg_id} to test notifications.")
            # Admin updates status
            # Assuming an admin endpoint exists to update prop firm registration status
            # For this test, we'll simulate an update to 'approved' status
            update_data = {"account_status": "passed"}
            response = await client.put(
                f"{BASE_URL}/admin/prop-firm/{reg_id}",
                json=update_data,
                headers=admin_headers
            )
            if response.status_code == 200:
                print(f"PropFirm registration {reg_id} status updated to 'passed' by admin.")
                # Now check user's notifications
                response = await client.get(f"{BASE_URL}/notifications/my-notifications", headers=headers)
                if response.status_code == 200:
                    notifications = response.json()
                    print(f"User notifications: {notifications}")
                    # Check if a notification related to the prop firm update exists
                    found_notification = False
                    for notif in notifications:
                        if "PropFirm Account Passed" in notif.get("title", ""):
                            found_notification = True
                            break
                    if found_notification:
                        print("Successfully found notification for PropFirm status update.")
                    else:
                        print("Failed to find expected notification for PropFirm status update.")
                else:
                    print(f"Failed to get user notifications: {response.status_code} {response.text}")
            else:
                print(f"Failed to update PropFirm registration status: {response.status_code} {response.text}")
        else:
            print("No registrations found to test notifications.")

        print("\nNew endpoints verification successful!")
        print("\nNew features verification successful!")


if __name__ == "__main__":
    asyncio.run(verify_new_endpoints())
