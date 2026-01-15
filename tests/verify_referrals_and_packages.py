import asyncio
import httpx
import uuid
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

# Import app modules for direct DB access
from app.db.session import engine, init_db
from app.models.admin import Admin
from app.models.notification import Notification # Fix for SQLAlchemy relationship error
from app.core.security import get_password_hash

BASE_URL = "http://localhost:8002/api/v1"

async def verify_referrals_and_packages():
    # 0. Initialize DB (Create Tables)
    print("--- Step 0: Initializing DB ---")
    await init_db()

    # 1. Create Admin directly in DB
    print("--- Step 1: Creating Admin ---")
    admin_email = f"admin_{uuid.uuid4()}@example.com"
    admin_password = "password123"

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        admin = Admin(
            email=admin_email,
            name="Test Admin",
            password=get_password_hash(admin_password),
            Status=True,
            email_verified=True
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)
        print(f"Admin created: {admin.email}")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        # 2. Login Admin
        print("\n--- Step 2: Logging in Admin ---")
        response = await client.post(
            "/auth/login/admin/access-token",
            data={"username": admin_email, "password": admin_password}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("Admin logged in.")

        # 3. Register Referrer
        print("\n--- Step 3: Registering Referrer ---")
        referrer_email = f"referrer_{uuid.uuid4()}@example.com"
        referrer_password = "password123"
        response = await client.post("/users", json={
            "email": referrer_email,
            "password": referrer_password,
            "name": "Referrer User"
        })
        assert response.status_code == 200, f"Referrer registration failed: {response.text}"
        referrer_data = response.json()
        referrer_code = referrer_data["referral_code"]
        print(f"Referrer registered. Code: {referrer_code}")

        # Login Referrer
        response = await client.post(
            "/auth/login/access-token",
            data={"username": referrer_email, "password": referrer_password}
        )
        referrer_token = response.json()["access_token"]
        referrer_headers = {"Authorization": f"Bearer {referrer_token}"}

        # 4. Register Referee
        print("\n--- Step 4: Registering Referee ---")
        referee_email = f"referee_{uuid.uuid4()}@example.com"
        referee_password = "password123"
        response = await client.post("/users", json={
            "email": referee_email,
            "password": referee_password,
            "name": "Referee User",
            "referred_by": referrer_code
        })
        assert response.status_code == 200, f"Referee registration failed: {response.text}"
        print("Referee registered with referral code.")

        # Login Referee
        response = await client.post(
            "/auth/login/access-token",
            data={"username": referee_email, "password": referee_password}
        )
        referee_token = response.json()["access_token"]
        referee_headers = {"Authorization": f"Bearer {referee_token}"}

        # 5. Check Initial Stats
        print("\n--- Step 5: Checking Initial Stats ---")
        response = await client.get("/users/referrals", headers=referrer_headers)
        assert response.status_code == 200
        stats = response.json()
        print(f"Stats: {stats}")
        assert stats["total_referrals"] == 1
        assert stats["successful_passes"] == 0
        assert stats["pending_referrals"] == 0 # No prop firm reg yet

        # 6. Create PropFirm Registration (Pending)
        print("\n--- Step 6: Creating PropFirm Registration ---")
        prop_firm_data = {
            "login_id": "12345",
            "password": "pass",
            "propfirm_name": "FTMO",
            "propfirm_website_link": "ftmo.com",
            "server_name": "Server 1",
            "server_type": "MT4",
            "challenges_step": 1,
            "propfirm_account_cost": 100.0,
            "account_size": 10000.0,
            "account_phases": 2,
            "trading_platform": "MT4",
            "propfirm_rules": "No news trading",
            "whatsapp_no": "123",
            "telegram_username": "user",
            "account_status": "pending"
        }
        response = await client.post("/prop-firm", json=prop_firm_data, headers=referee_headers)
        assert response.status_code == 200, f"PropFirm reg failed: {response.text}"
        reg_id = response.json()["id"]
        print(f"PropFirm registration created. ID: {reg_id}")

        # 7. Check Stats (Pending)
        print("\n--- Step 7: Checking Stats (Pending) ---")
        response = await client.get("/users/referrals", headers=referrer_headers)
        stats = response.json()
        print(f"Stats: {stats}")
        assert stats["pending_referrals"] == 1
        assert stats["successful_passes"] == 0

        # 8. Update PropFirm Status to Passed
        print("\n--- Step 8: Updating PropFirm Status to Passed ---")
        response = await client.put(
            f"/admin/prop-firm/{reg_id}",
            json={"account_status": "passed"},
            headers=admin_headers
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        print("PropFirm status updated to passed.")

        # 9. Check Stats (Passed)
        print("\n--- Step 9: Checking Stats (Passed) ---")
        response = await client.get("/users/referrals", headers=referrer_headers)
        stats = response.json()
        print(f"Stats: {stats}")
        assert stats["successful_passes"] == 1
        assert stats["pending_referrals"] == 0
        assert stats["total_earned"] == 2.0 # 2% of 100.0

        # 10. Admin Assign Package
        print("\n--- Step 10: Admin Assigning Package ---")
        package_data = {
            "user_id": referrer_data["id"],
            "package_name": "Premium Plan",
            "amount": 50.0,
            "status": "active"
        }
        response = await client.post("/admin/packages", json=package_data, headers=admin_headers)
        assert response.status_code == 200, f"Package assignment failed: {response.text}"
        print("Package assigned.")

        # 11. Check Packages
        print("\n--- Step 11: Checking Packages ---")
        response = await client.get("/users/packages", headers=referrer_headers)
        assert response.status_code == 200
        packages = response.json()
        print(f"Packages: {packages}")
        assert len(packages) == 1
        assert packages[0]["package_name"] == "Premium Plan"

        print("\n--- Verification Successful! ---")

if __name__ == "__main__":
    asyncio.run(verify_referrals_and_packages())
