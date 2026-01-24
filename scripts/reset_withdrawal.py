import asyncio
import sys
import os
from sqlalchemy import text
from sqlmodel import select

# Add app to path
sys.path.append(os.getcwd())

from app.db.session import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.wallet import WithdrawalRequest, WithdrawalStatus

async def main():
    async with AsyncSession(engine) as session:
        print("--- Resetting Withdrawal Status ---")

        # Delete all withdrawals
        stmt = text("DELETE FROM withdrawal_request")
        await session.exec(stmt)
        await session.commit()
        print("Deleted existing withdrawals.")

        # Create a new withdrawal
        # We need a wallet first
        from app.models.wallet import Wallet, PaymentMethod
        wallet_query = select(Wallet)
        wallet = (await session.exec(wallet_query)).first()

        if wallet:
            withdrawal = WithdrawalRequest(
                wallet_id=wallet.id,
                amount=100.00,
                payment_method=PaymentMethod.crypto,
                status=WithdrawalStatus.pending,
                crypto_wallet_address="0x123",
                crypto_network="eth",
                crypto_currency="eth"
            )
            session.add(withdrawal)
            await session.commit()
            print(f"Created new withdrawal with ID: {withdrawal.id}")
        else:
            print("No wallet found to create withdrawal.")

if __name__ == "__main__":
    asyncio.run(main())
