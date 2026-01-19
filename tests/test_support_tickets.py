"""
Test script for the Support Ticket System.
Tests all ticket and message endpoints for both users and admins.
"""
import asyncio
import httpx
from uuid import UUID

BASE_URL = "http://localhost:8001/api/v1"


async def test_support_tickets():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("SUPPORT TICKET SYSTEM TEST")
        print("=" * 60)

        # ============= Step 1: Login as User =============
        print("\n1. Logging in as user...")
        response = await client.post(
            f"{BASE_URL}/auth/login/access-token",
            data={"username": "testuser@example.com", "password": "testpassword"},
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            print("   Trying to create a test user first...")
            # Try to create test user
            register_data = {
                "email": "testuser@example.com",
                "name": "Test User",
                "password": "testpassword"
            }
            response = await client.post(f"{BASE_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                print("   Created test user, logging in again...")
                response = await client.post(
                    f"{BASE_URL}/auth/login/access-token",
                    data={"username": "testuser@example.com", "password": "testpassword"},
                )
            if response.status_code != 200:
                print(f"   FAILED to login: {response.status_code} - {response.text}")
                return

        user_token = response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        print("   SUCCESS: User logged in")

        # ============= Step 2: Create Support Ticket =============
        print("\n2. Creating support ticket...")
        ticket_data = {
            "subject": "Issue with my account",
            "message": "I am having trouble accessing my dashboard. Please help!",
            "priority": "high"
        }
        response = await client.post(
            f"{BASE_URL}/support/tickets",
            json=ticket_data,
            headers=user_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        ticket = response.json()
        ticket_id = ticket["id"]
        print(f"   SUCCESS: Created ticket ID: {ticket_id}")
        print(f"   Subject: {ticket['subject']}")
        print(f"   Status: {ticket['status']}")
        print(f"   Priority: {ticket['priority']}")
        print(f"   Messages: {len(ticket['messages'])}")

        # ============= Step 3: Get User's Tickets =============
        print("\n3. Getting user's tickets...")
        response = await client.get(
            f"{BASE_URL}/support/tickets",
            headers=user_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        tickets = response.json()
        print(f"   SUCCESS: Found {tickets['total']} ticket(s)")

        # ============= Step 4: Get Ticket Details =============
        print("\n4. Getting ticket details...")
        response = await client.get(
            f"{BASE_URL}/support/tickets/{ticket_id}",
            headers=user_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        ticket_detail = response.json()
        print(f"   SUCCESS: Ticket has {len(ticket_detail['messages'])} message(s)")

        # ============= Step 5: User Sends Follow-up Message =============
        print("\n5. User sending follow-up message...")
        message_data = {"message": "Just wanted to add more details about my issue."}
        response = await client.post(
            f"{BASE_URL}/support/tickets/{ticket_id}/messages",
            json=message_data,
            headers=user_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        message = response.json()
        print(f"   SUCCESS: Message sent by {message['sender_type']}")

        # ============= Step 6: Login as Admin =============
        print("\n6. Logging in as admin...")
        response = await client.post(
            f"{BASE_URL}/auth/login/admin/access-token",
            data={"username": "admin@example.com", "password": "adminsecret"},
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            print("   Skipping admin tests...")
            print("\n" + "=" * 60)
            print("TEST COMPLETED (User tests only)")
            print("=" * 60)
            return

        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("   SUCCESS: Admin logged in")

        # ============= Step 7: Admin Views All Tickets =============
        print("\n7. Admin viewing all tickets...")
        response = await client.get(
            f"{BASE_URL}/support/admin/tickets",
            headers=admin_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        all_tickets = response.json()
        print(f"   SUCCESS: Found {all_tickets['total']} total ticket(s)")

        # ============= Step 8: Admin Filters by Status =============
        print("\n8. Admin filtering tickets by status 'open'...")
        response = await client.get(
            f"{BASE_URL}/support/admin/tickets?status=open",
            headers=admin_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        open_tickets = response.json()
        print(f"   SUCCESS: Found {open_tickets['total']} open ticket(s)")

        # ============= Step 9: Admin Views Ticket Details =============
        print("\n9. Admin viewing ticket details...")
        response = await client.get(
            f"{BASE_URL}/support/admin/tickets/{ticket_id}",
            headers=admin_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        admin_view = response.json()
        print(f"   SUCCESS: Ticket has {len(admin_view['messages'])} messages")
        print(f"   User: {admin_view.get('user_name', 'N/A')} ({admin_view.get('user_email', 'N/A')})")

        # ============= Step 10: Admin Sends Reply =============
        print("\n10. Admin sending reply...")
        reply_data = {"message": "Thank you for contacting us. We are looking into your issue."}
        response = await client.post(
            f"{BASE_URL}/support/admin/tickets/{ticket_id}/messages",
            json=reply_data,
            headers=admin_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        admin_message = response.json()
        print(f"   SUCCESS: Message sent by {admin_message['sender_type']}")

        # ============= Step 11: Admin Updates Status =============
        print("\n11. Admin updating ticket status to 'in_progress'...")
        status_update = {"status": "in_progress"}
        response = await client.patch(
            f"{BASE_URL}/support/admin/tickets/{ticket_id}/status",
            json=status_update,
            headers=admin_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        updated_ticket = response.json()
        print(f"   SUCCESS: Status updated to '{updated_ticket['status']}'")

        # ============= Step 12: Verify Final State =============
        print("\n12. Verifying final ticket state...")
        response = await client.get(
            f"{BASE_URL}/support/tickets/{ticket_id}",
            headers=user_headers
        )
        if response.status_code != 200:
            print(f"   FAILED: {response.status_code} - {response.text}")
            return

        final_ticket = response.json()
        print(f"   SUCCESS: Final verification")
        print(f"   - Subject: {final_ticket['subject']}")
        print(f"   - Status: {final_ticket['status']}")
        print(f"   - Priority: {final_ticket['priority']}")
        print(f"   - Total messages: {len(final_ticket['messages'])}")

        for i, msg in enumerate(final_ticket['messages'], 1):
            print(f"     Message {i}: [{msg['sender_type']}] {msg['message'][:50]}...")

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_support_tickets())
