import asyncio
import sys
import os
from sqlalchemy import text
from sqlmodel import select

# Add app to path
sys.path.append(os.getcwd())

from app.db.session import engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.wallet import WithdrawalRequest

async def main():
    async with AsyncSession(engine) as session:
        print("--- Debugging UUIDs ---")

        # 1. Fetch all using SQLModel
        print("\n1. Fetching all via SQLModel:")
        query = select(WithdrawalRequest)
        result = await session.exec(query)
        withdrawals = result.all()
        for w in withdrawals:
            print(f"ID: {w.id} (Type: {type(w.id)})")
            print(f"Status: {w.status}")
            print(f"ID str: {str(w.id)}")
            print(f"ID repr: {repr(w.id)}")

            # Try to fetch this specific ID back
            print(f"  Fetching back by ID object: {w.id}")
            q2 = select(WithdrawalRequest).where(WithdrawalRequest.id == w.id)
            r2 = await session.exec(q2)
            found = r2.first()
            print(f"  Found: {found is not None}")

            # Try fetching by string
            print(f"  Fetching back by string: {str(w.id)}")
            q3 = select(WithdrawalRequest).where(text("id = :uid")).params(uid=str(w.id))
            r3 = await session.exec(q3)
            found3 = r3.first()
            print(f"  Found (text): {found3 is not None}")

        # 2. Raw SQL inspection
        print("\n2. Raw SQL Inspection:")
        result = await session.exec(text("SELECT id FROM withdrawal_request"))
        rows = result.all()
        for row in rows:
            print(f"Raw ID: {row[0]} (Type: {type(row[0])})")

if __name__ == "__main__":
    asyncio.run(main())
