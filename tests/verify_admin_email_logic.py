import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.admin import Admin
from app.service.notification_service import NotificationService
from app.core.security import get_password_hash

async def verify_admin_email_logic():
    async with AsyncSession(engine) as session:
        # 1. Create dummy admins
        print("Creating dummy admins...")
        active_admin = Admin(
            email="active_admin@test.com",
            name="Active Admin",
            password=get_password_hash("password"),
            Status=True,
            email_verified=True
        )
        inactive_admin = Admin(
            email="inactive_admin@test.com",
            name="Inactive Admin",
            password=get_password_hash("password"),
            Status=False,
            email_verified=True
        )

        session.add(active_admin)
        session.add(inactive_admin)
        await session.commit()
        await session.refresh(active_admin)
        await session.refresh(inactive_admin)
        print(f"Created active admin: {active_admin.email}")
        print(f"Created inactive admin: {inactive_admin.email}")

        try:
            # 2. Test fetching active emails
            print("\nTesting _get_active_admin_emails...")
            service = NotificationService(session)
            emails = await service._get_active_admin_emails()
            print(f"Active emails found: {emails}")

            if "active_admin@test.com" in emails and "inactive_admin@test.com" not in emails:
                print("SUCCESS: Only active admin email fetched.")
            else:
                print("FAILURE: Incorrect emails fetched.")

            # 3. Test sending email (mocked by printing in the service, but we call the method)
            print("\nTesting send_email_to_admins...")
            # We are not actually checking if email is sent because send_email prints to stdout if not configured
            # But we can verify no exceptions are raised
            await service.send_email_to_admins(
                subject="Test Notification",
                template_name="reset_password.html", # Using an existing template
                context={"name": "Admin", "reset_link": "http://test.com"}
            )
            print("send_email_to_admins executed without error.")

        finally:
            # Cleanup
            print("\nCleaning up...")
            await session.delete(active_admin)
            await session.delete(inactive_admin)
            await session.commit()
            print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(verify_admin_email_logic())
