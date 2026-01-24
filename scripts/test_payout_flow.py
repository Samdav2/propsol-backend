import asyncio
import sys
import os
from decimal import Decimal
from sqlmodel import select

# Add app to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.config import settings
from app.service.wallet_service import WalletService
from app.repository.user_repo import UserRepository
from app.models.user import User
from app.schema.wallet import WithdrawalCreate, PaymentMethod, CryptoDetails

async def main():
    print("Starting script...")

    # Create engine locally
    connect_args = {}
    if settings.db_uri.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_async_engine(
        settings.db_uri,
        echo=True,
        future=True,
        connect_args=connect_args,
    )

    async with AsyncSession(engine) as session:
        print("Session created")

        # Test simple query
        try:
            print("Testing simple query...")
            result = await session.exec(select(1))
            print(f"Simple query result: {result.first()}")
        except Exception as e:
            print(f"Simple query failed: {e}")
            import traceback
            traceback.print_exc()
            return

        user_repo = UserRepository(User, session)
        wallet_service = WalletService(session)

        email = "adoxop1@gmail.com"
        print(f"Finding user {email}...")
        try:
            user = await user_repo.get_by_email(email)
            print("User query finished")
        except Exception as e:
            print(f"Error finding user: {e}")
            import traceback
            traceback.print_exc()
            return

        if not user:
            print(f"User {email} not found!")
            return

        print(f"User found: {user.id}")

        # Get wallet
        print("Getting wallet...")
        try:
            wallet = await wallet_service.get_wallet(user.id)
            print(f"Current Balance: ${wallet.available_balance}")
        except Exception as e:
            print(f"Error getting wallet: {e}")
            import traceback
            traceback.print_exc()
            return

        # Add balance
        amount_to_add = Decimal("200.00")
        print(f"Adding ${amount_to_add} to available balance...")
        await wallet_service.wallet_repo.update_balances(
            wallet.id,
            available_delta=amount_to_add
        )

        # Refresh wallet
        wallet = await wallet_service.get_wallet(user.id)
        print(f"New Balance: ${wallet.available_balance}")

        # Create withdrawal request
        print("Creating withdrawal request for $100...")
        withdrawal_data = WithdrawalCreate(
            amount=100.00,
            payment_method=PaymentMethod.crypto,
            crypto_details=CryptoDetails(
                wallet_address="0x71C7656EC7ab88b098defB751B7401B5f6d8976F", # Valid looking ETH address
                network="eth",
                currency="eth"
            )
        )

        # Mock background tasks
        from fastapi import BackgroundTasks
        bg_tasks = BackgroundTasks()

        try:
            from unittest.mock import patch, AsyncMock

            with patch("app.service.nowpayments_service.NOWPaymentsService.validate_address", new_callable=AsyncMock) as mock_validate:
                mock_validate.return_value = True

                withdrawal = await wallet_service.request_withdrawal(
                    user_id=user.id,
                    withdrawal_data=withdrawal_data,
                    background_tasks=bg_tasks
                )

                print(f"Withdrawal created successfully!")
                print(f"ID: {withdrawal.id}")
                print(f"Amount: ${withdrawal.amount}")
                print(f"Status: {withdrawal.status}")
                print(f"Address: {withdrawal.crypto_wallet_address}")

        except Exception as e:
            print(f"Error creating withdrawal: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
