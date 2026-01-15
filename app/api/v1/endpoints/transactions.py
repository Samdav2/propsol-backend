from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schema.transactions import TransactionCreate, TransactionRead
from app.service.transactions_service import TransactionService

router = APIRouter()

@router.post("", response_model=TransactionRead)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = TransactionService(session)
    return await service.create_transaction(transaction, current_user.id)

@router.get("", response_model=List[TransactionRead])
async def read_transactions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = TransactionService(session)
    return await service.get_transactions_by_user(current_user.id)

@router.get("/{transaction_id}", response_model=TransactionRead)
async def read_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = TransactionService(session)
    transaction = await service.get_transaction(transaction_id)
    if not transaction or transaction.users_id != current_user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction
