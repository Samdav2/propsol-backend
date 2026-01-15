from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.session import get_session
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schema.payment import PaymentCreate, PaymentRead
from app.service.payment_service import PaymentService

router = APIRouter()

@router.post("", response_model=PaymentRead)
async def create_payment(
    payment: PaymentCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PaymentService(session)
    return await service.create_payment(payment, current_user.id, background_tasks)

@router.get("", response_model=List[PaymentRead])
async def read_payments(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PaymentService(session)
    return await service.get_payments_by_user(current_user.id)

@router.get("/{payment_id}", response_model=PaymentRead)
async def read_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PaymentService(session)
    payment = await service.get_payment(payment_id)
    if not payment or payment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.delete("/{payment_id}")
async def delete_payment(
    payment_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    service = PaymentService(session)
    payment = await service.get_payment(payment_id)
    if not payment or payment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Payment not found")
    await service.delete_payment(payment_id)
    return {"ok": True}
