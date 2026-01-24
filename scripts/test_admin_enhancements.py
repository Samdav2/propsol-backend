import asyncio
import sys
import os
from uuid import UUID

# Add app to path
sys.path.append(os.getcwd())

from app.db.session import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.api.v1.endpoints.admin import list_all_withdrawals, update_withdrawal_status
from app.models.admin import Admin
from app.schema.wallet import WithdrawalStatusUpdate
from app.models.wallet import WithdrawalStatus
from app.repository.wallet_repo import WalletRepository
import sys
print(f"DEBUG: WalletRepository file: {sys.modules[WalletRepository.__module__].__file__}")

async def main():
    async with AsyncSession(engine) as session:
        print("--- Testing List Withdrawals (Enriched) ---")

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

            print(f"Total count: {response['total_count']}")
            withdrawal_id = None
            for w in response['withdrawals']:
                print(f" - ID: {w.id}")
                print(f"   Amount: ${w.amount}")
                print(f"   User: {w.user_name} ({w.user_email})")
                print(f"   Status: {w.status}")
                withdrawal_id = w.id

            if not withdrawal_id:
                # Fallback: get any withdrawal
                from app.models.wallet import WithdrawalRequest
                from sqlmodel import select
                query = select(WithdrawalRequest)
                result = await session.exec(query)
                w = result.first()
                if w:
                    withdrawal_id = w.id
                    print(f"Fallback: Found withdrawal {withdrawal_id}")

            if withdrawal_id:
                print("\n--- Testing Rejection Reason ---")
                print(f"Rejecting withdrawal {withdrawal_id}...")

                update_data = WithdrawalStatusUpdate(
                    status=WithdrawalStatus.rejected,
                    admin_notes="Test rejection",
                    rejection_reason="Invalid wallet address provided"
                )

                updated_withdrawal = await update_withdrawal_status(
                    withdrawal_id=withdrawal_id,
                    status_update=update_data,
                    background_tasks=None, # Mock background tasks
                    current_admin=admin,
                    session=session
                )

                print(f"Updated Status: {updated_withdrawal.status}")
                print(f"Rejection Reason: {updated_withdrawal.rejection_reason}")

                # Revert status for future tests
                print("\n--- Reverting Status ---")
                revert_data = WithdrawalStatusUpdate(
                    status=WithdrawalStatus.pending,
                    admin_notes="Reverted test"
                )
                await update_withdrawal_status(
                    withdrawal_id=withdrawal_id,
                    status_update=revert_data,
                    background_tasks=None,
                    current_admin=admin,
                    session=session
                )
                print("Reverted to pending.")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
