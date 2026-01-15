import asyncio
import httpx

BASE_URL = "http://localhost:8000/api/v1"

async def verify_admin():
    async with httpx.AsyncClient() as client:
        # 1. Create Admin (This endpoint is protected, but for first admin we might need a way or just use the endpoint if it allows creation without auth?
        # Wait, app/api/v1/endpoints/admin.py: create_admin depends on get_current_admin!
        # So we can't create the FIRST admin via API unless we disable auth or have a seed script.
        # However, the requirements said "Create all necessary endpoints for a superuser administrator".
        # Usually first admin is created via CLI or seed.
        # But for this test, I'll check if I can create one.
        # Actually, looking at admin.py, create_admin uses `deps.get_current_admin`. So it's chicken and egg.
        # I should probably create an admin manually in DB or use a script.
        # Or maybe I should modify the code to allow first admin creation?
        # For now, I will try to create one directly in DB using the app code in this script.
        pass

    # Since I can't easily use the API to create the first admin, I will use a direct DB insertion in this script.
    from app.db.session import get_session
    from app.models.admin import Admin
    from app.core.security import get_password_hash
    from sqlmodel import select
    from app.main import app # to ensure models are loaded? No, just import models.
    from app.db.session import engine # need engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker

    print("Creating test admin in DB...")
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    admin_email = "admin@example.com"
    admin_password = "adminsecret"

    async with async_session() as session:
        # Check if exists
        query = select(Admin).where(Admin.email == admin_email)
        result = await session.execute(query)
        admin = result.scalars().first()

        if not admin:
            admin = Admin(
                email=admin_email,
                name="Super Admin",
                password=get_password_hash(admin_password),
                Status=True,
                email_verified=True
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            print(f"Admin created: {admin.email}")
        else:
            print("Admin already exists.")

    async with httpx.AsyncClient() as client:
        # 2. Login as Admin
        print("Logging in as admin...")
        response = await client.post(
            f"{BASE_URL}/auth/login/admin/access-token",
            data={"username": admin_email, "password": admin_password},
        )
        if response.status_code != 200:
            print(f"Failed to login: {response.status_code} {response.text}")
            return

        token = response.json()["access_token"]
        print("Admin login successful. Token received.")
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Get Admin Profile
        print("Getting admin profile...")
        response = await client.get(f"{BASE_URL}/admin/me", headers=headers)
        if response.status_code != 200:
            print(f"Failed to get admin profile: {response.status_code} {response.text}")
            return
        print(f"Admin profile retrieved: {response.json()['email']}")

        # 4. List Users
        print("Listing users...")
        response = await client.get(f"{BASE_URL}/admin/users", headers=headers)
        if response.status_code != 200:
            print(f"Failed to list users: {response.status_code} {response.text}")
            return
        users = response.json()
        print(f"Users listed: {len(users)} found.")

        print("\nAdmin verification successful!")

if __name__ == "__main__":
    asyncio.run(verify_admin())
