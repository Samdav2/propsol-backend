import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add app to path
sys.path.append(os.getcwd())

from app.db.session import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.v1.endpoints.admin import list_all_withdrawals
from app.api.v1.endpoints.wallet import get_pending_withdrawals
from app.models.admin import Admin

async def main():
    async with AsyncSession(engine) as session:
        print("Calling list_all_withdrawals...")

        # Mock admin
        admin = Admin(id="admin_id", email="admin@example.com")

        try:
            response = await list_all_withdrawals(
                status="pending",
                limit=10,
                page=0,
                current_admin=admin,
                session=session
            )

            print(f"Response (list_all): {response}")
            print(f"Total count: {response['total_count']}")
            print(f"Withdrawals: {len(response['withdrawals'])}")
            for w in response['withdrawals']:
                print(f" - {w.id}: {w.status} (${w.amount})")

            print("\nCalling get_pending_withdrawals...")
            response_pending = await get_pending_withdrawals(
                db=session,
                current_admin=admin
            )
            print(f"Response (pending): {response_pending}")
            print(f"Total count: {response_pending.total_count}")
            for w in response_pending.withdrawals:
                print(f" - {w.id}: {w.status} (${w.amount})")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
