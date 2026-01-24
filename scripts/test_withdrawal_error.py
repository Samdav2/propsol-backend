import asyncio
import sys
import os
from uuid import UUID
from decimal import Decimal

# Add app to path
sys.path.append(os.getcwd())

from app.db.session import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.service.wallet_service import WalletService
from app.schema.wallet import WithdrawalCreate, PaymentMethod, CryptoDetails
from app.models.user import User
from app.models.wallet import Wallet
from fastapi import BackgroundTasks

async def main():
    async with AsyncSession(engine) as session:
        print("--- Testing Withdrawal Request Error ---")

        # 1. Get a user
        from sqlmodel import select
        user = (await session.exec(select(User).limit(1))).first()
        if not user:
            print("No user found.")
            return

        user_id = user.id
        print(f"User: {user.email}")

        # 2. Ensure wallet has balance
        service = WalletService(session)
        wallet = await service.get_wallet(user.id)

        # Add fake balance
        await service.wallet_repo.update_balances(wallet.id, available_delta=Decimal("200.00"))
        print("Added balance to wallet.")

        # 3. Create withdrawal request that triggers validation
        withdrawal_data = WithdrawalCreate(
            amount=150.00,
            payment_method=PaymentMethod.crypto,
            crypto_details=CryptoDetails(
                wallet_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F",
                network="eth",
                currency="eth"
            )
        )

        bg_tasks = BackgroundTasks()

        try:
            print("Requesting withdrawal...")
            withdrawal = await service.request_withdrawal(
                user_id=user_id,
                withdrawal_data=withdrawal_data,
                background_tasks=bg_tasks
            )
            print(f"Withdrawal created: {withdrawal.id}")
        except Exception as e:
            print(f"Caught expected error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
